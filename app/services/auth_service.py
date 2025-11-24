"""Authentication and authorization service"""
import secrets
import hashlib
import bcrypt
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.orm import UserORM, OrganizationORM, APIKeyStatus, UserRole
from app.core.orm_api_keys import APIKeyORM


class AuthService:
    """Service for authentication and authorization"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify a password against a hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    @staticmethod
    def generate_api_key() -> tuple[str, str]:
        """Generate a new API key and return (key, hash)"""
        # Generate a secure random key
        key = f"ls_{secrets.token_urlsafe(32)}"  # "ls_" prefix for lead scraper
        
        # Hash it for storage
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        return key, key_hash
    
    @staticmethod
    def get_key_prefix(key: str) -> str:
        """Get the display prefix of an API key"""
        return key[:12] if len(key) > 12 else key[:len(key)]
    
    @staticmethod
    def hash_api_key(key: str) -> str:
        """Hash an API key for storage"""
        return hashlib.sha256(key.encode()).hexdigest()
    
    @staticmethod
    async def verify_api_key(db: AsyncSession, key: str) -> Optional[OrganizationORM]:
        """Verify an API key and return the organization"""
        key_hash = AuthService.hash_api_key(key)
        
        stmt = select(APIKeyORM).where(
            APIKeyORM.key_hash == key_hash,
            APIKeyORM.status == APIKeyStatus.active
        )
        result = await db.execute(stmt)
        api_key = result.scalar_one_or_none()
        
        if not api_key:
            return None
        
        # Update last used
        api_key.last_used_at = datetime.utcnow()
        await db.commit()
        
        # Get organization
        stmt = select(OrganizationORM).where(OrganizationORM.id == api_key.organization_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[UserORM]:
        """Get a user by email"""
        stmt = select(UserORM).where(UserORM.email == email)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_organization(db: AsyncSession, user_id: int) -> Optional[OrganizationORM]:
        """Get user's organization"""
        stmt = select(UserORM).where(UserORM.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        stmt = select(OrganizationORM).where(OrganizationORM.id == user.organization_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    def has_permission(user_role: UserRole, required_role: UserRole) -> bool:
        """Check if user role has required permission"""
        role_hierarchy = {
            UserRole.owner: 4,
            UserRole.admin: 3,
            UserRole.member: 2,
            UserRole.viewer: 1,
        }
        return role_hierarchy.get(user_role, 0) >= role_hierarchy.get(required_role, 0)

