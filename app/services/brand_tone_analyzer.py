"""Brand tone analysis - classify website tone"""
import logging
from typing import Dict, Optional
from sqlalchemy.orm import Session

from app.core.orm import LeadORM

logger = logging.getLogger(__name__)


class BrandToneAnalyzer:
    """Analyze brand tone from website content"""
    
    TONE_CATEGORIES = [
        "clinical_formal",
        "friendly_casual",
        "luxury_premium",
        "budget_affordable",
        "urgent_care",
        "family_warm",
        "professional_corporate",
        "modern_tech",
        "traditional_conservative",
        "playful_creative",
    ]
    
    @staticmethod
    def analyze_tone(
        db: Session,
        lead_id: int,
        website_text: Optional[str] = None
    ) -> Dict:
        """
        Analyze brand tone
        
        Returns:
            {
                "primary_tone": "friendly_casual",
                "confidence": 0.85,
                "secondary_tones": ["family_warm"],
                "description": "Warm, approachable tone with family-friendly messaging",
                "suggested_outreach_tone": "Match their friendly style"
            }
        """
        lead = db.query(LeadORM).filter(LeadORM.id == lead_id).first()
        if not lead:
            return {}
        
        # Get website text if not provided
        if not website_text and lead.website:
            website_text = BrandToneAnalyzer._fetch_website_text(lead.website)
        
        if not website_text:
            return {
                "primary_tone": "unknown",
                "confidence": 0.0,
                "description": "Insufficient content for tone analysis"
            }
        
        # Use LLM to analyze tone
        tone_analysis = BrandToneAnalyzer._analyze_with_llm(lead, website_text)
        
        return tone_analysis
    
    @staticmethod
    def _analyze_with_llm(lead: LeadORM, website_text: str) -> Dict:
        """Analyze tone using LLM"""
        try:
            from app.ai.factory import create_llm_client
            llm_client = create_llm_client()
            
            if not llm_client:
                return BrandToneAnalyzer._rule_based_tone(website_text)
            
            tones_desc = ", ".join(BrandToneAnalyzer.TONE_CATEGORIES)
            
            prompt = f"""Analyze the brand tone and voice of this business website.

Business: {lead.name or 'Unknown'}
Niche: {lead.niche or 'Unknown'}

Website content:
{website_text[:3000]}

Classify the tone into one or more of these categories:
{tones_desc}

Consider:
- Language formality (formal vs casual)
- Emotional tone (warm vs clinical)
- Price positioning (luxury vs budget)
- Urgency level
- Target audience (family, professionals, etc.)

Respond in JSON format:
{{
  "primary_tone": "friendly_casual",
  "confidence": 0.85,
  "secondary_tones": ["family_warm"],
  "description": "Brief description of the tone",
  "suggested_outreach_tone": "How to match this tone in outreach"
}}"""

            import asyncio
            import inspect
            if inspect.iscoroutinefunction(llm_client.chat_completion):
                result = asyncio.run(llm_client.chat_completion([
                    {"role": "user", "content": prompt}
                ], temperature=0.3))
            else:
                result = llm_client.chat_completion([
                    {"role": "user", "content": prompt}
                ], temperature=0.3)
            
            if result:
                import json
                import re
                json_match = re.search(r'\{[^}]+\}', result, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group())
                    # Validate tone is in our categories
                    if parsed.get("primary_tone") in BrandToneAnalyzer.TONE_CATEGORIES:
                        return parsed
            
        except Exception as e:
            logger.warning(f"LLM tone analysis failed: {e}")
        
        return BrandToneAnalyzer._rule_based_tone(website_text)
    
    @staticmethod
    def _rule_based_tone(text: str) -> Dict:
        """Fallback rule-based tone detection"""
        text_lower = text.lower()
        
        # Check for tone indicators
        if any(word in text_lower for word in ["luxury", "premium", "exclusive", "elite"]):
            return {
                "primary_tone": "luxury_premium",
                "confidence": 0.7,
                "description": "Premium, luxury positioning",
                "suggested_outreach_tone": "Professional, value-focused"
            }
        
        if any(word in text_lower for word in ["affordable", "budget", "cheap", "low cost"]):
            return {
                "primary_tone": "budget_affordable",
                "confidence": 0.7,
                "description": "Budget-conscious, affordable positioning",
                "suggested_outreach_tone": "Value-focused, cost-effective"
            }
        
        if any(word in text_lower for word in ["emergency", "urgent", "24/7", "immediate"]):
            return {
                "primary_tone": "urgent_care",
                "confidence": 0.7,
                "description": "Urgent, emergency-focused",
                "suggested_outreach_tone": "Direct, time-sensitive"
            }
        
        if any(word in text_lower for word in ["family", "children", "kids", "friendly"]):
            return {
                "primary_tone": "family_warm",
                "confidence": 0.7,
                "description": "Family-friendly, warm tone",
                "suggested_outreach_tone": "Warm, approachable"
            }
        
        # Default
        return {
            "primary_tone": "professional_corporate",
            "confidence": 0.5,
            "description": "Professional, corporate tone",
            "suggested_outreach_tone": "Professional, business-focused"
        }
    
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
                return text[:4000]
        
        except Exception as e:
            logger.warning(f"Failed to fetch website text: {e}")
            return None

