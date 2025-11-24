"""Advanced AI/ML API routes for LeadFlux AI v2"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.db import get_db
from app.core.orm import LeadORM, OrganizationORM
from app.services.identity_graph import IdentityGraphService
from app.services.dossier_service import DossierService
from app.services.next_action_service import NextActionService
from app.services.contrastive_embeddings import ContrastiveEmbeddingService
from app.services.social_intelligence import SocialIntelligenceService
from datetime import datetime

router = APIRouter()


def get_or_create_default_org(db: Session) -> OrganizationORM:
    """Get or create default organization"""
    from app.api.routes_settings import get_or_create_default_org as _get_org
    return _get_org(db)


# ============================================================================
# Identity Graph: Key People / Decision Makers
# ============================================================================

@router.get("/leads/{lead_id}/key-people")
def get_key_people(
    lead_id: int,
    limit: int = Query(5, le=20),
    db: Session = Depends(get_db),
):
    """Get key people (decision makers) for a lead"""
    org = get_or_create_default_org(db)
    
    lead = db.query(LeadORM).filter(
        LeadORM.organization_id == org.id,
        LeadORM.id == lead_id
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    people = IdentityGraphService.get_key_people(db, lead_id, org.id, limit=limit)
    
    return {
        "lead_id": lead_id,
        "people": people,
        "count": len(people),
    }


# ============================================================================
# Contrastive Embeddings: Similar Leads
# ============================================================================

@router.get("/leads/{lead_id}/similar-v2")
def find_similar_leads_v2(
    lead_id: int,
    limit: int = Query(20, le=50),
    min_similarity: float = Query(0.7, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
):
    """Find similar leads using contrastive embeddings"""
    org = get_or_create_default_org(db)
    embedding_service = ContrastiveEmbeddingService()
    
    similar = embedding_service.find_similar_leads(
        db, lead_id, org.id, limit=limit, min_similarity=min_similarity
    )
    
    return [
        {
            "id": lead.id,
            "name": lead.name,
            "website": lead.website,
            "city": lead.city,
            "country": lead.country,
            "niche": lead.niche,
            "quality_score": float(lead.quality_score) if lead.quality_score else None,
            "similarity": float(similarity),
        }
        for lead, similarity in similar
    ]


# ============================================================================
# Social Intelligence
# ============================================================================

@router.get("/leads/{lead_id}/social-insights")
def get_social_insights(
    lead_id: int,
    db: Session = Depends(get_db),
):
    """Get social media insights for a lead"""
    org = get_or_create_default_org(db)
    
    # Find entity for this lead
    lead = db.query(LeadORM).filter(LeadORM.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    from app.core.orm_v2 import EntityORM, EntityType, SocialInsightORM
    
    company_entity = db.query(EntityORM).filter(
        EntityORM.organization_id == org.id,
        EntityORM.type == EntityType.company,
        EntityORM.url == lead.website
    ).first()
    
    if not company_entity:
        # Create entity from lead
        company_entity = IdentityGraphService.create_entity_from_lead(
            db, lead, org.id
        )
    
    # Get or generate insights
    insight = db.query(SocialInsightORM).filter(
        SocialInsightORM.organization_id == org.id,
        SocialInsightORM.entity_id == company_entity.id
    ).first()
    
    if not insight:
        # Generate insights
        social_service = SocialIntelligenceService()
        insight = social_service.generate_insights(
            db, company_entity.id, org.id
        )
    
    return {
        "lead_id": lead_id,
        "entity_id": company_entity.id,
        "posts_per_month": insight.posts_per_month,
        "avg_engagement": insight.avg_engagement,
        "total_followers": insight.total_followers,
        "topic_distribution": insight.topic_distribution or {},
        "dominant_topics": insight.dominant_topics or [],
        "sentiment_distribution": insight.sentiment_distribution or {},
        "growth_stage": insight.growth_stage,
        "dominant_pain": insight.dominant_pain,
        "summary": insight.summary,
    }


# ============================================================================
# Next Best Action (RL/Bandit)
# ============================================================================

class NextActionRequest(BaseModel):
    lead_id: int


@router.get("/leads/{lead_id}/next-action")
def get_next_action(
    lead_id: int,
    db: Session = Depends(get_db),
):
    """Get recommended next action for a lead"""
    org = get_or_create_default_org(db)
    
    lead = db.query(LeadORM).filter(
        LeadORM.organization_id == org.id,
        LeadORM.id == lead_id
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    service = NextActionService(db, org.id)
    result = service.get_next_action_for_lead(lead_id)
    
    return {
        "lead_id": lead_id,
        "action": result["action"],
        "score": result["score"],
        "confidence": result["score"],  # Alias for compatibility
        "reason": result.get("reason", ""),
        "alternatives": result.get("alternatives", []),
    }


class RecordActionRequest(BaseModel):
    action: str
    outcome: Optional[str] = None
    suggested_by_ai: bool = False


@router.post("/leads/{lead_id}/actions")
def record_action(
    lead_id: int,
    request: RecordActionRequest,
    db: Session = Depends(get_db),
):
    """Record an action taken and its outcome"""
    org = get_or_create_default_org(db)
    
    lead = db.query(LeadORM).filter(
        LeadORM.organization_id == org.id,
        LeadORM.id == lead_id
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    service = NextActionService(db, org.id)
    service.record_action_outcome(
        lead_id,
        request.action,
        request.outcome,
        request.suggested_by_ai
    )
    
    return {"success": True, "message": "Action recorded"}


class BulkActionsRequest(BaseModel):
    lead_ids: List[int]


@router.post("/leads/bulk-next-actions")
def get_bulk_actions(
    request: BulkActionsRequest,
    db: Session = Depends(get_db),
):
    """Get next actions for multiple leads"""
    org = get_or_create_default_org(db)
    
    service = NextActionService(db, org.id)
    results = service.get_bulk_actions(request.lead_ids)
    
    return {
        "results": [
            {
                "lead_id": lead_id,
                **data
            }
            for lead_id, data in results.items()
        ]
    }


# ============================================================================
# Deep Research Dossier
# ============================================================================

@router.post("/leads/{lead_id}/dossier")
def generate_dossier(
    lead_id: int,
    db: Session = Depends(get_db),
):
    """Generate deep AI research dossier for a lead (creates/updates dossier)"""
    org = get_or_create_default_org(db)
    
    lead = db.query(LeadORM).filter(
        LeadORM.organization_id == org.id,
        LeadORM.id == lead_id
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    from app.core.orm_v2 import DossierORM, DossierStatus
    
    # Get or create dossier
    dossier = db.query(DossierORM).filter(
        DossierORM.organization_id == org.id,
        DossierORM.lead_id == lead_id
    ).first()
    
    if not dossier:
        dossier = DossierORM(
            organization_id=org.id,
            lead_id=lead_id,
            status=DossierStatus.pending
        )
        db.add(dossier)
        db.flush()
    
    # Update status
    dossier.status = DossierStatus.running
    dossier.started_at = datetime.utcnow()
    db.commit()
    
    try:
        # Generate dossier
        sections = DossierService.generate_dossier(lead, db)
        
        # Save sections
        dossier.sections = sections
        dossier.status = DossierStatus.completed
        dossier.completed_at = datetime.utcnow()
        
        # Populate legacy fields for backward compatibility
        dossier.business_summary = sections.get("overview", "")
        dossier.offerings = sections.get("social_topics", []) if isinstance(sections.get("social_topics"), list) else []
        dossier.target_audience = sections.get("audience", "")
        dossier.digital_maturity = sections.get("digital_presence", "")
        dossier.risks_constraints = sections.get("risks", "")
        dossier.suggested_outreach_angle = sections.get("angle", "")
        dossier.sample_email = sections.get("email", "")
        dossier.sample_linkedin_message = sections.get("linkedin_dm", "")
        
        db.commit()
        db.refresh(dossier)
        
        return {
            "lead_id": lead_id,
            "dossier_id": dossier.id,
            "status": dossier.status.value,
            "sections": sections,
            "updated_at": dossier.updated_at.isoformat(),
        }
    except Exception as e:
        dossier.status = DossierStatus.failed
        dossier.error = str(e)[:500]
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to generate dossier: {str(e)}")


@router.get("/leads/{lead_id}/dossier")
def get_dossier(
    lead_id: int,
    db: Session = Depends(get_db),
):
    """Get existing dossier for a lead"""
    org = get_or_create_default_org(db)
    
    from app.core.orm_v2 import DossierORM
    
    dossier = db.query(DossierORM).filter(
        DossierORM.organization_id == org.id,
        DossierORM.lead_id == lead_id
    ).first()
    
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier not found. Generate it first.")
    
    # Prefer sections JSONB, fallback to legacy fields
    sections = dossier.sections or {}
    if not sections:
        # Build from legacy fields
        sections = {
            "overview": dossier.business_summary or "",
            "offer": ", ".join(dossier.offerings or []),
            "audience": dossier.target_audience or "",
            "digital_presence": dossier.digital_maturity or "",
            "social_topics": dossier.offerings or [],
            "risks": dossier.risks_constraints or "",
            "angle": dossier.suggested_outreach_angle or "",
            "email": dossier.sample_email or "",
            "linkedin_dm": dossier.sample_linkedin_message or "",
        }
    
    return {
        "lead_id": lead_id,
        "dossier_id": dossier.id,
        "status": dossier.status.value,
        "sections": sections,
        "updated_at": dossier.updated_at.isoformat(),
        "completed_at": dossier.completed_at.isoformat() if dossier.completed_at else None,
    }

