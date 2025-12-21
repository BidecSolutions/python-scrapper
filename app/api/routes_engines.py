"""Engine status and orchestration endpoints."""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import func, case, or_

from app.core.db import get_db
from app.api.routes_auth import get_current_user
from app.api.routes_workspaces import get_current_workspace
from app.core.orm import LeadORM, UserORM
from app.core.orm_playbooks import PlaybookJobORM
from app.core.orm_templates import TemplateORM, TemplateStatus, TemplateGovernanceORM
from app.core.orm_workspaces import WorkspaceORM
from app.api.routes_lists import _automation_rules

router = APIRouter(prefix="/engines", tags=["engines"])

_list_engine_audit: List[dict] = []
_engine_audit: List[dict] = []
_engine_settings: Dict[int, dict] = {}
_engine_webhooks: Dict[int, List[dict]] = {}
_worker_queue: List[dict] = []


def _log_engine_event(message: str) -> None:
    _engine_audit.insert(0, {
        "id": f"{datetime.utcnow().timestamp()}",
        "message": message,
        "time": datetime.utcnow().isoformat(),
    })
    _engine_audit[:] = _engine_audit[:200]


@router.get("/playbooks/status")
def get_playbook_engine_status(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
) -> Dict[str, Any]:
    """Return playbook engine status for the organization."""
    org_id = current_user.organization_id
    query = db.query(PlaybookJobORM).filter(PlaybookJobORM.organization_id == org_id)
    jobs = query.order_by(PlaybookJobORM.created_at.desc()).limit(200).all()
    by_status: Dict[str, int] = {}
    last_run_at: Optional[str] = None
    for job in jobs:
        status = job.status or "unknown"
        by_status[status] = by_status.get(status, 0) + 1
    if jobs:
        last_run_at = jobs[0].created_at.isoformat() if jobs[0].created_at else None
    return {
        "total": len(jobs),
        "by_status": by_status,
        "last_run_at": last_run_at,
    }


@router.post("/lists/run")
def run_list_automation_engine(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
    workspace: WorkspaceORM = Depends(get_current_workspace),
) -> Dict[str, Any]:
    """Evaluate automation rules and return summary."""
    org_id = current_user.organization_id
    workspace_id = workspace.id
    total_rules = len(_automation_rules)
    matched_total = 0
    for rule in _automation_rules:
        min_score = rule.get("min_score") or 0
        count = (
            db.query(func.count(LeadORM.id))
            .filter(
                LeadORM.organization_id == org_id,
                or_(LeadORM.workspace_id == workspace_id, LeadORM.workspace_id.is_(None)),
                LeadORM.quality_score >= min_score,
            )
            .scalar()
        )
        matched_total += int(count or 0)
    payload = {
        "total_rules": total_rules,
        "matched_total": matched_total,
        "ran_at": datetime.utcnow().isoformat(),
    }
    _list_engine_audit.insert(0, {
        "id": f"{datetime.utcnow().timestamp()}",
        "message": f"Engine run: {total_rules} rules, {matched_total} matches",
        "time": payload["ran_at"],
    })
    _list_engine_audit[:] = _list_engine_audit[:25]
    _log_engine_event(f"List automation run ({total_rules} rules)")
    return payload


@router.get("/lists/audit")
def get_list_engine_audit() -> List[dict]:
    """Return list automation engine audit log (in-memory)."""
    return _list_engine_audit


@router.get("/audit")
def get_engine_audit() -> List[dict]:
    """Return engine audit log (in-memory)."""
    return _engine_audit


@router.get("/audit/export")
def export_engine_audit() -> Response:
    """Export engine audit log as CSV."""
    headers = ["id", "message", "time"]
    rows = [headers]
    for entry in _engine_audit:
        rows.append([entry.get("id", ""), entry.get("message", ""), entry.get("time", "")])
    csv = "\n".join([",".join([f"\"{str(cell).replace('\"', '\"\"')}\"" for cell in row]) for row in rows])
    return Response(content=csv, media_type="text/csv")


