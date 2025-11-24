"""API Keys Management API routes"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.db import get_db
from app.core.orm_api_keys import APIKeyORM, ApiKeyScope
from app.core.orm_workspaces import WorkspaceORM, WorkspaceRole
from app.core.orm import UserORM, OrganizationORM
from app.api.routes_workspaces import get_current_user_id
from app.services.workspace_permissions import require_role
from app.services.api_key_auth import (
    generate_api_key,
    hash_api_key,
    parse_scopes
)

logger = logging.getLogger(__name__)
router = APIRouter()


class ApiKeyCreate(BaseModel):
    """Request to create an API key"""
    name: str = Field(..., description="Key name (e.g., 'LinkedIn extension')")
    scopes: List[str] = Field(..., description="List of scopes (e.g., ['leads:read', 'leads:write'])")
    rate_limit_per_minute: Optional[int] = Field(None, description="Rate limit per minute (default: 60)")
    rate_limit_per_hour: Optional[int] = Field(None, description="Optional rate limit per hour")
    rate_limit_per_day: Optional[int] = Field(None, description="Optional rate limit per day")
    description: Optional[str] = Field(None, description="Optional description")
    expires_at: Optional[str] = Field(None, description="Optional expiration date (ISO format)")


class ApiKeyUpdate(BaseModel):
    """Request to update an API key"""
    name: Optional[str] = None
    active: Optional[bool] = None
    scopes: Optional[List[str]] = None
    rate_limit_per_minute: Optional[int] = None
    rate_limit_per_hour: Optional[int] = None
    rate_limit_per_day: Optional[int] = None
    description: Optional[str] = None
    expires_at: Optional[str] = None


class ApiKeyOut(BaseModel):
    """API key response (without token)"""
    id: int
    name: str
    scopes: List[str]
    rate_limit_per_minute: Optional[int] = None
    rate_limit_per_hour: Optional[int] = None
    rate_limit_per_day: Optional[int] = None
    active: bool
    expires_at: Optional[str] = None
    created_at: str
    last_used_at: Optional[str] = None
    last_used_ip: Optional[str] = None
    total_requests: int
    description: Optional[str] = None
    key_prefix: Optional[str] = None  # First few chars for display
    
    class Config:
        from_attributes = True


class ApiKeyCreateResponse(ApiKeyOut):
    """Response when creating a new API key (includes token)"""
    token: str  # Only shown once


@router.post("/api-keys", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
def create_api_key(
    key_data: ApiKeyCreate,
    workspace_id: Optional[int] = None,  # Get from JWT/session in production
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Create a new API key
    
    Requires Owner or Admin role in the workspace.
    Returns the raw token once - store it securely!
    """
    # Get workspace (for now, use default org's first workspace or create one)
    from app.api.routes_settings import get_or_create_default_org
    
    org = get_or_create_default_org(db)
    
    # If workspace_id not provided, get or create default workspace
    if not workspace_id:
        workspace = db.query(WorkspaceORM).filter(
            WorkspaceORM.organization_id == org.id
        ).first()
        
        if not workspace:
            # Create default workspace
            import re
            import secrets
            slug = f"default-{secrets.token_hex(4)}"
            workspace = WorkspaceORM(
                name="Default Workspace",
                slug=slug,
                organization_id=org.id,
            )
            db.add(workspace)
            db.flush()
            
            # Add user as owner
            from app.core.orm_workspaces import WorkspaceMemberORM
            member = WorkspaceMemberORM(
                workspace_id=workspace.id,
                user_id=current_user_id,
                role=WorkspaceRole.owner,
                accepted_at=datetime.utcnow(),
            )
            db.add(member)
            db.commit()
            db.refresh(workspace)
    else:
        workspace = db.query(WorkspaceORM).filter(
            WorkspaceORM.id == workspace_id,
            WorkspaceORM.organization_id == org.id
        ).first()
        
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        # Verify user has permission (Owner or Admin)
        from app.services.workspace_permissions import require_role
        require_role(db, workspace_id, current_user_id, [WorkspaceRole.owner, WorkspaceRole.admin])
    
    # Validate scopes
    valid_scopes = {scope.value for scope in ApiKeyScope}
    for scope in key_data.scopes:
        if scope not in valid_scopes:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid scope: {scope}. Valid scopes: {', '.join(valid_scopes)}"
            )
    
    # Generate API key
    raw_token, key_hash = generate_api_key()
    key_prefix = raw_token[:20] + "..."  # First 20 chars for display
    
    # Parse expiration
    expires_at = None
    if key_data.expires_at:
        try:
            expires_at = datetime.fromisoformat(key_data.expires_at.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid expires_at format. Use ISO 8601.")
    
    # Create API key record
    api_key = APIKeyORM(
        workspace_id=workspace.id,
        organization_id=org.id,  # Also store for backward compatibility
        name=key_data.name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        scopes=",".join(key_data.scopes),
        rate_limit_per_minute=key_data.rate_limit_per_minute,
        rate_limit_per_hour=key_data.rate_limit_per_hour,
        rate_limit_per_day=key_data.rate_limit_per_day,
        description=key_data.description,
        expires_at=expires_at,
        created_by_user_id=current_user_id,
        active=True,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    
    logger.info(f"Created API key {api_key.id} for workspace {workspace.id}")
    
    return ApiKeyCreateResponse(
        id=api_key.id,
        name=api_key.name,
        scopes=key_data.scopes,
        rate_limit_per_minute=api_key.rate_limit_per_minute,
        rate_limit_per_hour=api_key.rate_limit_per_hour,
        rate_limit_per_day=api_key.rate_limit_per_day,
        active=api_key.active,
        expires_at=api_key.expires_at.isoformat() if api_key.expires_at else None,
        created_at=api_key.created_at.isoformat(),
        last_used_at=api_key.last_used_at.isoformat() if api_key.last_used_at else None,
        last_used_ip=api_key.last_used_ip,
        total_requests=api_key.total_requests,
        description=api_key.description,
        key_prefix=api_key.key_prefix,
        token=raw_token,  # Show once!
    )


@router.get("/api-keys", response_model=List[ApiKeyOut])
def list_api_keys(
    workspace_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """List all API keys for the workspace"""
    from app.api.routes_settings import get_or_create_default_org
    
    org = get_or_create_default_org(db)
    
    # Get workspace
    if workspace_id:
        workspace = db.query(WorkspaceORM).filter(
            WorkspaceORM.id == workspace_id,
            WorkspaceORM.organization_id == org.id
        ).first()
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        # Verify membership
        from app.services.workspace_permissions import require_workspace_member
        require_workspace_member(db, workspace_id, current_user_id)
        
        query = db.query(APIKeyORM).filter(APIKeyORM.workspace_id == workspace_id)
    else:
        # List all keys for user's workspaces
        from app.core.orm_workspaces import WorkspaceMemberORM
        workspace_ids = db.query(WorkspaceMemberORM.workspace_id).filter(
            WorkspaceMemberORM.user_id == current_user_id,
            WorkspaceMemberORM.accepted_at.isnot(None)
        ).subquery()
        
        query = db.query(APIKeyORM).filter(
            APIKeyORM.workspace_id.in_(db.query(workspace_ids.c.workspace_id))
        )
    
    api_keys = query.order_by(APIKeyORM.created_at.desc()).all()
    
    return [
        ApiKeyOut(
            id=key.id,
            name=key.name,
            scopes=parse_scopes(key.scopes),
            rate_limit_per_minute=key.rate_limit_per_minute,
            rate_limit_per_hour=key.rate_limit_per_hour,
            rate_limit_per_day=key.rate_limit_per_day,
            active=key.active,
            expires_at=key.expires_at.isoformat() if key.expires_at else None,
            created_at=key.created_at.isoformat(),
            last_used_at=key.last_used_at.isoformat() if key.last_used_at else None,
            last_used_ip=key.last_used_ip,
            total_requests=key.total_requests,
            description=key.description,
            key_prefix=key.key_prefix,
        )
        for key in api_keys
    ]


@router.get("/api-keys/{key_id}", response_model=ApiKeyOut)
def get_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """Get a specific API key"""
    api_key = db.query(APIKeyORM).filter(APIKeyORM.id == key_id).first()
    
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    # Verify user has access (member of workspace)
    if api_key.workspace_id:
        from app.services.workspace_permissions import require_workspace_member
        require_workspace_member(db, api_key.workspace_id, current_user_id)
    
    return ApiKeyOut(
        id=api_key.id,
        name=api_key.name,
        scopes=parse_scopes(api_key.scopes),
        rate_limit_per_minute=api_key.rate_limit_per_minute,
        rate_limit_per_hour=api_key.rate_limit_per_hour,
        rate_limit_per_day=api_key.rate_limit_per_day,
        active=api_key.active,
        expires_at=api_key.expires_at.isoformat() if api_key.expires_at else None,
        created_at=api_key.created_at.isoformat(),
        last_used_at=api_key.last_used_at.isoformat() if api_key.last_used_at else None,
        last_used_ip=api_key.last_used_ip,
        total_requests=api_key.total_requests,
        description=api_key.description,
        key_prefix=api_key.key_prefix,
    )


@router.patch("/api-keys/{key_id}", response_model=ApiKeyOut)
def update_api_key(
    key_id: int,
    update_data: ApiKeyUpdate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """Update an API key (revoke, change name, update limits)"""
    api_key = db.query(APIKeyORM).filter(APIKeyORM.id == key_id).first()
    
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    # Verify user has permission (Owner or Admin)
    if api_key.workspace_id:
        from app.services.workspace_permissions import require_role
        require_role(db, api_key.workspace_id, current_user_id, [WorkspaceRole.owner, WorkspaceRole.admin])
    
    # Update fields
    if update_data.name is not None:
        api_key.name = update_data.name
    if update_data.active is not None:
        api_key.active = update_data.active
    if update_data.scopes is not None:
        # Validate scopes
        valid_scopes = {scope.value for scope in ApiKeyScope}
        for scope in update_data.scopes:
            if scope not in valid_scopes:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid scope: {scope}"
                )
        api_key.scopes = ",".join(update_data.scopes)
    if update_data.rate_limit_per_minute is not None:
        api_key.rate_limit_per_minute = update_data.rate_limit_per_minute
    if update_data.rate_limit_per_hour is not None:
        api_key.rate_limit_per_hour = update_data.rate_limit_per_hour
    if update_data.rate_limit_per_day is not None:
        api_key.rate_limit_per_day = update_data.rate_limit_per_day
    if update_data.description is not None:
        api_key.description = update_data.description
    if update_data.expires_at is not None:
        if update_data.expires_at:
            try:
                api_key.expires_at = datetime.fromisoformat(update_data.expires_at.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid expires_at format")
        else:
            api_key.expires_at = None
    
    db.commit()
    db.refresh(api_key)
    
    return ApiKeyOut(
        id=api_key.id,
        name=api_key.name,
        scopes=parse_scopes(api_key.scopes),
        rate_limit_per_minute=api_key.rate_limit_per_minute,
        rate_limit_per_hour=api_key.rate_limit_per_hour,
        rate_limit_per_day=api_key.rate_limit_per_day,
        active=api_key.active,
        expires_at=api_key.expires_at.isoformat() if api_key.expires_at else None,
        created_at=api_key.created_at.isoformat(),
        last_used_at=api_key.last_used_at.isoformat() if api_key.last_used_at else None,
        last_used_ip=api_key.last_used_ip,
        total_requests=api_key.total_requests,
        description=api_key.description,
        key_prefix=api_key.key_prefix,
    )


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """Delete an API key permanently"""
    api_key = db.query(APIKeyORM).filter(APIKeyORM.id == key_id).first()
    
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    # Verify user has permission (Owner or Admin)
    if api_key.workspace_id:
        from app.services.workspace_permissions import require_role
        require_role(db, api_key.workspace_id, current_user_id, [WorkspaceRole.owner, WorkspaceRole.admin])
    
    db.delete(api_key)
    db.commit()
    
    logger.info(f"Deleted API key {key_id}")
    return

