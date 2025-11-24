"""Multi-channel pitch generator for outreach"""
import logging
from typing import Dict, Optional, List
from sqlalchemy.orm import Session

from app.core.orm import LeadORM

logger = logging.getLogger(__name__)


class PitchGenerator:
    """Generate multi-channel pitches (email, LinkedIn, phone)"""
    
    @staticmethod
    def generate_pitches(
        db: Session,
        lead_id: int,
        service_offering: Optional[str] = None,
        tone: str = "professional"
    ) -> Dict[str, str]:
        """
        Generate pitches for multiple channels
        
        Args:
            lead_id: Lead to generate pitches for
            service_offering: What service you're offering (e.g., "SEO services")
            tone: "professional", "friendly", "casual"
        
        Returns:
            {
                "email": "...",
                "linkedin": "...",
                "phone": "..."
            }
        """
        lead = db.query(LeadORM).filter(LeadORM.id == lead_id).first()
        if not lead:
            return {}
        
        # Collect lead context
        context = {
            "name": lead.name or "there",
            "niche": lead.niche or "",
            "city": lead.city or "",
            "country": lead.country or "",
            "services": lead.service_tags or [],
            "tags": lead.tags or [],
            "website": lead.website or "",
            "has_online_booking": "online_booking" in (lead.tags or []),
            "has_live_chat": any("chat" in str(w).lower() for w in (lead.third_party_widgets or [])),
            "cms": lead.cms or "",
            "tech_stack": lead.tech_stack or [],
        }
        
        # Generate pitches using LLM
        pitches = PitchGenerator._generate_with_llm(context, service_offering, tone)
        
        if not pitches:
            # Fallback to templates
            pitches = PitchGenerator._generate_fallback(context, service_offering, tone)
        
        return pitches
    
    @staticmethod
    def _generate_with_llm(
        context: Dict,
        service_offering: Optional[str],
        tone: str
    ) -> Optional[Dict[str, str]]:
        """Generate pitches using LLM"""
        try:
            from app.ai.factory import create_llm_client
            llm_client = create_llm_client()
            
            if not llm_client:
                return None
            
            service_desc = service_offering or "digital marketing and web services"
            
            prompt = f"""Generate personalized outreach pitches for a {context['niche']} business.

Business: {context['name']}
Location: {context['city']}, {context['country']}
Services: {', '.join(context['services'][:5])}
Website: {context['website']}
Has Online Booking: {context['has_online_booking']}
Has Live Chat: {context['has_live_chat']}
Tech Stack: {', '.join(context['tech_stack'][:3])}

Service Offering: {service_desc}
Tone: {tone}

Generate three versions:

1. EMAIL (2-3 short paragraphs, professional but warm):
   - Subject line
   - Opening that shows you researched them
   - Value proposition
   - Clear call-to-action

2. LINKEDIN DM (1-2 short paragraphs, conversational):
   - Friendly opening
   - Quick value pitch
   - Soft CTA

3. PHONE SCRIPT (bullet points, conversational):
   - Opening line
   - Key talking points (3-4 bullets)
   - Objection handling (1-2 bullets)
   - Closing

Format as JSON:
{{
  "email": {{
    "subject": "...",
    "body": "..."
  }},
  "linkedin": "...",
  "phone": "..."
}}

Make it specific to their business, not generic."""

            import asyncio
            import inspect
            if inspect.iscoroutinefunction(llm_client.chat_completion):
                result = asyncio.run(llm_client.chat_completion([
                    {"role": "user", "content": prompt}
                ], temperature=0.8))
            else:
                result = llm_client.chat_completion([
                    {"role": "user", "content": prompt}
                ], temperature=0.8)
            
            if result:
                import json
                import re
                # Extract JSON
                json_match = re.search(r'\{[^}]+\}', result, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group())
                    # Handle nested email structure
                    if isinstance(parsed.get("email"), dict):
                        return {
                            "email_subject": parsed["email"].get("subject", ""),
                            "email_body": parsed["email"].get("body", ""),
                            "linkedin": parsed.get("linkedin", ""),
                            "phone": parsed.get("phone", ""),
                        }
                    return parsed
            
        except Exception as e:
            logger.warning(f"LLM pitch generation failed: {e}")
        
        return None
    
    @staticmethod
    def _generate_fallback(
        context: Dict,
        service_offering: Optional[str],
        tone: str
    ) -> Dict[str, str]:
        """Generate template-based pitches"""
        service = service_offering or "digital marketing services"
        name = context['name'] or "there"
        niche = context['niche'] or "business"
        
        # Email
        email_subject = f"Quick question about {niche} growth"
        email_body = f"""Hi {name.split()[0] if name else 'there'},

I noticed {context['name'] or 'your business'} in {context['city'] or 'your area'} and was impressed by your {niche} services.

I specialize in {service} and have helped similar businesses increase their online visibility and customer engagement.

Would you be open to a quick 15-minute call to discuss how we might help {context['name'] or 'you'} reach more customers?

Best regards"""
        
        # LinkedIn
        linkedin = f"""Hi! I came across {context['name'] or 'your business'} and thought you might be interested in {service} for {niche} businesses. 

I've helped similar businesses in {context['city'] or 'your area'} grow their online presence. Would love to chat if you're open to it!"""
        
        # Phone
        phone = f"""Opening: "Hi, is this {name}? This is [Your Name] calling about digital marketing opportunities."

Key Points:
• Noticed their {niche} business in {context['city'] or 'the area'}
• Specialize in {service}
• Have helped similar businesses grow
• Quick 15-min call to see if there's a fit

Objection Handling:
• "Just exploring" → "Understood, I'll send a quick email with info"
• "Not interested" → "No problem, thanks for your time"

Closing: "Would you be open to a brief conversation, or should I send some information via email?" """
        
        return {
            "email_subject": email_subject,
            "email_body": email_body,
            "linkedin": linkedin,
            "phone": phone,
        }

