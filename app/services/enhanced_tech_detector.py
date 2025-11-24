"""Enhanced tech stack detection with deeper analysis"""
import logging
import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class EnhancedTechDetector:
    """Enhanced tech stack detection with AI-powered analysis"""
    
    # Known tech patterns
    TECH_PATTERNS = {
        "cms": {
            "wordpress": [r"wp-content", r"wp-includes", r"/wp-admin", r"wordpress"],
            "wix": [r"wix\.com", r"wixstatic", r"wix-code"],
            "shopify": [r"shopify", r"cdn\.shopify", r"myshopify"],
            "squarespace": [r"squarespace", r"sqs-"],
            "drupal": [r"drupal", r"/sites/", r"drupal\.js"],
            "joomla": [r"joomla", r"/components/"],
        },
        "frameworks": {
            "react": [r"react", r"__REACT", r"react-dom"],
            "vue": [r"vue\.js", r"vuejs", r"__VUE__"],
            "angular": [r"angular", r"ng-", r"@angular"],
            "jquery": [r"jquery", r"\$\(\)"],
        },
        "analytics": {
            "google_analytics": [r"ga\(|gtag|google-analytics", r"UA-\d+", r"G-[A-Z0-9]+"],
            "facebook_pixel": [r"fbq\(", r"facebook\.net/tr"],
            "hotjar": [r"hotjar", r"hj\(\)"],
        },
        "widgets": {
            "calendly": [r"calendly", r"calendly\.com"],
            "intercom": [r"intercom", r"Intercom\("],
            "zendesk": [r"zendesk", r"zE\("],
            "livechat": [r"livechat", r"livechatinc"],
            "whatsapp": [r"wa\.me", r"whatsapp\.com/send", r"api\.whatsapp"],
            "chatbot": [r"chatbot", r"chat-widget", r"drift"],
        },
        "payment": {
            "stripe": [r"stripe", r"stripe\.com"],
            "paypal": [r"paypal", r"paypalobjects"],
            "square": [r"square", r"squareup\.com"],
        },
        "booking": {
            "opentable": [r"opentable", r"opentable\.com"],
            "resy": [r"resy", r"resy\.com"],
            "acuity": [r"acuity", r"acuityscheduling"],
        },
    }
    
    @staticmethod
    def detect_all(html: str, soup: Optional[BeautifulSoup] = None) -> Dict[str, List[str]]:
        """
        Enhanced tech stack detection
        
        Returns:
            {
                "cms": ["wordpress"],
                "frameworks": ["react", "jquery"],
                "analytics": ["google_analytics", "facebook_pixel"],
                "widgets": ["calendly", "whatsapp"],
                "payment": ["stripe"],
                "booking": ["opentable"],
                "security": ["ssl", "https"],
                "mobile": ["responsive", "mobile-friendly"],
            }
        """
        if soup is None:
            soup = BeautifulSoup(html, "html.parser")
        
        html_lower = html.lower()
        detected = {
            "cms": [],
            "frameworks": [],
            "analytics": [],
            "widgets": [],
            "payment": [],
            "booking": [],
            "security": [],
            "mobile": [],
        }
        
        # Detect each category
        for category, techs in EnhancedTechDetector.TECH_PATTERNS.items():
            for tech_name, patterns in techs.items():
                for pattern in patterns:
                    if re.search(pattern, html_lower, re.IGNORECASE):
                        detected[category].append(tech_name)
                        break  # Found, move to next tech
        
        # Security detection
        if "https://" in html or "ssl" in html_lower:
            detected["security"].append("ssl")
        
        # Mobile detection
        viewport = soup.find("meta", attrs={"name": "viewport"})
        if viewport:
            detected["mobile"].append("responsive")
        
        # Check for mobile-specific classes/indicators
        if any(mobile_indicator in html_lower for mobile_indicator in ["mobile-menu", "mobile-nav", "responsive"]):
            detected["mobile"].append("mobile-friendly")
        
        # Remove duplicates
        for key in detected:
            detected[key] = list(set(detected[key]))
        
        return detected
    
    @staticmethod
    def get_tech_summary(tech_stack: Dict[str, List[str]]) -> str:
        """Generate human-readable tech stack summary"""
        parts = []
        
        if tech_stack.get("cms"):
            parts.append(f"CMS: {', '.join(tech_stack['cms'])}")
        
        if tech_stack.get("frameworks"):
            parts.append(f"Framework: {', '.join(tech_stack['frameworks'])}")
        
        if tech_stack.get("analytics"):
            parts.append(f"Analytics: {', '.join(tech_stack['analytics'])}")
        
        if tech_stack.get("widgets"):
            parts.append(f"Widgets: {', '.join(tech_stack['widgets'])}")
        
        if tech_stack.get("payment"):
            parts.append(f"Payment: {', '.join(tech_stack['payment'])}")
        
        if tech_stack.get("booking"):
            parts.append(f"Booking: {', '.join(tech_stack['booking'])}")
        
        return " • ".join(parts) if parts else "Basic website"

