"""Unit tests for the QualityPilot FastAPI backend skeleton."""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.main import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_health_endpoint_returns_service_metadata() -> None:
    response = _client().get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "qualitypilot-api"
    assert payload["docs"] == "/docs"


def test_test_cases_endpoint_returns_catalog_and_summary() -> None:
    response = _client().get("/api/test-cases")

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["total"] >= 6
    assert payload["summary"]["api"] >= 4
    assert payload["items"][0]["case_id"].startswith("TC-")
    assert "pytest_target" in payload["items"][0]


def test_api_endpoints_are_linked_to_test_cases() -> None:
    response = _client().get("/api/api-endpoints")

    assert response.status_code == 200
    payload = response.json()
    paths = {item["path"] for item in payload["items"]}
    assert "/api/login" in paths
    assert "/api/upload" in paths
    assert payload["summary"]["methods"]["POST"] >= 2


def test_automation_scenarios_endpoint_returns_runner_command() -> None:
    response = _client().get("/api/automation/scenarios")

    assert response.status_code == 200
    payload = response.json()
    scenario_ids = {item["scenario_id"] for item in payload["items"]}
    assert {"api_login", "api_file_upload", "ui_login_smoke"}.issubset(scenario_ids)
    assert all("run_automation_suite.py" in item["runner_command"] for item in payload["items"])


def test_latest_report_endpoint_has_report_artifacts() -> None:
    response = _client().get("/api/reports/latest")

    assert response.status_code == 200
    payload = response.json()
    assert "junit_path" in payload
    assert "artifacts" in payload
    assert any(artifact["artifact_type"] == "junit_xml" for artifact in payload["artifacts"])
