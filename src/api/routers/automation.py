"""Automation scenario routes."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter

from src.observability.dashboard.services.automation_scenario_service import (
    build_runner_command,
    list_automation_scenarios,
)

router = APIRouter(prefix="/api/automation", tags=["automation"])


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