@router.get("/overview")
def get_engine_overview(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
    workspace: WorkspaceORM = Depends(get_current_workspace),
) -> Dict[str, Any]:
    """Return combined engine status summary."""
    org_id = current_user.organization_id
    workspace_id = workspace.id

    playbook_total = (
        db.query(func.count(PlaybookJobORM.id))
        .filter(PlaybookJobORM.organization_id == org_id)
        .scalar()
    )

    enrichment_counts = (
        db.query(
            func.sum(case((LeadORM.ai_status == "pending", 1), else_=0)).label("pending"),
            func.sum(case((LeadORM.ai_status == "processing", 1), else_=0)).label("processing"),
            func.sum(case((LeadORM.ai_status == "success", 1), else_=0)).label("success"),
            func.sum(case((LeadORM.ai_status == "failed", 1), else_=0)).label("failed"),
        )
        .filter(
            LeadORM.organization_id == org_id,
            or_(LeadORM.workspace_id == workspace_id, LeadORM.workspace_id.is_(None)),
        )
        .first()
    )

    template_pending = (
        db.query(func.count(TemplateORM.id))
        .filter(
            TemplateORM.workspace_id == workspace.id,
            TemplateORM.status == TemplateStatus.pending_approval,
        )
        .scalar()
    )

    return {
        "playbooks": {"total": int(playbook_total or 0)},
        "list_automation": {"rules": len(_automation_rules)},
        "templates": {"pending": int(template_pending or 0)},
        "enrichment": {
            "pending": int(enrichment_counts.pending or 0),
            "processing": int(enrichment_counts.processing or 0),
            "success": int(enrichment_counts.success or 0),
            "failed": int(enrichment_counts.failed or 0),
        },
        "workers": {"queue": len(_worker_queue)},
    }


@router.get("/templates/sla")
def get_template_sla(
    sla_hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
    workspace: WorkspaceORM = Depends(get_current_workspace),
) -> Dict[str, int]:
    """Return template approval SLA metrics."""
    pending = (
        db.query(TemplateORM)
        .filter(
            TemplateORM.workspace_id == workspace.id,
            TemplateORM.status == TemplateStatus.pending_approval,
        )
        .all()
    )
    cutoff = datetime.utcnow() - timedelta(hours=sla_hours)
    overdue = [t for t in pending if t.created_at and t.created_at < cutoff]
    return {
        "sla_hours": sla_hours,
        "pending": len(pending),
        "overdue": len(overdue),
    }


@router.get("/templates/alerts")
def get_template_alerts(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
    workspace: WorkspaceORM = Depends(get_current_workspace),
) -> Dict[str, Any]:
    """Return governance alerts for templates."""
    governance = db.query(TemplateGovernanceORM).filter(
        TemplateGovernanceORM.workspace_id == workspace.id
    ).first()
    pending = (
        db.query(func.count(TemplateORM.id))
        .filter(
            TemplateORM.workspace_id == workspace.id,
            TemplateORM.status == TemplateStatus.pending_approval,
        )
        .scalar()
    )
    return {
        "governance": {
            "require_approval_for_new_templates": bool(getattr(governance, "require_approval_for_new_templates", False)),
            "restrict_to_approved_only": bool(getattr(governance, "restrict_to_approved_only", False)),
            "allow_personal_templates": bool(getattr(governance, "allow_personal_templates", True)),
            "require_unsubscribe": bool(getattr(governance, "require_unsubscribe", False)),
        },
        "pending": int(pending or 0),
    }


