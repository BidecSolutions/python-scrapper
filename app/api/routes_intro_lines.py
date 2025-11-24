"""Intro Line Generation API routes"""
import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional

from app.core.db import get_db
from app.core.orm import LeadORM
from app.core.orm_lists import LeadListORM
from app.api.routes_settings import get_or_create_default_org
from app.services.intro_line_generator import (
    generate_intro_line_for_lead,
    generate_intro_lines_for_list
)

logger = logging.getLogger(__name__)
router = APIRouter()


class IntroLineRequest(BaseModel):
    """Request to generate intro line"""
    regenerate: bool = Field(default=False, description="Regenerate even if intro_line exists")


class IntroLineResponse(BaseModel):
    """Response from intro line generation"""
    intro_line: Optional[str] = None
    lead_id: int


@router.post("/leads/{lead_id}/intro-line", response_model=IntroLineResponse)
def generate_lead_intro_line(
    lead_id: int,
    request: IntroLineRequest,
    db: Session = Depends(get_db),
):
    """Generate an intro line for a specific lead"""
    org = get_or_create_default_org(db)
    
    lead = db.query(LeadORM).filter(
        LeadORM.id == lead_id,
        LeadORM.organization_id == org.id
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    intro_line = generate_intro_line_for_lead(db, lead, regenerate=request.regenerate)
    
    return IntroLineResponse(
        intro_line=intro_line,
        lead_id=lead.id,
    )


class BulkIntroLineRequest(BaseModel):
    """Request to generate intro lines for a list"""
    regenerate: bool = Field(default=False, description="Regenerate for all leads")


class BulkIntroLineResponse(BaseModel):
    """Response from bulk intro line generation"""
    total: int
    generated: int
    failed: int


@router.post("/lists/{list_id}/intro-lines", response_model=BulkIntroLineResponse)
def generate_list_intro_lines(
    list_id: int,
    request: BulkIntroLineRequest,
    db: Session = Depends(get_db),
):
    """Generate intro lines for all leads in a list"""
    org = get_or_create_default_org(db)
    
    # Verify list exists
    lead_list = db.query(LeadListORM).filter(
        LeadListORM.id == list_id,
        LeadListORM.organization_id == org.id
    ).first()
    
    if not lead_list:
        raise HTTPException(status_code=404, detail="List not found")
    
    # Generate intro lines (synchronous for now, can be moved to background job)
    result = generate_intro_lines_for_list(
        db=db,
        organization_id=org.id,
        list_id=list_id,
        regenerate=request.regenerate
    )
    
    return BulkIntroLineResponse(
        total=result["total"],
        generated=result["generated"],
        failed=result["failed"],
    )

