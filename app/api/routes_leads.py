"""Lead management API routes"""
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import Response
from typing import List, Optional, Union, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, String

from app.core.db import get_db
from app.core.orm import LeadORM, OrganizationORM, PlanTier
from app.api.schemas import LeadOut
from app.services.export_service import ExportService
# For now, we'll create a default org for testing
# In production, use: from app.api.middleware import get_organization_from_api_key

router = APIRouter()


def _normalize_tech_stack(tech_stack: Union[List[str], Dict[str, Any], None]) -> List[str]:
    """Convert tech_stack from dict or list to list format"""
    if tech_stack is None:
        return []
    
    # If already a list, return as is
    if isinstance(tech_stack, list):
        # Ensure all items are strings
        return [str(item) for item in tech_stack if item]
    
    # If it's a dict, convert to flat list
    if isinstance(tech_stack, dict):
        result = []
        for key, value in tech_stack.items():
            # Add the key itself (e.g., "cms")
            if key and key not in result:
                result.append(str(key))
            # Add values if they're lists
            if isinstance(value, list):
                for item in value:
                    if item and str(item) not in result:
                        result.append(str(item))
            # Add value if it's a string
            elif value and str(value) not in result:
                result.append(str(value))
        return result
    
    # Fallback: convert to string and wrap in list
    return [str(tech_stack)] if tech_stack else []


def get_or_create_default_org(db: Session) -> int:
    """Get or create default organization for testing"""
    # Check if default org exists
    org = db.query(OrganizationORM).filter(OrganizationORM.slug == "default").first()
    
    if not org:
        # Create default org
        org = OrganizationORM(
            name="Default Organization",
            slug="default",
            plan_tier=PlanTier.pro,
        )
        db.add(org)
        db.flush()
    
    return org.id


@router.get("/leads", response_model=List[LeadOut])
def get_leads(
    job_id: Optional[int] = Query(None, description="Filter by job ID"),
    quality_label: Optional[str] = Query(None, description="Filter by quality label (low/medium/high)"),
    has_email: Optional[bool] = Query(None, description="Filter leads with email"),
    has_phone: Optional[bool] = Query(None, description="Filter leads with phone"),
    city: Optional[str] = Query(None, description="Filter by city"),
    source: Optional[str] = Query(None, description="Filter by source"),
    min_score: Optional[float] = Query(None, description="Minimum quality score"),
    max_score: Optional[float] = Query(None, description="Maximum quality score"),
    search: Optional[str] = Query(None, description="Global search (name, email, website, city)"),
    limit: int = Query(100, le=500, description="Maximum number of leads"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
) -> List[LeadOut]:
    """Get leads with optional filters and global search"""
    org_id = get_or_create_default_org(db)
    # Build query
    query = db.query(LeadORM).filter(LeadORM.organization_id == org_id)
    
    # Apply filters
    if job_id:
        query = query.filter(LeadORM.job_id == job_id)
    if quality_label:
        query = query.filter(LeadORM.quality_label == quality_label)
    if has_email is not None:
        query = query.filter(LeadORM.has_email == has_email)
    if has_phone is not None:
        query = query.filter(LeadORM.has_phone == has_phone)
    if city:
        query = query.filter(LeadORM.city.ilike(f"%{city}%"))
    if source:
        # Search in both source and sources array
        query = query.filter(
            or_(
                LeadORM.source.ilike(f"%{source}%"),
                LeadORM.sources.contains([source])
            )
        )
    if min_score is not None:
        query = query.filter(LeadORM.quality_score >= min_score)
    if max_score is not None:
        query = query.filter(LeadORM.quality_score <= max_score)
    
    # Global search
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                LeadORM.name.ilike(search_term),
                LeadORM.website.ilike(search_term),
                LeadORM.city.ilike(search_term),
                LeadORM.address.ilike(search_term),
                LeadORM.niche.ilike(search_term),
                # Search in emails (JSON array)
                LeadORM.emails.cast(String).ilike(search_term),
            )
        )
    
    # Order and paginate
    leads = query.order_by(LeadORM.quality_score.desc().nulls_last()).limit(limit).offset(offset).all()
    
    # Convert to response
    return [
        LeadOut(
            id=lead.id,
            name=lead.name,
            niche=lead.niche,
            website=lead.website,
            emails=lead.emails or [],
            phones=lead.phones or [],
            address=lead.address,
            source=lead.source,
            sources=lead.sources or [lead.source] if lead.source else [],
            city=lead.city,
            country=lead.country,
            quality_score=float(lead.quality_score) if lead.quality_score else None,
            quality_label=lead.quality_label,
            tags=lead.tags or [],
            cms=lead.cms,
            tech_stack=_normalize_tech_stack(lead.tech_stack),
            social_links=lead.social_links or {},
            metadata=lead.meta or {},
        )
        for lead in leads
    ]


