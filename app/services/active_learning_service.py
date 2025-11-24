"""Active learning service - identify leads that need labeling"""
import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import numpy as np

from app.core.orm import LeadORM, LeadFeedbackORM

logger = logging.getLogger(__name__)

# Try to import sklearn
try:
    from sklearn.ensemble import GradientBoostingClassifier
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class ActiveLearningService:
    """Service for active learning - finding leads that need feedback"""
    
    @staticmethod
    def get_leads_for_labeling(
        db: Session,
        org_id: int,
        limit: int = 20,
        min_uncertainty: float = 0.3
    ) -> List[Dict]:
        """
        Get leads that would benefit most from user feedback
        
        Strategy:
        1. Find leads with high uncertainty (probability near 0.5)
        2. Prioritize leads with high potential value (good contact info, etc.)
        3. Exclude leads already labeled
        
        Returns:
            List of lead dicts with uncertainty scores
        """
        # Get all unlabeled leads with smart scores
        query = db.query(LeadORM).filter(
            LeadORM.organization_id == org_id,
            LeadORM.smart_score.isnot(None)
        )
        
        # Exclude already labeled leads
        labeled_lead_ids = db.query(LeadFeedbackORM.lead_id).filter(
            LeadFeedbackORM.organization_id == org_id
        ).subquery()
        
        query = query.filter(~LeadORM.id.in_(labeled_lead_ids))
        
        leads = query.all()
        
        if not leads:
            return []
        
        # Calculate uncertainty and value scores
        candidates = []
        for lead in leads:
            # Uncertainty: how close to 0.5 (most uncertain)
            if lead.smart_score is not None:
                uncertainty = abs(0.5 - float(lead.smart_score))
            else:
                uncertainty = 0.5  # No score = high uncertainty
            
            # Value score: how valuable this lead is (has contact info, etc.)
            value_score = 0.0
            if lead.emails and len(lead.emails) > 0:
                value_score += 0.3
            if lead.phones and len(lead.phones) > 0:
                value_score += 0.3
            if lead.website:
                value_score += 0.2
            if lead.social_links and len(lead.social_links) > 0:
                value_score += 0.2
            
            # Combined score: high uncertainty + high value = prioritize
            # Lower uncertainty score = more uncertain (closer to 0.5)
            # So we want: high value * (1 - uncertainty*2) 
            # This prioritizes uncertain but valuable leads
            combined_score = value_score * (1.0 - uncertainty * 2.0)
            
            candidates.append({
                "lead": lead,
                "uncertainty": uncertainty,
                "value_score": value_score,
                "combined_score": combined_score,
                "smart_score": float(lead.smart_score) if lead.smart_score else None,
            })
        
        # Sort by combined score (highest first)
        candidates.sort(key=lambda x: x["combined_score"], reverse=True)
        
        # Filter by minimum uncertainty
        candidates = [c for c in candidates if c["uncertainty"] <= (1.0 - min_uncertainty)]
        
        # Return top N
        result = []
        for candidate in candidates[:limit]:
            lead = candidate["lead"]
            result.append({
                "id": lead.id,
                "name": lead.name,
                "niche": lead.niche,
                "website": lead.website,
                "city": lead.city,
                "country": lead.country,
                "emails": lead.emails or [],
                "phones": lead.phones or [],
                "smart_score": candidate["smart_score"],
                "uncertainty": round(candidate["uncertainty"], 3),
                "value_score": round(candidate["value_score"], 3),
                "why_label": ActiveLearningService._explain_why_label(candidate),
            })
        
        return result
    
    @staticmethod
    def _explain_why_label(candidate: Dict) -> str:
        """Explain why this lead should be labeled"""
        uncertainty = candidate["uncertainty"]
        value_score = candidate["value_score"]
        smart_score = candidate.get("smart_score")
        
        reasons = []
        
        if uncertainty < 0.2:
            reasons.append("AI is uncertain about this lead")
        
        if value_score > 0.6:
            reasons.append("has good contact information")
        
        if smart_score and 0.4 <= smart_score <= 0.6:
            reasons.append("borderline quality score")
        
        if not reasons:
            reasons.append("needs human judgment")
        
        return " • ".join(reasons)

