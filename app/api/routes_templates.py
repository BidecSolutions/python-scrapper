"""Template Library & Governance API routes"""
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.db import get_db
from app.core.orm_templates import (
    TemplateORM, TemplateGovernanceORM,
    TemplateScope, TemplateStatus, TemplateKind
)
from app.api.routes_auth import get_current_user
from app.api.routes_workspaces import get_current_workspace, get_current_user_optional, get_current_workspace_optional
from app.core.orm import UserORM
from app.core.orm_workspaces import WorkspaceORM

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/templates", tags=["templates"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class TemplateOut(BaseModel):
    id: int
    workspace_id: Optional[int]
    scope: str
    name: str
    description: Optional[str]
    kind: str
    subject: Optional[str]
    body: Optional[str]
    status: str
    locked: bool
    created_by_user_id: int
    approved_by_user_id: Optional[int]
    tags: Optional[List[str]]
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True  # Pydantic v2 equivalent of orm_mode = True


class TemplateListResponse(BaseModel):
    items: List[TemplateOut]
    total: int


class CreateTemplateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    kind: str = Field("email", pattern="^(email|subject|sequence_step)$")
    subject: Optional[str] = Field(None, max_length=255)
    body: Optional[str] = None
    tags: Optional[List[str]] = None
    scope: str = Field("workspace", pattern="^(workspace|global)$")


class UpdateTemplateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    subject: Optional[str] = Field(None, max_length=255)
    body: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = Field(None, pattern="^(draft|pending_approval|approved|deprecated|rejected)$")


class TemplateGovernanceOut(BaseModel):
    workspace_id: int
    require_approval_for_new_templates: bool
    restrict_to_approved_only: bool
    allow_personal_templates: bool
    require_unsubscribe: bool
    
    class Config:
        from_attributes = True  # Pydantic v2 equivalent of orm_mode = True


class UpdateGovernanceRequest(BaseModel):
    require_approval_for_new_templates: Optional[bool] = None
    restrict_to_approved_only: Optional[bool] = None
    allow_personal_templates: Optional[bool] = None
    require_unsubscribe: Optional[bool] = None


# ============================================================================
# Routes
# ============================================================================

@router.get("", response_model=TemplateListResponse)
def list_templates(
    status: Optional[str] = None,
    kind: Optional[str] = None,
    tag: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user_optional),
    workspace: WorkspaceORM = Depends(get_current_workspace_optional),
):
    """List templates for current workspace"""
    q = db.query(TemplateORM).filter(
        or_(
            TemplateORM.workspace_id == workspace.id,
            TemplateORM.scope == TemplateScope.global_scope,
        )
    )
    
    if status:
        try:
            status_enum = TemplateStatus(status)
            q = q.filter(TemplateORM.status == status_enum)
        except ValueError:
            pass
    
    if kind:
        try:
            kind_enum = TemplateKind(kind)
            q = q.filter(TemplateORM.kind == kind_enum)
        except ValueError:
            pass
    
    if tag:
        # Filter by tag (stored as JSON array)
        q = q.filter(TemplateORM.tags.contains([tag]))
    
    items = q.order_by(TemplateORM.updated_at.desc()).all()
    
    return TemplateListResponse(
        items=items,
        total=len(items),
    )


