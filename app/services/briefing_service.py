"""Auto-generated account briefings for sales reps"""
import logging
from typing import Dict, Optional
from sqlalchemy.orm import Session

from app.core.orm import LeadORM

logger = logging.getLogger(__name__)


class BriefingService:
    """Generate AI-powered account briefings"""
    
    @staticmethod
    def generate_briefing(
        db: Session,
        lead_id: int
    ) -> Optional[Dict[str, str]]:
        """
        Generate a 1-page account briefing for a lead
        
        Returns:
            {
                "overview": "...",
                "services": "...",
                "digital_maturity": "...",
                "suggested_angle": "...",
                "key_contacts": "..."
            }
        """
        lead = db.query(LeadORM).filter(LeadORM.id == lead_id).first()
        if not lead:
            return None
        
        # Collect lead data
        lead_data = {
            "name": lead.name or "Unknown",
            "niche": lead.niche or "",
            "city": lead.city or "",
            "country": lead.country or "",
            "website": lead.website or "",
            "emails": lead.emails or [],
            "phones": lead.phones or [],
            "address": lead.address or "",
            "services": lead.service_tags or [],
            "tags": lead.tags or [],
            "social_links": lead.social_links or {},
            "tech_stack": lead.tech_stack or [],
            "cms": lead.cms or "",
            "has_online_booking": "online_booking" in (lead.tags or []),
            "has_live_chat": any("chat" in str(w).lower() for w in (lead.third_party_widgets or [])),
            "company_size": lead.company_size or "",
            "quality_score": float(lead.quality_score) if lead.quality_score else None,
        }
        
        # Generate briefing using LLM
        briefing = BriefingService._generate_with_llm(lead_data)
        
        if not briefing:
            # Fallback to template-based briefing
            briefing = BriefingService._generate_fallback(lead_data)
        
        return briefing
    
    @staticmethod
    def _generate_with_llm(lead_data: Dict) -> Optional[Dict]:
        """Generate briefing using LLM"""
        try:
            from app.ai.factory import create_llm_client
            llm_client = create_llm_client()
            
            if not llm_client:
                return None
            
            prompt = f"""Generate a concise 1-page account briefing for a sales rep.

Business Information:
- Name: {lead_data['name']}
- Niche: {lead_data['niche']}
- Location: {lead_data['city']}, {lead_data['country']}
- Website: {lead_data['website']}
- Services: {', '.join(lead_data['services'][:10])}
- Tags: {', '.join(lead_data['tags'][:10])}
- Tech Stack: {', '.join(lead_data['tech_stack'][:5])}
- CMS: {lead_data['cms']}
- Has Online Booking: {lead_data['has_online_booking']}
- Has Live Chat: {lead_data['has_live_chat']}
- Company Size: {lead_data['company_size']}
- Quality Score: {lead_data['quality_score']}

Generate a briefing with these sections (keep each section 2-3 sentences):

1. Overview: Brief description of the business
2. Services: Key services and specialties
3. Digital Maturity: Assessment of their online presence and tools
4. Suggested Angle: What to talk about in outreach (be specific)
5. Key Contacts: Available contact methods

Format as JSON:
{{
  "overview": "...",
  "services": "...",
  "digital_maturity": "...",
  "suggested_angle": "...",
  "key_contacts": "..."
}}"""

            import asyncio
            import inspect
            if inspect.iscoroutinefunction(llm_client.chat_completion):
                result = asyncio.run(llm_client.chat_completion([
                    {"role": "user", "content": prompt}
                ], temperature=0.7))
            else:
                result = llm_client.chat_completion([
                    {"role": "user", "content": prompt}
                ], temperature=0.7)
            
            if result:
                import json
                import re
                # Extract JSON
                json_match = re.search(r'\{[^}]+\}', result, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group())
                    return parsed
            
        except Exception as e:
            logger.warning(f"LLM briefing generation failed: {e}")
        
        return None
    
    @staticmethod
    def _generate_fallback(lead_data: Dict) -> Dict:
        """Generate template-based briefing if LLM fails"""
        overview = f"{lead_data['name']} is a {lead_data['niche']} business"
        if lead_data['city']:
            overview += f" located in {lead_data['city']}"
        if lead_data['country']:
            overview += f", {lead_data['country']}"
        overview += "."
        
        services = "Services: " + ", ".join(lead_data['services'][:5]) if lead_data['services'] else "Services not specified."
        
        digital = []
        if lead_data['cms']:
            digital.append(f"Uses {lead_data['cms']} CMS")
        if lead_data['has_online_booking']:
            digital.append("Has online booking")
        if lead_data['has_live_chat']:
            digital.append("Has live chat")
        if lead_data['tech_stack']:
            digital.append(f"Tech stack: {', '.join(lead_data['tech_stack'][:3])}")
        digital_maturity = ". ".join(digital) if digital else "Basic online presence."
        
        angle = f"Focus on how your solution can help {lead_data['niche']} businesses"
        if not lead_data['has_online_booking']:
            angle += " improve their online booking capabilities"
        elif not lead_data['has_live_chat']:
            angle += " enhance customer engagement with live chat"
        else:
            angle += " optimize their digital operations"
        angle += "."
        
        contacts = []
        if lead_data['emails']:
            contacts.append(f"Email: {lead_data['emails'][0]}")
        if lead_data['phones']:
            contacts.append(f"Phone: {lead_data['phones'][0]}")
        if lead_data['website']:
            contacts.append(f"Website: {lead_data['website']}")
        key_contacts = " | ".join(contacts) if contacts else "Contact information not available."
        
        return {
            "overview": overview,
            "services": services,
            "digital_maturity": digital_maturity,
            "suggested_angle": angle,
            "key_contacts": key_contacts,
        }

