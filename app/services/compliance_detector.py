"""Compliance detection - GDPR, privacy policies, etc."""
import logging
import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ComplianceDetector:
    """Detect compliance-related content on websites"""
    
    # Compliance patterns
    COMPLIANCE_PATTERNS = {
        "gdpr": [
            r"gdpr",
            r"general data protection regulation",
            r"eu data protection",
            r"right to be forgotten",
            r"data subject rights",
        ],
        "ccpa": [
            r"ccpa",
            r"california consumer privacy act",
            r"do not sell my personal information",
        ],
        "privacy_policy": [
            r"privacy policy",
            r"privacy notice",
            r"data protection",
            r"how we use your data",
        ],
        "cookie_consent": [
            r"cookie policy",
            r"cookie consent",
            r"accept cookies",
            r"cookie banner",
        ],
        "terms_of_service": [
            r"terms of service",
            r"terms and conditions",
            r"terms of use",
        ],
        "medical_consent": [
            r"informed consent",
            r"patient consent",
            r"medical disclaimer",
            r"health information",
        ],
        "hipaa": [
            r"hipaa",
            r"health insurance portability",
            r"protected health information",
        ],
    }
    
    @staticmethod
    def detect_compliance(html: str, soup: Optional[BeautifulSoup] = None) -> Dict[str, bool]:
        """
        Detect compliance-related content
        
        Returns:
            {
                "has_gdpr": True/False,
                "has_ccpa": True/False,
                "has_privacy_policy": True/False,
                "has_cookie_consent": True/False,
                "has_terms_of_service": True/False,
                "has_medical_consent": True/False,
                "has_hipaa": True/False,
            }
        """
        if soup is None:
            soup = BeautifulSoup(html, "html.parser")
        
        html_lower = html.lower()
        text_content = soup.get_text().lower()
        
        detected = {}
        
        for compliance_type, patterns in ComplianceDetector.COMPLIANCE_PATTERNS.items():
            found = False
            for pattern in patterns:
                if re.search(pattern, html_lower, re.IGNORECASE) or \
                   re.search(pattern, text_content, re.IGNORECASE):
                    found = True
                    break
            
            # Also check for links
            if not found:
                links = soup.find_all("a", href=True)
                link_texts = " ".join([a.get_text().lower() for a in links])
                for pattern in patterns:
                    if re.search(pattern, link_texts, re.IGNORECASE):
                        found = True
                        break
            
            detected[f"has_{compliance_type}"] = found
        
        return detected
    
    @staticmethod
    def get_compliance_tags(compliance: Dict) -> List[str]:
        """Convert compliance dict to tag list"""
        tags = []
        for key, value in compliance.items():
            if value:
                tag = key.replace("has_", "").upper()
                tags.append(tag)
        return tags
    
    @staticmethod
    def get_compliance_summary(compliance: Dict) -> str:
        """Generate human-readable compliance summary"""
        items = []
        
        if compliance.get("has_gdpr"):
            items.append("GDPR")
        if compliance.get("has_ccpa"):
            items.append("CCPA")
        if compliance.get("has_privacy_policy"):
            items.append("Privacy Policy")
        if compliance.get("has_cookie_consent"):
            items.append("Cookie Consent")
        if compliance.get("has_terms_of_service"):
            items.append("Terms of Service")
        if compliance.get("has_medical_consent"):
            items.append("Medical Consent")
        if compliance.get("has_hipaa"):
            items.append("HIPAA")
        
        if items:
            return ", ".join(items)
        return "No compliance signals detected"

