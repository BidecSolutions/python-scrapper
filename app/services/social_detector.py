"""Social media links detection service"""
import re
from typing import Dict, Optional
from bs4 import BeautifulSoup
from urllib.parse import urlparse


class SocialDetector:
    """Detect social media links from HTML"""
    
    # Social platform patterns
    SOCIAL_PATTERNS = {
        "facebook": [
            r'facebook\.com/[^/\s"\'<>]+',
            r'fb\.com/[^/\s"\'<>]+',
        ],
        "instagram": [
            r'instagram\.com/[^/\s"\'<>]+',
        ],
        "twitter": [
            r'twitter\.com/[^/\s"\'<>]+',
            r'x\.com/[^/\s"\'<>]+',
        ],
        "linkedin": [
            r'linkedin\.com/(company|in|pub)/[^/\s"\'<>]+',
        ],
        "youtube": [
            r'youtube\.com/(channel|c|user)/[^/\s"\'<>]+',
            r'youtu\.be/[^/\s"\'<>]+',
        ],
        "tiktok": [
            r'tiktok\.com/@[^/\s"\'<>]+',
        ],
        "pinterest": [
            r'pinterest\.com/[^/\s"\'<>]+',
        ],
        "snapchat": [
            r'snapchat\.com/add/[^/\s"\'<>]+',
        ],
        "whatsapp": [
            r'wa\.me/[^/\s"\'<>]+',
            r'whatsapp\.com',
        ],
    }
    
    @classmethod
    def extract_social_links(cls, html: str, soup: Optional[BeautifulSoup] = None, base_url: Optional[str] = None) -> Dict[str, str]:
        """Extract social media links from HTML"""
        social_links: Dict[str, str] = {}
        
        # Extract from <a> tags
        if soup:
            for link in soup.find_all("a", href=True):
                href = link.get("href", "").strip()
                if not href:
                    continue
                
                # Make absolute URL if base_url provided
                if base_url and not href.startswith(("http://", "https://")):
                    from urllib.parse import urljoin
                    href = urljoin(base_url, href)
                
                # Match against patterns
                for platform, patterns in cls.SOCIAL_PATTERNS.items():
                    if platform in social_links:
                        continue  # Already found
                    
                    for pattern in patterns:
                        match = re.search(pattern, href, re.IGNORECASE)
                        if match:
                            # Clean up the URL
                            url = match.group(0)
                            if not url.startswith(("http://", "https://")):
                                url = "https://" + url
                            social_links[platform] = url
                            break
        
        # Also search in plain HTML text
        html_lower = html.lower()
        for platform, patterns in cls.SOCIAL_PATTERNS.items():
            if platform in social_links:
                continue  # Already found
            
            for pattern in patterns:
                matches = re.finditer(pattern, html_lower, re.IGNORECASE)
                for match in matches:
                    url = match.group(0)
                    if not url.startswith(("http://", "https://")):
                        url = "https://" + url
                    social_links[platform] = url
                    break
                if platform in social_links:
                    break
        
        return social_links
    
    @classmethod
    def normalize_social_url(cls, url: str, platform: str) -> str:
        """Normalize social media URL"""
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        # Ensure proper format for each platform
        if platform == "facebook" and "fb.com" in url:
            url = url.replace("fb.com", "facebook.com")
        elif platform == "twitter" and "x.com" in url:
            # Keep x.com as is (Twitter's new domain)
            pass
        
        return url

