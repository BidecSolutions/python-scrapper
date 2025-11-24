"""Async lead service - orchestrates the scraping pipeline (asynchronous)"""
import asyncio
import logging
from typing import Iterable, List
from app.core.models import Lead
from app.scraper.async_crawler import AsyncCrawler
from app.scraper.extractor import extract_from_soup
from app.scraper.normalizer import normalize_emails, normalize_phones
from app.services.enrichment_service import EnrichmentService

logger = logging.getLogger(__name__)


class AsyncLeadService:
    """Async service for finding and enriching leads"""
    
    def __init__(
        self, 
        sources: Iterable, 
        crawler: AsyncCrawler,
        extract_config: dict = None,
        progress_callback=None
    ):
        self.sources = list(sources)
        self.crawler = crawler
        self.extract_config = extract_config or {}
        self.progress_callback = progress_callback
        self._processed_count = 0
    
    async def search_leads(
        self,
        niche: str,
        location: str | None = None,
        max_results: int = 50,
    ) -> List[Lead]:
        """Search for leads and enrich them with contact information"""
        # 1) Aggregate basic leads (sync for now)
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
        
        # 2) Enrich with async crawling
        websites_to_process = [l for l in raw_leads if l.website]
        total_targets = len(websites_to_process)
        self._processed_count = 0
        
        if self.progress_callback:
            self.progress_callback(0, total_targets)
        
        tasks = [
            self._enrich_lead(lead, total_targets)
            for lead in websites_to_process
        ]
        
        try:
            enriched_results = await asyncio.gather(*tasks, return_exceptions=True)
            enriched_leads = [r for r in enriched_results if isinstance(r, Lead)]
        except Exception as e:
            logger.warning(f"Some leads failed to enrich: {e}")
            enriched_leads = []
        
        # 3) Merge enriched leads with those that had no website
        no_website_leads = [l for l in raw_leads if not l.website]
        all_leads = no_website_leads + enriched_leads
        
        # 4) Dedupe & return
        return self._deduplicate(all_leads)
    
    async def _enrich_lead(self, lead: Lead, total_targets: int) -> Lead:
        """Enrich a single lead with contact information and tech/social data"""
        emails_enabled = self.extract_config.get("emails", True)
        phones_enabled = self.extract_config.get("phones", True)
        website_content_enabled = self.extract_config.get("website_content", False)
        social_links_enabled = self.extract_config.get("social_links", True)
        social_numbers_enabled = self.extract_config.get("social_numbers", True)
        services_enabled = self.extract_config.get("services", True)
        
        emails, phones = set(), set()
        html_pages = []  # Store HTML for enrichment
        
        try:
            # Only crawl if crawler is available
            if self.crawler:
                async for url, soup in self.crawler.crawl(lead.website):
                    # Extract contacts (if enabled)
                    if emails_enabled or phones_enabled:
                        e, p = extract_from_soup(soup)
                        if emails_enabled:
                            emails |= e
                        if phones_enabled:
                            phones |= p
                    
                    # Store HTML for enrichment (only if needed)
                    if soup and (website_content_enabled or services_enabled or social_links_enabled):
                        html_pages.append((url, str(soup)))
        except Exception as e:
            logger.warning(f"Failed to crawl {lead.website}: {e}")
        
        lead.emails = normalize_emails(list(emails)) if emails_enabled else []
        lead.phones = normalize_phones(list(phones)) if phones_enabled else []
        
        # Apply enrichment (tech stack, social links, etc.)
        if html_pages and lead.website:
            # Use first page HTML for enrichment
            url, html = html_pages[0]
            try:
                # Only enrich if services or social_links are enabled
                if services_enabled or social_links_enabled:
                    lead = EnrichmentService.enrich_lead(lead, html, url)
            except Exception as e:
                logger.warning(f"Failed to enrich lead {lead.website}: {e}")
        
        # Update progress
        self._processed_count += 1
        if self.progress_callback:
            self.progress_callback(self._processed_count, total_targets)
        
        return lead
    
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

