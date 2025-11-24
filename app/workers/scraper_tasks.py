"""Scraper worker tasks (queue-based processing)"""
import asyncio
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import AsyncSessionLocal
from app.core.orm import ScrapeJobORM, JobStatus, LeadORM, LeadSnapshotORM
from app.scraper.async_crawler import AsyncCrawler
from app.services.async_lead_service import AsyncLeadService
from app.services.lead_repo import upsert_leads
from app.sources.google_places import GooglePlacesSource
from app.sources.web_search import WebSearchSource
from app.workers.ai_tasks import ai_enrich_lead_task

logger = logging.getLogger(__name__)


async def scrape_job_task(job_id: int, enable_ai: bool = True):
    """
    Scrape job task - processes a scraping job
    
    This would be called by a task queue worker (Celery/RQ/etc.)
    
    Args:
        job_id: ID of job to process
        enable_ai: Whether to enqueue AI enrichment tasks
    """
    async with AsyncSessionLocal() as db:
        try:
            # Get job
            job: Optional[ScrapeJobORM] = await db.get(ScrapeJobORM, job_id)
            if not job:
                logger.warning(f"Job {job_id} not found")
                return
            
            # Update job status
            job.status = JobStatus.running
            await db.flush()
            
            logger.info(f"Starting scrape job {job_id}: {job.niche} in {job.location}")
            
            # Initialize sources
            sources = []
            try:
                sources.append(GooglePlacesSource())
            except ValueError:
                logger.warning("Google Places source not available")
            
            try:
                sources.append(WebSearchSource())
            except Exception:
                logger.warning("Web Search source not available")
            
            if not sources:
                job.status = JobStatus.failed
                job.error_message = "No sources available"
                await db.commit()
                return
            
            # Initialize crawler and service
            crawler = AsyncCrawler(max_pages=job.max_pages_per_site)
            service = AsyncLeadService(sources=sources, crawler=crawler)
            
            # Search for leads and crawl websites
            leads = await service.search_leads(
                niche=job.niche,
                location=job.location,
                max_results=job.max_results,
            )
            
            # Save leads to database
            saved_leads = await upsert_leads(db, leads, job_id=job.id)
            
            # Save website text snapshots for AI processing
            if enable_ai and saved_leads:
                await _save_lead_snapshots(db, saved_leads)
            
            # Update job status
            job.result_count = len(saved_leads)
            
            if enable_ai:
                # Mark job as waiting for AI processing
                job.status = JobStatus.ai_pending
                
                # Enqueue AI enrichment tasks for each lead
                # In production, this would enqueue to a task queue
                for lead in saved_leads:
                    # Example: ai_enrich_lead_task.delay(lead.id) for Celery
                    # For now, we'll call it directly (in production, use queue)
                    try:
                        await ai_enrich_lead_task(lead.id)
                    except Exception as e:
                        logger.error(f"Error enqueueing AI task for lead {lead.id}: {e}")
            else:
                # No AI processing, mark as completed
                job.status = JobStatus.completed
            
            await db.commit()
            logger.info(f"Completed scrape job {job_id}: {len(saved_leads)} leads")
        
        except Exception as e:
            logger.error(f"Error processing scrape job {job_id}: {e}", exc_info=True)
            await db.rollback()
            
            # Mark job as failed
            job: Optional[ScrapeJobORM] = await db.get(ScrapeJobORM, job_id)
            if job:
                job.status = JobStatus.failed
                job.error_message = str(e)[:500]
                await db.commit()


async def _save_lead_snapshots(db: AsyncSession, leads: list):
    """Save website text snapshots for AI processing"""
    from app.scraper.async_crawler import AsyncCrawler
    from bs4 import BeautifulSoup
    import hashlib
    
    crawler = AsyncCrawler(max_pages=3)  # Only save first few pages
    
    for lead in leads:
        if not lead.website:
            continue
        
        try:
            # Crawl website and save text snapshots
            page_count = 0
            async for url, soup in crawler.crawl(lead.website):
                # Determine page type from URL
                url_lower = url.lower()
                if "contact" in url_lower:
                    page_type = "contact"
                elif "about" in url_lower:
                    page_type = "about"
                elif page_count == 0:
                    page_type = "home"
                else:
                    page_type = "other"
                
                # Extract text
                text = soup.get_text(separator=" ", strip=True)
                
                # Hash HTML for deduplication
                html_hash = hashlib.sha256(soup.prettify().encode()).hexdigest()
                
                # Check if snapshot already exists
                from sqlalchemy import select
                existing = await db.execute(
                    select(LeadSnapshotORM).where(
                        LeadSnapshotORM.lead_id == lead.id,
                        LeadSnapshotORM.html_hash == html_hash
                    )
                )
                if existing.scalar_one_or_none():
                    continue  # Skip duplicate
                
                # Create snapshot
                snapshot = LeadSnapshotORM(
                    lead_id=lead.id,
                    page_type=page_type,
                    url=url,
                    text=text[:10000],  # Limit text size
                    html_hash=html_hash,
                )
                db.add(snapshot)
                
                page_count += 1
                if page_count >= 3:  # Limit to 3 pages per lead
                    break
        
        except Exception as e:
            logger.warning(f"Error saving snapshots for lead {lead.id}: {e}")
            continue


# For Celery/RQ integration (example structure)
# Uncomment and adapt based on your task queue choice

"""
from celery import Celery

celery_app = Celery("scraper_worker", broker="redis://localhost:6379/0")

@celery_app.task(name="scrape_job", max_retries=3, default_retry_delay=60)
def scrape_job_celery(job_id: int, enable_ai: bool = True):
    \"\"\"Celery task wrapper\"\"\"
    asyncio.run(scrape_job_task(job_id, enable_ai))

# Usage:
# scrape_job_celery.delay(job_id, enable_ai=True)
"""

