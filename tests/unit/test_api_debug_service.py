"""Unit tests for the controlled API debug runner."""

from __future__ import annotations

import pytest

from src.api.services.api_debug_service import (
    export_curl_command,
    generate_api_operation_plan,
    list_api_environments,
    run_api_debug_request,
    synthesize_api_test_cases,
)


def test_run_api_debug_request_uses_mock_login_success() -> None:
    result = run_api_debug_request(
        method="POST",
        path="/api/login",
        headers={"Content-Type": "application/json"},
        body='{"username": "tester", "password": "Passw0rd!"}',
        expected_status=200,
        json_assertions=[
            {"path": "token", "operator": "exists"},
            {"path": "user.username", "operator": "equals", "expected": "tester"},
        ],
    )

    assert result["request"]["target_mode"] == "mock"
    assert result["response"]["status_code"] == 200
    assert result["passed"] is True
    assert result["summary"] == {"total": 3, "passed": 3, "failed": 0}


def test_run_api_debug_request_reports_failed_assertion() -> None:
    result = run_api_debug_request(
        method="POST",
        path="/api/login",
        headers={"Content-Type": "application/json"},
        body='{"username": "tester", "password": "wrong"}',
        expected_status=200,
        json_assertions=[
            {"path": "error", "operator": "equals", "expected": "invalid_credentials"}
        ],
    )

    assert result["response"]["status_code"] == 401
    assert result["passed"] is False
    assert result["summary"]["failed"] == 1


def test_run_api_debug_request_supports_upload_missing_filename() -> None:
    result = run_api_debug_request(
        method="POST",
        path="/api/upload",
        headers={"Content-Type": "application/octet-stream"},
        body="demo-binary-content",
        expected_status=400,
        json_assertions=[
            {"path": "error", "operator": "equals", "expected": "missing_filename"}
        ],
    )

    assert result["passed"] is True
    assert result["response"]["json"]["error"] == "missing_filename"


def test_run_api_debug_request_rejects_remote_base_url() -> None:
    with pytest.raises(ValueError, match="Only localhost targets"):
        run_api_debug_request(
            method="GET",
            path="/api/health",
            base_url="https://example.com",
        )


def test_run_api_debug_request_replaces_environment_variables() -> None:
    result = run_api_debug_request(
        method="POST",
        path="/api/login",
        headers={"Content-Type": "application/json"},
        body='{"username": "{{username}}", "password": "{{password}}"}',
        environment={
            "environment_id": "mock-local",
            "name": "Mock",
            "variables": {"username": "tester", "password": "Passw0rd!"},
            "headers": {"X-Project": "{{username}}"},
        },
        expected_status=200,
        json_assertions=[{"path": "token", "operator": "exists"}],
    )

    assert result["request"]["body"] == '{"username": "tester", "password": "Passw0rd!"}'
    assert result["request"]["headers"]["X-Project"] == "tester"
    assert result["passed"] is True


def test_run_api_debug_request_supports_configured_mock_response() -> None:
    result = run_api_debug_request(
        method="GET",
        path="/api/anything",
        mock_config={
            "enabled": True,
            "status_code": 202,
            "headers": {"Content-Type": "application/json"},
            "body": {"accepted": True},
        },
        expected_status=202,
        json_assertions=[{"path": "accepted", "operator": "equals", "expected": "True"}],
    )

    assert result["request"]["target_mode"] == "configured_mock"
    assert result["response"]["status_code"] == 202
    assert result["response"]["json"] == {"accepted": True}


def test_list_api_environments_returns_workspace_presets() -> None:
    environments = list_api_environments()

    assert {item["environment_id"] for item in environments} == {"mock-local", "local-api"}
    assert environments[0]["variables"]["username"] == "tester"


def test_synthesize_api_test_cases_generates_login_mutations() -> None:
    result = synthesize_api_test_cases(
        method="POST",
        path="/api/login",
        headers={"Content-Type": "application/json"},
        body='{"username": "tester", "password": "Passw0rd!"}',
        count=6,
    )

    names = {item["name"] for item in result["cases"]}
    assert {"正常登录", "错误密码", "SQL 注入密码"}.issubset(names)
    assert result["summary"]["dimensions"] == ["happy_path", "negative", "boundary", "security"]


def test_generate_api_operation_plan_returns_runnable_operations() -> None:
    result = generate_api_operation_plan(
        prompt="帮我创建环境并执行登录接口测试",
        context={"selected_endpoint_id": "login-success"},
    )

    operation_types = [item["type"] for item in result["operations"]]
    assert "create_environment" in operation_types
    assert "create_collection" in operation_types
    assert "create_case" in operation_types
    assert "run_collection" in operation_types


def test_export_curl_command_replaces_variables_and_params() -> None:
    result = export_curl_command(
        method="POST",
        path="/api/login",
        base_url="http://127.0.0.1:9000",
        headers={"Content-Type": "application/json", "X-User": "{{username}}"},
        params={"trace": "{{trace_id}}"},
        body='{"username": "{{username}}", "password": "{{password}}"}',
        environment={
            "variables": {
                "username": "tester",
                "password": "Passw0rd!",
                "trace_id": "demo-1",
            }
        },
    )

    assert "curl -X POST" in result["curl"]
    assert "trace=demo-1" in result["curl"]
    assert "X-User: tester" in result["curl"]
    assert "Passw0rd!" in result["curl"]
