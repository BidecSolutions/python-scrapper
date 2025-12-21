"""Onboarding status API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.db import get_db
from app.api.routes_auth import get_current_user
from app.api.routes_workspaces import get_current_workspace
from app.core.orm import LeadORM, ScrapeJobORM, EmailORM, UserORM
from app.core.orm_workspaces import WorkspaceORM

router = APIRouter()


@router.get("/onboarding/status")
def get_onboarding_status(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
    workspace: WorkspaceORM = Depends(get_current_workspace),
):
    """Return onboarding step completion state."""
    org_id = current_user.organization_id
    if not org_id:
        raise HTTPException(status_code=400, detail="User is not associated with an organization.")
    workspace_id = workspace.id

    leads_query = db.query(LeadORM).filter(
        LeadORM.organization_id == org_id,
        or_(LeadORM.workspace_id == workspace_id, LeadORM.workspace_id.is_(None)),
    )
    total_leads = leads_query.count()

    verified_emails = db.query(EmailORM).filter(
        EmailORM.organization_id == org_id,
        EmailORM.verify_status.isnot(None),
    ).count()

    linkedin_leads = leads_query.filter(LeadORM.source == "linkedin_extension").count()

    jobs_count = db.query(ScrapeJobORM).filter(
        ScrapeJobORM.organization_id == org_id,
        ScrapeJobORM.workspace_id == workspace_id,
    ).count()

    steps = [
        {
            "id": "add_leads",
            "label": "Add your first leads",
            "completed": total_leads > 0,
            "action_url": "/leads",
        },
        {
            "id": "run_job",
            "label": "Run a scraping job",
            "completed": jobs_count > 0,
            "action_url": "/jobs/new",
        },
        {
            "id": "verify_email",
            "label": "Verify at least one email",
            "completed": verified_emails > 0,
            "action_url": "/verification",
        },
        {
            "id": "install_extension",
            "label": "Capture a LinkedIn lead",
            "completed": linkedin_leads > 0,
            "action_url": "/email-finder",
        },
    ]

    return {
        "total_leads": total_leads,
        "verified_emails": verified_emails,
        "linkedin_leads": linkedin_leads,
        "jobs_count": jobs_count,
        "steps": steps,
    }
