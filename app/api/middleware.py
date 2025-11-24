"""API middleware for authentication and authorization"""
from fastapi import Request, HTTPException, Depends, Header
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.services.auth_service import AuthService
from app.core.orm import UserORM, OrganizationORM


async def get_organization_from_api_key(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> OrganizationORM:
    """Dependency to get organization from API key"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    org = await AuthService.verify_api_key(db, x_api_key)
    if not org:
        raise HTTPException(status_code=401, detail="Invalid or revoked API key")
    
    return org


async def get_organization_from_auth(
    request: Request,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> OrganizationORM:
    """Dependency to get organization from JWT token (future implementation)"""
    # TODO: Implement JWT token verification
    # For now, this is a placeholder
    raise HTTPException(status_code=501, detail="JWT authentication not yet implemented")


async def require_role(required_role: str = "member"):
    """Dependency factory to require a specific role"""
    async def role_checker(
        org: OrganizationORM = Depends(get_organization_from_api_key),
        # In a real implementation, you'd get the current user from the session
    ):
        # TODO: Get current user from session/token
        # For now, we'll check at the organization level
        # In production, you'd check the user's role in the organization
        pass
    
    return role_checker

