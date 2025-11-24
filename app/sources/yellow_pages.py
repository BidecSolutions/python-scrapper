"""YellowPages directory source"""
from typing import Iterable, Optional
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from app.core.models import Lead
from app.sources.base import SourceBase
import logging

logger = logging.getLogger(__name__)


class YellowPagesSource(SourceBase):
    """Source for leads from YellowPages directory"""
    
    BASE_URL = "https://www.yellowpages.com"
    
    def __init__(self):
        """Initialize YellowPages source"""
        # Note: YellowPages may have ToS restrictions - use responsibly
        pass
    
    def search(self, niche: str, location: Optional[str] = None) -> Iterable[Lead]:
        """Search for businesses using YellowPages"""
        if not location:
            # YellowPages requires location
            logger.warning("YellowPages search requires location")
            return
        
        query = f"{niche} {location}"
        params = {
            "search_terms": niche,
            "geo_location_terms": location,
        }
        
        url = f"{self.BASE_URL}/search"
        max_results = 50  # Reasonable limit
        
        # Use sync httpx client since this is called from sync context
        try:
            with httpx.Client(timeout=20.0, follow_redirects=True) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Parse location
                city, country = None, None
                if location:
                    from app.utils.geo import parse_location
                    city, country = parse_location(location)
                
                # Extract results (YellowPages structure may vary)
                results = soup.select("div.result, div.search-result, article.business")
                count = 0
                
                for result in results:
                    if count >= max_results:
                        break
                    
                    # Extract business name
                    name_elem = result.select_one("a.business-name, h2.business-name, a[data-track='business-name']")
                    name = name_elem.get_text(strip=True) if name_elem else None
                    
                    # Extract phone
                    phone_elem = result.select_one("div.phones, div.phone, span.phone")
                    phone = phone_elem.get_text(strip=True) if phone_elem else None
                    
                    # Extract website
                    website_elem = result.select_one("a.track-visit-website, a.website, a[data-track='visit-website']")
                    website = None
                    if website_elem and website_elem.has_attr("href"):
                        website = website_elem["href"]
                        # Make absolute URL if needed
                        if website and not website.startswith(("http://", "https://")):
                            website = urljoin(self.BASE_URL, website)
                    
                    # Extract address
                    address_elem = result.select_one("div.address, div.street-address, span.address")
                    address = address_elem.get_text(strip=True) if address_elem else None
                    
                    # Only yield if we have at least name or website
                    if name or website or phone:
                        phones = [phone] if phone else []
                        yield Lead(
                            id=None,
                            name=name,
                            niche=niche,
                            website=website,
                            emails=[],
                            phones=phones,
                            address=address,
                            source="yellowpages",
                            city=city,
                            country=country,
                        )
                        count += 1
                        
        except httpx.HTTPError as e:
            logger.error(f"YellowPages API error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in YellowPages search: {e}")

