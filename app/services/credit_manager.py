"""Credit management service for tracking usage and billing"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.orm import (
    OrganizationORM,
    CreditTransactionORM,
    CreditTransactionType,
)

logger = logging.getLogger(__name__)


class CreditManager:
    """Manages credit balance, deductions, and usage tracking"""
    
    # Credit costs per operation
    COST_EMAIL_FINDER = 1
    COST_EMAIL_VERIFIER = 0.5
    COST_SCRAPING_JOB = 10
    COST_ROBOT_RUN = 5
    
    @staticmethod
    def get_balance(db: Session, organization_id: int) -> Dict[str, Any]:
        """Get current credit balance and limits"""
        org = db.query(OrganizationORM).filter(OrganizationORM.id == organization_id).first()
        if not org:
            return {"balance": 0, "limit": 0, "reset_at": None}
        
        # Check if credits need to be reset (monthly reset)
        if org.credits_reset_at and datetime.utcnow() >= org.credits_reset_at:
            CreditManager.reset_monthly_credits(db, organization_id)
            db.refresh(org)
        
        return {
            "balance": org.credits_balance or 0,
            "limit": org.credits_limit or 1000,
            "reset_at": org.credits_reset_at.isoformat() if org.credits_reset_at else None,
            "used": (org.credits_limit or 1000) - (org.credits_balance or 0),
        }
    
    @staticmethod
    def check_balance(db: Session, organization_id: int, required_credits: int) -> bool:
        """Check if organization has enough credits"""
        balance_info = CreditManager.get_balance(db, organization_id)
        return balance_info["balance"] >= required_credits
    
    @staticmethod
    def deduct_credits(
        db: Session,
        organization_id: int,
        amount: int,
        feature: str,
        reference_id: Optional[int] = None,
        reference_type: Optional[str] = None,
        description: Optional[str] = None,
    ) -> bool:
        """
        Deduct credits from organization balance
        
        Returns True if successful, False if insufficient credits
        """
        org = db.query(OrganizationORM).filter(OrganizationORM.id == organization_id).first()
        if not org:
            logger.error(f"Organization {organization_id} not found")
            return False
        
        # Check if credits need to be reset
        if org.credits_reset_at and datetime.utcnow() >= org.credits_reset_at:
            CreditManager.reset_monthly_credits(db, organization_id)
            db.refresh(org)
        
        current_balance = org.credits_balance or 0
        
        if current_balance < amount:
            logger.warning(
                f"Insufficient credits for org {organization_id}: "
                f"balance={current_balance}, required={amount}"
            )
            return False
        
        # Deduct credits
        new_balance = current_balance - amount
        org.credits_balance = new_balance
        db.commit()
        
        # Record transaction
        transaction = CreditTransactionORM(
            organization_id=organization_id,
            transaction_type=CreditTransactionType.deduction,
            amount=-amount,  # Negative for deduction
            balance_after=new_balance,
            feature=feature,
            reference_id=reference_id,
            reference_type=reference_type,
            description=description or f"{feature} operation",
        )
        db.add(transaction)
        db.commit()
        
        logger.info(
            f"Deducted {amount} credits from org {organization_id}. "
            f"New balance: {new_balance}"
        )
        return True
    
    @staticmethod
    def grant_credits(
        db: Session,
        organization_id: int,
        amount: int,
        reason: str = "Manual grant",
        feature: Optional[str] = None,
        reference_id: Optional[int] = None,
        reference_type: Optional[str] = None,
    ) -> bool:
        """Grant credits to organization"""
        org = db.query(OrganizationORM).filter(OrganizationORM.id == organization_id).first()
        if not org:
            logger.error(f"Organization {organization_id} not found")
            return False
        
        current_balance = org.credits_balance or 0
        new_balance = current_balance + amount
        
        # Don't exceed limit
        limit = org.credits_limit or 1000
        if new_balance > limit:
            new_balance = limit
        
        org.credits_balance = new_balance
        db.commit()
        
        # Record transaction
        transaction = CreditTransactionORM(
            organization_id=organization_id,
            transaction_type=CreditTransactionType.grant,
            amount=amount,
            balance_after=new_balance,
            feature=feature,
            reference_id=reference_id,
            reference_type=reference_type,
            description=reason,
        )
        db.add(transaction)
        db.commit()
        
        logger.info(
            f"Granted {amount} credits to org {organization_id}. "
            f"New balance: {new_balance}"
        )
        return True
    
    @staticmethod
    def reset_monthly_credits(db: Session, organization_id: int) -> bool:
        """Reset monthly credits (called at start of billing cycle)"""
        org = db.query(OrganizationORM).filter(OrganizationORM.id == organization_id).first()
        if not org:
            return False
        
        limit = org.credits_limit or 1000
        old_balance = org.credits_balance or 0
        
        # Reset to full limit
        org.credits_balance = limit
        
        # Set next reset date (30 days from now)
        org.credits_reset_at = datetime.utcnow() + timedelta(days=30)
        db.commit()
        
        # Record transaction
        transaction = CreditTransactionORM(
            organization_id=organization_id,
            transaction_type=CreditTransactionType.reset,
            amount=limit - old_balance,  # Difference
            balance_after=limit,
            description=f"Monthly credit reset (limit: {limit})",
        )
        db.add(transaction)
        db.commit()
        
        logger.info(
            f"Reset credits for org {organization_id}. "
            f"Old: {old_balance}, New: {limit}"
        )
        return True
    
    @staticmethod
    def get_usage_stats(
        db: Session,
        organization_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get usage statistics by feature"""
        query = db.query(CreditTransactionORM).filter(
            CreditTransactionORM.organization_id == organization_id,
            CreditTransactionORM.transaction_type == CreditTransactionType.deduction,
        )
        
        if start_date:
            query = query.filter(CreditTransactionORM.created_at >= start_date)
        if end_date:
            query = query.filter(CreditTransactionORM.created_at <= end_date)
        
        transactions = query.all()
        
        # Group by feature
        usage_by_feature: Dict[str, int] = {}
        total_credits = 0
        
        for txn in transactions:
            feature = txn.feature or "unknown"
            amount = abs(txn.amount)  # Make positive
            usage_by_feature[feature] = usage_by_feature.get(feature, 0) + amount
            total_credits += amount
        
        return {
            "total_credits_used": total_credits,
            "by_feature": usage_by_feature,
            "transaction_count": len(transactions),
        }
    
    @staticmethod
    def initialize_credits(db: Session, organization_id: int) -> None:
        """Initialize credits for a new organization"""
        org = db.query(OrganizationORM).filter(OrganizationORM.id == organization_id).first()
        if not org:
            return
        
        # Set default limit based on plan tier
        plan_limits = {
            "free": 100,
            "starter": 500,
            "pro": 5000,
            "agency": 50000,
            "enterprise": 100000,
        }
        
        limit = plan_limits.get(org.plan_tier.value.lower(), 100)
        org.credits_limit = limit
        org.credits_balance = limit
        
        # Set reset date to 30 days from now
        org.credits_reset_at = datetime.utcnow() + timedelta(days=30)
        db.commit()
        
        logger.info(f"Initialized {limit} credits for org {organization_id} ({org.plan_tier.value})")

