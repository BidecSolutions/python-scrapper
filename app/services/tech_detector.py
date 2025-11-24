"""Tech stack and digital maturity detection service"""
import logging
from typing import Dict, Optional, Any
from sqlalchemy.orm import Session
import re
import json

from app.core.orm import LeadORM

logger = logging.getLogger(__name__)


class TechDetector:
    """Service for detecting tech stack and digital maturity"""
    
    # Detection patterns
    CMS_PATTERNS = {
        "WordPress": [r"wp-content", r"wp-includes", r"wordpress", r"/wp-admin"],
        "Wix": [r"wixstatic", r"wix\.com", r"wixpress"],
        "Shopify": [r"shopify", r"cdn\.shopify\.com"],
        "Squarespace": [r"squarespace", r"sqs-cdn"],
        "Joomla": [r"joomla", r"/joomla/"],
        "Drupal": [r"drupal", r"/drupal/"],
    }
    
    TOOL_PATTERNS = {
        "Google Analytics": [r"googletagmanager\.com", r"gtag\(", r"ga\(", r"google-analytics"],
        "Google Tag Manager": [r"googletagmanager\.com/gtm\.js"],
        "Facebook Pixel": [r"facebook\.net", r"fbq\("],
        "Live Chat": [r"livechat", r"intercom", r"zendesk.*chat", r"drift", r"olark"],
        "Calendly": [r"calendly"],
        "WhatsApp": [r"wa\.me", r"whatsapp", r"api\.whatsapp\.com"],
        "Stripe": [r"stripe\.com", r"stripejs"],
        "PayPal": [r"paypal\.com"],
    }
    
    @staticmethod
    def detect_tech_stack(html_content: str, url: str) -> Dict[str, Any]:
        """
        Detect tech stack from HTML content
        
        Returns:
            Dict with cms, tools, and maturity indicators
        """
        html_lower = html_content.lower()
        
        # Detect CMS
        detected_cms = "Custom"
        for cms, patterns in TechDetector.CMS_PATTERNS.items():
            if any(re.search(pattern, html_lower) for pattern in patterns):
                detected_cms = cms
                break
        
        # Detect tools
        detected_tools = []
        for tool, patterns in TechDetector.TOOL_PATTERNS.items():
            if any(re.search(pattern, html_lower) for pattern in patterns):
                detected_tools.append(tool)
        
        # Compute maturity score (0-100)
        maturity_score = TechDetector._compute_maturity_score(
            detected_cms, detected_tools, html_content, url
        )
        
        # Generate notes
        notes = TechDetector._generate_maturity_notes(
            detected_cms, detected_tools, maturity_score
        )
        
        return {
            "cms": detected_cms,
            "tools": detected_tools,
            "maturity_score": maturity_score,
            "notes": notes,
        }
    
    @staticmethod
    def _compute_maturity_score(
        cms: str,
        tools: list,
        html_content: str,
        url: str
    ) -> float:
        """Compute digital maturity score (0-100)"""
        score = 0.0
        
        # CMS score (30 points)
        cms_scores = {
            "WordPress": 20,
            "Shopify": 25,
            "Wix": 15,
            "Squarespace": 20,
            "Custom": 30,  # Custom = likely more sophisticated
        }
        score += cms_scores.get(cms, 10)
        
        # Tools score (40 points)
        tool_scores = {
            "Google Analytics": 10,
            "Google Tag Manager": 5,
            "Live Chat": 10,
            "Calendly": 5,
            "WhatsApp": 5,
            "Stripe": 5,
        }
        for tool in tools:
            score += tool_scores.get(tool, 2)
        
        # HTTPS (10 points)
        if url.startswith("https://"):
            score += 10
        
        # Mobile responsiveness indicators (10 points)
        if any(indicator in html_content.lower() for indicator in ["viewport", "responsive", "mobile"]):
            score += 10
        
        # Modern features (10 points)
        if any(feature in html_content.lower() for feature in ["api", "json", "fetch", "async"]):
            score += 10
        
        return min(100.0, score)
    
    @staticmethod
    def _generate_maturity_notes(cms: str, tools: list, score: float) -> str:
        """Generate human-readable maturity notes"""
        if score >= 80:
            return "Highly digitalized with modern tools and infrastructure."
        elif score >= 60:
            return "Good digital presence with key tools in place."
        elif score >= 40:
            return "Basic digital setup, room for improvement."
        else:
            return "Limited digital maturity, significant opportunities."
    
    @staticmethod
    def enrich_lead_with_tech(
        db: Session,
        lead_id: int,
        html_content: Optional[str] = None
    ) -> bool:
        """
        Enrich a lead with tech stack detection
        
        Returns:
            True if successful
        """
        lead = db.query(LeadORM).filter(LeadORM.id == lead_id).first()
        if not lead or not lead.website:
            return False
        
        # Fetch HTML if not provided
        if not html_content:
            try:
                import httpx
                response = httpx.get(lead.website, timeout=10.0, follow_redirects=True)
                html_content = response.text
            except Exception as e:
                logger.warning(f"Failed to fetch HTML for lead {lead_id}: {e}")
                return False
        
        # Detect tech stack
        tech_data = TechDetector.detect_tech_stack(html_content, lead.website)
        
        # Optionally refine with AI
        try:
            tech_data = TechDetector._refine_with_ai(html_content, tech_data)
        except Exception as e:
            logger.warning(f"AI refinement failed: {e}")
        
        # Update lead
        lead.tech_stack = tech_data
        lead.digital_maturity = tech_data.get("maturity_score")
        db.commit()
        
        return True
    
    @staticmethod
    def _refine_with_ai(html_content: str, detected_data: Dict) -> Dict:
        """Refine tech detection with AI (optional enhancement)"""
        try:
            from app.ai.factory import create_llm_client
            llm_client = create_llm_client()
            
            if not llm_client:
                return detected_data
            
            # Use only first 2000 chars of HTML
            html_snippet = html_content[:2000]
            
            prompt = f"""You are analyzing a website's digital maturity and tech usage.

Detected flags:
{json.dumps(detected_data, indent=2)}

HTML snippet:
{html_snippet[:1000]}

Return JSON with:
- cms: string (refine if needed)
- tools: list of strings (add any missing tools)
- maturity_score: number 0-100 (refine based on HTML quality)
- notes: short text (1-2 sentences)

Respond as pure JSON only."""

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
                try:
                    ai_data = json.loads(result)
                    # Merge AI refinements
                    detected_data.update(ai_data)
                except:
                    pass
            
        except Exception as e:
            logger.warning(f"AI refinement error: {e}")
        
        return detected_data
