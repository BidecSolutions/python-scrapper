"""Job-based API routes with database persistence"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from app.api.schemas import ScrapeRequest, ScrapeResponse, LeadOut, JobResponse
from app.core.db import get_db
from app.core.orm import ScrapeJobORM, JobStatus, OrganizationORM, PlanTier, LeadORM
from app.scraper.async_crawler import AsyncCrawler
from app.services.async_lead_service import AsyncLeadService
from app.services.lead_repo import upsert_leads
from app.sources.google_places import GooglePlacesSource
from app.sources.google_search import GoogleSearchSource
from app.sources.web_search import WebSearchSource
# YellowPages disabled per user request
# from app.sources.yellow_pages import YellowPagesSource
# For now, we'll create a default org for testing
# In production, use: from app.api.middleware import get_organization_from_api_key

router = APIRouter()


def _update_job_progress(db: Session, job_id: int, processed: int, total: int):
    """Update job progress (called from async context, so we need to handle DB carefully)"""
    try:
        # Get fresh job instance
        from app.core.orm import ScrapeJobORM
        job = db.query(ScrapeJobORM).filter(ScrapeJobORM.id == job_id).first()
        if job:
            job.processed_targets = processed
            job.total_targets = total
            # Update result_count from current leads
            from app.core.orm import LeadORM
            lead_count = db.query(LeadORM).filter(LeadORM.job_id == job_id).count()
            job.result_count = lead_count
            db.commit()
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to update job progress: {e}")
        try:
            db.rollback()
        except:
            pass


def get_or_create_default_org(db: Session) -> int:
    """Get or create default organization for testing"""
    try:
        # Check if default org exists
        org = db.query(OrganizationORM).filter(OrganizationORM.slug == "default").first()
        
        if not org:
            # Create default org
            org = OrganizationORM(
                name="Default Organization",
                slug="default",
                plan_tier=PlanTier.pro,
            )
            db.add(org)
            db.flush()  # Flush to get the ID, but don't commit here
        
        return org.id
    except Exception as e:
        import traceback
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in get_or_create_default_org: {traceback.format_exc()}")
        raise


@router.get("/jobs", response_model=List[dict])
def get_jobs(
    db: Session = Depends(get_db),
) -> List[dict]:
    """Get all jobs"""
    org_id = get_or_create_default_org(db)
    jobs = db.query(ScrapeJobORM).filter(
        ScrapeJobORM.organization_id == org_id
    ).order_by(ScrapeJobORM.created_at.desc()).all()
    
    return [
        {
            "id": job.id,
            "niche": job.niche,
            "location": job.location,
            "status": job.status.value,
            "result_count": job.result_count,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "updated_at": job.updated_at.isoformat() if job.updated_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "duration_seconds": job.duration_seconds,
            "sites_crawled": job.sites_crawled,
            "sites_failed": job.sites_failed,
            "total_pages_crawled": job.total_pages_crawled,
            "sources_used": job.sources_used or [],
            "error_message": job.error_message,
            "max_results": job.max_results,
            "max_pages_per_site": job.max_pages_per_site,
            "total_targets": job.total_targets,
            "processed_targets": job.processed_targets or 0,
            "extract_config": job.extract_config or {},
        }
        for job in jobs
    ]


@router.get("/jobs/{job_id}", response_model=dict)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """Get a single job by ID"""
    org_id = get_or_create_default_org(db)
    job = db.query(ScrapeJobORM).filter(
        ScrapeJobORM.id == job_id,
        ScrapeJobORM.organization_id == org_id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "id": job.id,
        "niche": job.niche,
        "location": job.location,
        "status": job.status.value,
        "result_count": job.result_count,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "duration_seconds": job.duration_seconds,
        "sites_crawled": job.sites_crawled,
        "sites_failed": job.sites_failed,
        "total_pages_crawled": job.total_pages_crawled,
        "sources_used": job.sources_used or [],
        "error_message": job.error_message,
        "max_results": job.max_results,
        "max_pages_per_site": job.max_pages_per_site,
        "total_targets": job.total_targets,
        "processed_targets": job.processed_targets or 0,
        "extract_config": job.extract_config or {},
    }


@router.get("/jobs/{job_id}/leads", response_model=List[LeadOut])
def get_job_leads(
    job_id: int,
    db: Session = Depends(get_db),
) -> List[LeadOut]:
    """Get leads for a specific job"""
    org_id = get_or_create_default_org(db)
    # Verify job belongs to org
    job = db.query(ScrapeJobORM).filter(
        ScrapeJobORM.id == job_id,
        ScrapeJobORM.organization_id == org_id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get leads
    leads = db.query(LeadORM).filter(LeadORM.job_id == job_id).order_by(LeadORM.quality_score.desc().nulls_last()).all()
    
    return [
        LeadOut(
            id=lead.id,
            name=lead.name,
            niche=lead.niche,
            website=lead.website,
            emails=lead.emails or [],
            phones=lead.phones or [],
            address=lead.address,
            source=lead.source,
            city=lead.city,
            country=lead.country,
            quality_score=float(lead.quality_score) if lead.quality_score else None,
            quality_label=lead.quality_label,
            tags=lead.tags or [],
            cms=lead.cms,
            tech_stack=lead.tech_stack or [],
            social_links=lead.social_links or {},
            metadata=lead.meta or {},
        )
        for lead in leads
    ]


@router.post("/jobs/run-once", response_model=dict)
async def run_scrape_job(
    payload: ScrapeRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Run a scrape job and save results to database"""
    import logging
    from datetime import datetime
    logger = logging.getLogger(__name__)
    
    job = None
    try:
        # Get or create organization
        org_id = get_or_create_default_org(db)
        db.commit()  # Commit org creation separately
        logger.info(f"Using organization ID: {org_id}")
        
        # Create job
        extract_config_dict = payload.extract.dict() if payload.extract else {}
        job = ScrapeJobORM(
            organization_id=org_id,
            niche=payload.niche,
            location=payload.location,
            max_results=payload.max_results,
            max_pages_per_site=payload.max_pages_per_site,
            status=JobStatus.running,
            extract_config=extract_config_dict,
            processed_targets=0,
        )
        db.add(job)
        db.flush()  # Get job.id (sync, no await)
        logger.info(f"Created job {job.id}")
        
        job.started_at = datetime.utcnow()
        db.commit()  # Commit initial job state

        # 2) Run scraper (outside of DB transaction to avoid greenlet issues)
        sources = []
        source_errors = []
        
        # Get requested sources from payload (default to all if not specified)
        requested_sources = payload.sources if payload.sources else ["google_search", "google_places", "web_search"]
        use_crawling = payload.sources is None or "crawling" in payload.sources
        
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
        
        # YellowPages source disabled per user request
        # Try to initialize YellowPages source
        # try:
        #     yellow_pages_source = YellowPagesSource()
        #     sources.append(yellow_pages_source)
        #     logger.info("YellowPages source initialized successfully")
        # except Exception as e:
        #     error_msg = f"YellowPages source error: {str(e)}"
        #     logger.warning(error_msg)
        #     source_errors.append(error_msg)
        
        # If no sources available, return empty leads list with helpful error
        if not sources:
            error_message = "No scraping sources available. " + "; ".join(source_errors) if source_errors else "Please configure at least one API key (GOOGLE_PLACES_API_KEY, GOOGLE_SEARCH_API_KEY+GOOGLE_SEARCH_CX, or BING_SEARCH_API_KEY) in your .env file."
            logger.warning(error_message)
            job.error_message = error_message
            leads = []
        else:
            try:
                # Only use crawler if crawling is enabled
                crawler = AsyncCrawler(max_pages=payload.max_pages_per_site) if use_crawling else None
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
                        for lead in source.search(payload.niche, payload.location):
                            raw_leads.append(lead)
                            if len(raw_leads) >= payload.max_results:
                                break
                    except Exception as e:
                        logger.warning(f"Source {source.__class__.__name__} failed: {e}")
                        continue
                    if len(raw_leads) >= payload.max_results:
                        break
                
                # Set total_targets (websites to process)
                websites_to_process = len([l for l in raw_leads if l.website])
                job.total_targets = websites_to_process
                db.commit()
                logger.info(f"Job {job.id}: Processing {websites_to_process} websites")
                
                # Now enrich leads with progress tracking
                leads = await service.search_leads(
                    niche=payload.niche,
                    location=payload.location,
                    max_results=payload.max_results,
                )
                logger.info(f"Found {len(leads)} leads from scraping")
            except Exception as scrape_error:
                error_msg = f"Error during scraping: {str(scrape_error)}"
                logger.error(error_msg)
                import traceback
                logger.error(traceback.format_exc())
                job.error_message = error_msg
                leads = []  # Continue with empty list if scraping fails

        # 3) Save to DB
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
        job.completed_at = datetime.utcnow()
        if job.started_at:
            duration = (job.completed_at - job.started_at).total_seconds()
            job.duration_seconds = int(duration)
        
        # Commit everything together
        db.commit()
        logger.info(f"Job {job.id} completed successfully with {len(saved_leads)} leads")
        
        # Post-processing: ML scoring, segments, insights, niche classification (async, don't block response)
        try:
            from app.services.ml_scoring_service import MLScoringService
            from app.services.segmentation_service import SegmentationService
            from app.services.insights_service import InsightsService
            from app.services.niche_classifier import NicheClassifier
            
            # Classify and normalize niche
            try:
                NicheClassifier.normalize_niche_for_job(db, job.id)
            except Exception as e:
                logger.warning(f"Niche classification failed: {e}")
            
            # Score leads with ML (if model exists)
            scoring_service = MLScoringService()
            lead_ids = [l.id for l in saved_leads]
            scoring_service.score_leads_for_org(db, org_id, lead_ids)
            
            # Create segments if enough leads
            if len(saved_leads) >= 10:
                SegmentationService.create_segments_for_job(db, job.id)
            
            # Generate insights
            InsightsService.generate_insights_for_job(db, job.id)
            
            # Generate embeddings for lookalike finder (optional, can be done lazily)
            # For now, embeddings are generated on-demand when similar leads are requested
            
            # Run QA checks on leads (optional, can be done lazily)
            # For now, QA checks are run on-demand via API endpoint
            
        except Exception as e:
            logger.warning(f"Post-processing failed for job {job.id}: {e}")
            # Don't fail the job if post-processing fails

        return {
            "id": job.id,
            "niche": job.niche,
            "location": job.location,
            "max_results": job.max_results,
            "max_pages_per_site": job.max_pages_per_site,
            "status": job.status.value,
            "error_message": job.error_message,
            "result_count": job.result_count,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "updated_at": job.updated_at.isoformat() if job.updated_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "duration_seconds": job.duration_seconds,
            "sites_crawled": job.sites_crawled or 0,
            "sites_failed": job.sites_failed or 0,
            "total_pages_crawled": job.total_pages_crawled or 0,
            "sources_used": job.sources_used or [],
            "total_targets": job.total_targets,
            "processed_targets": job.processed_targets or 0,
            "extract_config": job.extract_config or {},
        }
    
    except Exception as e:
        import traceback
        error_msg = str(e)[:500]
        error_trace = traceback.format_exc()
        
        # Log the full error for debugging
        logger.error(f"Job {job.id if job else 'unknown'} failed: {error_trace}")
        
        # Try to save error to job
        if job:
            try:
                job.status = JobStatus.failed
                job.error_message = error_msg
                db.commit()
            except Exception as save_error:
                logger.error(f"Failed to save error to job: {save_error}")
                try:
                    db.rollback()
                except:
                    pass
        
        # Provide helpful error message
        if "relation" in str(e).lower() or "does not exist" in str(e).lower():
            raise HTTPException(
                status_code=500,
                detail=f"Database tables not found. Please run 'python init_db.py' to create them. Error: {error_msg}"
            )
        raise HTTPException(
            status_code=500, 
            detail=f"Job failed: {error_msg}"
        )
