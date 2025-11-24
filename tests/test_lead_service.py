"""Tests for lead service"""
import pytest
from app.core.models import Lead
from app.services.lead_service import LeadService
from app.scraper.crawler import SimpleCrawler
from app.sources.base import SourceBase


class MockSource(SourceBase):
    """Mock source for testing"""
    def search(self, niche: str, location: str | None = None):
        yield Lead(
            name="Test Business",
            niche=niche,
            website="https://example.com",
            source="test",
        )


def test_lead_service_deduplication():
    """Test that lead service deduplicates leads"""
    source = MockSource()
    crawler = SimpleCrawler(max_pages=1)
    service = LeadService(sources=[source], crawler=crawler)
    
    # Create duplicate leads
    leads = [
        Lead(website="https://example.com", emails=["test@example.com"]),
        Lead(website="https://example.com", emails=["test@example.com"]),
    ]
    
    deduplicated = service._deduplicate(leads)
    assert len(deduplicated) == 1