@router.get("/leads/export/csv")
def export_leads_csv(
    job_id: Optional[int] = Query(None),
    quality_label: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Export leads to CSV"""
    org_id = get_or_create_default_org(db)
    query = db.query(LeadORM).filter(LeadORM.organization_id == org_id)
    
    # Apply same filters as get_leads
    if job_id:
        query = query.filter(LeadORM.job_id == job_id)
    if quality_label:
        query = query.filter(LeadORM.quality_label == quality_label)
    if min_score is not None:
        query = query.filter(LeadORM.quality_score >= min_score)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                LeadORM.name.ilike(search_term),
                LeadORM.website.ilike(search_term),
                LeadORM.city.ilike(search_term),
            )
        )
    
    leads_orm = query.order_by(LeadORM.quality_score.desc().nulls_last()).all()
    
    # Convert to Lead models
    from app.core.models import Lead
    leads = [
        Lead(
            id=lead.id,
            name=lead.name,
            niche=lead.niche,
            website=lead.website,
            emails=lead.emails or [],
            phones=lead.phones or [],
            address=lead.address,
            source=lead.source,
            city=lead.city,
            country=lead.country,
            quality_score=float(lead.quality_score) if lead.quality_score else None,
            quality_label=lead.quality_label,
            social_links=lead.social_links or {},
        )
        for lead in leads_orm
    ]
    
    csv_content = ExportService.to_csv(leads)
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads.csv"}
    )


@router.get("/leads/export/excel")
def export_leads_excel(
    job_id: Optional[int] = Query(None),
    quality_label: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Export leads to Excel"""
    org_id = get_or_create_default_org(db)
    query = db.query(LeadORM).filter(LeadORM.organization_id == org_id)
    
    # Apply same filters as get_leads
    if job_id:
        query = query.filter(LeadORM.job_id == job_id)
    if quality_label:
        query = query.filter(LeadORM.quality_label == quality_label)
    if min_score is not None:
        query = query.filter(LeadORM.quality_score >= min_score)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                LeadORM.name.ilike(search_term),
                LeadORM.website.ilike(search_term),
                LeadORM.city.ilike(search_term),
            )
        )
    
    leads_orm = query.order_by(LeadORM.quality_score.desc().nulls_last()).all()
    
    # Convert to Lead models
    from app.core.models import Lead
    leads = [
        Lead(
            id=lead.id,
            name=lead.name,
            niche=lead.niche,
            website=lead.website,
            emails=lead.emails or [],
            phones=lead.phones or [],
            address=lead.address,
            source=lead.source,
            city=lead.city,
            country=lead.country,
            quality_score=float(lead.quality_score) if lead.quality_score else None,
            quality_label=lead.quality_label,
            social_links=lead.social_links or {},
        )
        for lead in leads_orm
    ]
    
    try:
        excel_content = ExportService.to_excel(leads)
        return Response(
            content=excel_content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=leads.xlsx"}
        )
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Excel export requires openpyxl. Install with: pip install openpyxl"
        )


@router.get("/leads/{lead_id}", response_model=LeadOut)
def get_lead(
    lead_id: int,
    db: Session = Depends(get_db),
) -> LeadOut:
    """Get a single lead by ID"""
    org_id = get_or_create_default_org(db)
    lead = db.query(LeadORM).filter(
        LeadORM.id == lead_id,
        LeadORM.organization_id == org_id
    ).first()
    
    if not lead:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return LeadOut(
        id=lead.id,
        name=lead.name,
        niche=lead.niche,
        website=lead.website,
        emails=lead.emails or [],
        phones=lead.phones or [],
        address=lead.address,
        source=lead.source,
        sources=lead.sources or [lead.source] if lead.source else [],
        city=lead.city,
        country=lead.country,
        quality_score=float(lead.quality_score) if lead.quality_score else None,
        quality_label=lead.quality_label,
        tags=lead.tags or [],
        cms=lead.cms,
        tech_stack=_normalize_tech_stack(lead.tech_stack),
        social_links=lead.social_links or {},
        metadata=lead.meta or {},
    )

