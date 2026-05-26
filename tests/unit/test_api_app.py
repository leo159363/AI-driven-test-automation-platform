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


def test_frontend_route_redirects_to_vue_dev_server() -> None:
    response = _client().get("/api-testing", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "http://127.0.0.1:5173/api-testing"


def test_platform_workspace_endpoint_returns_fullscope_modules() -> None:
    response = _client().get("/api/platform/workspace")

    assert response.status_code == 200
    payload = response.json()
    assert payload["project"]["name"] == "QualityPilot Demo"
    assert payload["web_tests"]
    assert payload["performance"]
    assert payload["cicd"]
    assert any("MCP tools" in item for item in payload["differentiation"])


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


def test_knowledge_source_types_endpoint_returns_taxonomy() -> None:
    response = _client().get("/api/knowledge/source-types")

    assert response.status_code == 200
    payload = response.json()
    assert {"requirement", "api_doc", "bug", "standard"}.issubset(set(payload["items"]))


def test_knowledge_search_endpoint_returns_contexts() -> None:
    response = _client().post(
        "/api/knowledge/search",
        json={
            "query": "login token 401",
            "project": "QualityPilot",
            "version": "demo",
            "source_types": ["api_doc", "standard"],
            "top_k": 3,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["retrieval_mode"] == "keyword_overlap_demo"
    assert payload["contexts"]
    assert {"source_id", "source_type", "content", "metadata"}.issubset(payload["contexts"][0])


def test_knowledge_upload_endpoint_returns_source(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.api.routers import knowledge

    monkeypatch.setattr(
        knowledge,
        "upload_knowledge_document",
        lambda **kwargs: {
            "source_id": "upload-demo.md",
            "title": kwargs["title"],
            "source_type": kwargs["source_type"],
            "project": kwargs["project"],
            "module": kwargs["module"],
            "version": kwargs["version"],
            "chunk_count": 1,
            "created_at": "2026-05-21T00:00:00+00:00",
        },
    )

    response = _client().post(
        "/api/knowledge/upload",
        data={
            "project": "QualityPilot",
            "module": "demo",
            "version": "v1",
            "source_type": "requirement",
            "title": "Demo Requirement",
        },
        files={"file": ("demo.md", b"# Demo\ncontent", "text/markdown")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"]["title"] == "Demo Requirement"
    assert payload["source"]["chunk_count"] == 1


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


def test_api_testing_debug_endpoint_runs_mock_request() -> None:
    response = _client().post(
        "/api/api-testing/debug",
        json={
            "method": "POST",
            "path": "/api/login",
            "headers": {"Content-Type": "application/json"},
            "body": '{"username": "tester", "password": "Passw0rd!"}',
            "expected_status": 200,
            "json_assertions": [
                {"path": "token", "operator": "exists"},
                {"path": "user.username", "operator": "equals", "expected": "tester"},
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["request"]["target_mode"] == "mock"
    assert payload["response"]["status_code"] == 200
    assert payload["passed"] is True


def test_api_testing_debug_endpoint_rejects_remote_target() -> None:
    response = _client().post(
        "/api/api-testing/debug",
        json={
            "method": "GET",
            "path": "/",
            "base_url": "https://example.com",
        },
    )

    assert response.status_code == 400
    assert "localhost" in response.json()["detail"]


def test_api_testing_environments_endpoint_returns_presets() -> None:
    response = _client().get("/api/api-testing/environments")

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["total"] >= 2
    assert {"mock-local", "local-api"}.issubset(
        {item["environment_id"] for item in payload["items"]}
    )


def test_api_testing_synthesize_endpoint_returns_case_mutations() -> None:
    response = _client().post(
        "/api/api-testing/synthesize",
        json={
            "method": "POST",
            "path": "/api/login",
            "headers": {"Content-Type": "application/json"},
            "body": '{"username": "tester", "password": "Passw0rd!"}',
            "count": 4,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["total"] == 4
    assert any(item["name"] == "错误密码" for item in payload["cases"])


def test_api_testing_plan_endpoint_returns_operations() -> None:
    response = _client().post(
        "/api/api-testing/plan",
        json={
            "prompt": "创建环境，生成登录接口用例并执行",
            "context": {"selected_endpoint_id": "login-success"},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "deterministic_planner"
    assert {"create_environment", "create_collection", "create_case", "run_collection"}.issubset(
        {item["type"] for item in payload["operations"]}
    )


def test_api_testing_curl_endpoint_exports_command() -> None:
    response = _client().post(
        "/api/api-testing/curl",
        json={
            "method": "POST",
            "path": "/api/login",
            "base_url": "http://127.0.0.1:9000",
            "headers": {"Content-Type": "application/json"},
            "params": {"trace": "demo"},
            "body": '{"username": "tester", "password": "Passw0rd!"}',
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert "curl -X POST" in payload["curl"]
    assert "trace=demo" in payload["curl"]


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
