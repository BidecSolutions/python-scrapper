"""Usage tracking and quota enforcement service"""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.core.orm import UsageRecordORM, OrganizationORM, PlanTier


# Plan limits configuration
PLAN_LIMITS = {
    PlanTier.free: {
        "leads_per_month": 50,
        "jobs_per_day": 3,
        "api_calls_per_minute": 10,
    },
    PlanTier.starter: {
        "leads_per_month": 500,
        "jobs_per_day": 10,
        "api_calls_per_minute": 30,
    },
    PlanTier.pro: {
        "leads_per_month": 5000,
        "jobs_per_day": 50,
        "api_calls_per_minute": 60,
    },
    PlanTier.agency: {
        "leads_per_month": 50000,
        "jobs_per_day": 200,
        "api_calls_per_minute": 120,
    },
    PlanTier.enterprise: {
        "leads_per_month": None,  # Unlimited
        "jobs_per_day": None,  # Unlimited
        "api_calls_per_minute": 300,
    },
}


class UsageTracker:
    """Track and enforce usage limits"""
    
    @staticmethod
    async def record_usage(
        db: AsyncSession,
        organization_id: int,
        usage_type: str,
        quantity: int = 1,
        api_key_id: Optional[int] = None,
        job_id: Optional[int] = None,
        metadata: Optional[dict] = None,
    ) -> UsageRecordORM:
        """Record usage"""
        usage_record = UsageRecordORM(
            organization_id=organization_id,
            api_key_id=api_key_id,
            job_id=job_id,
            usage_type=usage_type,
            quantity=quantity,
            metadata=metadata or {},
        )
        db.add(usage_record)
        await db.commit()
        await db.refresh(usage_record)
        return usage_record
    
    @staticmethod
    async def get_usage_count(
        db: AsyncSession,
        organization_id: int,
        usage_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """Get usage count for a period (defaults to current month)"""
        if not start_date:
            # Current month start
            start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if not end_date:
            end_date = datetime.now()
        
        stmt = select(func.sum(UsageRecordORM.quantity)).where(
            and_(
                UsageRecordORM.organization_id == organization_id,
                UsageRecordORM.usage_type == usage_type,
                UsageRecordORM.created_at >= start_date,
                UsageRecordORM.created_at <= end_date,
            )
        )
        result = await db.execute(stmt)
        count = result.scalar() or 0
        return int(count)
    
    @staticmethod
    async def check_quota(
        db: AsyncSession,
        organization_id: int,
        usage_type: str,
        quantity: int = 1,
    ) -> tuple[bool, Optional[str]]:
        """Check if usage is within quota. Returns (allowed, error_message)"""
        # Get organization
        stmt = select(OrganizationORM).where(OrganizationORM.id == organization_id)
        result = await db.execute(stmt)
        org = result.scalar_one_or_none()
        
        if not org:
            return False, "Organization not found"
        
        # Get plan limits
        limits = PLAN_LIMITS.get(org.plan_tier, PLAN_LIMITS[PlanTier.free])
        limit_key = f"{usage_type.split('_')[0]}s_per_{usage_type.split('_')[-1]}"
        
        # Handle different usage types
        if usage_type == "leads_scraped":
            limit_key = "leads_per_month"
        elif usage_type == "jobs_run":
            limit_key = "jobs_per_day"
            # For daily limits, check today's usage
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            current_usage = await UsageTracker.get_usage_count(
                db, organization_id, usage_type, start_date
            )
        else:
            # Monthly usage
            current_usage = await UsageTracker.get_usage_count(db, organization_id, usage_type)
        
        limit = limits.get(limit_key)
        
        # Unlimited plans
        if limit is None:
            return True, None
        
        # Check if adding quantity would exceed limit
        if current_usage + quantity > limit:
            return False, f"Quota exceeded. Limit: {limit}, Current: {current_usage}, Requested: {quantity}"
        
        return True, None
    
    @staticmethod
    async def get_usage_stats(
        db: AsyncSession,
        organization_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict:
        """Get usage statistics for an organization"""
        if not start_date:
            start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if not end_date:
            end_date = datetime.now()
        
        stmt = select(
            UsageRecordORM.usage_type,
            func.sum(UsageRecordORM.quantity).label("total")
        ).where(
            and_(
                UsageRecordORM.organization_id == organization_id,
                UsageRecordORM.created_at >= start_date,
                UsageRecordORM.created_at <= end_date,
            )
        ).group_by(UsageRecordORM.usage_type)
        
        result = await db.execute(stmt)
        stats = {row.usage_type: int(row.total or 0) for row in result}
        
        return stats

