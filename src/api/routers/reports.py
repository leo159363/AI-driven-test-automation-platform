"""Test-report discovery routes."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from fastapi import APIRouter

from src.observability.dashboard.services.test_report_service import (
    discover_report_artifacts,
    get_default_junit_report_path,
    load_execution_summary,
)

router = APIRouter(prefix="/api/reports", tags=["reports"])


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


@router.get("/latest")
def get_latest_report() -> dict[str, object]:
    """Return discovered JUnit and Allure report artifacts."""
    root = _repo_root()
    artifacts = [
        {
            **asdict(artifact),
            "path": str(artifact.path),
            "relative_path": str(artifact.path.relative_to(root))
            if artifact.path.is_relative_to(root)
            else str(artifact.path),
        }
        for artifact in discover_report_artifacts(root)
    ]
    junit_path = get_default_junit_report_path(root)
    summary, warning = load_execution_summary(junit_path)

    return {
        "junit_path": junit_path,
        "summary": None if summary is None else {**asdict(summary), "source_path": str(summary.source_path)},
        "warning": warning,
        "artifacts": artifacts,
    }

