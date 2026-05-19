"""Unit tests for run_api_tests MCP tool."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import src.mcp_server.tools.run_api_tests as run_module
from src.observability.dashboard.services.test_report_service import parse_junit_xml


@pytest.mark.asyncio
async def test_run_api_tests_handler_plan_dry_run_writes_reports(tmp_path: Path) -> None:
    junit_path = tmp_path / "api-login-junit.xml"
    allure_dir = tmp_path / "allure-results"

    result = await run_module.run_api_tests_handler(
        scenario_id="api_login",
        base_url="http://127.0.0.1:8000",
        dry_run=True,
        execution_mode="plan",
        junitxml=str(junit_path),
        allure_results=str(allure_dir),
    )

    assert result.isError is False
    payload = json.loads(result.content[0].text)
    assert payload["scenario_id"] == "api_login"
    assert payload["execution_mode"] == "plan"
    assert payload["status"] == "dry_run"
    assert payload["summary"] == {
        "total": 3,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "dry_run": 3,
    }
    assert payload["steps"][0]["request_url"] == "http://127.0.0.1:8000/api/login"
    assert payload["report_paths"]["junitxml"] == str(junit_path)
    assert "allure_result" in payload["report_paths"]
    assert junit_path.exists()
    assert any(allure_dir.glob("*-result.json"))

    summary = parse_junit_xml(junit_path)
    assert summary.total == 3
    assert summary.failed == 0
    assert summary.skipped == 3


@pytest.mark.asyncio
async def test_run_api_tests_handler_rejects_non_api_scenario() -> None:
    result = await run_module.run_api_tests_handler(scenario_id="ui_login_smoke")

    assert result.isError is True
    payload = json.loads(result.content[0].text)
    assert "Unsupported API scenario_id" in payload["error"]


def test_run_api_tests_pytest_mode_dry_run_returns_pytest_args(tmp_path: Path) -> None:
    junit_path = tmp_path / "pytest-junit.xml"

    payload = run_module.run_api_tests_payload(
        scenario_id="api_file_upload",
        execution_mode="pytest",
        dry_run=True,
        junitxml=str(junit_path),
    )

    assert payload["execution_mode"] == "pytest"
    assert payload["status"] == "dry_run"
    assert payload["summary"]["dry_run"] == 1
    assert f"--junitxml={junit_path}" in payload["pytest_args"]
    assert "tests/automation/test_api_file_upload.py" in payload["pytest_args"]


def test_run_api_tests_pytest_mode_uses_runner_and_parses_junit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    junit_path = tmp_path / "pytest-junit.xml"

    def fake_run_pytest(pytest_args: list[str]) -> int:
        junit_path.write_text(
            """<?xml version="1.0" encoding="utf-8"?>
<testsuite name="fake" tests="2" failures="0" errors="0" skipped="0" time="0.1">
  <testcase classname="fake" name="test_one" time="0.05" />
  <testcase classname="fake" name="test_two" time="0.05" />
</testsuite>
""",
            encoding="utf-8",
        )
        return 0

    monkeypatch.setattr(run_module, "_run_pytest", fake_run_pytest)

    payload = run_module.run_api_tests_payload(
        scenario_id="api_login",
        execution_mode="pytest",
        dry_run=False,
        junitxml=str(junit_path),
    )

    assert payload["status"] == "passed"
    assert payload["summary"]["total"] == 2
    assert payload["summary"]["passed"] == 2
    assert payload["pytest_exit_code"] == 0
