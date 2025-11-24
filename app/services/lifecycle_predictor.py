"""Lead lifecycle prediction - hot vs warm vs cold"""
import logging
from typing import Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.orm import LeadORM, ScrapeJobORM

logger = logging.getLogger(__name__)


class LifecyclePredictor:
    """Predict lead timing (hot/warm/cold)"""
    
    @staticmethod
    def predict_lifecycle(
        db: Session,
        lead_id: int
    ) -> Dict:
        """
        Predict lead lifecycle stage
        
        Returns:
            {
                "stage": "hot",  # "hot", "warm", "cold"
                "confidence": 0.75,
                "signals": ["New services added", "Website updated recently"],
                "reasoning": "Business appears to be in growth phase",
                "recommended_action": "Contact within 1 week"
            }
        """
        lead = db.query(LeadORM).filter(LeadORM.id == lead_id).first()
        if not lead:
            return {}
        
        # Get historical data for this lead (from previous jobs)
        previous_leads = db.query(LeadORM).filter(
            LeadORM.website == lead.website,
            LeadORM.organization_id == lead.organization_id,
            LeadORM.id != lead_id
        ).order_by(LeadORM.created_at.desc()).limit(3).all()
        
        # Get job history
        jobs = db.query(ScrapeJobORM).filter(
            ScrapeJobORM.organization_id == lead.organization_id,
            ScrapeJobORM.niche == lead.niche
        ).order_by(ScrapeJobORM.created_at.desc()).limit(5).all()
        
        # Analyze signals
        signals = []
        score = 0.5  # Start neutral
        
        # Signal 1: Recent changes (from change tracker)
        if previous_leads:
            from app.services.change_tracker import ChangeTracker
            changes = ChangeTracker.get_lead_changes(db, lead_id)
            if changes.get("has_changes"):
                change_count = changes.get("change_count", 0)
                if change_count >= 3:
                    signals.append("Multiple recent updates")
                    score += 0.2
                elif change_count >= 1:
                    signals.append("Recent updates detected")
                    score += 0.1
        
        # Signal 2: New services/tags
        if lead.service_tags:
            service_count = len(lead.service_tags)
            if service_count >= 5:
                signals.append("Extensive service offerings")
                score += 0.1
            if "new" in str(lead.service_tags).lower() or "launch" in str(lead.service_tags).lower():
                signals.append("New services mentioned")
                score += 0.15
        
        # Signal 3: Website quality (if recently improved)
        # This would require storing historical quality scores
        # For now, use current quality as proxy
        if lead.website:
            try:
                from app.services.website_quality_scorer import WebsiteQualityScorer
                import httpx
                from bs4 import BeautifulSoup
                
                response = httpx.get(lead.website, timeout=5.0, follow_redirects=True)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    quality = WebsiteQualityScorer.score_website(response.text, lead.website, soup)
                    if quality["score"] >= 75:
                        signals.append("Modern, well-maintained website")
                        score += 0.1
            except:
                pass
        
        # Signal 4: Contact information completeness
        contact_score = 0
        if lead.emails:
            contact_score += 0.1
        if lead.phones:
            contact_score += 0.1
        if lead.has_social:
            contact_score += 0.05
        score += contact_score
        if contact_score >= 0.2:
            signals.append("Complete contact information")
        
        # Signal 5: Job frequency (if org is actively scraping this niche)
        if jobs:
            recent_jobs = [j for j in jobs if j.created_at and (datetime.utcnow() - j.created_at).days <= 30]
            if len(recent_jobs) >= 3:
                signals.append("Active niche (frequent scraping)")
                score += 0.1
        
        # Determine stage
        if score >= 0.7:
            stage = "hot"
            reasoning = "Business appears to be in active growth or transition phase"
            action = "Contact within 1 week - high priority"
        elif score >= 0.5:
            stage = "warm"
            reasoning = "Business shows moderate activity signals"
            action = "Contact within 2-4 weeks"
        else:
            stage = "cold"
            reasoning = "Business appears stable with minimal recent changes"
            action = "Contact when capacity allows"
        
        return {
            "stage": stage,
            "confidence": min(0.95, max(0.3, score)),
            "signals": signals[:5],  # Top 5 signals
            "reasoning": reasoning,
            "recommended_action": action,
            "score": round(score, 2),
        }

