"""Lead enrichment service - orchestrates all enrichment features"""
import re
from typing import Optional
from bs4 import BeautifulSoup
from app.core.models import Lead
from app.services.tech_detector import TechDetector
from app.services.social_detector import SocialDetector


class EnrichmentService:
    """Service to enrich leads with additional data"""
    
    @staticmethod
    def enrich_lead(lead: Lead, html: str, url: str) -> Lead:
        """Enrich a lead with tech stack, social links, and other data"""
        soup = BeautifulSoup(html, "html.parser")
        
        # Tech stack detection (enhanced)
        from app.services.enhanced_tech_detector import EnhancedTechDetector
        tech_data = EnhancedTechDetector.detect_all(html, soup)
        lead.cms = tech_data.get("cms", [None])[0] if tech_data.get("cms") else None
        lead.tech_stack = tech_data.get("frameworks", []) + tech_data.get("cms", [])
        lead.third_party_widgets = (
            tech_data.get("widgets", []) + 
            tech_data.get("analytics", []) + 
            tech_data.get("payment", []) + 
            tech_data.get("booking", [])
        )
        
        # Social links detection
        social_links = SocialDetector.extract_social_links(html, soup, url)
        lead.social_links = social_links
        lead.has_social = len(social_links) > 0
        
        # Compliance detection
        from app.services.compliance_detector import ComplianceDetector
        compliance = ComplianceDetector.detect_compliance(html, soup)
        compliance_tags = ComplianceDetector.get_compliance_tags(compliance)
        
        # Add compliance tags to lead tags
        if not lead.tags:
            lead.tags = []
        lead.tags.extend([tag for tag in compliance_tags if tag not in lead.tags])
        
        # Website quality scoring
        from app.services.website_quality_scorer import WebsiteQualityScorer
        quality = WebsiteQualityScorer.score_website(html, url, soup)
        # Store in meta for now (can add dedicated column later)
        if not lead.meta:
            lead.meta = {}
        lead.meta["website_quality"] = quality
        
        # Company size estimation (basic heuristics)
        lead.company_size = EnrichmentService._estimate_company_size(html, soup)
        
        # Service tags (basic keyword matching)
        lead.service_tags = EnrichmentService._extract_service_tags(html, lead.niche)
        
        # Contact person extraction (basic)
        contact_info = EnrichmentService._extract_contact_person(html, soup)
        if contact_info:
            lead.contact_person_name = contact_info.get("name")
            lead.contact_person_role = contact_info.get("role")
            lead.contact_person_email = contact_info.get("email")
        
        # Multi-location detection
        lead.is_multi_location = EnrichmentService._detect_multi_location(html, soup)
        if lead.is_multi_location:
            lead.branch_locations = EnrichmentService._extract_branch_locations(html, soup)
        
        # Quality flags
        lead.has_email = len(lead.emails) > 0
        lead.has_phone = len(lead.phones) > 0
        
        # Calculate quality score
        lead.quality_score = EnrichmentService._calculate_quality_score(lead)
        
        return lead
    
    @staticmethod
    def _estimate_company_size(html: str, soup: BeautifulSoup) -> Optional[str]:
        """Estimate company size from content"""
        html_lower = html.lower()
        text = soup.get_text().lower()
        
        # Look for team size mentions
        team_patterns = [
            (r'team of (\d+)', lambda m: int(m.group(1))),
            (r'(\d+) employees?', lambda m: int(m.group(1))),
            (r'(\d+) staff', lambda m: int(m.group(1))),
            (r'(\d+) doctors?', lambda m: int(m.group(1))),
            (r'(\d+) members?', lambda m: int(m.group(1))),
        ]
        
        for pattern, extractor in team_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    size = extractor(match)
                    if size == 1:
                        return "solo"
                    elif size <= 10:
                        return "small"
                    elif size <= 50:
                        return "medium"
                    else:
                        return "large"
                except:
                    continue
        
        # Heuristic: check for careers page or job listings
        if any(keyword in html_lower for keyword in ["careers", "join our team", "we're hiring"]):
            return "medium"  # Likely has some structure
        
        # Check for "about" page mentioning founders only
        if any(keyword in text for keyword in ["founded by", "established by"]):
            # Could be small or solo, default to small
            return "small"
        
        return None
    
    @staticmethod
    def _extract_service_tags(html: str, niche: Optional[str]) -> list:
        """Extract service tags based on niche"""
        if not niche:
            return []
        
        niche_lower = niche.lower()
        tags = []
        
        # Medical/Healthcare
        if any(kw in niche_lower for kw in ["doctor", "clinic", "hospital", "medical", "dental"]):
            medical_services = [
                "dermatology", "cardiology", "pediatrics", "orthopedics",
                "neurology", "oncology", "psychiatry", "radiology",
                "surgery", "gynecology", "urology", "ophthalmology"
            ]
            html_lower = html.lower()
            for service in medical_services:
                if service in html_lower:
                    tags.append(service)
        
        # Restaurant
        elif any(kw in niche_lower for kw in ["restaurant", "cafe", "dining", "food"]):
            restaurant_tags = [
                "pizza", "vegan", "vegetarian", "halal", "kosher",
                "fine dining", "casual", "fast food", "delivery",
                "takeout", "catering", "buffet"
            ]
            html_lower = html.lower()
            for tag in restaurant_tags:
                if tag in html_lower:
                    tags.append(tag)
        
        return tags
    
    @staticmethod
    def _extract_contact_person(html: str, soup: BeautifulSoup) -> Optional[dict]:
        """Extract contact person information"""
        # Look for common patterns in about/contact pages
        contact_sections = soup.find_all(["div", "section"], class_=re.compile(r"contact|about|team|staff", re.I))
        
        for section in contact_sections:
            text = section.get_text()
            # Simple heuristics - can be improved
            # Look for "Dr. Name" or "Name, Role"
            name_pattern = r'(?:Dr\.|Mr\.|Ms\.|Mrs\.)?\s*([A-Z][a-z]+ [A-Z][a-z]+)'
            matches = re.finditer(name_pattern, text)
            for match in matches:
                name = match.group(1)
                # Try to find role nearby
                role_patterns = ["director", "manager", "owner", "founder", "ceo", "clinic"]
                for role_pattern in role_patterns:
                    if role_pattern in text[max(0, match.start()-100):match.end()+100].lower():
                        return {
                            "name": name,
                            "role": role_pattern,
                            "email": None  # Would need more sophisticated extraction
                        }
        
        return None
    
    @staticmethod
    def _detect_multi_location(html: str, soup: BeautifulSoup) -> bool:
        """Detect if business has multiple locations"""
        html_lower = html.lower()
        text = soup.get_text().lower()
        
        indicators = [
            "multiple locations",
            "locations",
            "branches",
            "find us in",
            "visit us at",
            "our locations",
        ]
        
        return any(indicator in text or indicator in html_lower for indicator in indicators)
    
    @staticmethod
    def _extract_branch_locations(html: str, soup: BeautifulSoup) -> list:
        """Extract branch locations"""
        # Very basic - would need more sophisticated parsing
        locations = []
        # Look for location sections
        location_sections = soup.find_all(["div", "section"], class_=re.compile(r"location|branch", re.I))
        for section in location_sections:
            # Try to extract city names (simplified)
            text = section.get_text()
            # This is a placeholder - real implementation would use NER or structured data
        return locations
    
    @staticmethod
    def _calculate_quality_score(lead: Lead) -> float:
        """Calculate quality score 0-100"""
        score = 0.0
        
        # Email presence (30 points)
        if lead.has_email:
            score += 30
        
        # Phone presence (25 points)
        if lead.has_phone:
            score += 25
        
        # Website quality (20 points)
        if lead.website:
            score += 20
            # HTTPS bonus
            if lead.website.startswith("https://"):
                score += 5
        
        # Social links (10 points)
        if lead.has_social:
            score += 10
        
        # Complete contact info (10 points)
        if lead.contact_person_name or lead.contact_person_email:
            score += 10
        
        return min(100.0, score)

