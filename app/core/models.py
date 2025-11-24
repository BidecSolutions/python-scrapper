"""Data models for leads (enhanced)"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class Lead:
    """Enhanced Lead model with all enrichment fields"""
    id: Optional[int] = None
    name: Optional[str] = None
    niche: Optional[str] = None
    website: Optional[str] = None
    emails: List[str] = field(default_factory=list)
    phones: List[str] = field(default_factory=list)
    address: Optional[str] = None
    source: str = ""
    city: Optional[str] = None
    country: Optional[str] = None
    job_id: Optional[int] = None
    
    # Tech stack detection
    cms: Optional[str] = None
    tech_stack: List[str] = field(default_factory=list)
    third_party_widgets: List[str] = field(default_factory=list)
    
    # Social links
    social_links: Dict[str, str] = field(default_factory=dict)
    
    # Company intelligence
    company_size: Optional[str] = None  # "solo", "small", "medium", "large"
    revenue_band: Optional[str] = None  # "micro", "small", "large"
    is_multi_location: bool = False
    branch_locations: List[str] = field(default_factory=list)
    
    # Content-based tags
    service_tags: List[str] = field(default_factory=list)
    audience_tags: List[str] = field(default_factory=list)
    
    # Contact person
    contact_person_name: Optional[str] = None
    contact_person_role: Optional[str] = None
    contact_person_email: Optional[str] = None
    
    # Outreach
    outreach_notes: Optional[str] = None
    
    # Workflow
    status: str = "new"
    assigned_to_user_id: Optional[int] = None
    
    # Quality flags
    has_email: bool = False
    has_phone: bool = False
    has_social: bool = False
    quality_score: Optional[float] = None
    quality_label: Optional[str] = None  # "low", "medium", "high"
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
