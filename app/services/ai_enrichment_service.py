"""AI enrichment service - orchestrates LLM extraction and ML scoring"""
import logging
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.orm import LeadORM, LeadSnapshotORM
from app.ai.llm_extractor import LLMExtractor
from app.ai.scoring import LeadScorer
from app.services.enrichment_service import EnrichmentService

logger = logging.getLogger(__name__)


class AIEnrichmentService:
    """Service to enrich leads with AI/ML"""
    
    def __init__(self, llm_extractor: Optional[LLMExtractor] = None, scorer=None):
        """
        Initialize AI enrichment service
        
        Args:
            llm_extractor: LLM extractor instance (optional, falls back to regex if None)
            scorer: Lead scorer (optional, defaults to rule-based LeadScorer)
        """
        self.llm_extractor = llm_extractor
        self.scorer = scorer or LeadScorer()
    
    async def enrich_lead(
        self,
        db: AsyncSession,
        lead_orm: LeadORM,
        force_llm: bool = False,
    ) -> bool:
        """
        Enrich a lead using AI/ML
        
        Args:
            db: Database session
            lead_orm: Lead ORM object to enrich
            force_llm: Force LLM extraction even if already enriched
        
        Returns:
            True if enrichment succeeded, False otherwise
        """
        try:
            # Load website text from snapshots
            website_text = await self._load_website_text(db, lead_orm)
            if not website_text:
                logger.warning(f"No website text found for lead {lead_orm.id}")
                lead_orm.ai_status = "failed"
                lead_orm.ai_last_error = "No website text available"
                await db.flush()
                return False
            
            # Update AI status
            lead_orm.ai_status = "processing"
            await db.flush()
            
            # Step 1: LLM extraction (if enabled and not already done)
            if self.llm_extractor and (force_llm or not lead_orm.meta.get("ai_extracted")):
                await self._llm_extract(db, lead_orm, website_text)
            
            # Step 2: Calculate quality score
            await self._calculate_score(lead_orm)
            
            # Step 3: Extract tags from metadata
            await self._extract_tags(lead_orm)
            
            # Mark as successful
            lead_orm.ai_status = "success"
            lead_orm.ai_processed_at = datetime.utcnow()
            if lead_orm.meta:
                lead_orm.meta["ai_extracted"] = True
            
            await db.flush()
            logger.info(f"Successfully enriched lead {lead_orm.id}")
            return True
        
        except Exception as e:
            logger.error(f"Error enriching lead {lead_orm.id}: {e}", exc_info=True)
            lead_orm.ai_status = "failed"
            lead_orm.ai_last_error = str(e)[:500]  # Truncate long errors
            await db.flush()
            return False
    
    async def _load_website_text(self, db: AsyncSession, lead_orm: LeadORM) -> Optional[str]:
        """Load website text from snapshots"""
        stmt = select(LeadSnapshotORM).where(
            LeadSnapshotORM.lead_id == lead_orm.id
        ).order_by(
            LeadSnapshotORM.page_type.asc(),  # Order: home, contact, about
            LeadSnapshotORM.created_at.desc()
        )
        
        result = await db.execute(stmt)
        snapshots = result.scalars().all()
        
        if not snapshots:
            return None
        
        # Combine text from multiple pages
        # Prefer: contact > about > home
        page_order = {"contact": 0, "about": 1, "home": 2, "other": 3}
        sorted_snapshots = sorted(
            snapshots,
            key=lambda s: (page_order.get(s.page_type.lower(), 99), s.created_at)
        )
        
        # Build text blob
        text_parts = []
        for snapshot in sorted_snapshots:
            if snapshot.text:
                text_parts.append(f"[PAGE] {snapshot.page_type}\n{snapshot.text}")
        
        return "\n\n".join(text_parts) if text_parts else None
    
    async def _llm_extract(self, db: AsyncSession, lead_orm: LeadORM, website_text: str):
        """Extract information using LLM"""
        if not self.llm_extractor:
            return
        
        try:
            # Extract using LLM
            extracted_data = await self.llm_extractor.extract(website_text)
            
            if not extracted_data:
                logger.warning(f"LLM extraction returned no data for lead {lead_orm.id}")
                return
            
            # Merge extracted data into lead
            # Convert ORM to model for merging
            from app.core.models import Lead
            lead_model = self._orm_to_model(lead_orm)
            lead_model = self.llm_extractor.merge_with_lead(lead_model, extracted_data)
            
            # Update ORM from model
            self._model_to_orm(lead_model, lead_orm)
            
            logger.info(f"LLM extraction completed for lead {lead_orm.id}")
        
        except Exception as e:
            logger.error(f"Error in LLM extraction for lead {lead_orm.id}: {e}", exc_info=True)
            # Don't fail the whole enrichment, just log the error
    
    async def _calculate_score(self, lead_orm: LeadORM):
        """Calculate quality score"""
        try:
            # Convert ORM to model for scoring
            from app.core.models import Lead
            lead_model = self._orm_to_model(lead_orm)
            
            # Calculate score
            score, label = self.scorer.score_and_label(lead_model)
            
            # Update ORM
            lead_orm.quality_score = score
            lead_orm.quality_label = label
        
        except Exception as e:
            logger.error(f"Error calculating score for lead {lead_orm.id}: {e}", exc_info=True)
    
    async def _extract_tags(self, lead_orm: LeadORM):
        """Extract tags from metadata and other fields"""
        tags = set(lead_orm.tags or [])
        
        # Extract from metadata.services
        if lead_orm.meta:
            services = lead_orm.meta.get("services", [])
            for service in services:
                # Normalize service to tag format
                tag = service.lower().replace(" ", "_").replace("-", "_")
                tags.add(tag)
        
        # Extract from service_tags
        if lead_orm.service_tags:
            for tag in lead_orm.service_tags:
                tags.add(tag.lower().replace(" ", "_"))
        
        # Add quality-based tags
        if lead_orm.quality_label:
            tags.add(f"quality_{lead_orm.quality_label}")
        
        # Add feature tags
        if lead_orm.has_email:
            tags.add("has_email")
        if lead_orm.has_phone:
            tags.add("has_phone")
        if lead_orm.has_social:
            tags.add("has_social")
        if lead_orm.cms:
            tags.add(f"cms_{lead_orm.cms}")
        
        lead_orm.tags = sorted(list(tags))
    
    def _orm_to_model(self, lead_orm: LeadORM):
        """Convert ORM to dataclass model"""
        from app.core.models import Lead
        return Lead(
            id=lead_orm.id,
            name=lead_orm.name,
            niche=lead_orm.niche,
            website=lead_orm.website,
            emails=lead_orm.emails or [],
            phones=lead_orm.phones or [],
            address=lead_orm.address,
            source=lead_orm.source,
            city=lead_orm.city,
            country=lead_orm.country,
            job_id=lead_orm.job_id,
            cms=lead_orm.cms,
            tech_stack=lead_orm.tech_stack or [],
            third_party_widgets=lead_orm.third_party_widgets or [],
            social_links=lead_orm.social_links or {},
            company_size=lead_orm.company_size,
            revenue_band=lead_orm.revenue_band,
            is_multi_location=lead_orm.is_multi_location,
            branch_locations=lead_orm.branch_locations or [],
            service_tags=lead_orm.service_tags or [],
            audience_tags=lead_orm.audience_tags or [],
            contact_person_name=lead_orm.contact_person_name,
            contact_person_role=lead_orm.contact_person_role,
            contact_person_email=lead_orm.contact_person_email,
            outreach_notes=lead_orm.outreach_notes,
            status=lead_orm.status.value if lead_orm.status else "new",
            assigned_to_user_id=lead_orm.assigned_to_user_id,
            has_email=lead_orm.has_email,
            has_phone=lead_orm.has_phone,
            has_social=lead_orm.has_social,
            quality_score=float(lead_orm.quality_score) if lead_orm.quality_score else None,
            metadata=lead_orm.meta or {},
        )
    
    def _model_to_orm(self, lead_model, lead_orm: LeadORM):
        """Update ORM from dataclass model"""
        # Update fields that might have changed from LLM extraction
        if lead_model.name and not lead_orm.name:
            lead_orm.name = lead_model.name
        if lead_model.emails:
            lead_orm.emails = list(set(lead_orm.emails or []) | set(lead_model.emails))
        if lead_model.phones:
            lead_orm.phones = list(set(lead_orm.phones or []) | set(lead_model.phones))
        if lead_model.address and not lead_orm.address:
            lead_orm.address = lead_model.address
        if lead_model.city and not lead_orm.city:
            lead_orm.city = lead_model.city
        if lead_model.country and not lead_orm.country:
            lead_orm.country = lead_model.country
        
        # Update metadata
        if lead_model.metadata:
            if not lead_orm.meta:
                lead_orm.meta = {}
            lead_orm.meta.update(lead_model.metadata)
        
        # Update social links
        if lead_model.social_links:
            if not lead_orm.social_links:
                lead_orm.social_links = {}
            lead_orm.social_links.update({k: v for k, v in lead_model.social_links.items() if v})
        
        # Update outreach notes
        if lead_model.outreach_notes:
            existing = lead_orm.outreach_notes or ""
            if lead_model.outreach_notes not in existing:
                lead_orm.outreach_notes = f"{existing}\n{lead_model.outreach_notes}".strip()

