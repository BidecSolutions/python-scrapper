"""LLM-based structured extraction service"""
import json
import re
import logging
from typing import Optional, Dict, Any
from app.core.models import Lead

logger = logging.getLogger(__name__)


class LLMExtractor:
    """Extract structured information from website text using LLM"""
    
    SYSTEM_PROMPT = """You are a highly accurate information extraction engine.
Your task is to read business website content and return a single JSON object with specific fields.
The website content may be incomplete or noisy.
Follow these rules strictly:
* If you are not confident about a value, use null or an empty list.
* Do NOT invent information that is not clearly implied.
* Return ONLY a JSON object, with no extra text or explanation.
* Ensure the JSON is valid and parsable.
"""
    
    USER_PROMPT_TEMPLATE = """Extract structured information about a local business from the text below.

Required JSON schema:
{{
  "business_name": string or null,
  "emails": string[] (unique, lowercase),
  "phones": string[] (unique, cleaned format),
  "address": string or null,
  "city": string or null,
  "country": string or null,
  "services": string[],
  "languages": string[],
  "social_links": {{
    "facebook": string or null,
    "instagram": string or null,
    "linkedin": string or null,
    "twitter": string or null,
    "youtube": string or null,
    "other": string[]
  }},
  "notes": string or null
}}

Guidelines:
- Include only emails that look like real contact addresses.
- For phones, keep the number as it appears, but remove obvious formatting noise.
- Services should be short phrases like "general dentistry", "teeth whitening", "emergency care".
- Languages: list human languages mentioned (e.g. "English", "Urdu").
- Social links: full URLs if possible.
- "notes" can include any useful info (e.g. "24/7 emergency service", "online booking available").

Website content:
----------------
{website_content}
----------------

Return ONLY the JSON object."""

    def __init__(self, llm_client=None):
        """
        Initialize LLM extractor
        
        Args:
            llm_client: LLM client (OpenAI, Anthropic, etc.)
                       Should have a `chat_completion` method
        """
        self.llm_client = llm_client
    
    async def extract(self, website_text: str) -> Optional[Dict[str, Any]]:
        """
        Extract structured information from website text
        
        Args:
            website_text: Cleaned website text (from multiple pages)
        
        Returns:
            Dictionary with extracted fields, or None if extraction fails
        """
        if not self.llm_client:
            logger.warning("LLM client not configured, skipping AI extraction")
            return None
        
        if not website_text or len(website_text.strip()) < 50:
            logger.warning("Website text too short for AI extraction")
            return None
        
        try:
            # Build prompt
            prompt = self._build_prompt(website_text)
            
            # Call LLM
            response = await self._call_llm(prompt)
            
            if not response:
                return None
            
            # Parse JSON from response
            data = self._parse_json(response)
            
            if data:
                logger.info(f"Successfully extracted data via LLM")
                return data
            else:
                logger.warning("Failed to parse LLM response as JSON")
                return None
        
        except Exception as e:
            logger.error(f"Error during LLM extraction: {e}", exc_info=True)
            return None
    
    def _build_prompt(self, website_text: str) -> str:
        """Build the user prompt with website content"""
        # Truncate if too long (most LLMs have token limits)
        max_chars = 8002  # Adjust based on your LLM's context window
        if len(website_text) > max_chars:
            website_text = website_text[:max_chars] + "\n[... content truncated ...]"
        
        return self.USER_PROMPT_TEMPLATE.format(website_content=website_text)
    
    async def _call_llm(self, prompt: str) -> Optional[str]:
        """Call LLM with prompt and return response"""
        try:
            # Example for OpenAI-style API
            if hasattr(self.llm_client, 'chat_completion'):
                response = await self.llm_client.chat_completion(
                    messages=[
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,  # Low temperature for consistent extraction
                    response_format={"type": "json_object"}  # If supported
                )
                return response
            else:
                # Fallback: try to call as async method
                response = await self.llm_client(prompt)
                return response
        except Exception as e:
            logger.error(f"Error calling LLM: {e}", exc_info=True)
            return None
    
    def _parse_json(self, raw_response: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON from LLM response (robust to extra text)
        
        Args:
            raw_response: Raw text from LLM (may contain extra text)
        
        Returns:
            Parsed JSON dictionary, or None if parsing fails
        """
        if not raw_response:
            return None
        
        raw_response = raw_response.strip()
        
        # Strategy 1: Try direct JSON parse
        try:
            return json.loads(raw_response)
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Find JSON object between first { and last }
        try:
            # Find first {
            start_idx = raw_response.find('{')
            if start_idx == -1:
                return None
            
            # Find last }
            end_idx = raw_response.rfind('}')
            if end_idx == -1 or end_idx < start_idx:
                return None
            
            # Extract candidate JSON
            candidate = raw_response[start_idx:end_idx + 1]
            return json.loads(candidate)
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Strategy 3: Try to extract JSON using regex (last resort)
        try:
            # Match JSON-like structure
            json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
            if json_match:
                candidate = json_match.group(0)
                # Try to clean up common issues
                candidate = candidate.replace(",\n}", "\n}")  # Remove trailing commas
                candidate = candidate.replace(",}", "}")
                return json.loads(candidate)
        except (json.JSONDecodeError, ValueError):
            pass
        
        logger.warning(f"Could not parse JSON from LLM response: {raw_response[:200]}...")
        return None
    
    def merge_with_lead(self, lead: Lead, extracted_data: Dict[str, Any]) -> Lead:
        """
        Merge extracted data into Lead object
        
        Args:
            lead: Existing Lead object
            extracted_data: Data extracted from LLM
        
        Returns:
            Updated Lead object
        """
        # Merge basic fields (only if missing or LLM found better data)
        if not lead.name and extracted_data.get("business_name"):
            lead.name = extracted_data["business_name"]
        
        # Merge emails (union)
        llm_emails = extracted_data.get("emails", [])
        existing_emails = set(lead.emails or [])
        llm_emails_lower = {email.lower().strip() for email in llm_emails if email}
        lead.emails = list(existing_emails | llm_emails_lower)
        
        # Merge phones (union)
        llm_phones = extracted_data.get("phones", [])
        existing_phones = set(lead.phones or [])
        lead.phones = list(existing_phones | {phone.strip() for phone in llm_phones if phone})
        
        # Merge address/city/country (only if missing)
        if not lead.address and extracted_data.get("address"):
            lead.address = extracted_data["address"]
        if not lead.city and extracted_data.get("city"):
            lead.city = extracted_data["city"]
        if not lead.country and extracted_data.get("country"):
            lead.country = extracted_data["country"]
        
        # Store AI-extracted data in metadata
        if not lead.metadata:
            lead.metadata = {}
        
        # Services and languages
        ai_services = extracted_data.get("services", [])
        existing_services = lead.metadata.get("services", [])
        lead.metadata["services"] = list(set(existing_services + ai_services))
        
        ai_languages = extracted_data.get("languages", [])
        existing_languages = lead.metadata.get("languages", [])
        lead.metadata["languages"] = list(set(existing_languages + ai_languages))
        
        # Social links (merge with existing)
        ai_social = extracted_data.get("social_links", {})
        existing_social = lead.social_links or {}
        merged_social = {**existing_social, **{k: v for k, v in ai_social.items() if v}}
        lead.social_links = merged_social
        
        # Notes
        if extracted_data.get("notes"):
            existing_notes = lead.outreach_notes or ""
            new_notes = extracted_data["notes"]
            if new_notes not in existing_notes:
                lead.outreach_notes = f"{existing_notes}\n{new_notes}".strip()
        
        return lead


class MockLLMClient:
    """Mock LLM client for testing without actual API calls"""
    
    async def chat_completion(self, messages, **kwargs):
        """Mock response for testing"""
        # Return a sample structured response
        return json.dumps({
            "business_name": "Mock Business",
            "emails": ["info@mockbusiness.com"],
            "phones": ["+1234567890"],
            "address": "123 Test St",
            "city": "Test City",
            "country": "Test Country",
            "services": ["service1", "service2"],
            "languages": ["English"],
            "social_links": {
                "facebook": "https://facebook.com/mock",
                "instagram": None,
                "linkedin": None,
                "twitter": None,
                "youtube": None,
                "other": []
            },
            "notes": "Mock business for testing"
        })

