"""Test-report discovery routes."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from fastapi import APIRouter, HTTPException

from src.api.services.automation_run_service import get_automation_run
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


@router.get("/{run_id}")
def get_report_by_run_id(run_id: str) -> dict[str, object]:
    """Return report metadata for one automation run."""
    try:
        run = get_automation_run(run_id, _repo_root())
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "run_id": run["run_id"],
        "scenario_id": run["scenario_id"],
        "scenario_name": run["scenario_name"],
        "status": run["status"],
        "summary": run.get("summary"),
        "paths": run["paths"],
        "stdout": run.get("stdout", ""),
        "stderr": run.get("stderr", ""),
    }
