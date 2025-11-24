"""Pydantic schemas for LinkedIn capture API"""
from pydantic import BaseModel, Field, AnyHttpUrl, EmailStr
from typing import Optional, Literal
from datetime import datetime


class LinkedInCaptureRequest(BaseModel):
    """Request to capture a lead from LinkedIn profile"""
    
    # Raw profile info from LinkedIn page
    full_name: str = Field(..., example="John Doe", description="Full name from LinkedIn")
    first_name: Optional[str] = Field(None, example="John", description="First name (optional, will be derived if missing)")
    last_name: Optional[str] = Field(None, example="Doe", description="Last name (optional, will be derived if missing)")
    
    headline: Optional[str] = Field(
        None, 
        example="Head of Marketing at Acme Inc",
        description="LinkedIn headline"
    )
    
    title: Optional[str] = Field(
        None,
        example="Head of Marketing",
        description="Current role/title (if parsed separately from headline)"
    )
    
    company_name: Optional[str] = Field(None, example="Acme Inc", description="Company name")
    
    linkedin_url: AnyHttpUrl = Field(
        ...,
        example="https://www.linkedin.com/in/johndoe",
        description="LinkedIn profile URL"
    )
    
    # Optional enrichment hints
    company_domain: Optional[str] = Field(
        None,
        example="acme.com",
        description="Company domain if extension already knows it"
    )
    
    # How to process
    list_id: Optional[int] = Field(
        None,
        description="If provided, add lead to this list (future feature)"
    )
    
    auto_find_email: bool = Field(
        True,
        description="If true, run Email Finder + Verifier pipeline automatically"
    )
    
    skip_smtp: bool = Field(
        False,
        description="If true, run pattern + light checks only (no SMTP verification)"
    )


class LeadEmailStatus(BaseModel):
    """Email status information for a lead"""
    email: Optional[EmailStr] = None
    status: Optional[Literal["valid", "invalid", "risky", "unknown", "disposable", "gibberish", "syntax_error"]] = None
    reason: Optional[str] = None  # e.g. "smtp_accepted", "no_mx_records"
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score 0.0-1.0")
    last_verified_at: Optional[datetime] = None


class JobRef(BaseModel):
    """Reference to a background job"""
    id: int
    type: Literal["find_email", "verify_email", "finder_and_verify"]
    status: Literal["pending", "running", "completed", "failed", "cancelled"]


class LinkedInCaptureResponse(BaseModel):
    """Response from LinkedIn capture endpoint"""
    id: int
    first_name: str
    last_name: str
    full_name: str
    title: Optional[str] = None
    headline: Optional[str] = None
    company_name: Optional[str] = None
    company_domain: Optional[str] = None
    linkedin_url: Optional[AnyHttpUrl] = None
    email_status: Optional[LeadEmailStatus] = None
    score: Optional[float] = Field(None, description="Lead quality score")
    source: str = Field(..., description="Source identifier, e.g. 'linkedin_extension'")
    created_at: datetime
    updated_at: datetime
    job: Optional[JobRef] = Field(None, description="Background job reference if email finder was triggered")