@router.get("/enrichment/status")
def get_enrichment_engine_status(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
    workspace: WorkspaceORM = Depends(get_current_workspace),
) -> Dict[str, int]:
    """Return enrichment queue status counts for the workspace."""
    org_id = current_user.organization_id
    workspace_id = workspace.id
    counts = (
        db.query(
            func.sum(case((LeadORM.ai_status == "pending", 1), else_=0)).label("pending"),
            func.sum(case((LeadORM.ai_status == "processing", 1), else_=0)).label("processing"),
            func.sum(case((LeadORM.ai_status == "success", 1), else_=0)).label("success"),
            func.sum(case((LeadORM.ai_status == "failed", 1), else_=0)).label("failed"),
            func.count(LeadORM.id).label("total"),
        )
        .filter(
            LeadORM.organization_id == org_id,
            or_(LeadORM.workspace_id == workspace_id, LeadORM.workspace_id.is_(None)),
        )
        .first()
    )
    return {
        "pending": int(counts.pending or 0),
        "processing": int(counts.processing or 0),
        "success": int(counts.success or 0),
        "failed": int(counts.failed or 0),
        "total": int(counts.total or 0),
    }


@router.get("/settings")
def get_engine_settings(
    current_user: UserORM = Depends(get_current_user),
    workspace: WorkspaceORM = Depends(get_current_workspace),
) -> dict:
    """Return engine settings for workspace (in-memory)."""
    settings = _engine_settings.get(workspace.id) or {
        "playbooks_enabled": True,
        "list_automation_enabled": True,
        "templates_governance_enabled": True,
        "enrichment_enabled": True,
        "worker_concurrency": 2,
    }
    _engine_settings[workspace.id] = settings
    return settings


@router.patch("/settings")
def update_engine_settings(
    body: dict,
    current_user: UserORM = Depends(get_current_user),
    workspace: WorkspaceORM = Depends(get_current_workspace),
) -> dict:
    """Update engine settings for workspace (in-memory)."""
    settings = _engine_settings.get(workspace.id) or {}
    settings.update(body)
    _engine_settings[workspace.id] = settings
    _log_engine_event("Engine settings updated")
    return settings


@router.get("/alerts/webhooks")
def list_engine_webhooks(
    current_user: UserORM = Depends(get_current_user),
    workspace: WorkspaceORM = Depends(get_current_workspace),
) -> List[dict]:
    """List engine webhooks for workspace (in-memory)."""
    return _engine_webhooks.get(workspace.id, [])


@router.post("/alerts/webhooks")
def create_engine_webhook(
    body: dict,
    current_user: UserORM = Depends(get_current_user),
    workspace: WorkspaceORM = Depends(get_current_workspace),
) -> dict:
    """Create a webhook registration (in-memory)."""
    entry = {
        "id": f"wh_{datetime.utcnow().timestamp()}",
        "url": body.get("url"),
        "events": body.get("events", []),
        "enabled": bool(body.get("enabled", True)),
        "created_at": datetime.utcnow().isoformat(),
    }
    _engine_webhooks.setdefault(workspace.id, []).insert(0, entry)
    _log_engine_event("Webhook created")
    return entry


@router.delete("/alerts/webhooks/{webhook_id}")
def delete_engine_webhook(
    webhook_id: str,
    current_user: UserORM = Depends(get_current_user),
    workspace: WorkspaceORM = Depends(get_current_workspace),
) -> dict:
    """Delete a webhook registration (in-memory)."""
    entries = _engine_webhooks.get(workspace.id, [])
    before = len(entries)
    entries = [entry for entry in entries if entry.get("id") != webhook_id]
    _engine_webhooks[workspace.id] = entries
    if len(entries) < before:
        _log_engine_event("Webhook deleted")
    return {"message": "Webhook deleted"}


@router.get("/workers/queue")
def get_worker_queue() -> List[dict]:
    """Return simulated worker queue."""
    return _worker_queue


@router.post("/workers/queue")
def enqueue_worker_task(body: dict) -> dict:
    """Add a simulated worker task to the queue."""
    entry = {
        "id": f"task_{datetime.utcnow().timestamp()}",
        "name": body.get("name", "Background task"),
        "status": body.get("status", "queued"),
        "created_at": datetime.utcnow().isoformat(),
    }
    _worker_queue.insert(0, entry)
    _worker_queue[:] = _worker_queue[:50]
    _log_engine_event("Worker task enqueued")
    return entry
