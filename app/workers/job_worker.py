"""Simple process-based job runner for scraping tasks."""
from __future__ import annotations

import logging
import multiprocessing
from typing import Any, Dict

logger = logging.getLogger(__name__)


def _worker_entry(job_id: int, org_id: int, payload: Dict[str, Any]) -> None:
    """Process entry point that executes the scraping coroutine."""
    try:
        from app.api.background_job_executor import run_job_in_background

        run_job_in_background(job_id, org_id, payload)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error(
            "Worker process for job %s failed: %s",
            job_id,
            exc,
            exc_info=True,
        )
        raise


def spawn_job_worker(job_id: int, org_id: int, payload: Dict[str, Any]) -> int:
    """
    Spawn a detached process to execute a job.

    Returns the child PID so callers can log/trace if needed.
    """
    process = multiprocessing.Process(
        target=_worker_entry,
        args=(job_id, org_id, payload),
        name=f"scrape-job-{job_id}",
        daemon=True,
    )
    process.start()
    logger.info("Spawned job worker for job %s (pid=%s)", job_id, process.pid)
    return process.pid or -1
