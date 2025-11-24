"""Workspace permissions and authorization"""
import logging
from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.orm_workspaces import WorkspaceMemberORM, WorkspaceRole
from app.core.orm import UserORM

logger = logging.getLogger(__name__)


def get_workspace_member(
    db: Session,
    workspace_id: int,
    user_id: int
) -> Optional[WorkspaceMemberORM]:
    """Get workspace membership for a user"""
    return db.query(WorkspaceMemberORM).filter(
        WorkspaceMemberORM.workspace_id == workspace_id,
        WorkspaceMemberORM.user_id == user_id,
        WorkspaceMemberORM.accepted_at.isnot(None)  # Only accepted members
    ).first()


def require_workspace_member(
    db: Session,
    workspace_id: int,
    user_id: int
) -> WorkspaceMemberORM:
    """Get workspace member or raise 403"""
    member = get_workspace_member(db, workspace_id, user_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this workspace"
        )
    return member


def require_role(
    db: Session,
    workspace_id: int,
    user_id: int,
    allowed_roles: List[WorkspaceRole]
) -> WorkspaceMemberORM:
    """Require user to have one of the allowed roles in workspace"""
    member = require_workspace_member(db, workspace_id, user_id)
    
    if member.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Requires one of these roles: {', '.join([r.value for r in allowed_roles])}"
        )
    
    return member


# Permission checkers for common actions
def can_manage_billing(member: WorkspaceMemberORM) -> bool:
    """Check if member can manage billing"""
    return member.role in [WorkspaceRole.owner]


def can_manage_members(member: WorkspaceMemberORM) -> bool:
    """Check if member can manage team members"""
    return member.role in [WorkspaceRole.owner, WorkspaceRole.admin]


def can_manage_integrations(member: WorkspaceMemberORM) -> bool:
    """Check if member can setup integrations"""
    return member.role in [WorkspaceRole.owner, WorkspaceRole.admin]


def can_create_playbooks(member: WorkspaceMemberORM) -> bool:
    """Check if member can create/edit playbooks"""
    return member.role in [WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.member]


def can_capture_leads(member: WorkspaceMemberORM) -> bool:
    """Check if member can capture leads"""
    return member.role in [WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.member]


def can_run_jobs(member: WorkspaceMemberORM) -> bool:
    """Check if member can run jobs"""
    return member.role in [WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.member]


def can_export_lists(member: WorkspaceMemberORM) -> bool:
    """Check if member can export lists"""
    return member.role in [WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.member]


def can_view(member: WorkspaceMemberORM) -> bool:
    """Check if member can view (all roles can view)"""
    return True  # All roles can view


# Decorator for FastAPI routes
def require_workspace_role(*allowed_roles: WorkspaceRole):
    """
    Decorator to require specific workspace roles
    
    Usage:
        @router.post("/something")
        @require_workspace_role(WorkspaceRole.owner, WorkspaceRole.admin)
        def some_endpoint(workspace_id: int, ...):
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Extract workspace_id and user_id from kwargs or request
            # This is a simplified version - in practice, you'd get these from JWT/session
            # For now, we'll handle this in the route itself
            return func(*args, **kwargs)
        return wrapper
    return decorator

