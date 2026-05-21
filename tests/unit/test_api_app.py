"""Unit tests for the QualityPilot FastAPI backend skeleton."""

from __future__ import annotations

import pytest
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


def test_assistant_templates_endpoint_returns_prompt_templates() -> None:
    response = _client().get("/api/assistant/templates")

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["total"] >= 5
    assert any(item["template_id"] == "test_case_generation" for item in payload["items"])


def test_assistant_chat_endpoint_generates_test_cases() -> None:
    response = _client().post(
        "/api/assistant/chat",
        json={
            "template_id": "test_case_generation",
            "message": "登录接口成功返回 token，错误密码返回 401",
            "module": "登录鉴权",
            "use_knowledge": True,
            "source_types": ["api_doc", "standard"],
            "top_k": 3,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["result_type"] == "test_cases"
    assert payload["contexts"]
    assert payload["result"]["test_cases"]


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
    assert {"登录鉴权", "文件上传"}.issubset(set(payload["summary"]["modules"]))
    assert {"api_login", "api_file_upload"}.issubset(set(payload["summary"]["scenarios"]))
    assert {"endpoint_id", "headers", "assertions", "pytest_target"}.issubset(
        payload["items"][0]
    )


def test_automation_scenarios_endpoint_returns_runner_command() -> None:
    response = _client().get("/api/automation/scenarios")

    assert response.status_code == 200
    payload = response.json()
    scenario_ids = {item["scenario_id"] for item in payload["items"]}
    assert {"api_login", "api_file_upload", "ui_login_smoke"}.issubset(scenario_ids)
    assert all("run_automation_suite.py" in item["runner_command"] for item in payload["items"])


def test_run_automation_endpoint_returns_execution_record(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.api.routers import automation

    def fake_run_automation_scenario(scenario_id: str, timeout_seconds: int = 120):
        assert timeout_seconds == 120
        return {
            "run_id": "api_login-demo",
            "scenario_id": scenario_id,
            "scenario_name": "API: 登录接口",
            "category": "API",
            "status": "passed",
            "return_code": 0,
            "timed_out": False,
            "started_at": "2026-05-21T00:00:00+00:00",
            "finished_at": "2026-05-21T00:00:01+00:00",
            "duration_seconds": 1.0,
            "command": ["python", "scripts/run_automation_suite.py"],
            "summary": {
                "total": 2,
                "passed": 2,
                "failed": 0,
                "errors": 0,
                "skipped": 0,
                "duration_seconds": 0.2,
            },
            "paths": {
                "run_dir": "reports/api-runs/api_login-demo",
                "junitxml": "reports/api-runs/api_login-demo/junit.xml",
                "allure_results": "reports/api-runs/api_login-demo/allure-results",
                "run_record": "reports/api-runs/api_login-demo/run.json",
            },
            "stdout": "ok",
            "stderr": "",
        }

    monkeypatch.setattr(automation, "run_automation_scenario", fake_run_automation_scenario)

    response = _client().post("/api/automation/run", json={"scenario_id": "api_login"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"] == "api_login-demo"
    assert payload["status"] == "passed"
    assert payload["summary"]["passed"] == 2


def test_automation_runs_endpoint_returns_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.api.routers import automation

    monkeypatch.setattr(
        automation,
        "list_automation_runs",
        lambda: [
            {"run_id": "a", "status": "passed"},
            {"run_id": "b", "status": "failed"},
        ],
    )

    response = _client().get("/api/automation/runs")

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"] == {"total": 2, "passed": 1, "failed": 1, "timeout": 0}


def test_latest_report_endpoint_has_report_artifacts() -> None:
    response = _client().get("/api/reports/latest")

    assert response.status_code == 200
    payload = response.json()
    assert "junit_path" in payload
    assert "artifacts" in payload
    assert any(artifact["artifact_type"] == "junit_xml" for artifact in payload["artifacts"])


def test_run_report_endpoint_returns_one_run(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.api.routers import reports

    monkeypatch.setattr(
        reports,
        "get_automation_run",
        lambda run_id, project_root: {
            "run_id": run_id,
            "scenario_id": "api_login",
            "scenario_name": "API: 登录接口",
            "status": "passed",
            "summary": {"total": 2, "passed": 2, "failed": 0, "errors": 0, "skipped": 0},
            "paths": {
                "run_dir": "reports/api-runs/api_login-demo",
                "junitxml": "reports/api-runs/api_login-demo/junit.xml",
                "allure_results": "reports/api-runs/api_login-demo/allure-results",
                "run_record": "reports/api-runs/api_login-demo/run.json",
            },
            "stdout": "ok",
            "stderr": "",
        },
    )

    response = _client().get("/api/reports/api_login-demo")

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"] == "api_login-demo"
    assert payload["summary"]["passed"] == 2
