"""Lead quality scoring models"""
import logging
from typing import Optional
from app.core.models import Lead

logger = logging.getLogger(__name__)


class LeadScorer:
    """Lead quality scoring (rule-based with ML-ready architecture)"""
    
    @staticmethod
    def calculate_score(lead: Lead) -> float:
        """
        Calculate quality score (0-100) using rule-based heuristics
        
        Can be replaced with ML model later using same interface
        """
        score = 0.0
        
        # Email presence and quality (30 points)
        if lead.has_email and lead.emails:
            score += 20
            # Bonus for multiple emails
            if len(lead.emails) > 1:
                score += 5
            # Penalty for generic emails
            generic_emails = {"info@", "webmaster@", "noreply@", "no-reply@", "contact@", "support@"}
            has_non_generic = any(
                not any(generic in email.lower() for generic in generic_emails)
                for email in lead.emails
            )
            if has_non_generic:
                score += 5
            else:
                score -= 5  # Penalty for only generic emails
        
        # Phone presence (25 points)
        if lead.has_phone and lead.phones:
            score += 25
        
        # Website quality (20 points)
        if lead.website:
            score += 15
            # HTTPS bonus
            if lead.website.startswith("https://"):
                score += 5
        
        # Social links (10 points)
        if lead.has_social and lead.social_links:
            score += 10
            # Bonus for multiple social platforms
            if len([v for v in lead.social_links.values() if v]) > 2:
                score += 2
        
        # Complete contact info (10 points)
        if lead.contact_person_name or lead.contact_person_email:
            score += 10
        
        # Tech stack / CMS indicators (5 points)
        if lead.cms or lead.tech_stack:
            score += 5
        
        # Services / tags (5 points)
        if lead.service_tags or (lead.metadata and lead.metadata.get("services")):
            score += 5
        
        # Penalties
        # No website at all
        if not lead.website:
            score -= 10
        
        # Only generic email and no phone
        if lead.emails and not lead.phones:
            generic_emails = {"info@", "webmaster@", "noreply@", "contact@"}
            if all(any(generic in email.lower() for generic in generic_emails) for email in lead.emails):
                score -= 5
        
        # Clamp to 0-100
        return max(0.0, min(100.0, score))
    
    @staticmethod
    def label_from_score(score: float) -> str:
        """Convert numeric score to quality label"""
        if score >= 80:
            return "high"
        elif score >= 50:
            return "medium"
        else:
            return "low"
    
    @staticmethod
    def score_and_label(lead: Lead) -> tuple[float, str]:
        """Calculate score and label in one call"""
        score = LeadScorer.calculate_score(lead)
        label = LeadScorer.label_from_score(score)
        return score, label


class MLLeadScorer:
    """
    ML-based lead scorer (placeholder for future ML model)
    
    This class has the same interface as LeadScorer but uses a trained model
    """
    
    def __init__(self, model=None):
        """Initialize with trained model (XGBoost, sklearn, etc.)"""
        self.model = model
    
    def calculate_score(self, lead: Lead) -> float:
        """
        Calculate score using ML model
        
        Args:
            lead: Lead object
        
        Returns:
            Score (0-100) or probability (0-1) * 100
        """
        if not self.model:
            # Fallback to rule-based
            return LeadScorer.calculate_score(lead)
        
        # Extract features from lead
        features = self._extract_features(lead)
        
        # Predict using model
        try:
            # Assuming model.predict_proba returns probability
            proba = self.model.predict_proba([features])[0][1]  # Probability of "good" lead
            return float(proba * 100)
        except Exception as e:
            logger.error(f"Error in ML scoring: {e}")
            # Fallback to rule-based
            return LeadScorer.calculate_score(lead)
    
    def _extract_features(self, lead: Lead) -> list:
        """
        Extract features from lead for ML model
        
        Returns:
            List of feature values
        """
        return [
            # Boolean features
            1.0 if lead.has_email else 0.0,
            1.0 if lead.has_phone else 0.0,
            1.0 if lead.has_social else 0.0,
            1.0 if lead.website else 0.0,
            1.0 if lead.website and lead.website.startswith("https://") else 0.0,
            
            # Count features
            float(len(lead.emails)),
            float(len(lead.phones)),
            float(len(lead.social_links) if lead.social_links else 0),
            float(len(lead.tech_stack) if lead.tech_stack else 0),
            float(len(lead.service_tags) if lead.service_tags else 0),
            
            # Metadata counts
            float(len(lead.metadata.get("services", [])) if lead.metadata else 0),
            float(len(lead.metadata.get("languages", [])) if lead.metadata else 0),
            
            # Contact person
            1.0 if lead.contact_person_name else 0.0,
            1.0 if lead.contact_person_email else 0.0,
        ]

