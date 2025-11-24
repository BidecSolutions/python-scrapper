"""AI service for generating robot schemas and workflows from natural language"""
import logging
from typing import Dict, Any, List, Optional
import json
import re

from app.ai.factory import create_llm_client

logger = logging.getLogger(__name__)


class RobotsAIService:
    """Service for AI-powered robot generation"""
    
    @staticmethod
    async def generate_robot_from_prompt(
        prompt: str,
        sample_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate robot schema and workflow from natural language prompt
        
        Args:
            prompt: User's natural language description
            sample_url: Optional sample URL for context
        
        Returns:
            Dict with 'schema' and 'workflow_spec'
        """
        llm_client = create_llm_client()
        
        if not llm_client:
            logger.warning("LLM client not available, using fallback schema generation")
            return RobotsAIService._generate_fallback_schema(prompt)
        
        # Build prompt for LLM
        system_prompt = """You are an expert web scraping engineer. You help define scraping robots for lead generation.

You receive:
- A natural language description of what the user wants
- A sample URL of a page showing the structure (optional)

You must output **valid JSON** with two keys:
- "schema": list of fields the robot should extract. Each field: { "name": "field_name", "type": "string|number|boolean", "required": true|false }
- "workflow_spec": a JSON config describing how to scrape. Use CSS selectors. Structure:
  {
    "source": "html_list_page" or "html_single_page",
    "item_selector": "CSS selector for each item (if list page)",
    "fields": {
      "field_name": {
        "type": "css_text" or "css_attr" or "regex" or "static",
        "selector": "CSS selector",
        "attr": "attribute name (if css_attr)",
        "pattern": "regex pattern (if regex)",
        "value": "static value (if static)"
      }
    },
    "pagination": {
      "type": "link_selector" or "none",
      "selector": "CSS selector for next link"
    }
  }

Output ONLY valid JSON, no markdown, no code blocks."""

        user_prompt = f"""User description:
{prompt}
"""
        
        if sample_url:
            user_prompt += f"""
Sample URL:
{sample_url}
"""
        
        try:
            # Call LLM (async)
            response = await llm_client.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
            )
            
            # Handle response - could be string or dict
            if isinstance(response, str):
                content = response
            elif isinstance(response, dict):
                content = response.get("content", "") or response.get("message", {}).get("content", "") or str(response)
            else:
                content = str(response) if response else ""
            
            if not content:
                logger.warning("Empty response from LLM, using fallback")
                return RobotsAIService._generate_fallback_schema(prompt)
            
            # Try to parse JSON (might be wrapped in markdown code blocks)
            content = content.strip()
            if content.startswith("```"):
                # Extract JSON from code block
                lines = content.split("\n")
                json_lines = []
                in_json = False
                for line in lines:
                    if line.strip().startswith("```"):
                        in_json = not in_json
                        continue
                    if in_json:
                        json_lines.append(line)
                content = "\n".join(json_lines)
            
            # Parse JSON
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # Try to find JSON object in text
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    raise ValueError("Could not parse JSON from LLM response")
            
            # Validate structure
            if "schema" not in result or "workflow_spec" not in result:
                raise ValueError("LLM response missing 'schema' or 'workflow_spec'")
            
            # Ensure schema is a list
            if not isinstance(result["schema"], list):
                raise ValueError("Schema must be a list")
            
            # Ensure workflow_spec is a dict
            if not isinstance(result["workflow_spec"], dict):
                raise ValueError("workflow_spec must be a dict")
            
            return {
                "schema": result["schema"],
                "workflow_spec": result["workflow_spec"],
            }
            
        except Exception as e:
            logger.error(f"Failed to generate robot with AI: {e}")
            # Return a fallback schema
            return RobotsAIService._generate_fallback_schema(prompt)
    
    @staticmethod
    def _generate_fallback_schema(prompt: str) -> Dict[str, Any]:
        """Generate a simple fallback schema when LLM fails"""
        # Simple keyword-based extraction
        prompt_lower = prompt.lower()
        
        schema = []
        workflow_spec = {
            "source": "html_list_page",
            "item_selector": "article, .item, .result, .listing, .card, .business-card, [class*='result'], [class*='listing']",
            "fields": {},
        }
        
        # Common fields - check for exact matches first
        if any(word in prompt_lower for word in ["name", "title", "business", "doctor", "clinic", "restaurant"]):
            schema.append({"name": "name", "type": "string", "required": True})
            workflow_spec["fields"]["name"] = {
                "type": "css_text",
                "selector": "h1, h2, h3, .name, .title, .business-name, [class*='name'], [class*='title'], a[href]",
            }
        
        if any(word in prompt_lower for word in ["phone", "tel", "telephone", "phone number", "contact"]):
            schema.append({"name": "phone", "type": "string", "required": False})
            workflow_spec["fields"]["phone"] = {
                "type": "css_text",
                "selector": ".phone, .tel, [class*='phone'], [class*='tel'], [href^='tel:']",
            }
            # Also try regex extraction from text
            workflow_spec["fields"]["phone_regex"] = {
                "type": "regex",
                "pattern": r"[\d\s\-\+\(\)]{10,}",
            }
        
        if any(word in prompt_lower for word in ["email", "e-mail", "mail"]):
            schema.append({"name": "email", "type": "string", "required": False})
            workflow_spec["fields"]["email"] = {
                "type": "regex",
                "pattern": r"[\w\.-]+@[\w\.-]+\.\w+",
            }
        
        if any(word in prompt_lower for word in ["website", "url", "link", "web"]):
            schema.append({"name": "website", "type": "string", "required": False})
            workflow_spec["fields"]["website"] = {
                "type": "css_attr",
                "selector": "a[href*='http'], .website a, [class*='website'] a",
                "attr": "href",
            }
        
        if any(word in prompt_lower for word in ["address", "location", "city", "street"]):
            schema.append({"name": "address", "type": "string", "required": False})
            workflow_spec["fields"]["address"] = {
                "type": "css_text",
                "selector": ".address, [class*='address'], [class*='location'], [class*='street']",
            }
        
        if any(word in prompt_lower for word in ["rating", "score", "stars", "review"]):
            schema.append({"name": "rating", "type": "number", "required": False})
            workflow_spec["fields"]["rating"] = {
                "type": "css_text",
                "selector": "[class*='rating'], [class*='star'], [class*='review']",
            }
        
        # Default: at least name field
        if not schema:
            schema.append({"name": "name", "type": "string", "required": True})
            workflow_spec["fields"]["name"] = {
                "type": "css_text",
                "selector": "h1, h2, h3, .title, .name",
            }
        
        return {
            "schema": schema,
            "workflow_spec": workflow_spec,
        }

