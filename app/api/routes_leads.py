"""Lead management API routes"""
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import String, or_
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.routes_auth import get_current_user
from app.api.routes_workspaces import get_current_workspace
from app.api.schemas import LeadOut
from app.core.db import get_db
from app.core.orm import LeadORM, UserORM
from app.core.orm_activity import ActivityORM, ActivityType
from app.core.orm_workspaces import WorkspaceORM
from app.services.export_service import ExportService
from app.services.lead_scoring_service import explain_lead_score

router = APIRouter()


class BulkTagRequest(BaseModel):
    lead_ids: List[int]
    tag: str
    action: str = "add"


def _require_org_and_workspace(
    current_user: UserORM,
    workspace: WorkspaceORM,
) -> tuple[int, int]:
    """Ensure the user has an org and the workspace belongs to that org."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with an organization.",
        )

    if workspace.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Workspace does not belong to your organization.",
        )

    return current_user.organization_id, workspace.id


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
    current_user: UserORM = Depends(get_current_user),
    workspace: WorkspaceORM = Depends(get_current_workspace),
) -> List[LeadOut]:
    """Get leads with optional filters and global search"""
    org_id, workspace_id = _require_org_and_workspace(current_user, workspace)
    # Build query
    query = db.query(LeadORM).filter(
        LeadORM.organization_id == org_id,
        or_(LeadORM.workspace_id == workspace_id, LeadORM.workspace_id.is_(None)),
    )
    
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
            ai_status=lead.ai_status,
            ai_last_error=lead.ai_last_error,
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
    current_user: UserORM = Depends(get_current_user),
    workspace: WorkspaceORM = Depends(get_current_workspace),
):
    """Export leads to CSV"""
    org_id, workspace_id = _require_org_and_workspace(current_user, workspace)
    query = db.query(LeadORM).filter(
        LeadORM.organization_id == org_id,
        or_(LeadORM.workspace_id == workspace_id, LeadORM.workspace_id.is_(None)),
    )
    
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
    current_user: UserORM = Depends(get_current_user),
    workspace: WorkspaceORM = Depends(get_current_workspace),
):
    """Export leads to Excel"""
    org_id, workspace_id = _require_org_and_workspace(current_user, workspace)
    query = db.query(LeadORM).filter(
        LeadORM.organization_id == org_id,
        or_(LeadORM.workspace_id == workspace_id, LeadORM.workspace_id.is_(None)),
    )
    
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
    current_user: UserORM = Depends(get_current_user),
    workspace: WorkspaceORM = Depends(get_current_workspace),
) -> LeadOut:
    """Get a single lead by ID"""
    org_id, workspace_id = _require_org_and_workspace(current_user, workspace)
    lead = (
        db.query(LeadORM)
        .filter(
            LeadORM.id == lead_id,
            LeadORM.organization_id == org_id,
            or_(LeadORM.workspace_id == workspace_id, LeadORM.workspace_id.is_(None)),
        )
        .first()
    )
    
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
        ai_status=lead.ai_status,
        ai_last_error=lead.ai_last_error,
    )


@router.get("/leads/{lead_id}/score-explain")
def get_lead_score_explain(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
    workspace: WorkspaceORM = Depends(get_current_workspace),
):
    """Get explainable score breakdown for a lead."""
    org_id, workspace_id = _require_org_and_workspace(current_user, workspace)
    lead = (
        db.query(LeadORM)
        .filter(
            LeadORM.id == lead_id,
            LeadORM.organization_id == org_id,
            or_(LeadORM.workspace_id == workspace_id, LeadORM.workspace_id.is_(None)),
        )
        .first()
    )
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    return explain_lead_score(db, lead)


@router.get("/leads/{lead_id}/score-history")
def get_lead_score_history(
    lead_id: int,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
    workspace: WorkspaceORM = Depends(get_current_workspace),
):
    """Get lead score change history."""
    org_id, workspace_id = _require_org_and_workspace(current_user, workspace)
    lead = (
        db.query(LeadORM)
        .filter(
            LeadORM.id == lead_id,
            LeadORM.organization_id == org_id,
            or_(LeadORM.workspace_id == workspace_id, LeadORM.workspace_id.is_(None)),
        )
        .first()
    )
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    history = (
        db.query(ActivityORM)
        .filter(
            ActivityORM.organization_id == org_id,
            ActivityORM.lead_id == lead_id,
            ActivityORM.type == ActivityType.lead_score_updated,
        )
        .order_by(ActivityORM.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": item.id,
            "created_at": item.created_at.isoformat(),
            "score_type": (item.meta or {}).get("score_type"),
            "previous_score": (item.meta or {}).get("previous_score"),
            "new_score": (item.meta or {}).get("new_score"),
            "delta": (item.meta or {}).get("delta"),
        }
        for item in history
    ]


@router.post("/leads/tags/bulk")
def bulk_update_tags(
    body: BulkTagRequest,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
    workspace: WorkspaceORM = Depends(get_current_workspace),
):
    """Add or remove a tag across multiple leads."""
    org_id, workspace_id = _require_org_and_workspace(current_user, workspace)
    if not body.tag or not body.tag.strip():
        raise HTTPException(status_code=400, detail="Tag is required")

    if body.action not in {"add", "remove"}:
        raise HTTPException(status_code=400, detail="Invalid action")

    leads = (
        db.query(LeadORM)
        .filter(
            LeadORM.organization_id == org_id,
            LeadORM.id.in_(body.lead_ids),
            or_(LeadORM.workspace_id == workspace_id, LeadORM.workspace_id.is_(None)),
        )
        .all()
    )

    updated = 0
    tag_value = body.tag.strip()
    for lead in leads:
        existing = lead.tags or []
        if body.action == "add":
            if tag_value not in existing:
                lead.tags = existing + [tag_value]
                updated += 1
        else:
            if tag_value in existing:
                lead.tags = [tag for tag in existing if tag != tag_value]
                updated += 1

    db.commit()
    return {"updated": updated, "action": body.action, "tag": tag_value}

