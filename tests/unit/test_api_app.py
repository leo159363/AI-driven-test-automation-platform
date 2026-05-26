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


def test_test_case_crud_flow() -> None:
    client = _client()

    create_response = client.post(
        "/api/test-cases",
        json={
            "title": "登录接口-自定义边界用例",
            "test_type": "接口测试",
            "module": "登录鉴权",
            "priority": "P2",
            "method": "POST",
            "path": "/api/login",
            "collection_id": "auth",
            "description": "自定义创建的接口测试用例",
            "scenario_id": "api_login",
            "scenario_name": "API: 登录接口",
            "automation_status": "草稿",
            "pytest_target": "",
            "assertion": "缺少 password 时返回 400",
            "related_report": "",
        },
    )

    assert create_response.status_code == 200
    created = create_response.json()["case"]
    assert created["case_id"].startswith("TC-CUSTOM-")
    assert created["is_builtin"] is False

    update_response = client.put(
        f"/api/test-cases/{created['case_id']}",
        json={
            "title": "登录接口-自定义边界用例更新",
            "test_type": "接口测试",
            "module": "登录鉴权",
            "priority": "P1",
            "method": "POST",
            "path": "/api/login",
            "collection_id": "auth",
            "description": "更新后的接口测试用例",
            "scenario_id": "api_login",
            "scenario_name": "API: 登录接口",
            "automation_status": "草稿",
            "pytest_target": "",
            "assertion": "缺少 username 时返回 400",
            "related_report": "",
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["case"]["title"].endswith("更新")

    delete_response = client.delete(f"/api/test-cases/{created['case_id']}")
    assert delete_response.status_code == 200


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


def test_api_testing_environment_crud_flow() -> None:
    client = _client()

    create_response = client.post(
        "/api/api-testing/environments",
        json={
            "name": "Staging API",
            "base_url": "http://127.0.0.1:9000",
            "description": "staging demo",
            "variables": {"token": "demo-token"},
            "headers": {"Content-Type": "application/json"},
            "is_default": True,
        },
    )

    assert create_response.status_code == 200
    created = create_response.json()["environment"]
    assert created["name"] == "Staging API"
    assert created["is_default"] is True

    list_response = client.get("/api/api-testing/environments")
    assert list_response.status_code == 200
    assert created["environment_id"] in {
        item["environment_id"] for item in list_response.json()["items"]
    }

    update_response = client.put(
        f"/api/api-testing/environments/{created['environment_id']}",
        json={
            "name": "Staging API Updated",
            "base_url": "http://127.0.0.1:9001",
            "description": "updated",
            "variables": {"token": "updated-token"},
            "headers": {"Content-Type": "application/json"},
            "is_default": False,
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["environment"]["name"] == "Staging API Updated"

    delete_response = client.delete(f"/api/api-testing/environments/{created['environment_id']}")
    assert delete_response.status_code == 200


def test_api_testing_collections_and_saved_cases_flow() -> None:
    client = _client()
    collections_response = client.get("/api/api-testing/collections")

    assert collections_response.status_code == 200
    collections_payload = collections_response.json()
    assert collections_payload["summary"]["total"] >= 6
    assert collections_payload["summary"]["case_total"] >= 4

    save_response = client.post(
        "/api/api-testing/cases",
        json={
            "name": "登录成功草稿",
            "method": "POST",
            "path": "/api/login",
            "collection_id": "auth",
            "headers": {"Content-Type": "application/json"},
            "body": '{"username": "tester", "password": "Passw0rd!"}',
            "expected_status": 200,
            "json_assertions": [{"path": "token", "operator": "exists"}],
        },
    )

    assert save_response.status_code == 200
    assert save_response.json()["case"]["source"] == "api_workbench"

    run_response = client.post("/api/api-testing/collections/auth/run")
    assert run_response.status_code == 200
    assert run_response.json()["status"] == "passed"


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


def test_platform_dashboard_and_copilot_endpoints() -> None:
    client = _client()
    dashboard_response = client.get("/api/platform/dashboard")

    assert dashboard_response.status_code == 200
    dashboard = dashboard_response.json()
    assert dashboard["api_tests"]["total"] >= 4
    assert dashboard["qualitypilot_features"]

    search_response = client.post("/api/platform/global-search", json={"keyword": "登录"})
    assert search_response.status_code == 200
    assert search_response.json()["summary"]["total"] >= 1

    copilot_response = client.post("/api/platform/copilot/chat", json={"message": "帮我跑接口测试"})
    assert copilot_response.status_code == 200
    copilot = copilot_response.json()
    assert any(item["type"] == "open_page" for item in copilot["operations"])


def test_platform_run_actions_return_demo_records() -> None:
    client = _client()

    web_response = client.post("/api/platform/web-tests/scripts/web-login-smoke/run")
    app_response = client.post("/api/platform/app-tests/scripts/app-login-contract/run")
    perf_response = client.post("/api/platform/performance/scenarios/perf-login-baseline/run")
    cicd_response = client.post("/api/platform/cicd/jobs/ci-quality-gate/run")

    assert web_response.status_code == 200
    assert app_response.status_code == 200
    assert perf_response.status_code == 200
    assert cicd_response.status_code == 200
    assert web_response.json()["summary"]["passed"] >= 1
    assert app_response.json()["module"] == "移动端登录"
    assert "metrics" in perf_response.json()
    assert cicd_response.json()["module"] == "CI/CD"


def test_app_test_script_crud_flow() -> None:
    client = _client()
    payload = {
        "name": "App 支付回调兼容性脚本",
        "description": "覆盖 Android 和 iOS 的支付回调跳转链路。",
        "platform": "Android / iOS",
        "automation_engine": "Appium",
        "case_set": "支付回调",
        "priority": "P1",
        "device": "真机云 / 模拟器",
        "status": "draft",
        "pytest_target": "",
        "steps": ["打开支付页", "触发支付回调", "返回 App 结果页"],
        "assertions": ["订单状态更新", "重复回调不重复扣款"],
    }

    create_response = client.post("/api/platform/app-tests/scripts", json=payload)

    assert create_response.status_code == 200
    created = create_response.json()["script"]
    assert created["case_set"] == "支付回调"
    assert created["automation_engine"] == "Appium"

    list_response = client.get("/api/platform/app-tests/scripts")
    assert list_response.status_code == 200
    assert list_response.json()["summary"]["total"] >= 3

    update_response = client.put(
        f"/api/platform/app-tests/scripts/{created['script_id']}",
        json={**payload, "status": "ready", "pytest_target": "tests/automation/test_app_payment.py"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["script"]["status"] == "ready"

    delete_response = client.delete(f"/api/platform/app-tests/scripts/{created['script_id']}")
    assert delete_response.status_code == 200


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
