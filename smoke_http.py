"""Quick end-to-end smoke checks against a running backend.

Usage (PowerShell):
  cd python-scrapper
  $env:SMOKE_BASE_URL="http://localhost:8003"
  $env:SMOKE_EMAIL="admin@admin.com"
  $env:SMOKE_PASSWORD="Admin@123456"
  python smoke_http.py
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from typing import Any, Optional

import requests


@dataclass
class Result:
    name: str
    ok: bool
    status: Optional[int] = None
    details: str = ""


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv(override=False)
    except Exception:
        pass


def _req(
    method: str,
    url: str,
    *,
    token: Optional[str] = None,
    json_body: Any | None = None,
    params: dict[str, Any] | None = None,
    timeout: int = 30,
) -> requests.Response:
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return requests.request(
        method,
        url,
        headers=headers,
        json=json_body,
        params=params,
        timeout=timeout,
    )


def main() -> int:
    _load_dotenv()

    base_url = os.getenv("SMOKE_BASE_URL", "http://localhost:8003").rstrip("/")
    email = os.getenv("SMOKE_EMAIL")
    password = os.getenv("SMOKE_PASSWORD")

    results: list[Result] = []

    # Health
    try:
        r = _req("GET", f"{base_url}/health", timeout=10)
        results.append(Result("backend.health", r.ok, r.status_code, r.text[:200]))
    except Exception as exc:
        results.append(Result("backend.health", False, None, str(exc)))
        _print(results)
        return 1

    # OpenAPI sanity
    try:
        r = _req("GET", f"{base_url}/openapi.json", timeout=30)
        ok = r.ok and "paths" in r.json()
        results.append(Result("backend.openapi", ok, r.status_code, "ok" if ok else r.text[:200]))
    except Exception as exc:
        results.append(Result("backend.openapi", False, None, str(exc)))

    token: Optional[str] = None

    # Login + /me (required for jobs/leads exports)
    if email and password:
        try:
            r = _req(
                "POST",
                f"{base_url}/api/auth/login",
                json_body={"email": email, "password": password},
                timeout=20,
            )
            if r.ok:
                token = r.json().get("access_token")
            results.append(Result("auth.login", bool(token), r.status_code, r.text[:200]))
        except Exception as exc:
            results.append(Result("auth.login", False, None, str(exc)))

        if token:
            try:
                r = _req("GET", f"{base_url}/api/me", token=token, timeout=20)
                results.append(Result("auth.me", r.ok, r.status_code, r.text[:200]))
            except Exception as exc:
                results.append(Result("auth.me", False, None, str(exc)))
    else:
        results.append(Result("auth.login", False, None, "Set SMOKE_EMAIL and SMOKE_PASSWORD to test auth-required APIs"))

    # Jobs (auth + workspace membership required)
    if token:
        try:
            r = _req("GET", f"{base_url}/api/jobs", token=token, timeout=30)
            ok = r.ok and isinstance(r.json(), list)
            results.append(Result("jobs.list", ok, r.status_code, "count=" + str(len(r.json())) if ok else r.text[:200]))
        except Exception as exc:
            results.append(Result("jobs.list", False, None, str(exc)))

    # Leads list + exports (auth required)
    if token:
        try:
            r = _req("GET", f"{base_url}/api/leads", token=token, params={"limit": 1, "offset": 0}, timeout=60)
            ok = r.ok and isinstance(r.json(), list)
            results.append(Result("leads.list", ok, r.status_code, "count>=" + str(len(r.json())) if ok else r.text[:200]))
        except Exception as exc:
            results.append(Result("leads.list", False, None, str(exc)))

        try:
            r = _req("GET", f"{base_url}/api/leads/export/csv", token=token, timeout=60)
            ok = r.ok and ("text/csv" in (r.headers.get("content-type", "").lower()))
            results.append(Result("leads.export_csv", ok, r.status_code, r.headers.get("content-type", "")))
        except Exception as exc:
            results.append(Result("leads.export_csv", False, None, str(exc)))

    # Email verification (no auth required)
    try:
        r = _req(
            "POST",
            f"{base_url}/api/email-verifier",
            json_body={"email": "test@example.com", "skip_smtp": True},
            timeout=30,
        )
        ok = r.ok and "status" in r.json()
        results.append(Result("email.verify_single", ok, r.status_code, r.text[:200]))
    except Exception as exc:
        results.append(Result("email.verify_single", False, None, str(exc)))

    # Email verification jobs list (may be empty)
    try:
        r = _req("GET", f"{base_url}/api/verification/jobs", timeout=30)
        ok = r.ok
        results.append(Result("email.verification_jobs_list", ok, r.status_code, r.text[:200]))
    except Exception as exc:
        results.append(Result("email.verification_jobs_list", False, None, str(exc)))

    # Google Maps scraper health (often fails locally without Chrome/WebDriver)
    try:
        r = _req("GET", f"{base_url}/api/google-maps/health", timeout=60)
        ok = r.ok and isinstance(r.json(), dict) and "status" in r.json()
        results.append(Result("google_maps.health", ok, r.status_code, r.text[:200]))
    except Exception as exc:
        results.append(Result("google_maps.health", False, None, str(exc)))

    # Robots (no auth required)
    try:
        r = _req("GET", f"{base_url}/api/robots", timeout=30)
        ok = r.ok
        results.append(Result("robots.list", ok, r.status_code, r.text[:200]))
    except Exception as exc:
        results.append(Result("robots.list", False, None, str(exc)))

    # Lookalike jobs list (auth required)
    try:
        r = _req("GET", f"{base_url}/api/lookalike/jobs", token=token, timeout=30)
        ok = r.ok
        results.append(Result("lookalike.jobs_list", ok, r.status_code, r.text[:200]))
    except Exception as exc:
        results.append(Result("lookalike.jobs_list", False, None, str(exc)))

    _print(results)
    return 0 if all(r.ok for r in results if not r.name.startswith("auth.")) else 2


def _print(results: list[Result]) -> None:
    print("\nSMOKE RESULTS")
    print("=" * 60)
    for r in results:
        status = f"{r.status}" if r.status is not None else "-"
        marker = "PASS" if r.ok else "FAIL"
        details = (r.details or "").replace("\n", " ")[:160]
        print(f"{marker:4}  {r.name:28}  status={status:>3}  {details}")
    print("=" * 60)


if __name__ == "__main__":
    raise SystemExit(main())
