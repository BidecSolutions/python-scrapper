"""Custom field extraction service - extract any field users define"""
import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from app.core.orm import LeadORM

logger = logging.getLogger(__name__)


class CustomFieldExtractor:
    """Extract custom fields defined by users"""
    
    @staticmethod
    def extract_custom_fields(
        db: Session,
        lead_id: int,
        field_definitions: List[Dict[str, Any]],
        website_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract custom fields for a lead
        
        Args:
            lead_id: Lead to extract fields for
            field_definitions: List of field definitions, e.g.:
                [
                    {"name": "has_parking", "type": "boolean", "description": "Does the business have parking?"},
                    {"name": "avg_waiting_time", "type": "number", "description": "Average waiting time in minutes"},
                    {"name": "accepts_insurance", "type": "text", "description": "Which insurance plans are accepted"}
                ]
            website_text: Optional pre-fetched website text
        
        Returns:
            Dict of extracted field values
        """
        lead = db.query(LeadORM).filter(LeadORM.id == lead_id).first()
        if not lead:
            return {}
        
        # Get website text if not provided
        if not website_text and lead.website:
            website_text = CustomFieldExtractor._fetch_website_text(lead.website)
        
        if not website_text:
            logger.warning(f"No website text available for lead {lead_id}")
            return {}
        
        # Generate extraction prompt
        prompt = CustomFieldExtractor._build_extraction_prompt(
            lead, field_definitions, website_text
        )
        
        # Extract using LLM
        extracted = CustomFieldExtractor._extract_with_llm(prompt, field_definitions)
        
        return extracted
    
    @staticmethod
    def _build_extraction_prompt(
        lead: LeadORM,
        field_definitions: List[Dict],
        website_text: str
    ) -> str:
        """Build LLM prompt for custom field extraction"""
        fields_desc = []
        for field in field_definitions:
            field_type = field.get("type", "text")
            desc = field.get("description", "")
            fields_desc.append(f"- {field['name']} ({field_type}): {desc}")
        
        prompt = f"""Extract custom data fields from this business website.

Business: {lead.name or 'Unknown'}
Niche: {lead.niche or 'Unknown'}
Location: {lead.city or ''}, {lead.country or ''}

Website content:
{website_text[:5000]}  # Limit to avoid token limits

Extract the following fields:
{chr(10).join(fields_desc)}

Respond in JSON format with field names as keys:
{{
  "has_parking": true,
  "avg_waiting_time": 15,
  "accepts_insurance": "BCBS, Aetna, Cigna"
}}

If a field cannot be determined, use null. Be precise and only extract information explicitly mentioned."""
        
        return prompt
    
    @staticmethod
    def _extract_with_llm(
        prompt: str,
        field_definitions: List[Dict]
    ) -> Dict[str, Any]:
        """Extract fields using LLM"""
        try:
            from app.ai.factory import create_llm_client
            llm_client = create_llm_client()
            
            if not llm_client:
                return {}
            
            import asyncio
            import inspect
            if inspect.iscoroutinefunction(llm_client.chat_completion):
                result = asyncio.run(llm_client.chat_completion([
                    {"role": "user", "content": prompt}
                ], temperature=0.1))
            else:
                result = llm_client.chat_completion([
                    {"role": "user", "content": prompt}
                ], temperature=0.1)
            
            if result:
                import json
                import re
                # Extract JSON
                json_match = re.search(r'\{[^}]+\}', result, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group())
                    # Validate and type-convert
                    return CustomFieldExtractor._validate_fields(parsed, field_definitions)
            
        except Exception as e:
            logger.warning(f"LLM extraction failed: {e}")
        
        return {}
    
    @staticmethod
    def _validate_fields(
        extracted: Dict,
        field_definitions: List[Dict]
    ) -> Dict:
        """Validate and type-convert extracted fields"""
        validated = {}
        
        for field_def in field_definitions:
            field_name = field_def["name"]
            field_type = field_def.get("type", "text")
            value = extracted.get(field_name)
            
            if value is None:
                validated[field_name] = None
                continue
            
            # Type conversion
            try:
                if field_type == "boolean":
                    if isinstance(value, bool):
                        validated[field_name] = value
                    elif isinstance(value, str):
                        validated[field_name] = value.lower() in ("true", "yes", "1", "has", "available")
                    else:
                        validated[field_name] = bool(value)
                
                elif field_type == "number":
                    if isinstance(value, (int, float)):
                        validated[field_name] = float(value)
                    elif isinstance(value, str):
                        # Extract number from string
                        import re
                        numbers = re.findall(r'\d+\.?\d*', value)
                        validated[field_name] = float(numbers[0]) if numbers else None
                    else:
                        validated[field_name] = None
                
                else:  # text
                    validated[field_name] = str(value)
            
            except Exception as e:
                logger.warning(f"Failed to convert {field_name} to {field_type}: {e}")
                validated[field_name] = None
        
        return validated
    
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
                # Remove script and style
                for script in soup(["script", "style"]):
                    script.decompose()
                
                text = soup.get_text(separator=" ", strip=True)
                # Clean up whitespace
                text = " ".join(text.split())
                return text[:10000]  # Limit length
        
        except Exception as e:
            logger.warning(f"Failed to fetch website text: {e}")
            return None

