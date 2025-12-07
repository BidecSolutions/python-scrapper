"""Background job executor - runs scraping jobs asynchronously"""
import logging
import asyncio
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.core.orm import ScrapeJobORM, JobStatus, LeadORM
from app.scraper.async_crawler import AsyncCrawler
from app.services.async_lead_service import AsyncLeadService
from app.services.lead_repo import upsert_leads
from app.sources.google_places import GooglePlacesSource
from app.sources.google_search import GoogleSearchSource
from app.sources.web_search import WebSearchSource
from app.sources.basic_web_search import BasicWebSearchSource

logger = logging.getLogger(__name__)


def _update_job_progress(db: Session, job_id: int, processed: int, total: int):
    """Update job progress"""
    try:
        job = db.query(ScrapeJobORM).filter(ScrapeJobORM.id == job_id).first()
        if job:
            job.processed_targets = processed
            job.total_targets = total
            # Update result_count from current leads
            lead_count = db.query(LeadORM).filter(LeadORM.job_id == job_id).count()
            job.result_count = lead_count
            db.commit()
    except Exception as e:
        logger.warning(f"Failed to update job progress: {e}")
        try:
            db.rollback()
        except:
            pass


async def execute_job_background(job_id: int, org_id: int, payload_dict: dict):
    """
    Execute a scraping job in the background
    
    Args:
        job_id: Job ID to execute
        org_id: Organization ID
        payload_dict: Original payload as dict (for sources, extract config, etc.)
    """
    db = SessionLocal()
    job = None
    
    try:
        # Get job
        job = db.query(ScrapeJobORM).filter(ScrapeJobORM.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return
        
        # Update status to running
        job.status = JobStatus.running
        job.started_at = datetime.now(timezone.utc)
        db.commit()
        logger.info(f"Job {job_id} started in background")
        
        # Extract payload data
        niche = payload_dict.get("niche", job.niche)
        location = payload_dict.get("location")
        max_results = payload_dict.get("max_results", job.max_results)
        max_pages_per_site = payload_dict.get("max_pages_per_site", job.max_pages_per_site)
        requested_sources = payload_dict.get("sources", ["google_search", "google_places", "web_search"])
        use_crawling = payload_dict.get("sources") is None or "crawling" in requested_sources
        extract_config_dict = payload_dict.get("extract", job.extract_config or {})
        
        # Initialize sources
        sources = []
        source_errors = []
        
        # Try to initialize Google Places source (if requested)
        if "google_places" in requested_sources:
            try:
                google_source = GooglePlacesSource()
                sources.append(google_source)
                logger.info("Google Places source initialized successfully")
            except ValueError as e:
                error_msg = f"Google Places source unavailable: {str(e)}"
                logger.warning(error_msg)
                source_errors.append(error_msg)
            except Exception as e:
                error_msg = f"Google Places source error: {str(e)}"
                logger.warning(error_msg)
                source_errors.append(error_msg)
        
        # Try to initialize Google Custom Search source (if requested)
        if "google_search" in requested_sources:
            try:
                google_search_source = GoogleSearchSource()
                sources.append(google_search_source)
                logger.info("Google Custom Search source initialized successfully")
            except ValueError as e:
                error_msg = f"Google Custom Search source unavailable: {str(e)}"
                logger.warning(error_msg)
                source_errors.append(error_msg)
            except Exception as e:
                error_msg = f"Google Custom Search source error: {str(e)}"
                logger.warning(error_msg)
                source_errors.append(error_msg)
        
        # Try to initialize Web Search (Bing) source (if requested)
        if "web_search" in requested_sources:
            try:
                web_source = WebSearchSource()
                if web_source.api_key:
                    sources.append(web_source)
                    logger.info("Web Search (Bing) source initialized successfully")
                else:
                    logger.warning("Web Search source skipped: BING_SEARCH_API_KEY not set")
                    source_errors.append("Web Search source unavailable: BING_SEARCH_API_KEY not set")
            except Exception as e:
                error_msg = f"Web Search source error: {str(e)}"
                logger.warning(error_msg)
                source_errors.append(error_msg)
        
        # If no API sources available, use basic web search as fallback
        if not sources:
            logger.warning("No API sources available. Using basic web search fallback (no API key required).")
            logger.warning("For better results, configure API keys: " + "; ".join(source_errors) if source_errors else "GOOGLE_PLACES_API_KEY, GOOGLE_SEARCH_API_KEY+GOOGLE_SEARCH_CX, or BING_SEARCH_API_KEY")
            try:
                basic_source = BasicWebSearchSource()
                sources.append(basic_source)
                logger.info("Basic web search source initialized (fallback mode)")
                job.error_message = "Using basic web search (no API keys). For better results, configure API keys in .env file."
                db.commit()
            except Exception as e:
                error_message = "No scraping sources available. " + "; ".join(source_errors) if source_errors else "Please configure at least one API key (GOOGLE_PLACES_API_KEY, GOOGLE_SEARCH_API_KEY+GOOGLE_SEARCH_CX, or BING_SEARCH_API_KEY) in your .env file."
                logger.error(f"Failed to initialize basic web search: {e}")
                logger.warning(error_message)
                job.error_message = error_message
                job.status = JobStatus.failed
                db.commit()
                return
        
        # Run scraping
        leads = []
        if sources:
            try:
                # Only use crawler if crawling is enabled
                crawler = AsyncCrawler(max_pages=max_pages_per_site) if use_crawling else None
                service = AsyncLeadService(
                    sources=sources, 
                    crawler=crawler,
                    extract_config=extract_config_dict,
                    progress_callback=lambda processed, total: _update_job_progress(db, job.id, processed, total)
                )
                logger.info(f"Starting lead search with {len(sources)} source(s): {[type(s).__name__ for s in sources]}")
                
                # First, get raw leads to determine total_targets
                raw_leads = []
                for source in sources:
                    try:
                        for lead in source.search(niche, location):
                            raw_leads.append(lead)
                            if len(raw_leads) >= max_results:
                                break
                    except Exception as e:
                        logger.warning(f"Source {source.__class__.__name__} failed: {e}")
                        continue
                    if len(raw_leads) >= max_results:
                        break
                
                # Set total_targets (websites to process)
                websites_to_process = len([l for l in raw_leads if l.website])
                job.total_targets = websites_to_process
                db.commit()
                logger.info(f"Job {job.id}: Processing {websites_to_process} websites")
                
                # Now enrich leads with progress tracking
                leads = await service.search_leads(
                    niche=niche,
                    location=location,
                    max_results=max_results,
                )
                logger.info(f"Found {len(leads)} leads from scraping")
            except Exception as scrape_error:
                error_msg = f"Error during scraping: {str(scrape_error)}"
                logger.error(error_msg)
                import traceback
                logger.error(traceback.format_exc())
                job.error_message = error_msg
                leads = []  # Continue with empty list if scraping fails
        
        # Save to DB
        saved_leads = []
        if leads:
            try:
                saved_leads = upsert_leads(db, leads, job_id=job.id, organization_id=org_id, commit=False)
            except Exception as save_error:
                logger.error(f"Error saving leads: {save_error}")
                import traceback
                logger.error(traceback.format_exc())
                saved_leads = []
        
        # Update job status
        job.status = JobStatus.completed
        job.result_count = len(saved_leads)
        job.completed_at = datetime.now(timezone.utc)
        if job.started_at:
            # Ensure both datetimes are timezone-aware for subtraction
            if job.started_at.tzinfo is None:
                started_at = job.started_at.replace(tzinfo=timezone.utc)
            else:
                started_at = job.started_at
            duration = (job.completed_at - started_at).total_seconds()
            job.duration_seconds = int(duration)
        
        # Commit everything together
        db.commit()
        logger.info(f"Job {job.id} completed successfully with {len(saved_leads)} leads")
        
        # Create notification for job completion
        try:
            from app.services.notification_service import create_notification
            from app.core.orm_notifications import NotificationType
            from app.core.orm_workspaces import WorkspaceORM
            
            # Get workspace_id - use job's workspace_id if available, otherwise get first workspace for org
            workspace_id = job.workspace_id
            if not workspace_id:
                workspace = db.query(WorkspaceORM).filter(
                    WorkspaceORM.organization_id == org_id
                ).first()
                if workspace:
                    workspace_id = workspace.id
            
            if workspace_id:
                job_name = f"{job.niche}{' - ' + job.location if job.location else ''}"
                create_notification(
                    db=db,
                    workspace_id=workspace_id,
                    type=NotificationType.job_completed,
                    title=f"Job finished: {job_name}",
                    body=f"We found {len(saved_leads)} leads for \"{job_name}\".",
                    user_id=job.created_by_user_id,
                    target_url=f"/jobs/{job.id}",
                    meta={"job_id": job.id, "lead_count": len(saved_leads)},
                )
                db.commit()
                logger.info(f"Created completion notification for job {job.id}")
        except Exception as e:
            logger.warning(f"Failed to create notification for job {job.id}: {e}")
            # Don't fail the job if notification creation fails
        
        # Post-processing: ML scoring, segments, insights, niche classification (async, don't block response)
        try:
            from app.services.ml_scoring_service import MLScoringService
            from app.services.segmentation_service import SegmentationService
            from app.services.insights_service import InsightsService
            from app.services.niche_classifier import NicheClassifier
            
            # Classify and normalize niche (async)
            try:
                await NicheClassifier.normalize_niche_for_job(db, job.id)
            except Exception as e:
                logger.warning(f"Niche classification failed: {e}")
            
            # Score leads with ML (if model exists)
            scoring_service = MLScoringService()
            lead_ids = [l.id for l in saved_leads]
            scoring_service.score_leads_for_org(db, org_id, lead_ids)
            
            # Create segments if enough leads (async)
            if len(saved_leads) >= 10:
                await SegmentationService.create_segments_for_job(db, job.id)
            
            # Generate insights (async)
            await InsightsService.generate_insights_for_job(db, job.id)
            
        except Exception as e:
            logger.warning(f"Post-processing failed for job {job.id}: {e}")
            # Don't fail the job if post-processing fails
    
    except Exception as e:
        import traceback
        error_msg = str(e)[:500]
        error_trace = traceback.format_exc()
        
        # Log the full error for debugging
        logger.error(f"Job {job_id} failed in background: {error_trace}")
        
        # Try to save error to job
        if job:
            try:
                job.status = JobStatus.failed
                job.error_message = error_msg
                job.completed_at = datetime.now(timezone.utc)
                db.commit()
                
                # Create notification for job failure
                try:
                    from app.services.notification_service import create_notification
                    from app.core.orm_notifications import NotificationType
                    from app.core.orm_workspaces import WorkspaceORM
                    
                    # Get workspace_id - use job's workspace_id if available, otherwise get first workspace for org
                    workspace_id = job.workspace_id
                    if not workspace_id:
                        workspace = db.query(WorkspaceORM).filter(
                            WorkspaceORM.organization_id == org_id
                        ).first()
                        if workspace:
                            workspace_id = workspace.id
                    
                    if workspace_id:
                        job_name = f"{job.niche}{' - ' + job.location if job.location else ''}"
                        create_notification(
                            db=db,
                            workspace_id=workspace_id,
                            type=NotificationType.job_failed,
                            title=f"Job failed: {job_name}",
                            body=error_msg[:200],
                            user_id=job.created_by_user_id,
                            target_url=f"/jobs/{job.id}",
                            meta={"job_id": job.id},
                        )
                        db.commit()
                        logger.info(f"Created failure notification for job {job.id}")
                except Exception as notif_error:
                    logger.warning(f"Failed to create failure notification for job {job.id}: {notif_error}")
                    # Don't fail if notification creation fails
                    
            except Exception as save_error:
                logger.error(f"Failed to save error to job: {save_error}")
                try:
                    db.rollback()
                except:
                    pass
    
    finally:
        db.close()


def run_job_in_background(job_id: int, org_id: int, payload_dict: dict):
    """Wrapper to run async job in background task"""
    asyncio.run(execute_job_background(job_id, org_id, payload_dict))

