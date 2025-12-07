"""Automatic niche classification and normalization"""
import logging
import re
from typing import Dict, Optional, List, Tuple
from sqlalchemy.orm import Session

from app.core.orm import LeadORM, ScrapeJobORM

logger = logging.getLogger(__name__)

# Canonical niche categories
CANONICAL_NICHES = [
    "dentist", "hospital", "clinic", "restaurant", "hotel", "salon", "spa",
    "gym", "fitness", "school", "university", "lawyer", "accountant",
    "real_estate", "insurance", "pharmacy", "veterinary", "auto_repair",
    "plumber", "electrician", "contractor", "retail", "cafe", "bar",
    "bakery", "beauty", "wellness", "therapy", "counseling", "finance",
    "banking", "technology", "software", "marketing", "advertising",
    "consulting", "logistics", "transportation", "manufacturing", "other"
]

# Niche mappings (common variations -> canonical)
NICHE_MAPPINGS = {
    "dental": "dentist",
    "dental clinic": "dentist",
    "dental office": "dentist",
    "orthodontist": "dentist",
    "periodontist": "dentist",
    "endodontist": "dentist",
    "hospital": "hospital",
    "medical center": "hospital",
    "medical facility": "hospital",
    "healthcare": "hospital",
    "clinic": "clinic",
    "medical clinic": "clinic",
    "health clinic": "clinic",
    "restaurant": "restaurant",
    "dining": "restaurant",
    "eatery": "restaurant",
    "cafe": "cafe",
    "coffee shop": "cafe",
    "salon": "salon",
    "hair salon": "salon",
    "beauty salon": "salon",
    "spa": "spa",
    "day spa": "spa",
    "wellness": "wellness",
    "fitness": "fitness",
    "gym": "gym",
    "fitness center": "gym",
}


class NicheClassifier:
    """Classify and normalize business niches"""
    
    @staticmethod
    async def classify_niche(
        raw_niche: str,
        use_llm: bool = True
    ) -> Dict[str, any]:
        """
        Classify a raw niche string into canonical category (async)
        
        Returns:
            {
                "canonical": "dentist",
                "subspecialty": ["cosmetic", "orthodontic"],
                "confidence": 0.95
            }
        """
        if not raw_niche:
            return {
                "canonical": "other",
                "subspecialty": [],
                "confidence": 0.0
            }
        
        raw_lower = raw_niche.lower().strip()
        
        # First try direct mapping
        if raw_lower in NICHE_MAPPINGS:
            canonical = NICHE_MAPPINGS[raw_lower]
            return {
                "canonical": canonical,
                "subspecialty": [],
                "confidence": 0.9
            }
        
        # Try fuzzy matching
        for variant, canonical in NICHE_MAPPINGS.items():
            if variant in raw_lower or raw_lower in variant:
                return {
                    "canonical": canonical,
                    "subspecialty": [],
                    "confidence": 0.8
                }
        
        # Try LLM classification if available
        if use_llm:
            try:
                result = await NicheClassifier._llm_classify(raw_niche)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"LLM classification failed: {e}")
        
        # Fallback: try to match against canonical list
        for canonical in CANONICAL_NICHES:
            if canonical in raw_lower:
                return {
                    "canonical": canonical,
                    "subspecialty": [],
                    "confidence": 0.7
                }
        
        return {
            "canonical": "other",
            "subspecialty": [],
            "confidence": 0.5
        }
    
    @staticmethod
    async def _llm_classify(raw_niche: str) -> Optional[Dict]:
        """Use LLM to classify niche (async)"""
        try:
            from app.ai.factory import create_llm_client
            llm_client = create_llm_client()
            
            if not llm_client:
                return None
            
            prompt = f"""Classify this business niche into a canonical category and subspecialties.

Raw niche: "{raw_niche}"

Canonical categories: {', '.join(CANONICAL_NICHES[:20])}

Respond in JSON format:
{{
  "canonical": "dentist",
  "subspecialty": ["cosmetic", "orthodontic"],
  "confidence": 0.95
}}

If unsure, use "other" as canonical."""

            # LLM client is async, await it directly
            result = await llm_client.chat_completion([
                {"role": "user", "content": prompt}
            ], temperature=0.3)
            
            if result:
                import json
                # Try to extract JSON from response
                json_match = re.search(r'\{[^}]+\}', result)
                if json_match:
                    parsed = json.loads(json_match.group())
                    return parsed
            
        except Exception as e:
            logger.warning(f"LLM niche classification failed: {e}")
        
        return None
    
    @staticmethod
    async def normalize_niche_for_job(
        db: Session,
        job_id: int
    ) -> Optional[str]:
        """Normalize niche for a job and update it (async)"""
        job = db.query(ScrapeJobORM).filter(ScrapeJobORM.id == job_id).first()
        if not job:
            return None
        
        classification = await NicheClassifier.classify_niche(job.niche)
        
        # Store canonical niche in job metadata
        if not job.meta:
            job.meta = {}
        job.meta['canonical_niche'] = classification['canonical']
        job.meta['niche_subspecialty'] = classification['subspecialty']
        db.commit()
        
        return classification['canonical']

