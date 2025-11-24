"""AI worker tasks (queue-based processing)"""
import asyncio
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.db import AsyncSessionLocal
from app.core.orm import LeadORM, ScrapeJobORM, JobStatus, LeadSnapshotORM
from app.services.ai_enrichment_service import AIEnrichmentService
from app.ai.llm_extractor import LLMExtractor, MockLLMClient
from app.ai.scoring import LeadScorer

logger = logging.getLogger(__name__)


# Note: This is a conceptual implementation
# In production, you'd use Celery, RQ, or similar task queue
# For now, this shows the structure

async def ai_enrich_lead_task(lead_id: int, llm_client=None):
    """
    AI enrichment task for a single lead
    
    This would be called by a task queue worker (Celery/RQ/etc.)
    
    Args:
        lead_id: ID of lead to enrich
        llm_client: LLM client (optional, uses mock if not provided)
    """
    async with AsyncSessionLocal() as db:
        try:
            # Get lead
            lead: Optional[LeadORM] = await db.get(LeadORM, lead_id)
            if not lead:
                logger.warning(f"Lead {lead_id} not found")
                return
            
            # Initialize AI services
            # Try to create LLM client from configuration, fallback to mock if not available
            if llm_client is None:
                from app.ai.factory import create_llm_client
                llm_client = create_llm_client()
                if llm_client is None:
                    logger.warning("No LLM client available, using mock client for testing")
                    llm_client = MockLLMClient()
            
            llm_extractor = LLMExtractor(llm_client=llm_client)
            scorer = LeadScorer()
            ai_service = AIEnrichmentService(llm_extractor=llm_extractor, scorer=scorer)
            
            # Enrich lead
            success = await ai_service.enrich_lead(db, lead)
            
            if success:
                logger.info(f"Successfully enriched lead {lead_id}")
                
                # Check if job is complete
                if lead.job_id:
                    await _maybe_mark_job_completed(db, lead.job_id)
            else:
                logger.warning(f"Failed to enrich lead {lead_id}")
            
            await db.commit()
        
        except Exception as e:
            logger.error(f"Error enriching lead {lead_id}: {e}", exc_info=True)
            await db.rollback()


async def _maybe_mark_job_completed(db: AsyncSession, job_id: int):
    """Check if all leads for a job have been AI-enriched"""
    try:
        job: Optional[ScrapeJobORM] = await db.get(ScrapeJobORM, job_id)
        if not job:
            return
        
        # Check AI status of leads
        stmt = select(
            func.count(LeadORM.id).label("total"),
            func.count(LeadORM.id).filter(LeadORM.ai_status == "success").label("enriched"),
            func.count(LeadORM.id).filter(LeadORM.ai_status == "failed").label("failed"),
            func.count(LeadORM.id).filter(LeadORM.ai_status.in_(["pending", "processing"])).label("pending"),
        ).where(LeadORM.job_id == job_id)
        
        result = await db.execute(stmt)
        row = result.first()
        
        if row:
            total = row.total or 0
            enriched = row.enriched or 0
            failed = row.failed or 0
            pending = row.pending or 0
            
            # If all leads are processed (success or failed), mark job as completed
            if total > 0 and (enriched + failed) == total and pending == 0:
                job.status = JobStatus.completed
                job.result_count = enriched
                await db.flush()
                logger.info(f"Job {job_id} marked as completed: {enriched} enriched, {failed} failed")
    
    except Exception as e:
        logger.error(f"Error checking job completion for job {job_id}: {e}", exc_info=True)


# For Celery/RQ integration (example structure)
# Uncomment and adapt based on your task queue choice

"""
from celery import Celery

celery_app = Celery("ai_worker", broker="redis://localhost:6379/0")

@celery_app.task(name="ai_enrich_lead", max_retries=3, default_retry_delay=30)
def ai_enrich_lead_celery(lead_id: int):
    \"\"\"Celery task wrapper\"\"\"
    asyncio.run(ai_enrich_lead_task(lead_id))

# Usage:
# ai_enrich_lead_celery.delay(lead_id)
"""

