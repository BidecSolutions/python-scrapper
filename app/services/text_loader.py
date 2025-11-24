"""Helper service for loading website text from snapshots"""
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.orm import LeadSnapshotORM, LeadORM

logger = logging.getLogger(__name__)


async def load_website_text_for_lead(db: AsyncSession, lead: LeadORM) -> Optional[str]:
    """
    Load website text from snapshots for AI processing
    
    Args:
        db: Database session
        lead: Lead ORM object
    
    Returns:
        Combined text from all snapshots, or None if no snapshots
    """
    try:
        stmt = select(LeadSnapshotORM).where(
            LeadSnapshotORM.lead_id == lead.id
        ).order_by(
            LeadSnapshotORM.page_type.asc(),  # Order: home, contact, about
            LeadSnapshotORM.created_at.desc()
        )
        
        result = await db.execute(stmt)
        snapshots = result.scalars().all()
        
        if not snapshots:
            return None
        
        # Combine text from multiple pages
        # Prefer: contact > about > home
        page_order = {"contact": 0, "about": 1, "home": 2, "other": 3}
        sorted_snapshots = sorted(
            snapshots,
            key=lambda s: (page_order.get(s.page_type.lower(), 99), s.created_at)
        )
        
        # Build text blob with page markers
        text_parts = []
        for snapshot in sorted_snapshots:
            if snapshot.text:
                text_parts.append(f"[PAGE] {snapshot.page_type}\n<title>{snapshot.url}</title>\n<content>\n{snapshot.text}\n</content>")
        
        return "\n\n".join(text_parts) if text_parts else None
    
    except Exception as e:
        logger.error(f"Error loading website text for lead {lead.id}: {e}", exc_info=True)
        return None

