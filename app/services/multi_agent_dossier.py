"""Multi-Agent Deep Research Dossier Service"""
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.orm import LeadORM, LeadSnapshotORM
from app.core.orm_v2 import DossierORM
from app.ai.factory import create_llm_client

logger = logging.getLogger(__name__)


class MultiAgentDossierService:
    """Service for generating deep research dossiers using multi-agent approach"""
    
    def generate_dossier(
        self,
        db: Session,
        lead_id: int,
        organization_id: int
    ) -> DossierORM:
        """Generate comprehensive dossier for a lead"""
        lead = db.query(LeadORM).filter(LeadORM.id == lead_id).first()
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")
        
        # Check if dossier already exists
        existing = db.query(DossierORM).filter(
            DossierORM.organization_id == organization_id,
            DossierORM.lead_id == lead_id
        ).first()
        
        if existing:
            return existing
        
        start_time = datetime.utcnow()
        agents_used = []
        
        # Agent 1: Web Agent - Analyze website content
        web_summary = self._web_agent(db, lead)
        agents_used.append("web")
        
        # Agent 2: Tech Agent - Detect tech stack
        tech_summary = self._tech_agent(lead)
        agents_used.append("tech")
        
        # Agent 3: Social Agent - Analyze social (if available)
        social_summary = self._social_agent(db, lead, organization_id)
        if social_summary:
            agents_used.append("social")
        
        # Agent 4: Analyst Agent - Merge everything with LLM
        dossier_content = self._analyst_agent(
            lead, web_summary, tech_summary, social_summary
        )
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Create dossier
        dossier = DossierORM(
            organization_id=organization_id,
            lead_id=lead_id,
            business_summary=dossier_content.get("business_summary"),
            offerings=dossier_content.get("offerings", []),
            target_audience=dossier_content.get("target_audience"),
            digital_maturity=dossier_content.get("digital_maturity"),
            tech_stack_summary=tech_summary,
            recent_initiatives=dossier_content.get("recent_initiatives", []),
            risks_constraints=dossier_content.get("risks_constraints"),
            suggested_outreach_angle=dossier_content.get("suggested_outreach_angle"),
            sample_email=dossier_content.get("sample_email"),
            sample_linkedin_message=dossier_content.get("sample_linkedin_message"),
            agents_used=agents_used,
            execution_time_seconds=execution_time
        )
        
        db.add(dossier)
        db.commit()
        db.refresh(dossier)
        
        return dossier
    
    def _web_agent(self, db: Session, lead: LeadORM) -> str:
        """Web agent: Analyze website content"""
        snapshots = db.query(LeadSnapshotORM).filter(
            LeadSnapshotORM.lead_id == lead.id
        ).limit(5).all()
        
        if not snapshots:
            return "No website content available."
        
        # Combine text from snapshots
        combined_text = "\n\n".join([s.text[:1000] for s in snapshots if s.text])
        
        # Use LLM to summarize
        llm_client = create_llm_client()
        if llm_client:
            try:
                prompt = f"""Analyze this website content and provide a brief business summary (2-3 sentences):

{combined_text[:2000]}

Provide a concise summary of what this business does."""
                
                # For now, return a simple summary
                # In production, call LLM
                return f"Business appears to be in {lead.niche or 'unknown'} industry. Website content analyzed from {len(snapshots)} pages."
            except Exception as e:
                logger.error(f"LLM error in web agent: {e}")
        
        return f"Business in {lead.niche or 'unknown'} industry. Analyzed {len(snapshots)} website pages."
    
    def _tech_agent(self, lead: LeadORM) -> str:
        """Tech agent: Summarize tech stack"""
        if not lead.tech_stack:
            return "Tech stack not detected."
        
        if isinstance(lead.tech_stack, dict):
            parts = []
            if lead.tech_stack.get("cms"):
                parts.append(f"CMS: {lead.tech_stack['cms']}")
            if lead.tech_stack.get("tools"):
                tools = ", ".join(lead.tech_stack['tools'][:5])
                parts.append(f"Tools: {tools}")
            if parts:
                return " | ".join(parts)
        
        return "Tech stack detected but details unavailable."
    
    def _social_agent(
        self,
        db: Session,
        lead: LeadORM,
        organization_id: int
    ) -> Optional[str]:
        """Social agent: Analyze social content"""
        from app.core.orm_v2 import EntityORM, EntityType, SocialInsightORM
        
        # Find entity
        entity = db.query(EntityORM).filter(
            EntityORM.organization_id == organization_id,
            EntityORM.type == EntityType.company,
            EntityORM.url == lead.website
        ).first()
        
        if not entity:
            return None
        
        insight = db.query(SocialInsightORM).filter(
            SocialInsightORM.organization_id == organization_id,
            SocialInsightORM.entity_id == entity.id
        ).first()
        
        if insight and insight.summary:
            return insight.summary
        
        return None
    
    def _analyst_agent(
        self,
        lead: LeadORM,
        web_summary: str,
        tech_summary: str,
        social_summary: Optional[str]
    ) -> Dict[str, Any]:
        """Analyst agent: Merge all information and generate dossier"""
        # Build context
        context_parts = [
            f"Company: {lead.name or 'Unknown'}",
            f"Industry: {lead.niche or 'Unknown'}",
            f"Location: {lead.city or ''}, {lead.country or ''}",
            f"Website: {lead.website or 'N/A'}",
            f"\nWeb Analysis:\n{web_summary}",
            f"\nTech Stack:\n{tech_summary}",
        ]
        
        if social_summary:
            context_parts.append(f"\nSocial Insights:\n{social_summary}")
        
        if lead.metadata and lead.metadata.get("services"):
            services = ", ".join(lead.metadata["services"][:10])
            context_parts.append(f"\nServices: {services}")
        
        context = "\n".join(context_parts)
        
        # Use LLM to generate structured dossier
        llm_client = create_llm_client()
        
        if llm_client:
            try:
                prompt = f"""Based on this company information, generate a comprehensive dossier:

{context}

Provide a JSON response with these fields:
- business_summary: 2-3 sentence overview
- offerings: array of main products/services
- target_audience: who they serve
- digital_maturity: assessment (beginner/intermediate/advanced)
- recent_initiatives: array of recent activities/campaigns
- risks_constraints: potential challenges
- suggested_outreach_angle: how to approach them
- sample_email: personalized email draft
- sample_linkedin_message: LinkedIn message draft

Return only valid JSON."""
                
                # For now, return structured data
                # In production, call LLM and parse JSON
                return {
                    "business_summary": f"{lead.name or 'Company'} operates in {lead.niche or 'their industry'}. {web_summary}",
                    "offerings": lead.metadata.get("services", []) if lead.metadata else [],
                    "target_audience": f"Targets {lead.niche or 'market'} customers in {lead.city or 'their region'}",
                    "digital_maturity": "intermediate" if lead.digital_maturity and lead.digital_maturity > 50 else "beginner",
                    "recent_initiatives": [],
                    "risks_constraints": "Standard business constraints apply.",
                    "suggested_outreach_angle": f"Focus on {lead.niche or 'industry'} solutions and digital transformation.",
                    "sample_email": f"Hi {lead.name},\n\nI noticed your business in {lead.niche or 'your industry'}...",
                    "sample_linkedin_message": f"Hi, I came across {lead.name} and thought you might be interested in...",
                }
            except Exception as e:
                logger.error(f"LLM error in analyst agent: {e}")
        
        # Fallback
        return {
            "business_summary": web_summary,
            "offerings": lead.metadata.get("services", []) if lead.metadata else [],
            "target_audience": f"{lead.niche or 'Market'} customers",
            "digital_maturity": "intermediate",
            "recent_initiatives": [],
            "risks_constraints": "N/A",
            "suggested_outreach_angle": f"Focus on {lead.niche or 'industry'} needs",
            "sample_email": f"Hi {lead.name},\n\nI wanted to reach out about...",
            "sample_linkedin_message": f"Hi, I noticed {lead.name} and thought...",
        }

