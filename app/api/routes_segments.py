"""Segments API routes"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.db import get_db
from app.core.orm_segments import SegmentORM
from app.core.orm import LeadORM
from app.core.orm_companies import CompanyORM
from app.api.routes_settings import get_or_create_default_org

logger = logging.getLogger(__name__)
router = APIRouter()


class SegmentCreate(BaseModel):
    """Request to create a segment"""
    name: str = Field(..., description="Segment name")
    description: Optional[str] = Field(None, description="Segment description")
    filter_json: dict = Field(..., description="Filter criteria as JSON")


class SegmentUpdate(BaseModel):
    """Request to update a segment"""
    name: Optional[str] = None
    description: Optional[str] = None
    filter_json: Optional[dict] = None


class SegmentOut(BaseModel):
    """Segment response"""
    id: int
    name: str
    description: Optional[str] = None
    filter_json: dict
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


@router.post("/segments", response_model=SegmentOut, status_code=201)
def create_segment(
    segment_data: SegmentCreate,
    db: Session = Depends(get_db),
):
    """Create a new segment"""
    org = get_or_create_default_org(db)
    
    # Check for duplicate name
    existing = db.query(SegmentORM).filter(
        SegmentORM.organization_id == org.id,
        SegmentORM.name == segment_data.name
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Segment with this name already exists")
    
    new_segment = SegmentORM(
        organization_id=org.id,
        name=segment_data.name,
        description=segment_data.description,
        filter_json=segment_data.filter_json,
    )
    db.add(new_segment)
    db.commit()
    db.refresh(new_segment)
    
    return SegmentOut(
        id=new_segment.id,
        name=new_segment.name,
        description=new_segment.description,
        filter_json=new_segment.filter_json,
        created_at=new_segment.created_at.isoformat(),
        updated_at=new_segment.updated_at.isoformat(),
    )


@router.get("/segments", response_model=List[SegmentOut])
def get_segments(
    db: Session = Depends(get_db),
):
    """Get all segments for the organization"""
    org = get_or_create_default_org(db)
    
    segments = db.query(SegmentORM).filter(
        SegmentORM.organization_id == org.id
    ).order_by(SegmentORM.created_at.desc()).all()
    
    return [
        SegmentOut(
            id=s.id,
            name=s.name,
            description=s.description,
            filter_json=s.filter_json,
            created_at=s.created_at.isoformat(),
            updated_at=s.updated_at.isoformat(),
        )
        for s in segments
    ]


@router.get("/segments/{segment_id}", response_model=SegmentOut)
def get_segment(
    segment_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific segment"""
    org = get_or_create_default_org(db)
    
    segment = db.query(SegmentORM).filter(
        SegmentORM.id == segment_id,
        SegmentORM.organization_id == org.id
    ).first()
    
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
    
    return SegmentOut(
        id=segment.id,
        name=segment.name,
        description=segment.description,
        filter_json=segment.filter_json,
        created_at=segment.created_at.isoformat(),
        updated_at=segment.updated_at.isoformat(),
    )


@router.get("/segments/{segment_id}/leads")
def get_segment_leads(
    segment_id: int,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Get leads matching a segment's filters"""
    org = get_or_create_default_org(db)
    
    segment = db.query(SegmentORM).filter(
        SegmentORM.id == segment_id,
        SegmentORM.organization_id == org.id
    ).first()
    
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
    
    # Build query from filter_json
    query = db.query(LeadORM).filter(LeadORM.organization_id == org.id)
    
    filters = segment.filter_json
    
    # Apply filters
    if "sources" in filters and filters["sources"]:
        query = query.filter(LeadORM.source.in_(filters["sources"]))
    
    if "countries" in filters and filters["countries"]:
        query = query.filter(LeadORM.country.in_(filters["countries"]))
    
    if "min_score" in filters and filters["min_score"] is not None:
        query = query.filter(LeadORM.quality_score >= filters["min_score"])
    
    if "roles_contains" in filters and filters["roles_contains"]:
        # Search in contact_person_role
        from sqlalchemy import or_
        role_filters = [
            LeadORM.contact_person_role.ilike(f"%{role}%")
            for role in filters["roles_contains"]
        ]
        query = query.filter(or_(*role_filters))
    
    if "company_sizes" in filters and filters["company_sizes"]:
        # Join with companies table
        query = query.join(CompanyORM, LeadORM.company_id == CompanyORM.id).filter(
            CompanyORM.size.in_(filters["company_sizes"])
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    leads = query.order_by(LeadORM.quality_score.desc().nulls_last()).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "leads": [
            {
                "id": lead.id,
                "name": lead.name,
                "contact_person_name": lead.contact_person_name,
                "contact_person_role": lead.contact_person_role,
                "website": lead.website,
                "quality_score": float(lead.quality_score) if lead.quality_score else None,
                "source": lead.source,
            }
            for lead in leads
        ],
    }


@router.put("/segments/{segment_id}", response_model=SegmentOut)
def update_segment(
    segment_id: int,
    segment_data: SegmentUpdate,
    db: Session = Depends(get_db),
):
    """Update a segment"""
    org = get_or_create_default_org(db)
    
    segment = db.query(SegmentORM).filter(
        SegmentORM.id == segment_id,
        SegmentORM.organization_id == org.id
    ).first()
    
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
    
    if segment_data.name is not None:
        segment.name = segment_data.name
    if segment_data.description is not None:
        segment.description = segment_data.description
    if segment_data.filter_json is not None:
        segment.filter_json = segment_data.filter_json
    
    db.commit()
    db.refresh(segment)
    
    return SegmentOut(
        id=segment.id,
        name=segment.name,
        description=segment.description,
        filter_json=segment.filter_json,
        created_at=segment.created_at.isoformat(),
        updated_at=segment.updated_at.isoformat(),
    )


@router.delete("/segments/{segment_id}", status_code=204)
def delete_segment(
    segment_id: int,
    db: Session = Depends(get_db),
):
    """Delete a segment"""
    org = get_or_create_default_org(db)
    
    segment = db.query(SegmentORM).filter(
        SegmentORM.id == segment_id,
        SegmentORM.organization_id == org.id
    ).first()
    
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
    
    db.delete(segment)
    db.commit()
    return

