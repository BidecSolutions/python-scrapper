"""Website quality & UX scoring model"""
import logging
import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class WebsiteQualityScorer:
    """Score website quality from UX/SEO perspective"""
    
    @staticmethod
    def score_website(html: str, url: str, soup: Optional[BeautifulSoup] = None) -> Dict:
        """
        Score website quality (0-100)
        
        Returns:
            {
                "score": 75,
                "grade": "C",
                "breakdown": {
                    "mobile": 20/20,
                    "security": 15/15,
                    "seo": 12/20,
                    "performance": 8/15,
                    "design": 10/15,
                    "content": 10/15
                },
                "issues": ["No HTTPS", "Missing meta description"],
                "suggestions": ["Add SSL certificate", "Improve page load speed"]
            }
        """
        if soup is None:
            soup = BeautifulSoup(html, "html.parser")
        
        breakdown = {}
        issues = []
        suggestions = []
        
        # Mobile Responsiveness (20 points)
        mobile_score = WebsiteQualityScorer._score_mobile(soup, html)
        breakdown["mobile"] = mobile_score
        if mobile_score < 15:
            issues.append("Mobile responsiveness issues")
            suggestions.append("Add responsive design and test on mobile devices")
        
        # Security (15 points)
        security_score = WebsiteQualityScorer._score_security(url, html)
        breakdown["security"] = security_score
        if security_score < 10:
            issues.append("Security concerns")
            suggestions.append("Enable HTTPS and add security headers")
        
        # SEO (20 points)
        seo_score = WebsiteQualityScorer._score_seo(soup, html)
        breakdown["seo"] = seo_score
        if seo_score < 12:
            issues.append("SEO optimization needed")
            suggestions.append("Add meta tags, improve headings structure")
        
        # Performance (15 points)
        performance_score = WebsiteQualityScorer._score_performance(html, soup)
        breakdown["performance"] = performance_score
        if performance_score < 10:
            issues.append("Performance issues")
            suggestions.append("Optimize images, reduce page weight, enable caching")
        
        # Design & UX (15 points)
        design_score = WebsiteQualityScorer._score_design(soup, html)
        breakdown["design"] = design_score
        if design_score < 10:
            issues.append("Design/UX improvements needed")
            suggestions.append("Add clear CTAs, improve navigation structure")
        
        # Content Quality (15 points)
        content_score = WebsiteQualityScorer._score_content(soup, html)
        breakdown["content"] = content_score
        if content_score < 10:
            issues.append("Content quality issues")
            suggestions.append("Improve content structure, add clear service descriptions")
        
        # Total score
        total_score = sum(breakdown.values())
        
        # Grade
        if total_score >= 90:
            grade = "A"
        elif total_score >= 75:
            grade = "B"
        elif total_score >= 60:
            grade = "C"
        elif total_score >= 45:
            grade = "D"
        else:
            grade = "F"
        
        return {
            "score": total_score,
            "grade": grade,
            "breakdown": breakdown,
            "issues": issues[:5],  # Top 5 issues
            "suggestions": suggestions[:5],  # Top 5 suggestions
        }
    
    @staticmethod
    def _score_mobile(soup: BeautifulSoup, html: str) -> int:
        """Score mobile responsiveness (0-20)"""
        score = 0
        
        # Viewport meta tag (5 points)
        viewport = soup.find("meta", attrs={"name": "viewport"})
        if viewport:
            score += 5
        
        # Mobile-friendly indicators (5 points)
        mobile_indicators = ["mobile-menu", "mobile-nav", "responsive", "mobile-friendly"]
        html_lower = html.lower()
        if any(indicator in html_lower for indicator in mobile_indicators):
            score += 5
        
        # Touch-friendly elements (5 points)
        # Check for large buttons/links (heuristic)
        buttons = soup.find_all(["button", "a"], class_=re.compile(r"btn|button|cta", re.I))
        if len(buttons) >= 3:
            score += 5
        
        # No horizontal scroll indicators (5 points)
        # If page has reasonable width constraints
        if "max-width" in html or "container" in html_lower:
            score += 5
        
        return min(20, score)
    
    @staticmethod
    def _score_security(url: str, html: str) -> int:
        """Score security (0-15)"""
        score = 0
        
        # HTTPS (10 points)
        if url.startswith("https://"):
            score += 10
        elif "ssl" in html.lower() or "secure" in html.lower():
            score += 5
        
        # Security headers mention (5 points)
        security_terms = ["security", "privacy policy", "data protection", "gdpr"]
        html_lower = html.lower()
        if any(term in html_lower for term in security_terms):
            score += 5
        
        return min(15, score)
    
    @staticmethod
    def _score_seo(soup: BeautifulSoup, html: str) -> int:
        """Score SEO (0-20)"""
        score = 0
        
        # Title tag (3 points)
        title = soup.find("title")
        if title and title.get_text().strip():
            title_text = title.get_text().strip()
            if 30 <= len(title_text) <= 60:
                score += 3
            elif title_text:
                score += 1
        
        # Meta description (3 points)
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            desc = meta_desc.get("content", "")
            if 120 <= len(desc) <= 160:
                score += 3
            elif desc:
                score += 1
        
        # H1 tag (2 points)
        h1 = soup.find("h1")
        if h1 and h1.get_text().strip():
            score += 2
        
        # Heading structure (3 points)
        headings = soup.find_all(["h1", "h2", "h3"])
        if len(headings) >= 3:
            score += 3
        elif len(headings) >= 1:
            score += 1
        
        # Alt text on images (3 points)
        images = soup.find_all("img")
        if images:
            images_with_alt = sum(1 for img in images if img.get("alt"))
            alt_ratio = images_with_alt / len(images) if images else 0
            score += int(3 * alt_ratio)
        
        # Meta keywords or structured data (3 points)
        if soup.find("meta", attrs={"name": "keywords"}) or "schema.org" in html.lower():
            score += 3
        
        # Open Graph / social meta (3 points)
        og_tags = soup.find_all("meta", attrs={"property": re.compile(r"^og:", re.I)})
        if len(og_tags) >= 2:
            score += 3
        
        return min(20, score)
    
    @staticmethod
    def _score_performance(html: str, soup: BeautifulSoup) -> int:
        """Score performance (0-15)"""
        score = 0
        
        # Page size (5 points)
        html_size = len(html)
        if html_size < 100000:  # < 100KB
            score += 5
        elif html_size < 500000:  # < 500KB
            score += 3
        elif html_size < 1000000:  # < 1MB
            score += 1
        
        # Image optimization indicators (5 points)
        images = soup.find_all("img")
        if images:
            # Check for lazy loading or optimized images
            lazy_loaded = sum(1 for img in images if img.get("loading") == "lazy")
            if lazy_loaded > 0:
                score += 3
            # Check for modern formats or CDN
            if any("cdn" in str(img.get("src", "")).lower() for img in images):
                score += 2
        
        # Script optimization (5 points)
        scripts = soup.find_all("script")
        if scripts:
            # Check for async/defer
            async_scripts = sum(1 for s in scripts if s.get("async") or s.get("defer"))
            if async_scripts > 0:
                score += 3
            # Reasonable number of scripts
            if len(scripts) < 10:
                score += 2
        
        return min(15, score)
    
    @staticmethod
    def _score_design(soup: BeautifulSoup, html: str) -> int:
        """Score design & UX (0-15)"""
        score = 0
        
        # Navigation structure (3 points)
        nav = soup.find("nav") or soup.find(class_=re.compile(r"nav|menu", re.I))
        if nav:
            score += 3
        
        # Call-to-action buttons (3 points)
        cta_indicators = ["cta", "button", "book now", "contact us", "get started"]
        html_lower = html.lower()
        if any(indicator in html_lower for indicator in cta_indicators):
            score += 3
        
        # Hero section or prominent header (3 points)
        hero_indicators = ["hero", "banner", "header", "jumbotron"]
        if any(indicator in html_lower for indicator in hero_indicators):
            score += 3
        
        # Footer (2 points)
        footer = soup.find("footer") or soup.find(class_=re.compile(r"footer", re.I))
        if footer:
            score += 2
        
        # Contact information visible (2 points)
        contact_indicators = ["contact", "phone", "email", "address"]
        if any(indicator in html_lower for indicator in contact_indicators):
            score += 2
        
        # Social media links (2 points)
        social_domains = ["facebook", "twitter", "instagram", "linkedin"]
        links = soup.find_all("a", href=True)
        social_links = sum(1 for a in links if any(domain in a.get("href", "").lower() for domain in social_domains))
        if social_links >= 2:
            score += 2
        
        return min(15, score)
    
    @staticmethod
    def _score_content(soup: BeautifulSoup, html: str) -> int:
        """Score content quality (0-15)"""
        score = 0
        
        # Text content length (5 points)
        text = soup.get_text()
        text_length = len(text.strip())
        if text_length > 1000:
            score += 5
        elif text_length > 500:
            score += 3
        elif text_length > 200:
            score += 1
        
        # Structured content (5 points)
        # Check for lists, sections
        lists = soup.find_all(["ul", "ol"])
        sections = soup.find_all(["section", "article", "main"])
        if len(lists) >= 2 or len(sections) >= 2:
            score += 5
        elif len(lists) >= 1 or len(sections) >= 1:
            score += 3
        
        # Service descriptions (5 points)
        service_indicators = ["service", "about", "what we do", "our services"]
        html_lower = html.lower()
        if any(indicator in html_lower for indicator in service_indicators):
            score += 5
        
        return min(15, score)

