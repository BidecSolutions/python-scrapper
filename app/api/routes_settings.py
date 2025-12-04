"""Settings and organization management API routes"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from pydantic import BaseModel
import hashlib
import secrets
import os
import shutil
from pathlib import Path

from app.core.db import get_db
from app.core.orm import OrganizationORM, PlanTier, LeadORM, ScrapeJobORM, APIKeyStatus
from app.core.orm_api_keys import APIKeyORM


class UpdateOrganizationRequest(BaseModel):
    name: str
    brand_name: Optional[str] = None
    tagline: Optional[str] = None


class CreateApiKeyRequest(BaseModel):
    name: Optional[str] = None

router = APIRouter()


def get_or_create_default_org(db: Session) -> OrganizationORM:
    """Get or create default organization for testing"""
    org = db.query(OrganizationORM).filter(OrganizationORM.slug == "default").first()
    
    if not org:
        org = OrganizationORM(
            name="Acme Growth Agency",
            slug="default",
            plan_tier=PlanTier.pro,
        )
        db.add(org)
        db.commit()
        db.refresh(org)
    
    return org


@router.get("/settings/organization")
@router.get("/organization")  # Alias for frontend compatibility
def get_organization(db: Session = Depends(get_db)):
    """Get current organization details"""
    org = get_or_create_default_org(db)
    
    return {
        "id": org.id,
        "name": org.name,
        "slug": org.slug,
        "plan_tier": org.plan_tier.value,
        "logo_url": org.logo_url,
        "brand_name": org.brand_name,
        "tagline": org.tagline,
        "created_at": org.created_at.isoformat(),
    }


@router.put("/settings/organization")
@router.patch("/organization")  # Alias for frontend compatibility (PATCH method)
def update_organization(
    request: UpdateOrganizationRequest,
    db: Session = Depends(get_db),
):
    """Update organization details"""
    org = get_or_create_default_org(db)
    org.name = request.name
    if request.brand_name is not None:
        org.brand_name = request.brand_name if request.brand_name.strip() else None
    if request.tagline is not None:
        org.tagline = request.tagline if request.tagline.strip() else None
    db.commit()
    db.refresh(org)
    
    return {
        "id": org.id,
        "name": org.name,
        "slug": org.slug,
        "plan_tier": org.plan_tier.value,
        "logo_url": org.logo_url,
        "brand_name": org.brand_name,
        "tagline": org.tagline,
    }


# Create uploads directory if it doesn't exist
# Note: On serverless platforms (Vercel, AWS Lambda), filesystem may be read-only
# In production, use cloud storage (S3, Vercel Blob, etc.) instead of local filesystem
UPLOADS_DIR = Path("uploads/logos")
try:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
except (OSError, PermissionError) as e:
    # Serverless platforms have read-only filesystem - this is expected
    # File uploads won't work on serverless, should use cloud storage instead
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Could not create uploads directory (read-only filesystem on serverless): {e}")
    UPLOADS_DIR = None  # Disable file uploads on serverless


@router.post("/settings/organization/logo")
async def upload_logo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload organization logo"""
    # Check if file uploads are supported (not on serverless platforms)
    if UPLOADS_DIR is None:
        raise HTTPException(
            status_code=503,
            detail="File uploads not supported on serverless platforms. Please use cloud storage (S3, Vercel Blob, etc.)"
        )
    
    org = get_or_create_default_org(db)
    
    # Validate file type
    allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/gif", "image/svg+xml", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}")
    
    # Validate file size (max 5MB)
    file_content = await file.read()
    if len(file_content) > 5 * 1024 * 1024:  # 5MB
        raise HTTPException(status_code=400, detail="File size too large. Maximum size is 5MB")
    
    # Generate unique filename
    file_ext = Path(file.filename).suffix or ".png"
    filename = f"org_{org.id}_{int(datetime.utcnow().timestamp())}{file_ext}"
    
    # UPLOADS_DIR is already checked above, so it's safe to use here
    file_path = UPLOADS_DIR / filename
    
    # Save file
    try:
        with open(file_path, "wb") as f:
            f.write(file_content)
    except (OSError, PermissionError) as e:
        raise HTTPException(
            status_code=503,
            detail=f"Could not save file (read-only filesystem on serverless): {str(e)}"
        )
    
    # Delete old logo if exists
    if org.logo_url and UPLOADS_DIR:
        old_path = Path(org.logo_url.lstrip("/"))
        if old_path.exists() and old_path.parent == UPLOADS_DIR:
            try:
                old_path.unlink()
            except Exception:
                pass  # Ignore errors deleting old file
    
    # Update organization with new logo URL
    logo_url = f"/uploads/logos/{filename}"
    org.logo_url = logo_url
    db.commit()
    db.refresh(org)
    
    return {
        "id": org.id,
        "name": org.name,
        "slug": org.slug,
        "plan_tier": org.plan_tier.value,
        "logo_url": org.logo_url,
        "brand_name": org.brand_name,
        "tagline": org.tagline,
    }


