"""Unit tests for the controlled API debug runner."""

from __future__ import annotations

import pytest

from src.api.services.api_debug_service import run_api_debug_request


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
