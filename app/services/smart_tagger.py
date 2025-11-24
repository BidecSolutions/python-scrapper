"""Smart tagging from unstructured content"""
import logging
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.core.orm import LeadORM

logger = logging.getLogger(__name__)


class SmartTagger:
    """Auto-tag leads with specific tags from content"""
    
    # Default tag taxonomy
    DEFAULT_TAGS = [
        "accepts_insurance",
        "offers_telemedicine",
        "emergency_only",
        "children_specialist",
        "luxury_brand",
        "religious_affiliation",
        "multi_location",
        "online_booking",
        "24_7",
        "walk_in",
        "appointment_only",
        "accepts_walk_ins",
        "has_parking",
        "wheelchair_accessible",
        "multi_language",
        "senior_focused",
        "family_friendly",
        "pet_friendly",
        "organic",
        "vegan_options",
        "halal",
        "kosher",
        "certified",
        "award_winning",
        "new_patient_welcome",
        "payment_plans",
        "financing_available",
    ]
    
    @staticmethod
    def tag_lead(
        db: Session,
        lead_id: int,
        custom_tags: Optional[List[str]] = None,
        website_text: Optional[str] = None
    ) -> List[str]:
        """
        Auto-tag a lead based on content
        
        Args:
            lead_id: Lead to tag
            custom_tags: Optional custom tag definitions
            website_text: Optional pre-fetched website text
        
        Returns:
            List of detected tags
        """
        lead = db.query(LeadORM).filter(LeadORM.id == lead_id).first()
        if not lead:
            return []
        
        # Get website text if not provided
        if not website_text and lead.website:
            website_text = SmartTagger._fetch_website_text(lead.website)
        
        if not website_text:
            # Fallback to existing lead data
            website_text = f"{lead.name or ''} {lead.niche or ''} {lead.address or ''}"
        
        # Use LLM to classify tags
        tags_to_check = custom_tags or SmartTagger.DEFAULT_TAGS
        detected_tags = SmartTagger._classify_tags(lead, website_text, tags_to_check)
        
        return detected_tags
    
    @staticmethod
    def _classify_tags(lead: LeadORM, website_text: str, tags: List[str]) -> List[str]:
        """Classify which tags apply using LLM"""
        try:
            from app.ai.factory import create_llm_client
            llm_client = create_llm_client()
            
            if not llm_client:
                # Fallback to keyword matching
                return SmartTagger._keyword_match_tags(website_text, tags)
            
            # Build prompt
            tags_desc = "\n".join([f"- {tag}" for tag in tags])
            
            prompt = f"""Analyze this business website and determine which tags apply.

Business: {lead.name or 'Unknown'}
Niche: {lead.niche or 'Unknown'}
Location: {lead.city or ''}, {lead.country or ''}

Website content:
{website_text[:3000]}

Available tags:
{tags_desc}

For each tag, determine if it applies based on the content. Only include tags that are clearly mentioned or strongly implied.

Respond with a JSON array of applicable tag names:
["tag1", "tag2", "tag3"]

Be conservative - only include tags you're confident about."""

            import asyncio
            import inspect
            if inspect.iscoroutinefunction(llm_client.chat_completion):
                result = asyncio.run(llm_client.chat_completion([
                    {"role": "user", "content": prompt}
                ], temperature=0.2))
            else:
                result = llm_client.chat_completion([
                    {"role": "user", "content": prompt}
                ], temperature=0.2)
            
            if result:
                import json
                import re
                # Extract JSON array
                json_match = re.search(r'\[[^\]]+\]', result, re.DOTALL)
                if json_match:
                    detected = json.loads(json_match.group())
                    # Validate tags exist in our list
                    valid_tags = [tag for tag in detected if tag in tags]
                    return valid_tags
            
        except Exception as e:
            logger.warning(f"LLM tag classification failed: {e}")
        
        # Fallback to keyword matching
        return SmartTagger._keyword_match_tags(website_text, tags)
    
    @staticmethod
    def _keyword_match_tags(text: str, tags: List[str]) -> List[str]:
        """Fallback keyword matching"""
        text_lower = text.lower()
        detected = []
        
        # Keyword patterns for common tags
        patterns = {
            "accepts_insurance": ["insurance", "covered by", "accept insurance"],
            "offers_telemedicine": ["telemedicine", "telehealth", "virtual", "online consultation"],
            "emergency_only": ["emergency only", "emergency services"],
            "children_specialist": ["pediatric", "children", "kids", "child specialist"],
            "luxury_brand": ["luxury", "premium", "exclusive", "high-end"],
            "multi_location": ["multiple locations", "locations", "branches"],
            "online_booking": ["book online", "online booking", "schedule online"],
            "24_7": ["24/7", "24 hours", "round the clock", "always open"],
            "walk_in": ["walk-in", "walk in", "no appointment"],
            "has_parking": ["parking", "parking available", "free parking"],
            "wheelchair_accessible": ["wheelchair", "accessible", "ada"],
            "multi_language": ["multiple languages", "bilingual", "multilingual"],
            "family_friendly": ["family", "families welcome"],
            "payment_plans": ["payment plans", "financing", "installments"],
        }
        
        for tag in tags:
            if tag in patterns:
                pattern_list = patterns[tag]
                if any(pattern in text_lower for pattern in pattern_list):
                    detected.append(tag)
        
        return detected
    
    @staticmethod
    def _fetch_website_text(website: str) -> Optional[str]:
        """Fetch and extract text from website"""
        try:
            import httpx
            from bs4 import BeautifulSoup
            
            with httpx.Client(timeout=10.0, follow_redirects=True) as client:
                response = client.get(website, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, "html.parser")
                for script in soup(["script", "style"]):
                    script.decompose()
                
                text = soup.get_text(separator=" ", strip=True)
                text = " ".join(text.split())
                return text[:5000]
        
        except Exception as e:
            logger.warning(f"Failed to fetch website text: {e}")
            return None

