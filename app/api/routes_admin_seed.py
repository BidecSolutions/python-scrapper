"""Admin utilities for demo seeding."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.routes_auth import require_super_admin
from app.core.db import get_db
from seed_demo_data import SeedConfig, seed_demo

router = APIRouter()


@router.post("/admin/seed-demo")
def seed_demo_data_endpoint(
    db: Session = Depends(get_db),
    _: object = Depends(require_super_admin),
):
    """Seed demo data (super admin only)."""
    try:
        cfg = SeedConfig(
            admin_email="admin@admin.com",
            admin_password="Admin@123456",
            workspace_slug="default",
        )
        summary = seed_demo(db, cfg)
        return {"status": "ok", "summary": summary}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to seed demo data: {exc}",
        )
