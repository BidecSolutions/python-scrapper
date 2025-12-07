"""Market insights generation service"""
import logging
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.orm import LeadORM, ScrapeJobORM, JobInsightORM

logger = logging.getLogger(__name__)


class InsightsService:
    """Service for generating market insights using LLM"""
    
    @staticmethod
    async def generate_insights_for_job(
        db: Session,
        job_id: int
    ) -> Optional[JobInsightORM]:
        """
        Generate market insights for a job (async)
        
        Returns:
            JobInsightORM instance or None if generation failed
        """
        job = db.query(ScrapeJobORM).filter(ScrapeJobORM.id == job_id).first()
        if not job:
            return None
        
        leads = db.query(LeadORM).filter(LeadORM.job_id == job_id).all()
        
        if not leads:
            return None
        
        # Compute statistics
        stats = InsightsService._compute_stats(leads)
        
        # Prepare sample lead profiles
        sample_profiles = InsightsService._prepare_sample_profiles(leads[:20])
        
        # Generate insights using LLM (async)
        insights_text = await InsightsService._generate_insights_text(
            job.niche,
            job.location,
            stats,
            sample_profiles
        )
        
        if not insights_text:
            return None
        
        # Save insights
        insight = JobInsightORM(
            job_id=job_id,
            text=insights_text,
            stats=stats,
            generated_at=datetime.utcnow(),
        )
        
        # Update or create
        existing = db.query(JobInsightORM).filter(JobInsightORM.job_id == job_id).first()
        if existing:
            existing.text = insights_text
            existing.stats = stats
            existing.generated_at = datetime.utcnow()
            db.commit()
            return existing
        else:
            db.add(insight)
            db.commit()
            return insight
    
    @staticmethod
    def _compute_stats(leads: List[LeadORM]) -> Dict:
        """Compute summary statistics for leads"""
        total = len(leads)
        if total == 0:
            return {}
        
        stats = {
            "total": total,
            "with_email": sum(1 for l in leads if l.emails),
            "with_phone": sum(1 for l in leads if l.phones),
            "with_social": sum(1 for l in leads if l.social_links),
            "with_website": sum(1 for l in leads if l.website),
            "score_distribution": {
                "high": sum(1 for l in leads if l.quality_label == "high"),
                "medium": sum(1 for l in leads if l.quality_label == "medium"),
                "low": sum(1 for l in leads if l.quality_label == "low"),
            },
            "tag_counts": {},
            "city_counts": {},
            "country_counts": {},
        }
        
        # Tag frequency
        all_tags = []
        for lead in leads:
            all_tags.extend(lead.tags or [])
            if lead.city:
                stats["city_counts"][lead.city] = stats["city_counts"].get(lead.city, 0) + 1
            if lead.country:
                stats["country_counts"][lead.country] = stats["country_counts"].get(lead.country, 0) + 1
        
        from collections import Counter
        stats["tag_counts"] = dict(Counter(all_tags).most_common(10))
        
        # Calculate percentages
        stats["pct_with_email"] = (stats["with_email"] / total * 100) if total > 0 else 0
        stats["pct_with_phone"] = (stats["with_phone"] / total * 100) if total > 0 else 0
        stats["pct_with_social"] = (stats["with_social"] / total * 100) if total > 0 else 0
        
        return stats
    
    @staticmethod
    def _prepare_sample_profiles(leads: List[LeadORM]) -> List[Dict]:
        """Prepare sample lead profiles for LLM"""
        profiles = []
        for lead in leads[:20]:
            profile = {
                "name": lead.name or "Unknown",
                "city": lead.city or "",
                "country": lead.country or "",
                "services": lead.service_tags or [],
                "tags": lead.tags or [],
                "has_online_booking": "online_booking" in (lead.tags or []),
                "score": float(lead.quality_score or 0),
            }
            profiles.append(profile)
        return profiles
    
    @staticmethod
    async def _generate_insights_text(
        niche: str,
        location: Optional[str],
        stats: Dict,
        sample_profiles: List[Dict]
    ) -> Optional[str]:
        """Generate insights text using LLM (async)"""
        try:
            from app.ai.factory import create_llm_client
            llm_client = create_llm_client()
            
            if not llm_client:
                return InsightsService._generate_fallback_insights(niche, location, stats)
            
            prompt = f"""You are an analyst summarizing a list of scraped businesses for a sales/marketing team.

They are running a campaign for: "{niche}" in "{location or 'various locations'}".

Summary Statistics:
- Total leads: {stats.get('total', 0)}
- With email: {stats.get('pct_with_email', 0):.1f}%
- With phone: {stats.get('pct_with_phone', 0):.1f}%
- With social links: {stats.get('pct_with_social', 0):.1f}%
- Quality distribution: High: {stats.get('score_distribution', {}).get('high', 0)}, Medium: {stats.get('score_distribution', {}).get('medium', 0)}, Low: {stats.get('score_distribution', {}).get('low', 0)}

Top tags: {', '.join(list(stats.get('tag_counts', {}).keys())[:5])}

Sample lead profiles:
{chr(10).join(f"- {p['name']} ({p['city']}): {', '.join(p['tags'][:3])}" for p in sample_profiles[:10])}

Write:
1. 3-6 bullet points with key patterns and opportunities
2. 2-3 suggestions on how to approach this market (what to say in outreach)

Keep the language concrete and business-focused. Avoid generic advice.
Format as markdown with bullet points."""

            # LLM client is async, await it directly
            try:
                result = await llm_client.chat_completion([
                    {"role": "user", "content": prompt}
                ], temperature=0.7)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"LLM call failed: {e}")
            
            return InsightsService._generate_fallback_insights(niche, location, stats)
            
        except Exception as e:
            logger.error(f"Failed to generate insights with LLM: {e}")
            return InsightsService._generate_fallback_insights(niche, location, stats)
    
    @staticmethod
    def _generate_fallback_insights(niche: str, location: Optional[str], stats: Dict) -> str:
        """Generate basic insights without LLM"""
        lines = [
            f"## Market Insights for {niche}",
            "",
            f"- Total leads found: {stats.get('total', 0)}",
            f"- {stats.get('pct_with_email', 0):.1f}% have email addresses",
            f"- {stats.get('pct_with_phone', 0):.1f}% have phone numbers",
            f"- {stats.get('pct_with_social', 0):.1f}% have social media links",
        ]
        
        if stats.get('tag_counts'):
            lines.append("")
            lines.append("Common features:")
            for tag, count in list(stats['tag_counts'].items())[:5]:
                lines.append(f"- {tag}: {count} leads")
        
        return "\n".join(lines)

