"""Enhanced scoring service with configurable weights"""
from typing import Dict, Optional
from app.core.models import Lead


class ScoringService:
    """Calculate quality scores for leads with configurable weights"""
    
    DEFAULT_WEIGHTS = {
        "email": 30,
        "phone": 25,
        "website": 20,
        "website_https": 5,
        "social_links": 10,
        "address": 5,
        "services": 5,
    }
    
    @staticmethod
    def calculate_score(lead: Lead, weights: Optional[Dict[str, float]] = None) -> float:
        """
        Calculate quality score (0-100) for a lead
        
        Args:
            lead: Lead to score
            weights: Optional custom weights (defaults to DEFAULT_WEIGHTS)
        
        Returns:
            Score from 0 to 100
        """
        weights = weights or ScoringService.DEFAULT_WEIGHTS
        score = 0.0
        
        # Email presence
        if lead.emails and len(lead.emails) > 0:
            score += weights.get("email", 30)
        
        # Phone presence
        if lead.phones and len(lead.phones) > 0:
            score += weights.get("phone", 25)
        
        # Website quality
        if lead.website:
            score += weights.get("website", 20)
            # HTTPS bonus
            if lead.website.startswith("https://"):
                score += weights.get("website_https", 5)
        
        # Social links
        if lead.social_links and len(lead.social_links) > 0:
            score += weights.get("social_links", 10)
        
        # Address
        if lead.address:
            score += weights.get("address", 5)
        
        # Services (if we have service tags or tech stack)
        if (hasattr(lead, 'service_tags') and lead.service_tags) or \
           (hasattr(lead, 'tech_stack') and lead.tech_stack):
            score += weights.get("services", 5)
        
        return min(100.0, score)
    
    @staticmethod
    def get_quality_label(score: float) -> str:
        """Get quality label based on score"""
        if score >= 70:
            return "high"
        elif score >= 40:
            return "medium"
        else:
            return "low"

