"""Shared dependencies for permission checks"""
from fastapi import Depends, HTTPException, status
from app.core.orm import UserORM
from app.api.routes_auth import get_current_user


def require_advanced_user(current_user: UserORM = Depends(get_current_user)) -> UserORM:
    """Require user to have advanced features enabled"""
    if not current_user.can_use_advanced:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Advanced features are not enabled for this account. Please contact your administrator.",
        )
    return current_user


def require_super_admin(current_user: UserORM = Depends(get_current_user)) -> UserORM:
    """Require super admin access"""
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required",
        )
    return current_user

