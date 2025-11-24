"""Pydantic schemas for API requests and responses"""
from typing import List, Optional
from pydantic import BaseModel, HttpUrl, Field


class ExtractConfig(BaseModel):
    """Configuration for what data to extract"""
    emails: bool = Field(True, description="Extract email addresses")
    phones: bool = Field(True, description="Extract phone numbers")
    website_content: bool = Field(False, description="Extract full website content")
    services: bool = Field(True, description="Extract services/categories")
    social_links: bool = Field(True, description="Extract social media links")
    social_numbers: bool = Field(True, description="Extract contacts from social media pages")


class ScrapeRequest(BaseModel):
    """Request schema for scraping leads"""
    niche: str = Field(..., example="dentist clinic")
    location: Optional[str] = Field(None, example="Karachi")
    max_results: int = Field(20, ge=1, le=500, description="Max leads to collect")
    max_pages_per_site: int = Field(5, ge=1, le=20, description="Pages to crawl per website")
    extract: ExtractConfig = Field(default_factory=ExtractConfig, description="What data to extract")
    sources: Optional[List[str]] = Field(
        None,
        description="List of sources to use: 'google_search', 'google_places', 'web_search', 'crawling'. If not provided, all available sources will be used."
    )


class LeadOut(BaseModel):
    """Lead output schema"""
    id: Optional[int] = None
    name: Optional[str] = None
    niche: Optional[str] = None
    website: Optional[str] = None
    emails: List[str] = []
    phones: List[str] = []
    address: Optional[str] = None
    source: str = ""
    sources: Optional[List[str]] = None  # All sources this lead came from
    city: Optional[str] = None
    country: Optional[str] = None
    quality_score: Optional[float] = None
    quality_label: Optional[str] = None
    tags: List[str] = []
    cms: Optional[str] = None
    tech_stack: Optional[List[str]] = None
    social_links: dict = {}
    metadata: dict = {}

    class Config:
        from_attributes = True


class ScrapeResponse(BaseModel):
    """Response schema for scraping endpoint"""
    total: int
    leads: List[LeadOut]


class JobResponse(BaseModel):
    """Response schema for job creation"""
    job_id: int
    status: str
    message: str

