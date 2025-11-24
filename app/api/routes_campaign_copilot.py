"""AI Campaign Copilot API routes"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.db import get_db
from app.api.routes_settings import get_or_create_default_org
from app.api.routes_workspaces import get_current_user_id
from app.core.orm_campaigns import CampaignORM, CampaignTemplateORM
from app.services.ai_campaign_copilot import generate_ai_templates, get_template_performance

logger = logging.getLogger(__name__)
router = APIRouter()


class GenerateTemplatesRequest(BaseModel):
    num_subjects: int = Field(3, ge=1, le=5, description="Number of subject line variants")
    num_bodies: int = Field(2, ge=1, le=4, description="Number of body variants")
    tone: str = Field("friendly", description="Tone: friendly, professional, direct, casual")
    goal: str = Field("start a conversation", description="Campaign goal")
    offer: Optional[str] = Field(None, description="What you're offering")


class TemplateOut(BaseModel):
    id: int
    name: str
    content: str
    ai_generated: bool
    created_at: str
    
    class Config:
        from_attributes = True


class GenerateTemplatesResponse(BaseModel):
    subjects: List[TemplateOut]
    bodies: List[TemplateOut]


class TemplateStatsOut(BaseModel):
    id: int
    name: str
    content: str
    sent: int
    opened: int
    clicked: int
    replied: int
    open_rate: float
    click_rate: float
    reply_rate: float


class TemplatePerformanceResponse(BaseModel):
    subjects: List[TemplateStatsOut]
    bodies: List[TemplateStatsOut]
    best_subject: Optional[TemplateStatsOut] = None
    best_body: Optional[TemplateStatsOut] = None


@router.post("/campaigns/{campaign_id}/ai-templates", response_model=GenerateTemplatesResponse)
def generate_campaign_templates(
    campaign_id: int,
    request: GenerateTemplatesRequest = Body(...),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Generate AI email templates (subjects and bodies) for a campaign
    """
    campaign = db.query(CampaignORM).filter(CampaignORM.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Verify workspace access
    # TODO: Add workspace permission check
    
    try:
        result = generate_ai_templates(
            db=db,
            campaign=campaign,
            num_subjects=request.num_subjects,
            num_bodies=request.num_bodies,
            tone=request.tone,
            goal=request.goal,
            offer=request.offer,
        )
        
        return GenerateTemplatesResponse(
            subjects=[
                TemplateOut(
                    id=t.id,
                    name=t.name,
                    content=t.content,
                    ai_generated=t.ai_generated,
                    created_at=t.created_at.isoformat(),
                )
                for t in result["subjects"]
            ],
            bodies=[
                TemplateOut(
                    id=t.id,
                    name=t.name,
                    content=t.content,
                    ai_generated=t.ai_generated,
                    created_at=t.created_at.isoformat(),
                )
                for t in result["bodies"]
            ],
        )
    except Exception as e:
        logger.error(f"Error generating templates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate templates: {str(e)}")


@router.get("/campaigns/{campaign_id}/template-stats", response_model=TemplatePerformanceResponse)
def get_campaign_template_stats(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Get performance statistics for each template variant in a campaign
    """
    campaign = db.query(CampaignORM).filter(CampaignORM.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # TODO: Add workspace permission check
    
    try:
        stats = get_template_performance(db=db, campaign=campaign)
        
        return TemplatePerformanceResponse(
            subjects=[
                TemplateStatsOut(**s)
                for s in stats["subjects"]
            ],
            bodies=[
                TemplateStatsOut(**s)
                for s in stats["bodies"]
            ],
            best_subject=TemplateStatsOut(**stats["best_subject"]) if stats["best_subject"] else None,
            best_body=TemplateStatsOut(**stats["best_body"]) if stats["best_body"] else None,
        )
    except Exception as e:
        logger.error(f"Error getting template stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get template stats: {str(e)}")


@router.get("/campaigns/{campaign_id}/templates", response_model=List[TemplateOut])
def list_campaign_templates(
    campaign_id: int,
    template_type: Optional[str] = None,  # "subject" or "body"
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    List all templates for a campaign
    """
    campaign = db.query(CampaignORM).filter(CampaignORM.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    query = db.query(CampaignTemplateORM).filter(
        CampaignTemplateORM.campaign_id == campaign_id
    )
    
    if template_type:
        from app.core.orm_campaigns import TemplateType
        query = query.filter(CampaignTemplateORM.type == TemplateType(template_type))
    
    templates = query.order_by(CampaignTemplateORM.created_at).all()
    
    return [
        TemplateOut(
            id=t.id,
            name=t.name,
            content=t.content,
            ai_generated=t.ai_generated,
            created_at=t.created_at.isoformat(),
        )
        for t in templates
    ]

