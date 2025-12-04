"""API routes for Duplicate Detection & Merging"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.core.db import get_db
from app.core.orm_duplicates import DuplicateGroupORM, DuplicateLeadORM
from app.api.routes_workspaces import get_current_user_optional, get_current_workspace_optional
from app.core.orm import UserORM, LeadORM
from app.core.orm_workspaces import WorkspaceORM
from app.services.duplicate_detection import (
    find_duplicate_groups,
    save_duplicate_groups,
    merge_duplicates,
)

router = APIRouter()


class MergeRequest(BaseModel):
    canonical_lead_id: int
    merge_fields: Optional[Dict[str, str]] = None


@router.post("/duplicates/detect")
async def detect_duplicates(
    min_confidence: float = 0.7,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user_optional),
    current_workspace: WorkspaceORM = Depends(get_current_workspace_optional),
):
    """Detect duplicate leads and save groups to database"""
    if not current_user or not current_workspace:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Find duplicates
    groups = find_duplicate_groups(
        db=db,
        organization_id=current_workspace.organization_id,
        workspace_id=current_workspace.id,
        min_confidence=min_confidence,
    )
    
    # Save to database
    saved_groups = save_duplicate_groups(
        db=db,
        organization_id=current_workspace.organization_id,
        workspace_id=current_workspace.id,
        groups=groups,
    )
    
    return {
        "groups_found": len(groups),
        "groups_saved": len(saved_groups),
        "message": f"Found {len(groups)} duplicate groups",
    }


@router.get("/duplicates/groups")
async def list_duplicate_groups(
    status: Optional[str] = "pending",
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user_optional),
    current_workspace: WorkspaceORM = Depends(get_current_workspace_optional),
):
    """List all duplicate groups"""
    if not current_user or not current_workspace:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    query = db.query(DuplicateGroupORM).filter(
        DuplicateGroupORM.organization_id == current_workspace.organization_id
    )
    
    if status:
        query = query.filter(DuplicateGroupORM.status == status)
    
    groups = query.order_by(DuplicateGroupORM.confidence_score.desc()).all()
    
    result = []
    for group in groups:
        # Get all leads in this group
        duplicate_leads = db.query(DuplicateLeadORM).filter(
            DuplicateLeadORM.duplicate_group_id == group.id
        ).all()
        
        leads_data = []
        for dl in duplicate_leads:
            lead = db.query(LeadORM).filter(LeadORM.id == dl.lead_id).first()
            if lead:
                leads_data.append({
                    "id": lead.id,
                    "name": lead.name,
                    "website": lead.website,
                    "emails": lead.emails or [],
                    "phones": lead.phones or [],
                    "source": lead.source,
                    "created_at": lead.created_at.isoformat() if lead.created_at else None,
                    "similarity_score": dl.similarity_score,
                    "matched_fields": dl.matched_fields or [],
                })
        
        result.append({
            "id": group.id,
            "confidence_score": group.confidence_score,
            "match_reason": group.match_reason,
            "status": group.status,
            "canonical_lead_id": group.canonical_lead_id,
            "leads": leads_data,
            "created_at": group.created_at.isoformat() if group.created_at else None,
        })
    
    return result


@router.get("/duplicates/groups/{group_id}")
async def get_duplicate_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user_optional),
    current_workspace: WorkspaceORM = Depends(get_current_workspace_optional),
):
    """Get details of a specific duplicate group"""
    if not current_user or not current_workspace:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    group = db.query(DuplicateGroupORM).filter(
        and_(
            DuplicateGroupORM.id == group_id,
            DuplicateGroupORM.organization_id == current_workspace.organization_id,
        )
    ).first()
    
    if not group:
        raise HTTPException(status_code=404, detail="Duplicate group not found")
    
    # Get all leads in this group
    duplicate_leads = db.query(DuplicateLeadORM).filter(
        DuplicateLeadORM.duplicate_group_id == group.id
    ).all()
    
    leads_data = []
    for dl in duplicate_leads:
        lead = db.query(LeadORM).filter(LeadORM.id == dl.lead_id).first()
        if lead:
            leads_data.append({
                "id": lead.id,
                "name": lead.name,
                "website": lead.website,
                "emails": lead.emails or [],
                "phones": lead.phones or [],
                "address": lead.address,
                "source": lead.source,
                "sources": lead.sources or [],
                "city": lead.city,
                "country": lead.country,
                "created_at": lead.created_at.isoformat() if lead.created_at else None,
                "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
                "similarity_score": dl.similarity_score,
                "matched_fields": dl.matched_fields or [],
            })
    
    return {
        "id": group.id,
        "confidence_score": group.confidence_score,
        "match_reason": group.match_reason,
        "status": group.status,
        "canonical_lead_id": group.canonical_lead_id,
        "leads": leads_data,
        "created_at": group.created_at.isoformat() if group.created_at else None,
    }


@router.post("/duplicates/groups/{group_id}/merge")
async def merge_duplicate_group(
    group_id: int,
    request: MergeRequest,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user_optional),
    current_workspace: WorkspaceORM = Depends(get_current_workspace_optional),
):
    """Merge a duplicate group into a canonical lead"""
    if not current_user or not current_workspace:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Verify group exists and belongs to org
    group = db.query(DuplicateGroupORM).filter(
        and_(
            DuplicateGroupORM.id == group_id,
            DuplicateGroupORM.organization_id == current_workspace.organization_id,
        )
    ).first()
    
    if not group:
        raise HTTPException(status_code=404, detail="Duplicate group not found")
    
    if group.status != "pending":
        raise HTTPException(status_code=400, detail=f"Group is already {group.status}")
    
    # Verify canonical lead exists and is in the group
    duplicate_leads = db.query(DuplicateLeadORM).filter(
        DuplicateLeadORM.duplicate_group_id == group_id
    ).all()
    
    lead_ids_in_group = [dl.lead_id for dl in duplicate_leads]
    if request.canonical_lead_id not in lead_ids_in_group:
        raise HTTPException(
            status_code=400,
            detail="Canonical lead must be one of the leads in this duplicate group"
        )
    
    # Perform merge
    try:
        canonical = merge_duplicates(
            db=db,
            group_id=group_id,
            canonical_lead_id=request.canonical_lead_id,
            merge_fields=request.merge_fields,
        )
        
        return {
            "success": True,
            "canonical_lead_id": canonical.id,
            "message": f"Successfully merged {len(duplicate_leads) - 1} duplicate(s) into lead {canonical.id}",
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Merge failed: {str(e)}")


@router.post("/duplicates/groups/{group_id}/ignore")
async def ignore_duplicate_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user_optional),
    current_workspace: WorkspaceORM = Depends(get_current_workspace_optional),
):
    """Mark a duplicate group as ignored (not duplicates)"""
    if not current_user or not current_workspace:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    group = db.query(DuplicateGroupORM).filter(
        and_(
            DuplicateGroupORM.id == group_id,
            DuplicateGroupORM.organization_id == current_workspace.organization_id,
        )
    ).first()
    
    if not group:
        raise HTTPException(status_code=404, detail="Duplicate group not found")
    
    group.status = "ignored"
    db.commit()
    
    return {"success": True, "message": "Duplicate group marked as ignored"}


@router.get("/duplicates/stats")
async def get_duplicate_stats(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user_optional),
    current_workspace: WorkspaceORM = Depends(get_current_workspace_optional),
):
    """Get statistics about duplicates"""
    if not current_user or not current_workspace:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    total_groups = db.query(DuplicateGroupORM).filter(
        DuplicateGroupORM.organization_id == current_workspace.organization_id
    ).count()
    
    pending_groups = db.query(DuplicateGroupORM).filter(
        and_(
            DuplicateGroupORM.organization_id == current_workspace.organization_id,
            DuplicateGroupORM.status == "pending",
        )
    ).count()
    
    merged_groups = db.query(DuplicateGroupORM).filter(
        and_(
            DuplicateGroupORM.organization_id == current_workspace.organization_id,
            DuplicateGroupORM.status == "merged",
        )
    ).count()
    
    total_duplicate_leads = db.query(DuplicateLeadORM).join(DuplicateGroupORM).filter(
        DuplicateGroupORM.organization_id == current_workspace.organization_id
    ).count()
    
    return {
        "total_groups": total_groups,
        "pending_groups": pending_groups,
        "merged_groups": merged_groups,
        "total_duplicate_leads": total_duplicate_leads,
    }

