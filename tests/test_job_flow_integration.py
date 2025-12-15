"""Integration tests for job -> lead -> AI insights flow."""
from __future__ import annotations

import importlib
import json
import os
import pkgutil
from typing import Generator

import pytest


@pytest.fixture
def sqlite_session(tmp_path) -> Generator:
    """Create a temporary SQLite-backed session by reloading core modules."""
    test_db = tmp_path / "job_flow.db"
    original_db_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = f"sqlite:///{test_db}"

    import app.core as core_pkg
    import app.core.config as config_mod
    import app.core.db as db_mod
    import app.core.orm as orm_mod
    import app.services.lead_repo as lead_repo_mod
    import app.services.ai_insights_service as ai_service_mod

    orm_modules = [orm_mod]
    for _, name, _ in pkgutil.iter_modules(core_pkg.__path__, core_pkg.__name__ + "."):
        if name.startswith("app.core.orm_"):
            module = importlib.import_module(name)
            orm_modules.append(module)

    modules = [config_mod, db_mod, *orm_modules, lead_repo_mod, ai_service_mod]
    for module in modules:
        importlib.reload(module)

    from app.core.db import Base, SessionLocal, engine

    Base.metadata.create_all(bind=engine)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
        if original_db_url is not None:
            os.environ["DATABASE_URL"] = original_db_url
        else:
            os.environ.pop("DATABASE_URL", None)

        for module in modules:
            importlib.reload(module)


def test_job_lead_ai_flow(sqlite_session, monkeypatch):
    """Ensure leads saved for a job can produce AI insights."""
    from app.core.models import Lead
    from app.core.orm import JobStatus, OrganizationORM, ScrapeJobORM, UserORM, UserStatus, UserRole
    from app.core.orm_workspaces import WorkspaceORM
    from app.services.lead_repo import upsert_leads
    from app.services import ai_insights_service

    # Seed org, workspace, and user
    org = OrganizationORM(name="Test Org", slug="test-org", plan_tier="pro")
    workspace = WorkspaceORM(name="Workspace", slug="workspace", organization=org)
    user = UserORM(
        email="founder@test.dev",
        password_hash="hash",
        full_name="Tester",
        status=UserStatus.active,
        is_super_admin=True,
        can_use_advanced=True,
        organization=org,
        role=UserRole.admin,
        current_workspace=workspace,
    )
    sqlite_session.add_all([org, workspace, user])
    sqlite_session.commit()

    job = ScrapeJobORM(
        organization_id=org.id,
        workspace_id=workspace.id,
        created_by_user_id=user.id,
        niche="Test niche",
        location="Remote",
        max_results=5,
        max_pages_per_site=1,
        status=JobStatus.completed,
    )
    sqlite_session.add(job)
    sqlite_session.commit()

    leads = [
        Lead(name="Alpha Co", website="https://alpha.example", emails=["hello@alpha.example"], source="test"),
        Lead(name="Beta Co", website="https://beta.example", emails=["info@beta.example"], source="test"),
    ]
    saved = upsert_leads(
        sqlite_session,
        leads,
        job_id=job.id,
        organization_id=org.id,
        workspace_id=workspace.id,
        commit=True,
    )
    assert len(saved) == 2

    # Stub LLM client
    summary_payload = {
        "summary": "These leads focus on local services.",
        "segments": [
            {
                "name": "Boutique Firms",
                "description": "Small boutique agencies serving local clients.",
                "ideal_use_case": "Great for outbound personalization.",
                "rough_percentage_of_leads": 60,
            }
        ],
    }

    class DummyLLM:
        provider = "test-llm"

        async def chat_completion(self, *args, **kwargs):
            return {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(summary_payload),
                        }
                    }
                ]
            }

    monkeypatch.setattr(ai_insights_service, "create_llm_client", lambda *args, **kwargs: DummyLLM())

    # Run AI insights
    import asyncio

    asyncio.run(ai_insights_service.generate_job_ai_insights(sqlite_session, job.id, org.id))

    refreshed_job = sqlite_session.get(ScrapeJobORM, job.id)
    assert refreshed_job.ai_status == "ready"
    assert refreshed_job.ai_summary == summary_payload["summary"]
    assert refreshed_job.ai_segments and refreshed_job.ai_segments[0]["name"] == "Boutique Firms"