@router.delete("/settings/organization/logo")
def delete_logo(db: Session = Depends(get_db)):
    """Delete organization logo"""
    org = get_or_create_default_org(db)
    
    if org.logo_url:
        # Delete file
        file_path = Path(org.logo_url.lstrip("/"))
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception:
                pass  # Ignore errors deleting file
        
        # Clear logo URL
        org.logo_url = None
        db.commit()
        db.refresh(org)
    
    return {
        "id": org.id,
        "name": org.name,
        "slug": org.slug,
        "plan_tier": org.plan_tier.value,
        "logo_url": None,
        "brand_name": org.brand_name,
        "tagline": org.tagline,
    }


@router.get("/settings/api-keys")
def list_api_keys(db: Session = Depends(get_db)):
    """List all API keys for the organization"""
    org = get_or_create_default_org(db)
    keys = db.query(APIKeyORM).filter(APIKeyORM.organization_id == org.id).all()
    
    return [
        {
            "id": key.id,
            "name": key.name,
            "key_prefix": key.key_prefix,
            "status": key.status.value,
            "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
            "created_at": key.created_at.isoformat(),
        }
        for key in keys
    ]


@router.post("/settings/api-keys")
def create_api_key(
    request: CreateApiKeyRequest,
    db: Session = Depends(get_db),
):
    """Create a new API key"""
    org = get_or_create_default_org(db)
    
    # Generate a secure API key
    api_key = secrets.token_urlsafe(32)
    key_prefix = api_key[:8]
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    # Create API key record
    api_key_orm = APIKeyORM(
        organization_id=org.id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=request.name or "API Key",
        status=APIKeyStatus.active,
    )
    db.add(api_key_orm)
    db.commit()
    db.refresh(api_key_orm)
    
    # Return the full key only once (frontend should store it securely)
    return {
        "id": api_key_orm.id,
        "name": api_key_orm.name,
        "key": api_key,  # Only returned on creation
        "key_prefix": api_key_orm.key_prefix,
        "status": api_key_orm.status.value,
        "created_at": api_key_orm.created_at.isoformat(),
    }


@router.delete("/settings/api-keys/{key_id}")
def revoke_api_key(
    key_id: int,
    db: Session = Depends(get_db),
):
    """Revoke an API key"""
    org = get_or_create_default_org(db)
    key = db.query(APIKeyORM).filter(
        APIKeyORM.id == key_id,
        APIKeyORM.organization_id == org.id
    ).first()
    
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    key.status = APIKeyStatus.revoked
    db.commit()
    
    return {"message": "API key revoked"}


@router.get("/settings/usage")
@router.get("/usage/stats")  # Alias for frontend compatibility
def get_usage_stats(db: Session = Depends(get_db)):
    """Get current plan and usage statistics"""
    org = get_or_create_default_org(db)
    
    # Get current month's lead count
    now = datetime.utcnow()
    start_of_month = datetime(now.year, now.month, 1)
    
    leads_this_month = db.query(func.count(LeadORM.id)).filter(
        LeadORM.organization_id == org.id,
        LeadORM.created_at >= start_of_month
    ).scalar() or 0
    
    # Get total leads
    total_leads = db.query(func.count(LeadORM.id)).filter(
        LeadORM.organization_id == org.id
    ).scalar() or 0
    
    # Get total jobs
    total_jobs = db.query(func.count(ScrapeJobORM.id)).filter(
        ScrapeJobORM.organization_id == org.id
    ).scalar() or 0
    
    # Plan limits (based on plan tier)
    plan_limits = {
        PlanTier.free: {"leads_per_month": 100},
        PlanTier.starter: {"leads_per_month": 1000},
        PlanTier.pro: {"leads_per_month": 5000},
        PlanTier.agency: {"leads_per_month": 20000},
        PlanTier.enterprise: {"leads_per_month": 100000},
    }
    
    limit = plan_limits.get(org.plan_tier, plan_limits[PlanTier.free])["leads_per_month"]
    
    return {
        "plan_tier": org.plan_tier.value,
        "leads_used_this_month": leads_this_month,
        "leads_limit_per_month": limit,
        "total_leads": total_leads,
        "total_jobs": total_jobs,
    }

