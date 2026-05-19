"""Unit tests for get_test_report MCP tool."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.mcp_server.tools.get_test_report import (
    get_test_report_handler,
    get_test_report_payload,
)


def _write_junit(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """
<testsuite name="api_login" tests="3" failures="1" errors="0" skipped="1" time="0.321">
  <testcase classname="api_http.api_login" name="step_01_call_api" time="0.120" />
  <testcase classname="api_http.api_login" name="step_02_assert_text" time="0.050">
    <failure message="Response does not contain expected text: token">status=failed
message=Response does not contain expected text: token</failure>
  </testcase>
  <testcase classname="api_http.api_login" name="step_03_wait" time="0.010">
    <skipped message="Dry run only" />
  </testcase>
</testsuite>
""".strip(),
        encoding="utf-8",
    )


def test_get_test_report_payload_parses_junit_and_failed_cases(tmp_path: Path) -> None:
    report = tmp_path / "reports" / "api-junit.xml"
    allure_dir = tmp_path / "reports" / "allure-results"
    _write_junit(report)
    allure_dir.mkdir(parents=True)
    (allure_dir / "case-result.json").write_text("{}", encoding="utf-8")

    payload = get_test_report_payload(
        report_path=str(report),
        project_root=str(tmp_path),
        allure_results=str(allure_dir),
    )

    assert payload["status"] == "failed"
    assert payload["summary"] == {
        "suite_name": "api_login",
        "total": 3,
        "passed": 1,
        "failed": 1,
        "errors": 0,
        "skipped": 1,
        "duration_seconds": 0.321,
        "pass_rate": 0.3333,
    }
    assert payload["suites"][0]["name"] == "api_login"
    assert len(payload["failed_cases"]) == 2
    assert payload["failed_cases"][0]["status"] == "failure"
    assert payload["failed_cases"][0]["name"] == "step_02_assert_text"
    assert any(
        artifact["path"] == str(allure_dir)
        and artifact["exists"] is True
        and artifact["detail"] == "1 result files"
        for artifact in payload["artifacts"]
    )


def test_get_test_report_payload_resolves_path_from_run_id(tmp_path: Path) -> None:
    run_id = "api-api_login-test1234"
    report = tmp_path / "reports" / "mcp-api-tests" / run_id / "junit.xml"
    _write_junit(report)

    payload = get_test_report_payload(run_id=run_id, project_root=str(tmp_path))

    assert payload["run_id"] == run_id
    assert payload["report_path"] == str(report)
    assert payload["summary"]["total"] == 3


def test_get_test_report_payload_returns_not_found_for_missing_report(tmp_path: Path) -> None:
    payload = get_test_report_payload(
        run_id="missing-run",
        project_root=str(tmp_path),
    )

    assert payload["status"] == "not_found"
    assert payload["summary"]["total"] == 0
    assert payload["failed_cases"] == []
    assert "JUnit report not found" in payload["message"]


@pytest.mark.asyncio
async def test_get_test_report_handler_returns_json(tmp_path: Path) -> None:
    report = tmp_path / "junit.xml"
    _write_junit(report)

    result = await get_test_report_handler(report_path=str(report), project_root=str(tmp_path))

    assert result.isError is False
    payload = json.loads(result.content[0].text)
    assert payload["status"] == "failed"
    assert payload["summary"]["failed"] == 1
