"""Authentication routes (signup, login, /me)"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

from app.core.db import get_db
from app.core.orm import UserORM, UserStatus, OrganizationORM
from app.services.auth_service import AuthService
from app.services.jwt_service import create_user_token, decode_access_token

logger = logging.getLogger(__name__)
router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ============================================================================
# Pydantic Schemas
# ============================================================================

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    is_super_admin: bool = False
    can_use_advanced: bool = False
    status: UserStatus = UserStatus.pending


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    status: UserStatus
    is_super_admin: bool
    can_use_advanced: bool
    organization_id: Optional[int]
    current_workspace_id: Optional[int]
    created_at: datetime
    last_login_at: Optional[datetime]
    
    class Config:
        from_attributes = True  # Pydantic v2 equivalent of orm_mode = True


# ============================================================================
# Dependencies
# ============================================================================

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> UserORM:
    """Get current authenticated user from JWT token"""
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(UserORM).filter(UserORM.id == int(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def require_super_admin(
    current_user: UserORM = Depends(get_current_user)
) -> UserORM:
    """Require super admin permissions"""
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    return current_user


# ============================================================================
# Routes
# ============================================================================

@router.post("/auth/signup", response_model=MeResponse, status_code=201)
def signup(
    payload: SignupRequest,
    db: Session = Depends(get_db)
):
    """Sign up a new user (status will be 'pending' until approved)"""
    # Check if email already exists
    existing_user = db.query(UserORM).filter(UserORM.email == payload.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    password_hash = AuthService.hash_password(payload.password)
    
    # Get or create default organization (for backward compatibility)
    # In a real app, you might want to create a new org per user or use a different flow
    default_org = db.query(OrganizationORM).first()
    if not default_org:
        default_org = OrganizationORM(
            name="Default Organization",
            slug="default",
        )
        db.add(default_org)
        db.flush()
    
    # Create user with status=pending
    user = UserORM(
        email=payload.email,
        password_hash=password_hash,
        full_name=payload.full_name,
        status=UserStatus.pending,
        is_super_admin=False,
        can_use_advanced=False,
        organization_id=default_org.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    logger.info(f"New user signed up: {user.email} (status: {user.status})")
    
    return user


@router.post("/auth/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db)
):
    """Login and get JWT token (only if status is 'active')"""
    user = db.query(UserORM).filter(UserORM.email == payload.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not AuthService.verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if account is active
    if user.status != UserStatus.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {user.status.value}. Please wait for approval or contact support."
        )
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    db.add(user)
    db.commit()
    
    # Create JWT token
    access_token = create_user_token(
        user_id=user.id,
        email=user.email,
        is_super_admin=user.is_super_admin,
        can_use_advanced=user.can_use_advanced,
    )
    
    logger.info(f"User logged in: {user.email}")
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=MeResponse)
def get_me(
    current_user: UserORM = Depends(get_current_user)
):
    """Get current user information"""
    return current_user


@router.post("/auth/create-user", response_model=MeResponse, status_code=201)
def create_user(
    payload: CreateUserRequest,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(require_super_admin),
):
    """Create a new user (super admin only)"""
    # Check if email already exists
    existing_user = db.query(UserORM).filter(UserORM.email == payload.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    password_hash = AuthService.hash_password(payload.password)
    
    # Get organization (use current user's org or default)
    org_id = current_user.organization_id
    if not org_id:
        default_org = db.query(OrganizationORM).first()
        if not default_org:
            default_org = OrganizationORM(
                name="Default Organization",
                slug="default",
            )
            db.add(default_org)
            db.flush()
        org_id = default_org.id
    
    # Create user
    user = UserORM(
        email=payload.email,
        password_hash=password_hash,
        full_name=payload.full_name,
        status=payload.status,
        is_super_admin=payload.is_super_admin,
        can_use_advanced=payload.can_use_advanced,
        organization_id=org_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    logger.info(f"User created by {current_user.email}: {user.email} (status: {user.status}, super_admin: {user.is_super_admin})")
    
    return user
