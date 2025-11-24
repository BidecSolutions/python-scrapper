"""Tests for lead sources"""
import pytest
from app.sources.base import SourceBase
from app.sources.google_places import GooglePlacesSource
from app.sources.web_search import WebSearchSource


def test_source_base():
    """Test that SourceBase is abstract"""
    with pytest.raises(TypeError):
        SourceBase()


def test_google_places_source_requires_key():
    """Test that Google Places source requires API key"""
    with pytest.raises(ValueError):
        GooglePlacesSource(api_key=None)


def test_web_search_source_handles_no_key():
    """Test that Web Search source handles missing API key gracefully"""
    source = WebSearchSource(api_key=None)
    # Should not raise, but won't work
    results = list(source.search("test", "location"))
    assert len(results) == 0  # No results without API key

