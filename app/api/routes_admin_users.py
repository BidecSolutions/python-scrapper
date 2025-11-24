"""Admin routes for managing users (super admin only)"""
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel
from datetime import datetime

from app.core.db import get_db
from app.core.orm import UserORM, UserStatus
from app.api.dependencies import require_super_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/users", tags=["admin-users"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class AdminUser(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    status: UserStatus
    is_super_admin: bool
    can_use_advanced: bool
    organization_id: Optional[int]
    created_at: datetime
    last_login_at: Optional[datetime]
    
    class Config:
        from_attributes = True  # Pydantic v2 equivalent of orm_mode = True


class AdminUserListResponse(BaseModel):
    items: List[AdminUser]
    total: int
    page: int
    page_size: int


class UpdateUserAdminRequest(BaseModel):
    status: Optional[UserStatus] = None
    can_use_advanced: Optional[bool] = None
    is_super_admin: Optional[bool] = None


# ============================================================================
# Routes
# ============================================================================

@router.get("", response_model=AdminUserListResponse)
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: Optional[str] = None,
    status: Optional[str] = None,  # "pending|active|suspended"
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(require_super_admin),
):
    """List all users (super admin only)"""
    query = db.query(UserORM)
    
    # Search filter
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                UserORM.email.ilike(like),
                UserORM.full_name.ilike(like)
            )
        )
    
    # Status filter
    if status:
        try:
            status_enum = UserStatus(status)
            query = query.filter(UserORM.status == status_enum)
        except ValueError:
            pass  # Invalid status, ignore
    
    # Count total
    total = query.count()
    
    # Paginate
    users = (
        query
        .order_by(UserORM.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    
    # Convert ORM objects to Pydantic models (Pydantic v2)
    admin_users = [AdminUser.model_validate(user) for user in users]
    
    return AdminUserListResponse(
        items=admin_users,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{user_id}", response_model=AdminUser)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(require_super_admin),
):
    """Get a specific user (super admin only)"""
    user = db.query(UserORM).filter(UserORM.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=AdminUser)
def update_user_admin(
    user_id: int,
    body: UpdateUserAdminRequest,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(require_super_admin),
):
    """Update user (approve, suspend, toggle advanced features, etc.)"""
    user = db.query(UserORM).filter(UserORM.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent self-demotion from super admin
    if user_id == current_user.id and body.is_super_admin is False:
        raise HTTPException(
            status_code=400,
            detail="Cannot remove super admin status from yourself"
        )
    
    # Update fields
    if body.status is not None:
        user.status = body.status
        logger.info(f"User {user.email} status changed to {body.status} by {current_user.email}")
    
    if body.can_use_advanced is not None:
        user.can_use_advanced = body.can_use_advanced
        logger.info(f"User {user.email} advanced access {'enabled' if body.can_use_advanced else 'disabled'} by {current_user.email}")
    
    if body.is_super_admin is not None:
        user.is_super_admin = body.is_super_admin
        logger.info(f"User {user.email} super admin status {'enabled' if body.is_super_admin else 'disabled'} by {current_user.email}")
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user

