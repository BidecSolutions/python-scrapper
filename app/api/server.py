"""FastAPI application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import asyncio

# Configure logging early so it's available for error handling
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import all ORM models to ensure they're registered with SQLAlchemy Base
# This must happen before any routes are imported that might use these models
from app.core import orm  # Main ORM models
from app.core import orm_agency  # Agency models
from app.core import orm_workspaces  # Workspace models
from app.core import orm_api_keys  # API key models
from app.core import orm_companies  # Company models
from app.core import orm_tech_intent  # Tech & intent models
from app.core import orm_ai_playbook  # AI playbook models
from app.core import orm_campaigns  # Campaign models
from app.core import orm_email_sync  # Email sync models
from app.core import orm_tasks_notes  # Tasks & notes models
from app.core import orm_activity  # Activity models
from app.core import orm_notifications  # Notification models
from app.core import orm_deals  # Deal models
from app.core import orm_health  # Health metrics models
from app.core import orm_templates  # Template models
from app.core import orm_lookalike  # Lookalike models
from app.core import orm_integrations  # Integration models
from app.core import orm_segments  # Segment models
from app.core import orm_lists  # List models
from app.core import orm_company_search  # Company search models
from app.core import orm_playbooks  # Playbook models
from app.core import orm_v2  # V2 AI models
from app.core import orm_robots  # Robot models
from app.core import orm_saved_views  # Saved views models
from app.core import orm_duplicates  # Duplicate detection models

from app.api.routes import router as api_router
from app.api.routes_jobs import router as jobs_router
from app.api.routes_leads import router as leads_router
# ML routes are optional - may fail if numpy/scikit-learn not installed
try:
    from app.api.routes_ml import router as ml_router
    ML_ROUTES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"ML routes not available: {e}")
    ml_router = None
    ML_ROUTES_AVAILABLE = False
from app.api.routes_settings import router as settings_router
from app.api.routes_dashboard import router as dashboard_router
from app.api.routes_v2 import router as v2_router
from app.api.routes_robots import router as robots_router
from app.api.routes_geo import router as geo_router
from app.api.routes_dashboard_ai import router as dashboard_ai_router
from app.api.routes_email import router as email_router
from app.api.routes_email_tools import router as email_tools_router
from app.api.routes_extension import router as extension_router
from app.api.routes_linkedin import router as linkedin_router
from app.api.routes_lists import router as lists_router
from app.api.routes_usage import router as usage_router
from app.api.routes_leads_email_status import router as leads_email_status_router
from app.api.routes_dashboard_linkedin import router as dashboard_linkedin_router
from app.api.routes_playbooks import router as playbooks_router
from app.api.routes_analytics import router as analytics_router
from app.api.routes_company_search import router as company_search_router
from app.api.routes_segments import router as segments_router
from app.api.routes_intro_lines import router as intro_lines_router
from app.api.routes_hubspot import router as hubspot_router
from app.api.routes_workspaces import router as workspaces_router
from app.api.routes_api_keys import router as api_keys_router
from app.api.routes_dashboard_segments import router as dashboard_segments_router
from app.api.routes_lead_scoring import router as lead_scoring_router
from app.api.routes_tasks_notes import router as tasks_notes_router
from app.api.routes_activity import router as activity_router
from app.api.routes_rep_performance import router as rep_performance_router
from app.api.routes_campaign_copilot import router as campaign_copilot_router
from app.api.routes_email_sync import router as email_sync_router
from app.api.routes_ai_playbook import router as ai_playbook_router
from app.api.routes_tech_intent import router as tech_intent_router
from app.api.routes_auth import router as auth_router
from app.api.routes_admin_users import router as admin_users_router
from app.api.routes_admin_activity import router as admin_activity_router
from app.api.routes_workspace_activity import router as workspace_activity_router
from app.api.routes_notifications import router as notifications_router
from app.api.routes_deals import router as deals_router
from app.api.routes_health import router as health_router
from app.api.routes_templates import router as templates_router
from app.api.routes_lookalike import router as lookalike_router
from app.api.routes_saved_views import router as saved_views_router
from app.api.routes_duplicates import router as duplicates_router
from app.api.routes_health_score import router as health_score_router
from app.api.routes_google_maps import router as google_maps_router

# Configure logging (logger already defined at top)
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown"""
    # Startup
    logger.info("Starting up application...")
    try:
        # Any startup tasks can go here
        logger.info("Application startup complete.")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    
    # Yield control to the application
    try:
        yield
    except (asyncio.CancelledError, KeyboardInterrupt):
        # These are expected when shutting down - log but don't raise
        logger.info("Shutting down application...")
    except Exception as e:
        logger.error(f"Error during runtime: {e}")
        raise
    finally:
        # Shutdown cleanup
        try:
            logger.info("Application shutdown complete.")
        except:
            pass  # Ignore errors during shutdown logging


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    app = FastAPI(
        title="Lead Scraper API",
        version="0.1.0",
        description="API for scraping lead information from various sources",
        lifespan=lifespan,
    )

    # CORS (adjust for your frontend/clients)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Unhandled exception: {error_trace}")
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error: {str(exc)}"}
        )

    app.include_router(api_router, prefix="/api", tags=["scraping"])
    app.include_router(jobs_router, prefix="/api", tags=["jobs"])
    app.include_router(leads_router, prefix="/api", tags=["leads"])
    # Register playbooks_router BEFORE ml_router to avoid route conflict
    # (ml_router has /playbooks/{playbook_id} which would match /playbooks/jobs)
    app.include_router(playbooks_router, prefix="/api", tags=["playbooks"])
    # ML routes are optional - only include if available (numpy/scikit-learn installed)
    if ML_ROUTES_AVAILABLE and ml_router:
        app.include_router(ml_router, prefix="/api", tags=["ml"])
    else:
        logger.warning("ML routes not registered - numpy/scikit-learn may not be installed")
    app.include_router(settings_router, prefix="/api", tags=["settings"])
    app.include_router(dashboard_router, prefix="/api", tags=["dashboard"])
    app.include_router(v2_router, prefix="/api/v2", tags=["v2-ai"])
    app.include_router(robots_router, prefix="/api", tags=["robots"])
    app.include_router(geo_router, prefix="/api", tags=["geo"])
    app.include_router(dashboard_ai_router, prefix="/api", tags=["dashboard-ai"])
    app.include_router(email_router, prefix="/api", tags=["email"])
    app.include_router(email_tools_router, prefix="/api", tags=["email-tools"])
    app.include_router(extension_router, prefix="/api", tags=["extension"])
    app.include_router(linkedin_router, prefix="/api", tags=["linkedin"])
    app.include_router(lists_router, prefix="/api", tags=["lists"])
    app.include_router(usage_router, prefix="/api", tags=["usage"])
    app.include_router(leads_email_status_router, prefix="/api", tags=["leads"])
    app.include_router(dashboard_linkedin_router, prefix="/api", tags=["dashboard"])
    app.include_router(analytics_router, prefix="/api", tags=["analytics"])
    app.include_router(company_search_router, prefix="/api", tags=["company-search"])
    app.include_router(segments_router, prefix="/api", tags=["segments"])
    app.include_router(intro_lines_router, prefix="/api", tags=["intro-lines"])
    app.include_router(hubspot_router, prefix="/api", tags=["hubspot"])
    app.include_router(workspaces_router, prefix="/api", tags=["workspaces"])
    app.include_router(api_keys_router, prefix="/api", tags=["api-keys"])
    app.include_router(dashboard_segments_router, prefix="/api", tags=["dashboard"])
    app.include_router(lead_scoring_router, prefix="/api", tags=["leads"])
    app.include_router(tasks_notes_router, prefix="/api", tags=["tasks", "notes"])
    app.include_router(activity_router, prefix="/api", tags=["activity"])
    app.include_router(rep_performance_router, prefix="/api", tags=["reports"])
    app.include_router(campaign_copilot_router, prefix="/api", tags=["campaigns", "ai"])
    app.include_router(email_sync_router, prefix="/api", tags=["email-sync"])
    app.include_router(ai_playbook_router, prefix="/api", tags=["ai-playbooks"])
    app.include_router(tech_intent_router, prefix="/api", tags=["tech-intent"])
    app.include_router(auth_router, prefix="/api", tags=["auth"])
    app.include_router(admin_users_router, prefix="/api", tags=["admin"])
    app.include_router(admin_activity_router, prefix="/api", tags=["admin"])
    app.include_router(workspace_activity_router, prefix="/api", tags=["activity"])
    app.include_router(notifications_router, prefix="/api", tags=["notifications"])
    app.include_router(deals_router, prefix="/api", tags=["deals"])
    app.include_router(health_router, prefix="/api", tags=["health"])
    app.include_router(templates_router, prefix="/api", tags=["templates"])
    app.include_router(lookalike_router, prefix="/api", tags=["lookalike"])
    app.include_router(saved_views_router, prefix="/api", tags=["saved-views"])
    app.include_router(duplicates_router, prefix="/api", tags=["duplicates"])
    app.include_router(health_score_router, prefix="/api", tags=["health-score"])
    app.include_router(google_maps_router, prefix="/api", tags=["google-maps"])

    # Serve static files (uploads)
    import os
    uploads_dir = "uploads"
    if os.path.exists(uploads_dir):
        app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

    @app.get("/")
    async def root():
        return {"message": "Lead Scraper API", "version": "0.1.0"}

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    # Add admin health route for frontend compatibility
    # Frontend expects /api/admin/health/all-workspaces
    from app.api.routes_health import get_all_workspaces_health
    from app.api.dependencies import require_super_admin
    app.add_api_route(
        "/api/admin/health/all-workspaces",
        get_all_workspaces_health,
        methods=["GET"],
        tags=["admin", "health"]
    )

    return app


app = create_app()

