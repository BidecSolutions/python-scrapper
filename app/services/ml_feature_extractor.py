"""Feature extraction for ML scoring"""
import re
from typing import Dict, List, Optional
from urllib.parse import urlparse
from app.core.orm import LeadORM


class MLFeatureExtractor:
    """Extract features from leads for ML model training and prediction"""
    
    @staticmethod
    def extract_features(lead: LeadORM) -> Dict[str, float]:
        """
        Extract feature vector for a lead
        
        Returns:
            Dictionary of feature names to values
        """
        features = {}
        
        # ========== Numeric/Boolean Features ==========
        
        # Contact information
        features['has_email'] = 1.0 if (lead.emails and len(lead.emails) > 0) else 0.0
        features['has_phone'] = 1.0 if (lead.phones and len(lead.phones) > 0) else 0.0
        features['num_emails'] = float(len(lead.emails or []))
        features['num_phones'] = float(len(lead.phones or []))
        
        # Social links
        num_social = len(lead.social_links or {})
        features['num_social_links'] = float(num_social)
        features['has_social'] = 1.0 if num_social > 0 else 0.0
        
        # Website quality
        features['has_website'] = 1.0 if lead.website else 0.0
        features['website_https'] = 0.0
        if lead.website:
            features['website_https'] = 1.0 if lead.website.startswith("https://") else 0.0
        
        # Basic rule-based score (as a feature)
        features['ai_score_basic'] = float(lead.quality_score or 0.0) / 100.0  # Normalize to 0-1
        
        # Address
        features['has_address'] = 1.0 if lead.address else 0.0
        
        # Services/Tags
        features['num_service_tags'] = float(len(lead.service_tags or []))
        features['num_tags'] = float(len(lead.tags or []))
        
        # Tech stack
        features['num_tech_stack'] = float(len(lead.tech_stack or []))
        features['has_cms'] = 1.0 if lead.cms else 0.0
        
        # Company size proxy
        size_map = {"solo": 1.0, "small": 2.0, "medium": 3.0, "large": 4.0}
        features['company_size_numeric'] = size_map.get(lead.company_size or "", 0.0)
        
        # Multi-location
        features['is_multi_location'] = 1.0 if lead.is_multi_location else 0.0
        features['num_branches'] = float(len(lead.branch_locations or []))
        
        # Contact person
        features['has_contact_person'] = 1.0 if lead.contact_person_name else 0.0
        features['has_contact_email'] = 1.0 if lead.contact_person_email else 0.0
        
        # ========== Categorical Features (One-hot encoding) ==========
        
        # Country (top countries only, rest as "other")
        top_countries = ["US", "UK", "GB", "CA", "AU", "PK", "IN", "AE", "DE", "FR"]
        country = (lead.country or "").upper()
        for top_country in top_countries:
            features[f'country_{top_country}'] = 1.0 if country == top_country else 0.0
        features['country_other'] = 1.0 if country not in top_countries else 0.0
        
        # Niche (simplified - could be more sophisticated)
        niche_lower = (lead.niche or "").lower()
        common_niches = ["hospital", "clinic", "dentist", "restaurant", "hotel", "school"]
        for niche in common_niches:
            features[f'niche_contains_{niche}'] = 1.0 if niche in niche_lower else 0.0
        
        # Source (one-hot for top sources)
        sources = lead.sources or [lead.source] if lead.source else []
        top_sources = ["google_search", "google_places", "yellowpages", "web_search"]
        for source in top_sources:
            features[f'source_{source}'] = 1.0 if source in sources else 0.0
        
        # ========== Text Features (Simplified - could use embeddings later) ==========
        
        # Name length (proxy for business maturity)
        name = lead.name or ""
        features['name_length'] = float(len(name))
        features['name_word_count'] = float(len(name.split()))
        
        # Website domain length
        if lead.website:
            try:
                domain = urlparse(lead.website).netloc.replace("www.", "")
                features['domain_length'] = float(len(domain))
            except:
                features['domain_length'] = 0.0
        else:
            features['domain_length'] = 0.0
        
        return features
    
    @staticmethod
    def get_feature_names() -> List[str]:
        """Get list of all feature names (for model training)"""
        # This should match the features extracted above
        # For now, return a sample lead to get feature names
        from app.core.orm import LeadORM
        sample_lead = LeadORM(
            emails=[],
            phones=[],
            social_links={},
            service_tags=[],
            tags=[],
            tech_stack=[],
        )
        features = MLFeatureExtractor.extract_features(sample_lead)
        return sorted(features.keys())

