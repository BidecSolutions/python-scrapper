"""AI Lead Dossier generation service"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup

from app.ai.factory import create_llm_client

logger = logging.getLogger(__name__)


class DossierService:
    """Service for generating deep research dossiers"""
    
    @staticmethod
    def generate_dossier(lead, db) -> Dict[str, Any]:
        """
        Generate a comprehensive dossier for a lead
        
        Args:
            lead: LeadORM instance
            db: Database session
        
        Returns:
            Dict with dossier sections
        """
        llm_client = create_llm_client()
        
        if not llm_client:
            raise ValueError("LLM client not available")
        
        # 1. Collect raw data
        context = DossierService._collect_context(lead)
        
        # 2. Generate dossier with LLM
        sections = DossierService._call_llm_for_dossier(context, llm_client)
        
        return sections
    
    @staticmethod
    def _collect_context(lead) -> Dict[str, Any]:
        """Collect all available context about a lead"""
        context = {
            "lead": {
                "name": lead.name,
                "niche": lead.niche,
                "location": f"{lead.city or ''}, {lead.country or ''}".strip(", "),
                "website": lead.website,
                "description": lead.meta.get("description", "") if lead.meta else "",
            },
            "tech": {},
            "website_text": "",
            "social_posts": [],
        }
        
        # Fetch website content if available
        if lead.website:
            try:
                response = requests.get(lead.website, timeout=10, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    # Extract main text
                    for script in soup(["script", "style"]):
                        script.decompose()
                    text = soup.get_text()
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text = " ".join(chunk for chunk in chunks if chunk)
                    context["website_text"] = text[:10000]  # Limit to 10k chars
                    
                    # Extract tech stack hints
                    tech_hints = {}
                    if "wordpress" in text.lower():
                        tech_hints["cms"] = "WordPress"
                    if "shopify" in text.lower():
                        tech_hints["ecommerce"] = "Shopify"
                    context["tech"] = tech_hints
            except Exception as e:
                logger.warning(f"Failed to fetch website for {lead.website}: {e}")
        
        # Add tech stack from lead if available
        if lead.tech_stack and isinstance(lead.tech_stack, dict):
            context["tech"].update(lead.tech_stack)
        
        return context
    
    @staticmethod
    def _call_llm_for_dossier(context: Dict[str, Any], llm_client) -> Dict[str, Any]:
        """Call LLM to generate dossier sections"""
        system_prompt = """You are an expert business analyst and sales strategist. You analyze companies and generate comprehensive research dossiers for sales teams.

Generate a structured dossier with the following sections:
- overview: Brief 2-3 sentence summary of the company
- offer: What products/services they offer
- audience: Who their target customers are
- digital_presence: Assessment of their online presence and digital maturity
- social_topics: List of 3-5 topics they frequently discuss on social media
- risks: Potential risks or constraints (e.g., small team, limited budget, etc.)
- angle: Recommended outreach angle/pitch strategy
- email: Draft email template for outreach
- linkedin_dm: Draft LinkedIn DM template

Return ONLY valid JSON with these exact keys. Be concise but insightful."""

        user_prompt = f"""Analyze this company and generate a sales dossier:

Company: {context['lead']['name']}
Niche: {context['lead']['niche'] or 'Unknown'}
Location: {context['lead']['location'] or 'Unknown'}
Website: {context['lead']['website'] or 'N/A'}

Website Content (excerpt):
{context['website_text'][:5000] if context['website_text'] else 'No website content available'}

Tech Stack: {context.get('tech', {})}

Generate a comprehensive dossier in JSON format."""

        try:
            response = llm_client.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
            )
            
            content = response.get("content", "") or response.get("message", {}).get("content", "")
            
            # Parse JSON (handle markdown code blocks)
            content = content.strip()
            if content.startswith("```"):
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
            
            import json
            import re
            
            try:
                sections = json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON object
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    sections = json.loads(json_match.group())
                else:
                    raise ValueError("Could not parse JSON from LLM response")
            
            # Ensure all required keys exist
            required_keys = ["overview", "offer", "audience", "digital_presence", "social_topics", "risks", "angle", "email", "linkedin_dm"]
            for key in required_keys:
                if key not in sections:
                    sections[key] = "Not available"
            
            # Ensure social_topics is a list
            if isinstance(sections.get("social_topics"), str):
                sections["social_topics"] = [sections["social_topics"]]
            
            return sections
            
        except Exception as e:
            logger.error(f"Failed to generate dossier with LLM: {e}")
            # Return fallback
            return {
                "overview": f"{context['lead']['name']} is a company in the {context['lead']['niche'] or 'general'} niche.",
                "offer": "Products/services information not available.",
                "audience": "Target audience information not available.",
                "digital_presence": "Digital presence assessment not available.",
                "social_topics": [],
                "risks": "No specific risks identified.",
                "angle": f"Focus on how your solution can help {context['lead']['name']} improve their operations.",
                "email": f"Subject: Partnership opportunity\n\nHi,\n\nI noticed {context['lead']['name']} and thought there might be a good fit...",
                "linkedin_dm": f"Hi, I saw {context['lead']['name']} and thought you might be interested in...",
            }

