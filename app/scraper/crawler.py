"""Synchronous web crawler"""
from collections import deque
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from app.core.config import settings
from app.utils.http import make_request, get_session


class SimpleCrawler:
    """Simple synchronous crawler for internal website links"""
    
    def __init__(self, max_pages: int = None, timeout: int = None):
        self.max_pages = max_pages or settings.DEFAULT_MAX_PAGES
        self.timeout = timeout or settings.DEFAULT_TIMEOUT
        self.session = get_session()
    
    def crawl(self, root_url: str):
        """Crawl a website starting from root_url"""
        visited = set()
        queue = deque([root_url])
        
        while queue and len(visited) < self.max_pages:
            url = queue.popleft()
            
            if url in visited:
                continue
            
            visited.add(url)
            
            try:
                response = make_request(url, session=self.session, timeout=self.timeout)
                if not response:
                    continue
            except Exception:
                continue
            
            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type:
                continue
            
            try:
                soup = BeautifulSoup(response.text, "html.parser")
            except Exception:
                continue
            
            yield url, soup
            
            # Discover internal links
            for a in soup.select("a[href]"):
                href = a.get("href")
                if not href:
                    continue
                
                absolute = urljoin(url, href)
                # Remove fragments
                absolute = absolute.split("#")[0]
                
                if self._same_domain(root_url, absolute) and absolute not in visited:
                    if absolute not in queue:
                        queue.append(absolute)
    
    def _same_domain(self, root: str, url: str) -> bool:
        """Check if URL is from the same domain as root"""
        try:
            root_domain = urlparse(root).netloc
            url_domain = urlparse(url).netloc
            # Handle www. variations
            root_domain = root_domain.replace("www.", "")
            url_domain = url_domain.replace("www.", "")
            return root_domain == url_domain
        except Exception:
            return False

