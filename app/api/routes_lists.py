"""Lists API routes for organizing leads"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from datetime import datetime

from app.core.db import get_db
from app.core.orm import OrganizationORM
from app.core.orm_lists import LeadListORM, LeadListLeadORM
from app.api.routes_settings import get_or_create_default_org

logger = logging.getLogger(__name__)
router = APIRouter()


class ListOut(BaseModel):
    """List output schema"""
    id: int
    name: str
    description: Optional[str] = None
    total_leads: int = 0
    is_campaign_ready: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ListCreateRequest(BaseModel):
    """Request to create a list"""
    name: str
    description: Optional[str] = None
    is_campaign_ready: bool = False


class ListUpdateRequest(BaseModel):
    """Request to update a list"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_campaign_ready: Optional[bool] = None


@router.get("/lists", response_model=List[ListOut])
def get_lists(
    db: Session = Depends(get_db),
):
    """
    Get all lists for the current organization
    """
    org = get_or_create_default_org(db)
    
    lists = db.query(LeadListORM).filter(
        LeadListORM.organization_id == org.id
    ).order_by(LeadListORM.created_at.desc()).all()
    
    result = []
    for list_obj in lists:
        # Count leads in this list
        total_leads = db.query(func.count(LeadListLeadORM.id)).filter(
            LeadListLeadORM.list_id == list_obj.id
        ).scalar() or 0
        
        result.append(ListOut(
            id=list_obj.id,
            name=list_obj.name,
            description=list_obj.description,
            total_leads=total_leads,
            is_campaign_ready=list_obj.is_campaign_ready,
            created_at=list_obj.created_at,
            updated_at=list_obj.updated_at,
        ))
    
    return result


@router.post("/lists", response_model=ListOut, status_code=status.HTTP_201_CREATED)
def create_list(
    request: ListCreateRequest,
    db: Session = Depends(get_db),
):
    """Create a new lead list"""
    org = get_or_create_default_org(db)
    
    list_obj = LeadListORM(
        organization_id=org.id,
        name=request.name,
        description=request.description,
        is_campaign_ready=request.is_campaign_ready,
    )
    db.add(list_obj)
    db.commit()
    db.refresh(list_obj)
    
    return ListOut(
        id=list_obj.id,
        name=list_obj.name,
        description=list_obj.description,
        total_leads=0,
        is_campaign_ready=list_obj.is_campaign_ready,
        created_at=list_obj.created_at,
        updated_at=list_obj.updated_at,
    )


@router.put("/lists/{list_id}", response_model=ListOut)
def update_list(
    list_id: int,
    request: ListUpdateRequest,
    db: Session = Depends(get_db),
):
    """Update a lead list"""
    org = get_or_create_default_org(db)
    
    list_obj = db.query(LeadListORM).filter(
        LeadListORM.id == list_id,
        LeadListORM.organization_id == org.id
    ).first()
    
    if not list_obj:
        raise HTTPException(status_code=404, detail="List not found")
    
    if request.name is not None:
        list_obj.name = request.name
    if request.description is not None:
        list_obj.description = request.description
    if request.is_campaign_ready is not None:
        list_obj.is_campaign_ready = request.is_campaign_ready
    
    db.commit()
    db.refresh(list_obj)
    
    total_leads = db.query(func.count(LeadListLeadORM.id)).filter(
        LeadListLeadORM.list_id == list_obj.id
    ).scalar() or 0
    
    return ListOut(
        id=list_obj.id,
        name=list_obj.name,
        description=list_obj.description,
        total_leads=total_leads,
        is_campaign_ready=list_obj.is_campaign_ready,
        created_at=list_obj.created_at,
        updated_at=list_obj.updated_at,
    )


@router.post("/lists/{list_id}/leads/{lead_id}")
def add_lead_to_list(
    list_id: int,
    lead_id: int,
    db: Session = Depends(get_db),
):
    """Add a lead to a list"""
    org = get_or_create_default_org(db)
    
    # Verify list exists
    list_obj = db.query(LeadListORM).filter(
        LeadListORM.id == list_id,
        LeadListORM.organization_id == org.id
    ).first()
    
    if not list_obj:
        raise HTTPException(status_code=404, detail="List not found")
    
    # Verify lead exists and belongs to org
    from app.core.orm import LeadORM
    lead = db.query(LeadORM).filter(
        LeadORM.id == lead_id,
        LeadORM.organization_id == org.id
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Check if already in list
    existing = db.query(LeadListLeadORM).filter(
        LeadListLeadORM.list_id == list_id,
        LeadListLeadORM.lead_id == lead_id
    ).first()
    
    if existing:
        return {"message": "Lead already in list", "list_id": list_id, "lead_id": lead_id}
    
    # Add to list
    list_lead = LeadListLeadORM(
        list_id=list_id,
        lead_id=lead_id,
    )
    db.add(list_lead)
    db.commit()
    
    return {"message": "Lead added to list", "list_id": list_id, "lead_id": lead_id}


@router.delete("/lists/{list_id}/leads/{lead_id}")
def remove_lead_from_list(
    list_id: int,
    lead_id: int,
    db: Session = Depends(get_db),
):
    """Remove a lead from a list"""
    org = get_or_create_default_org(db)
    
    # Verify list exists
    list_obj = db.query(LeadListORM).filter(
        LeadListORM.id == list_id,
        LeadListORM.organization_id == org.id
    ).first()
    
    if not list_obj:
        raise HTTPException(status_code=404, detail="List not found")
    
    # Remove from list
    list_lead = db.query(LeadListLeadORM).filter(
        LeadListLeadORM.list_id == list_id,
        LeadListLeadORM.lead_id == lead_id
    ).first()
    
    if not list_lead:
        raise HTTPException(status_code=404, detail="Lead not in list")
    
    db.delete(list_lead)
    db.commit()
    
    return {"message": "Lead removed from list"}


@router.delete("/lists/{list_id}")
def delete_list(
    list_id: int,
    db: Session = Depends(get_db),
):
    """Delete a list"""
    org = get_or_create_default_org(db)
    
    list_obj = db.query(LeadListORM).filter(
        LeadListORM.id == list_id,
        LeadListORM.organization_id == org.id
    ).first()
    
    if not list_obj:
        raise HTTPException(status_code=404, detail="List not found")
    
    db.delete(list_obj)
    db.commit()
    
    return {"message": "List deleted"}

