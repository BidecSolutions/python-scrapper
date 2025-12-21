"""Seed demo data for a predictable "world class" walkthrough.

This script is:
- Idempotent: re-running replaces only demo-tagged data
- Safe: does not touch non-demo data
- Compatible: works with Postgres (Supabase) and local SQLite

PowerShell:
  cd python-scrapper
  python seed_demo_data.py

Optional env overrides:
  DEMO_ADMIN_EMAIL=admin@admin.com
  DEMO_ADMIN_PASSWORD=Admin@123456
  DEMO_WORKSPACE_SLUG=default
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Optional


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv(override=False)
    except Exception:
        pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _import_all_orm_models() -> None:
    """
    Ensure SQLAlchemy can resolve string-based relationships.

    The backend registers many models across `app.core.orm_*` modules. If those
    modules aren't imported, SQLAlchemy mapper configuration can fail when
    relationships reference classes by string.
    """
    import importlib
    import pkgutil

    import app.core as core_pkg

    # Import the primary ORM module first.
    importlib.import_module("app.core.orm")

    for _, name, _ in pkgutil.iter_modules(core_pkg.__path__, core_pkg.__name__ + "."):
        if name.startswith("app.core.orm_"):
            importlib.import_module(name)


@dataclass
class SeedConfig:
    admin_email: str
    admin_password: str
    workspace_slug: str

    demo_source: str = "demo_seed"
    demo_prefix: str = "Demo:"


def _get_config() -> SeedConfig:
    return SeedConfig(
        admin_email=os.getenv("DEMO_ADMIN_EMAIL", "admin@admin.com").strip(),
        admin_password=os.getenv("DEMO_ADMIN_PASSWORD", "Admin@123456"),
        workspace_slug=os.getenv("DEMO_WORKSPACE_SLUG", "default").strip(),
    )


def _print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def seed_demo(db, cfg: SeedConfig) -> dict[str, Any]:
    """Seed demo data and return a summary."""
    from app.core.orm import (
        EmailORM,
        EmailVerificationItemORM,
        EmailVerificationJobORM,
        EmailVerificationJobStatus,
        JobStatus,
        LeadORM,
        OrganizationORM,
        PlanTier,
        ScrapeJobORM,
        UserORM,
        UserRole,
        UserStatus,
    )
    from app.core.orm_lists import LeadListLeadORM, LeadListORM
    from app.core.orm_segments import SegmentORM
    from app.core.orm_workspaces import WorkspaceMemberORM, WorkspaceORM, WorkspaceRole
    from app.core.orm_robots import (
        RobotMode,
        RobotORM,
        RobotRunORM,
        RobotRunRowORM,
        RobotRunUrlORM,
        RobotRunStatus,
        URLStatus,
    )
    from app.core.orm_lookalike import LookalikeJobORM, LookalikeJobStatus
    from app.services.auth_service import AuthService
    from app.services.lookalike_service import build_lookalike_profile, find_lookalikes

    org = _ensure_org(db, PlanTier=PlanTier, OrganizationORM=OrganizationORM)
    ws = _ensure_workspace(db, org=org, WorkspaceORM=WorkspaceORM, workspace_slug=cfg.workspace_slug)
    admin = _ensure_admin_user(
        db,
        org=org,
        ws=ws,
        email=cfg.admin_email,
        password=cfg.admin_password,
        AuthService=AuthService,
        UserORM=UserORM,
        UserRole=UserRole,
        UserStatus=UserStatus,
    )
    _ensure_workspace_membership(
        db, user=admin, ws=ws, WorkspaceMemberORM=WorkspaceMemberORM, WorkspaceRole=WorkspaceRole
    )

    _cleanup_demo_data(
        db,
        cfg=cfg,
        org_id=org.id,
        ws_id=ws.id,
        LeadORM=LeadORM,
        ScrapeJobORM=ScrapeJobORM,
        SegmentORM=SegmentORM,
        LeadListORM=LeadListORM,
        EmailVerificationJobORM=EmailVerificationJobORM,
        RobotORM=RobotORM,
        LookalikeJobORM=LookalikeJobORM,
    )

    completed_job, running_job = _seed_jobs_and_leads(
        db,
        cfg=cfg,
        org_id=org.id,
        ws_id=ws.id,
        admin_user_id=admin.id,
        ScrapeJobORM=ScrapeJobORM,
        JobStatus=JobStatus,
        LeadORM=LeadORM,
    )

    segment, lead_list = _seed_segment_and_list(
        db,
        cfg=cfg,
        org_id=org.id,
        ws_id=ws.id,
        admin_user_id=admin.id,
        SegmentORM=SegmentORM,
        LeadListORM=LeadListORM,
        LeadListLeadORM=LeadListLeadORM,
        LeadORM=LeadORM,
    )

    ver_job = _seed_email_verification_demo(
        db,
        cfg=cfg,
        org_id=org.id,
        admin_user_id=admin.id,
        EmailORM=EmailORM,
        EmailVerificationJobORM=EmailVerificationJobORM,
        EmailVerificationItemORM=EmailVerificationItemORM,
        EmailVerificationJobStatus=EmailVerificationJobStatus,
    )

    robot, run = _seed_robot_demo(
        db,
        cfg=cfg,
        org_id=org.id,
        RobotORM=RobotORM,
        RobotMode=RobotMode,
        RobotRunORM=RobotRunORM,
        RobotRunStatus=RobotRunStatus,
        RobotRunUrlORM=RobotRunUrlORM,
        RobotRunRowORM=RobotRunRowORM,
        URLStatus=URLStatus,
    )

    lookalike_job = _seed_lookalike_demo(
        db,
        cfg=cfg,
        org_id=org.id,
        ws_id=ws.id,
        admin_user_id=admin.id,
        lead_list_id=lead_list.id,
        LookalikeJobORM=LookalikeJobORM,
        LookalikeJobStatus=LookalikeJobStatus,
        build_lookalike_profile=build_lookalike_profile,
        find_lookalikes=find_lookalikes,
    )

    return {
        "organization_id": org.id,
        "workspace_id": ws.id,
        "admin_user_id": admin.id,
        "completed_job_id": completed_job.id,
        "running_job_id": running_job.id,
        "segment_id": segment.id,
        "list_id": lead_list.id,
        "verification_job_id": ver_job.id,
        "robot_id": robot.id,
        "robot_run_id": run.id,
        "lookalike_job_id": lookalike_job.id,
        "lookalike_status": lookalike_job.status.value if hasattr(lookalike_job.status, "value") else str(lookalike_job.status),
    }


def _ensure_org(db, *, PlanTier, OrganizationORM):
    org = db.query(OrganizationORM).filter(OrganizationORM.slug == "default").first()
    if org:
        return org
    org = OrganizationORM(name="Acme Growth Agency", slug="default", plan_tier=PlanTier.pro)
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def _ensure_workspace(db, *, org, WorkspaceORM, workspace_slug: str):
    ws = db.query(WorkspaceORM).filter(WorkspaceORM.slug == workspace_slug).first()
    if ws:
        if ws.organization_id != org.id:
            ws.organization_id = org.id
            db.add(ws)
            db.commit()
            db.refresh(ws)
        return ws

    ws = WorkspaceORM(
        name="Default Workspace",
        slug=workspace_slug,
        description="Seeded workspace for local demos",
        organization_id=org.id,
    )
    db.add(ws)
    db.commit()
    db.refresh(ws)
    return ws


def _ensure_admin_user(
    db,
    *,
    org,
    ws,
    email: str,
    password: str,
    AuthService,
    UserORM,
    UserRole,
    UserStatus,
):
    user = db.query(UserORM).filter(UserORM.email == email).first()
    password_hash = AuthService.hash_password(password)

    if not user:
        user = UserORM(
            email=email,
            password_hash=password_hash,
            full_name="Admin User",
            status=UserStatus.active,
            is_super_admin=True,
            can_use_advanced=True,
            organization_id=org.id,
            current_workspace_id=ws.id,
            role=UserRole.admin,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    user.password_hash = password_hash
    user.status = UserStatus.active
    user.is_super_admin = True
    user.can_use_advanced = True
    user.organization_id = org.id
    user.current_workspace_id = ws.id
    user.role = UserRole.admin
    user.is_active = True
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _ensure_workspace_membership(db, *, user, ws, WorkspaceMemberORM, WorkspaceRole):
    membership = (
        db.query(WorkspaceMemberORM)
        .filter(WorkspaceMemberORM.workspace_id == ws.id, WorkspaceMemberORM.user_id == user.id)
        .first()
    )
    if membership:
        if membership.accepted_at is None:
            membership.accepted_at = _utcnow()
            db.add(membership)
            db.commit()
        return membership

    membership = WorkspaceMemberORM(
        workspace_id=ws.id,
        user_id=user.id,
        role=WorkspaceRole.owner,
        accepted_at=_utcnow(),
    )
    db.add(membership)
    db.commit()
    return membership


def _delete_where(items: Iterable[Any], db) -> int:
    count = 0
    for item in items:
        db.delete(item)
        count += 1
    if count:
        db.commit()
    return count


def _cleanup_demo_data(
    db,
    *,
    cfg: SeedConfig,
    org_id: int,
    ws_id: int,
    LeadORM,
    ScrapeJobORM,
    SegmentORM,
    LeadListORM,
    EmailVerificationJobORM,
    RobotORM,
    LookalikeJobORM,
):
    # Lookalike jobs tied to the demo list (delete before list)
    demo_list = db.query(LeadListORM).filter(LeadListORM.organization_id == org_id, LeadListORM.name == f"{cfg.demo_prefix} Best Leads").first()
    if demo_list:
        jobs = db.query(LookalikeJobORM).filter(LookalikeJobORM.source_list_id == demo_list.id).all()
        _delete_where(jobs, db)

    robots = db.query(RobotORM).filter(RobotORM.organization_id == org_id, RobotORM.name.like(f"{cfg.demo_prefix}%")).all()
    _delete_where(robots, db)

    ver_jobs = db.query(EmailVerificationJobORM).filter(
        EmailVerificationJobORM.organization_id == org_id,
        (EmailVerificationJobORM.source_description.isnot(None)),
        EmailVerificationJobORM.source_description.like(f"{cfg.demo_prefix}%"),
    ).all()
    _delete_where(ver_jobs, db)

    lists = db.query(LeadListORM).filter(LeadListORM.organization_id == org_id, LeadListORM.name.like(f"{cfg.demo_prefix}%")).all()
    _delete_where(lists, db)

    segments = db.query(SegmentORM).filter(SegmentORM.organization_id == org_id, SegmentORM.name.like(f"{cfg.demo_prefix}%")).all()
    _delete_where(segments, db)

    jobs = db.query(ScrapeJobORM).filter(ScrapeJobORM.organization_id == org_id, ScrapeJobORM.niche.like(f"{cfg.demo_prefix}%")).all()
    _delete_where(jobs, db)

    leads = db.query(LeadORM).filter(
        LeadORM.organization_id == org_id,
        LeadORM.workspace_id == ws_id,
        LeadORM.source == cfg.demo_source,
    ).all()
    _delete_where(leads, db)


def _seed_jobs_and_leads(
    db,
    *,
    cfg: SeedConfig,
    org_id: int,
    ws_id: int,
    admin_user_id: int,
    ScrapeJobORM,
    JobStatus,
    LeadORM,
):
    now = _utcnow()

    completed_job = ScrapeJobORM(
        organization_id=org_id,
        workspace_id=ws_id,
        created_by_user_id=admin_user_id,
        niche=f"{cfg.demo_prefix} Local Service Businesses (Completed)",
        location="New York, NY",
        max_results=25,
        max_pages_per_site=1,
        status=JobStatus.completed,
        started_at=now,
        completed_at=now,
        duration_seconds=42,
        sites_crawled=12,
        sites_failed=1,
        total_pages_crawled=28,
        sources_used=["demo_seed"],
        extract_config={"emails": True, "phones": True, "tech_stack": True},
        ai_status="ready",
        ai_summary="Demo insights: strong cluster of local service providers with modern websites and responsive contact forms.",
        ai_segments=[
            {
                "name": "Modern Websites",
                "description": "Businesses with updated tech stacks and clear CTAs.",
                "ideal_use_case": "Outbound personalization and quick-win campaigns.",
                "rough_percentage_of_leads": 55,
            },
            {
                "name": "Legacy Stack",
                "description": "Older CMS / outdated UX; good upsell potential.",
                "ideal_use_case": "Website redesign + SEO outreach.",
                "rough_percentage_of_leads": 45,
            },
        ],
        meta={"seed": True},
        total_targets=12,
        processed_targets=12,
        result_count=0,
    )

    running_job = ScrapeJobORM(
        organization_id=org_id,
        workspace_id=ws_id,
        created_by_user_id=admin_user_id,
        niche=f"{cfg.demo_prefix} B2B SaaS (Running)",
        location="Remote",
        max_results=15,
        max_pages_per_site=1,
        status=JobStatus.running,
        started_at=now,
        total_targets=10,
        processed_targets=4,
        sites_crawled=4,
        sites_failed=0,
        total_pages_crawled=9,
        sources_used=["demo_seed"],
        extract_config={"emails": True, "phones": False, "tech_stack": True},
        ai_status="idle",
        meta={"seed": True},
        result_count=0,
    )

    db.add_all([completed_job, running_job])
    db.commit()
    db.refresh(completed_job)
    db.refresh(running_job)

    # Leads: include a few "good"/"won" for lookalike profile and lots of candidates.
    demo_leads: list[Any] = []
    for idx in range(1, 26):
        is_best = idx <= 6
        demo_leads.append(
            LeadORM(
                organization_id=org_id,
                workspace_id=ws_id,
                job_id=completed_job.id if idx <= 18 else None,
                name=f"Demo Lead {idx}: {['Alpha','Beta','Gamma','Delta','Epsilon','Zeta'][idx-1] if idx<=6 else 'Company'}",
                niche="local_services" if idx <= 18 else "b2b_saas",
                website=f"https://demo-{idx}.example.com",
                emails=[f"hello{idx}@demo-{idx}.example.com"] if idx % 3 != 0 else [],
                phones=[f"+1-555-010{idx:02d}"] if idx % 4 != 0 else [],
                address=f"{100+idx} Demo Street",
                city="New York",
                country="United States",
                source=cfg.demo_source,
                has_email=(idx % 3 != 0),
                has_phone=(idx % 4 != 0),
                quality_score=92 if is_best else (70 + (idx % 20)),
                quality_label="high" if is_best else ("medium" if idx % 2 == 0 else "low"),
                fit_label=("won" if idx <= 2 else ("good" if idx <= 6 else None)),
                health_score=95 if idx <= 2 else (88 if idx <= 6 else (60 + (idx % 35))),
                tags=["demo", "seed", "priority"] if is_best else ["demo", "seed"],
                cms=("wordpress" if idx % 2 == 0 else "shopify"),
                # Intentionally store tech stack as dict to exercise normalization in APIs.
                tech_stack={
                    "cms": "WordPress" if idx % 2 == 0 else "Shopify",
                    "tools": ["GA4", "Stripe"] if idx % 2 == 0 else ["GA4"],
                    "maturity_score": float(65 + (idx % 25)),
                },
                social_links={"linkedin": f"https://linkedin.com/company/demo-{idx}"},
                meta={"seed": True, "seed_tag": "demo_seed_v1"},
            )
        )

    # A couple leads tied to the running job (so Jobs -> Leads shows both states)
    for idx in range(26, 31):
        demo_leads.append(
            LeadORM(
                organization_id=org_id,
                workspace_id=ws_id,
                job_id=running_job.id,
                name=f"Demo SaaS Lead {idx}",
                niche="b2b_saas",
                website=f"https://saas-demo-{idx}.example.com",
                emails=[f"team@saas-demo-{idx}.example.com"],
                phones=[],
                address=None,
                city="Remote",
                country="United States",
                source=cfg.demo_source,
                has_email=True,
                has_phone=False,
                quality_score=78,
                quality_label="medium",
                health_score=72,
                tags=["demo", "seed"],
                cms="nextjs",
                tech_stack={"framework": "Next.js", "tools": ["PostHog"], "maturity_score": 82.0},
                meta={"seed": True, "seed_tag": "demo_seed_v1"},
            )
        )

    db.add_all(demo_leads)
    db.commit()

    # Update job result counts
    completed_job.result_count = db.query(LeadORM).filter(LeadORM.job_id == completed_job.id).count()
    running_job.result_count = db.query(LeadORM).filter(LeadORM.job_id == running_job.id).count()
    db.add_all([completed_job, running_job])
    db.commit()

    return completed_job, running_job


def _seed_segment_and_list(
    db,
    *,
    cfg: SeedConfig,
    org_id: int,
    ws_id: int,
    admin_user_id: int,
    SegmentORM,
    LeadListORM,
    LeadListLeadORM,
    LeadORM,
):
    segment = SegmentORM(
        organization_id=org_id,
        workspace_id=ws_id,
        created_by_user_id=admin_user_id,
        name=f"{cfg.demo_prefix} High-Health Leads",
        description="Demo segment: leads with health_score >= 80.",
        filter_json={"min_health_score": 80, "source": cfg.demo_source},
    )
    db.add(segment)
    db.commit()
    db.refresh(segment)

    lead_list = LeadListORM(
        organization_id=org_id,
        workspace_id=ws_id,
        name=f"{cfg.demo_prefix} Best Leads",
        description="Demo list: best leads used as positive examples for Lookalike.",
        is_campaign_ready=True,
        tags="demo,seed",
    )
    db.add(lead_list)
    db.commit()
    db.refresh(lead_list)

    best_leads = (
        db.query(LeadORM)
        .filter(LeadORM.organization_id == org_id, LeadORM.workspace_id == ws_id, LeadORM.source == cfg.demo_source)
        .order_by(LeadORM.health_score.desc().nulls_last())
        .limit(6)
        .all()
    )
    memberships = [
        LeadListLeadORM(list_id=lead_list.id, lead_id=lead.id, added_by_user_id=admin_user_id, notes="Seeded best lead")
        for lead in best_leads
    ]
    db.add_all(memberships)
    db.commit()

    return segment, lead_list


def _seed_email_verification_demo(
    db,
    *,
    cfg: SeedConfig,
    org_id: int,
    admin_user_id: int,
    EmailORM,
    EmailVerificationJobORM,
    EmailVerificationItemORM,
    EmailVerificationJobStatus,
):
    now = _utcnow()
    emails = [
        ("ceo@demo-1.example.com", "valid", "mx_found", 0.95),
        ("info@demo-2.example.com", "risky", "catch_all", 0.7),
        ("sales@demo-3.example.com", "unknown", "smtp_skipped", 0.4),
        ("bad@@demo-4.example.com", "syntax_error", "invalid_syntax", 0.0),
        ("temp@demo-5.example.com", "disposable", "disposable_domain", 0.1),
        ("nobody@demo-6.example.com", "invalid", "mailbox_not_found", 0.0),
    ]

    job = EmailVerificationJobORM(
        organization_id=org_id,
        created_by_user_id=admin_user_id,
        source_type="csv",
        source_description=f"{cfg.demo_prefix} Email Verification Demo",
        status=EmailVerificationJobStatus.completed,
        skip_smtp=True,
        total_emails=len(emails),
        processed_count=len(emails),
        valid_count=1,
        risky_count=1,
        unknown_count=1,
        syntax_error_count=1,
        disposable_count=1,
        invalid_count=1,
        started_at=now,
        completed_at=now,
        credits_used=len(emails),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    for raw_email, status, reason, conf in emails:
        email_record = EmailORM(
            organization_id=org_id,
            lead_id=None,
            email=raw_email.lower(),
            label="demo",
            verify_status=status,
            verify_reason=reason,
            verify_confidence=conf,
            verified_at=now,
            found_via="import",
        )
        db.add(email_record)
        db.commit()
        db.refresh(email_record)

        item = EmailVerificationItemORM(
            organization_id=org_id,
            job_id=job.id,
            email_id=email_record.id,
            raw_email=raw_email,
            status="done",
            verify_status=status,
            verify_reason=reason,
            verify_confidence=conf,
            error=None,
        )
        db.add(item)

    db.commit()
    return job


def _seed_robot_demo(
    db,
    *,
    cfg: SeedConfig,
    org_id: int,
    RobotORM,
    RobotMode,
    RobotRunORM,
    RobotRunStatus,
    RobotRunUrlORM,
    RobotRunRowORM,
    URLStatus,
):
    robot = RobotORM(
        organization_id=org_id,
        name=f"{cfg.demo_prefix} Pricing Page Extractor",
        description="Demo robot that extracts pricing plan names and starting prices.",
        mode=RobotMode.manual,
        prompt=None,
        sample_url="https://example.com/pricing",
        schema=[
            {"name": "plan_name", "type": "string", "required": True},
            {"name": "starting_price", "type": "string", "required": False},
            {"name": "billing_period", "type": "string", "required": False},
        ],
        workflow_spec={
            "version": 1,
            "steps": [{"type": "fetch_html"}, {"type": "extract", "fields": ["plan_name", "starting_price", "billing_period"]}],
        },
    )
    db.add(robot)
    db.commit()
    db.refresh(robot)

    run = RobotRunORM(
        organization_id=org_id,
        robot_id=robot.id,
        status=RobotRunStatus.completed,
        total_urls=1,
        processed_urls=1,
        total_rows=2,
        started_at=_utcnow(),
        finished_at=_utcnow(),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    url = RobotRunUrlORM(run_id=run.id, url="https://example.com/pricing", status=URLStatus.done, error=None)
    row1 = RobotRunRowORM(run_id=run.id, source_url=url.url, data={"plan_name": "Starter", "starting_price": "$29", "billing_period": "month"})
    row2 = RobotRunRowORM(run_id=run.id, source_url=url.url, data={"plan_name": "Pro", "starting_price": "$99", "billing_period": "month"})
    db.add_all([url, row1, row2])
    db.commit()
    return robot, run


def _seed_lookalike_demo(
    db,
    *,
    cfg: SeedConfig,
    org_id: int,
    ws_id: int,
    admin_user_id: int,
    lead_list_id: int,
    LookalikeJobORM,
    LookalikeJobStatus,
    build_lookalike_profile,
    find_lookalikes,
):
    job = LookalikeJobORM(
        workspace_id=ws_id,
        organization_id=org_id,
        started_by_user_id=admin_user_id,
        source_list_id=lead_list_id,
        status=LookalikeJobStatus.running,
        meta={"seed": True, "min_score": 0.65, "max_results": 50, "filters": {}},
        started_at=_utcnow(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    profile = build_lookalike_profile(db, job)
    if profile is None:
        job.status = LookalikeJobStatus.failed
        job.meta = {**(job.meta or {}), "error": "No positive examples available"}
        job.completed_at = _utcnow()
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    candidates = find_lookalikes(db, job, min_score=0.65, max_results=50, filters={})
    for c in candidates:
        db.add(c)

    job.candidates_found = len(candidates)
    job.status = LookalikeJobStatus.completed
    job.completed_at = _utcnow()
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def main() -> int:
    _load_dotenv()
    cfg = _get_config()

    if not cfg.admin_email or not cfg.admin_password:
        print("ERROR: Missing DEMO_ADMIN_EMAIL or DEMO_ADMIN_PASSWORD.")
        return 1

    try:
        _import_all_orm_models()

        from app.core.db import SessionLocal
        from app.core.orm import (
            EmailORM,
            EmailVerificationItemORM,
            EmailVerificationJobORM,
            EmailVerificationJobStatus,
            JobStatus,
            LeadORM,
            OrganizationORM,
            PlanTier,
            ScrapeJobORM,
            UserORM,
            UserRole,
            UserStatus,
        )
        from app.core.orm_lists import LeadListLeadORM, LeadListORM
        from app.core.orm_segments import SegmentORM
        from app.core.orm_workspaces import WorkspaceMemberORM, WorkspaceORM, WorkspaceRole
        from app.core.orm_robots import (
            RobotMode,
            RobotORM,
            RobotRunORM,
            RobotRunRowORM,
            RobotRunUrlORM,
            RobotRunStatus,
            URLStatus,
        )
        from app.core.orm_lookalike import LookalikeJobORM, LookalikeJobStatus
        from app.services.auth_service import AuthService
        from app.services.lookalike_service import build_lookalike_profile, find_lookalikes
    except Exception as exc:
        print(f"ERROR: Failed to import backend modules: {exc}")
        return 1

    db = SessionLocal()
    try:
        _print_header("Seeding demo data")
        summary = seed_demo(db, cfg)
        print("OK: Demo seed complete")

        _print_header("Demo credentials / next steps")
        print(f"Backend base URL:  http://localhost:8003")
        print(f"Frontend base URL: http://localhost:3000")
        print("")
        print("Login:")
        print(f"  Email:    {cfg.admin_email}")
        print(f"  Password: {cfg.admin_password}")
        print("")
        print("Useful:")
        print(f"  Jobs page:        /jobs (completed job id: {summary['completed_job_id']})")
        print(f"  Leads page:       /leads")
        print(f"  Verification:     /verification (job id: {summary['verification_job_id']})")
        print(f"  Robots:           /robots (robot id: {summary['robot_id']})")
        print(f"  Lookalike jobs:   /lookalike/jobs (job id: {summary['lookalike_job_id']})")
        return 0

    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
