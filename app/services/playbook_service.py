"""AI Playbook generation service"""
import logging
from typing import Dict, Optional
from sqlalchemy.orm import Session
import json

from app.core.orm import LeadORM, PlaybookORM

logger = logging.getLogger(__name__)


class PlaybookService:
    """Service for generating AI market playbooks"""
    
    @staticmethod
    def generate_playbook(
        db: Session,
        org_id: int,
        niche: str,
        location: str
    ) -> Optional[PlaybookORM]:
        """
        Generate or retrieve a playbook for a niche+location
        
        Returns:
            PlaybookORM instance or None if generation failed
        """
        # Check if playbook already exists
        existing = db.query(PlaybookORM).filter(
            PlaybookORM.organization_id == org_id,
            PlaybookORM.niche == niche,
            PlaybookORM.location == location
        ).first()
        
        if existing:
            return existing
        
        # Get leads for this niche+location
        # Match by niche and location (location can be None)
        query = db.query(LeadORM).filter(
            LeadORM.organization_id == org_id,
            LeadORM.niche == niche
        )
        if location:
            query = query.filter(LeadORM.location == location)
        else:
            query = query.filter(LeadORM.location.is_(None))
        
        leads = query.limit(100).all()
        
        if len(leads) < 10:
            logger.warning(f"Not enough leads ({len(leads)}) to generate playbook for {niche} in {location}")
            return None
        
        # Compute stats
        stats = PlaybookService._compute_stats(leads)
        
        # Prepare sample leads
        sample_leads = []
        for lead in leads[:50]:
            sample_leads.append({
                "name": lead.name or "Unknown",
                "city": lead.city or "",
                "country": lead.country or "",
                "services": lead.service_tags or [],
                "tags": lead.tags or [],
                "smart_score": float(lead.smart_score) if lead.smart_score else None,
                "has_email": bool(lead.emails and len(lead.emails) > 0),
                "has_phone": bool(lead.phones and len(lead.phones) > 0),
            })
        
        # Generate playbook text using LLM
        playbook_text = PlaybookService._generate_playbook_text(
            niche, location, stats, sample_leads
        )
        
        if not playbook_text:
            return None
        
        # Create playbook
        playbook = PlaybookORM(
            organization_id=org_id,
            niche=niche,
            location=location,
            text=playbook_text,
            stats=stats,
        )
        db.add(playbook)
        db.commit()
        db.refresh(playbook)
        
        return playbook
    
    @staticmethod
    def _compute_stats(leads: list) -> Dict:
        """Compute aggregate statistics for leads"""
        total = len(leads)
        if total == 0:
            return {}
        
        with_email = sum(1 for l in leads if l.emails and len(l.emails) > 0)
        with_phone = sum(1 for l in leads if l.phones and len(l.phones) > 0)
        high_score = sum(1 for l in leads if (l.smart_score or 0) >= 0.75)
        
        # Service tags frequency
        service_counts = {}
        for lead in leads:
            if lead.service_tags:
                for service in lead.service_tags:
                    service_counts[service] = service_counts.get(service, 0) + 1
        
        # Tag frequency
        tag_counts = {}
        for lead in leads:
            if lead.tags:
                for tag in lead.tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        return {
            "total_leads": total,
            "with_email_pct": (with_email / total) * 100,
            "with_phone_pct": (with_phone / total) * 100,
            "high_score_pct": (high_score / total) * 100,
            "top_services": dict(sorted(service_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            "top_tags": dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
        }
    
    @staticmethod
    def _generate_playbook_text(
        niche: str,
        location: str,
        stats: Dict,
        sample_leads: list
    ) -> Optional[str]:
        """Generate playbook text using LLM"""
        try:
            from app.ai.factory import create_llm_client
            llm_client = create_llm_client()
            
            if not llm_client:
                logger.warning("LLM client not available")
                return None
            
            prompt = f"""You are helping a sales/agency team understand a market.

Market:
- Niche: {niche}
- Location: {location}

You have data on {stats.get('total_leads', 0)} businesses with services, tags, and AI scores.

Stats:
{json.dumps(stats, indent=2, default=str)}

Sample leads (first 20):
{json.dumps(sample_leads[:20], ensure_ascii=False, indent=2)}

Write a concise playbook in markdown format with these sections:

## Who They Are
Describe typical organization sizes, roles, and their customers/patients.

## What They Care About
List the top 3-5 priorities, pain points, and desired outcomes.

## Common Gaps
Identify digital, marketing, or operational gaps you see in the data.

## How to Approach Them
Recommend pitch angles, tone, and communication channels.

## Key Phrases to Use
A bullet list of real-sounding phrases that would resonate with this market.

Keep it practical and actionable. Use specific examples from the data when relevant."""

            import asyncio
            import inspect
            if inspect.iscoroutinefunction(llm_client.chat_completion):
                result = asyncio.run(llm_client.chat_completion([
                    {"role": "user", "content": prompt}
                ], temperature=0.7))
            else:
                result = llm_client.chat_completion([
                    {"role": "user", "content": prompt}
                ], temperature=0.7)
            
            if result:
                return result.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate playbook text: {e}")
        
        return None

