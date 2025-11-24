"""Tech Stack & Intent Enrichment API routes"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.db import get_db
from app.api.routes_settings import get_or_create_default_org
from app.api.routes_workspaces import get_current_user_id
from app.core.orm_tech_intent import CompanyTechORM, CompanyIntentORM, TechCategory, IntentSignalType, IntentStrength
from app.core.orm_companies import CompanyORM
from app.services.tech_intent_enrichment import enrich_company_tech_intent, get_company_tech_stack, get_company_intent_signals

logger = logging.getLogger(__name__)
router = APIRouter()


class CompanyTechOut(BaseModel):
    id: int
    product_name: str
    category: str
    confidence: float
    source: Optional[str]
    detected_at: str
    
    class Config:
        from_attributes = True


class CompanyIntentOut(BaseModel):
    id: int
    type: str
    strength: str
    description: Optional[str]
    source: Optional[str]
    detected_at: str
    expires_at: Optional[str]
    
    class Config:
        from_attributes = True


class EnrichCompanyRequest(BaseModel):
    company_id: int
    domain: Optional[str] = None
    html_content: Optional[str] = None
    force_refresh: bool = Field(False, description="Force re-enrichment even if already enriched")


class BatchEnrichRequest(BaseModel):
    company_ids: List[int] = Field(..., description="List of company IDs to enrich")
    only_missing: bool = Field(True, description="Only enrich companies without tech/intent data")


@router.post("/companies/{company_id}/enrich-tech-intent", response_model=dict)
def enrich_company_tech_intent_endpoint(
    company_id: int,
    request: EnrichCompanyRequest = Body(...),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Enrich company with tech stack and intent signals
    """
    org = get_or_create_default_org(db)
    
    try:
        result = enrich_company_tech_intent(
            db=db,
            company_id=company_id,
            organization_id=org.id,
            domain=request.domain,
            html_content=request.html_content,
            force_refresh=request.force_refresh,
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error enriching company: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to enrich company: {str(e)}")


@router.get("/companies/{company_id}/tech", response_model=List[CompanyTechOut])
def get_company_tech(
    company_id: int,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Get company tech stack
    """
    tech_category = None
    if category:
        try:
            tech_category = TechCategory(category)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
    
    tech_stack = get_company_tech_stack(db=db, company_id=company_id, category=tech_category)
    
    return [
        CompanyTechOut(
            id=t.id,
            product_name=t.product_name,
            category=t.category.value,
            confidence=t.confidence,
            source=t.source,
            detected_at=t.detected_at.isoformat(),
        )
        for t in tech_stack
    ]


@router.get("/companies/{company_id}/intent", response_model=List[CompanyIntentOut])
def get_company_intent(
    company_id: int,
    type: Optional[str] = None,
    strength: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Get company intent signals
    """
    intent_type = None
    if type:
        try:
            intent_type = IntentSignalType(type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid type: {type}")
    
    intent_strength = None
    if strength:
        try:
            intent_strength = IntentStrength(strength)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid strength: {strength}")
    
    intent_signals = get_company_intent_signals(
        db=db,
        company_id=company_id,
        type=intent_type,
        strength=intent_strength,
        active_only=active_only,
    )
    
    return [
        CompanyIntentOut(
            id=i.id,
            type=i.type.value,
            strength=i.strength.value,
            description=i.description,
            source=i.source,
            detected_at=i.detected_at.isoformat(),
            expires_at=i.expires_at.isoformat() if i.expires_at else None,
        )
        for i in intent_signals
    ]


@router.post("/companies/enrich-batch", response_model=dict)
def batch_enrich_companies(
    request: BatchEnrichRequest = Body(...),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Enrich multiple companies with tech stack and intent signals
    """
    org = get_or_create_default_org(db)
    
    results = {
        "processed": 0,
        "enriched": 0,
        "skipped": 0,
        "errors": 0,
    }
    
    for company_id in request.company_ids:
        try:
            # Check if already enriched (if only_missing)
            if request.only_missing:
                existing_tech = db.query(CompanyTechORM).filter(
                    CompanyTechORM.company_id == company_id
                ).count()
                
                if existing_tech > 0:
                    results["skipped"] += 1
                    continue
            
            # Enrich
            result = enrich_company_tech_intent(
                db=db,
                company_id=company_id,
                organization_id=org.id,
                force_refresh=not request.only_missing,
            )
            
            results["enriched"] += 1
            results["processed"] += 1
            
        except Exception as e:
            logger.error(f"Error enriching company {company_id}: {e}", exc_info=True)
            results["errors"] += 1
            results["processed"] += 1
    
    return results

