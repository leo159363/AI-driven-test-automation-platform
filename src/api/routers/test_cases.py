"""Test-case and API endpoint catalog routes."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict

from fastapi import APIRouter

from src.observability.dashboard.services.test_case_library_service import (
    list_api_request_examples,
    list_test_cases,
    summarize_test_cases,
)

router = APIRouter(prefix="/api", tags=["test-cases"])


@router.get("/test-cases")
def get_test_cases() -> dict[str, object]:
    """Return the current test-case catalog for platform pages."""
    cases = [asdict(case) for case in list_test_cases()]
    return {
        "items": cases,
        "summary": summarize_test_cases(),
    }


@router.get("/api-endpoints")
def get_api_endpoints() -> dict[str, object]:
    """Return API request examples linked to automated test cases."""
    endpoints = [asdict(endpoint) for endpoint in list_api_request_examples()]
    methods = Counter(endpoint["method"] for endpoint in endpoints)
    modules = sorted({endpoint["module"] for endpoint in endpoints})
    scenarios = sorted({endpoint["scenario_id"] for endpoint in endpoints})
    return {
        "items": endpoints,
        "summary": {
            "total": len(endpoints),
            "methods": dict(sorted(methods.items())),
            "modules": modules,
            "scenarios": scenarios,
        },
    }
