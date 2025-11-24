"""Lead service - orchestrates the scraping pipeline (synchronous)"""
import logging
from typing import Iterable, List
from app.core.models import Lead
from app.scraper.crawler import SimpleCrawler
from app.scraper.extractor import extract_from_soup
from app.scraper.normalizer import normalize_emails, normalize_phones

logger = logging.getLogger(__name__)


class LeadService:
    """Service for finding and enriching leads"""
    
    def __init__(self, sources: Iterable, crawler: SimpleCrawler):
        self.sources = list(sources)
        self.crawler = crawler
    
    def search_leads(
        self,
        niche: str,
        location: str | None = None,
        max_results: int = 50,
    ) -> List[Lead]:
        """Search for leads and enrich them with contact information"""
        # 1) Aggregate basic leads from all sources
        raw_leads: List[Lead] = []
        for source in self.sources:
            try:
                for lead in source.search(niche, location):
                    raw_leads.append(lead)
                    if len(raw_leads) >= max_results:
                        break
            except Exception as e:
                logger.warning(f"Source {source.__class__.__name__} failed: {e}")
                continue
            
            if len(raw_leads) >= max_results:
                break
        
        # 2) Enrich each lead by crawling its website
        enriched_leads: List[Lead] = []
        for lead in raw_leads:
            if not lead.website:
                enriched_leads.append(lead)
                continue
            
            emails, phones = set(), set()
            try:
                for _, soup in self.crawler.crawl(lead.website):
                    e, p = extract_from_soup(soup)
                    emails |= e
                    phones |= p
            except Exception as e:
                logger.warning(f"Failed to crawl {lead.website}: {e}")
            
            lead.emails = normalize_emails(list(emails))
            lead.phones = normalize_phones(list(phones))
            enriched_leads.append(lead)
        
        # 3) Simple dedup by website+email
        return self._deduplicate(enriched_leads)
    
    def _deduplicate(self, leads: List[Lead]) -> List[Lead]:
        """Remove duplicate leads"""
        seen_keys = set()
        result: List[Lead] = []
        
        for lead in leads:
            # Create a key from website and emails
            key = (lead.website or "", tuple(sorted(lead.emails)))
            if key in seen_keys:
                continue
            
            seen_keys.add(key)
            result.append(lead)
        
        return result