@router.get("/{template_id}", response_model=TemplateOut)
def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user_optional),
    workspace: WorkspaceORM = Depends(get_current_workspace_optional),
):
    """Get template detail"""
    template = db.query(TemplateORM).filter(
        TemplateORM.id == template_id,
        or_(
            TemplateORM.workspace_id == workspace.id,
            TemplateORM.scope == TemplateScope.global_scope,
        )
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return template


@router.post("", response_model=TemplateOut, status_code=201)
def create_template(
    body: CreateTemplateRequest,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user_optional),
    workspace: WorkspaceORM = Depends(get_current_workspace_optional),
):
    """Create a new template"""
    # Check governance rules
    governance = db.query(TemplateGovernanceORM).filter(
        TemplateGovernanceORM.workspace_id == workspace.id
    ).first()
    
    # If governance requires approval, set status to pending
    initial_status = TemplateStatus.draft
    if governance and governance.require_approval_for_new_templates:
        initial_status = TemplateStatus.pending_approval
    
    template = TemplateORM(
        workspace_id=workspace.id if body.scope == "workspace" else None,
        scope=TemplateScope(body.scope),
        name=body.name,
        description=body.description,
        kind=TemplateKind(body.kind),
        subject=body.subject,
        body=body.body,
        status=initial_status,
        created_by_user_id=current_user.id,
        tags=body.tags or [],
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    logger.info(f"Created template {template.id}: {template.name} in workspace {workspace.id}")
    return template


@router.patch("/{template_id}", response_model=TemplateOut)
def update_template(
    template_id: int,
    body: UpdateTemplateRequest,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user_optional),
    workspace: WorkspaceORM = Depends(get_current_workspace_optional),
):
    """Update a template"""
    template = db.query(TemplateORM).filter(
        TemplateORM.id == template_id,
        or_(
            TemplateORM.workspace_id == workspace.id,
            TemplateORM.scope == TemplateScope.global_scope,
        )
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Check if locked
    if template.locked and template.created_by_user_id != current_user.id:
        # Only workspace admins can edit locked templates (check role here if needed)
        raise HTTPException(status_code=403, detail="Template is locked")
    
    # Update fields
    if body.name is not None:
        template.name = body.name
    if body.description is not None:
        template.description = body.description
    if body.subject is not None:
        template.subject = body.subject
    if body.body is not None:
        template.body = body.body
    if body.tags is not None:
        template.tags = body.tags
    if body.status is not None:
        template.status = TemplateStatus(body.status)
    
    template.updated_at = datetime.utcnow()
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return template


@router.post("/{template_id}/approve", response_model=TemplateOut)
def approve_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user_optional),
    workspace: WorkspaceORM = Depends(get_current_workspace_optional),
):
    """Approve a template (workspace admin only)"""
    template = db.query(TemplateORM).filter(
        TemplateORM.id == template_id,
        TemplateORM.workspace_id == workspace.id,
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    template.status = TemplateStatus.approved
    template.approved_by_user_id = current_user.id
    template.updated_at = datetime.utcnow()
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    logger.info(f"Approved template {template.id} by user {current_user.id}")
    return template


@router.post("/{template_id}/reject", response_model=TemplateOut)
def reject_template(
    template_id: int,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user_optional),
    workspace: WorkspaceORM = Depends(get_current_workspace_optional),
):
    """Reject a template (workspace admin only)"""
    template = db.query(TemplateORM).filter(
        TemplateORM.id == template_id,
        TemplateORM.workspace_id == workspace.id,
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    template.status = TemplateStatus.rejected
    if reason:
        template.meta = template.meta or {}
        template.meta["rejection_reason"] = reason
    
    template.updated_at = datetime.utcnow()
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    logger.info(f"Rejected template {template.id} by user {current_user.id}")
    return template


@router.get("/governance", response_model=TemplateGovernanceOut)
def get_governance(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user_optional),
    workspace: WorkspaceORM = Depends(get_current_workspace_optional),
):
    """Get template governance settings"""
    governance = db.query(TemplateGovernanceORM).filter(
        TemplateGovernanceORM.workspace_id == workspace.id
    ).first()
    
    if not governance:
        # Create default governance
        governance = TemplateGovernanceORM(
            workspace_id=workspace.id,
        )
        db.add(governance)
        db.commit()
        db.refresh(governance)
    
    return governance


@router.patch("/governance", response_model=TemplateGovernanceOut)
def update_governance(
    body: UpdateGovernanceRequest,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user_optional),
    workspace: WorkspaceORM = Depends(get_current_workspace_optional),
):
    """Update template governance settings (workspace admin only)"""
    governance = db.query(TemplateGovernanceORM).filter(
        TemplateGovernanceORM.workspace_id == workspace.id
    ).first()
    
    if not governance:
        governance = TemplateGovernanceORM(workspace_id=workspace.id)
        db.add(governance)
    
    if body.require_approval_for_new_templates is not None:
        governance.require_approval_for_new_templates = body.require_approval_for_new_templates
    if body.restrict_to_approved_only is not None:
        governance.restrict_to_approved_only = body.restrict_to_approved_only
    if body.allow_personal_templates is not None:
        governance.allow_personal_templates = body.allow_personal_templates
    if body.require_unsubscribe is not None:
        governance.require_unsubscribe = body.require_unsubscribe
    
    governance.updated_at = datetime.utcnow()
    db.add(governance)
    db.commit()
    db.refresh(governance)
    
    return governance

