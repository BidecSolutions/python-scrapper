"""Usage and credits API routes"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.core.db import get_db
from app.core.orm import OrganizationORM
from app.services.credit_manager import CreditManager
from app.api.routes_settings import get_or_create_default_org

logger = logging.getLogger(__name__)
router = APIRouter()


class UsageResponse(BaseModel):
    """Usage and credits information"""
    plan: str
    credits_total: int
    credits_used: int
    credits_remaining: int
    credits_reset_at: Optional[str] = None


@router.get("/me/usage", response_model=UsageResponse)
def get_usage(
    db: Session = Depends(get_db),
):
    """
    Get current usage and credits for the organization
    """
    org = get_or_create_default_org(db)
    
    balance_info = CreditManager.get_balance(db, org.id)
    
    return UsageResponse(
        plan=org.plan_tier.value,
        credits_total=balance_info.get("limit", 1000),
        credits_used=balance_info.get("used", 0),
        credits_remaining=balance_info.get("balance", 0),
        credits_reset_at=balance_info.get("reset_at"),
    )

