"""Automation scenario routes."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.api.services.automation_run_service import (
    list_automation_runs,
    run_automation_scenario,
)
from src.observability.dashboard.services.automation_scenario_service import (
    build_runner_command,
    list_automation_scenarios,
)

router = APIRouter(prefix="/api/automation", tags=["automation"])


class AutomationRunRequest(BaseModel):
    """Request body for running one automation scenario."""

    scenario_id: str = Field(..., min_length=1)
    timeout_seconds: int = Field(default=120, ge=10, le=600)


@router.get("/scenarios")
def get_automation_scenarios() -> dict[str, object]:
    """Return built-in pytest automation scenarios."""
    items = []
    for scenario in list_automation_scenarios():
        payload = asdict(scenario)
        payload["runner_command"] = build_runner_command(scenario.scenario_id)
        items.append(payload)

    return {
        "items": items,
        "summary": {
            "total": len(items),
            "categories": sorted({item["category"] for item in items}),
        },
    }


@router.post("/run")
def run_automation(request: AutomationRunRequest) -> dict[str, object]:
    """Run one built-in automation scenario and return report paths."""
    try:
        return run_automation_scenario(
            request.scenario_id,
            timeout_seconds=request.timeout_seconds,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/runs")
def get_automation_runs() -> dict[str, object]:
    """Return recent automation execution records."""
    runs = list_automation_runs()
    return {
        "items": runs,
        "summary": {
            "total": len(runs),
            "passed": sum(1 for run in runs if run.get("status") == "passed"),
            "failed": sum(1 for run in runs if run.get("status") == "failed"),
            "timeout": sum(1 for run in runs if run.get("status") == "timeout"),
        },
    }
