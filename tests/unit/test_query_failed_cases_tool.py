"""Unit tests for query_failed_cases MCP tool."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.mcp_server.tools.query_failed_cases import (
    query_failed_cases_handler,
    query_failed_cases_payload,
)


def _write_junit(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """
<testsuite name="api_login" tests="4" failures="1" errors="1" skipped="1" time="0.500">
  <testcase classname="api_http.api_login" name="step_01_call_api" time="0.100" />
  <testcase classname="api_http.api_login" name="step_02_assert_token" time="0.050">
    <failure message="Response does not contain expected text: token">status=failed
message=Response does not contain expected text: token</failure>
  </testcase>
  <testcase classname="api_http.api_login" name="step_03_parse_json" time="0.020">
    <error message="JSONDecodeError: invalid response">Traceback: JSONDecodeError</error>
  </testcase>
  <testcase classname="api_http.api_login" name="step_04_wait" time="0.010">
    <skipped message="Dry run only" />
  </testcase>
</testsuite>
""".strip(),
        encoding="utf-8",
    )


def test_query_failed_cases_defaults_to_failure_and_error(tmp_path: Path) -> None:
    report = tmp_path / "junit.xml"
    _write_junit(report)

    payload = query_failed_cases_payload(report_path=str(report), project_root=str(tmp_path))

    assert payload["status"] == "cases_found"
    assert payload["summary"]["total"] == 4
    assert payload["case_count"] == 2
    assert [case["status"] for case in payload["cases"]] == ["failure", "error"]
    assert payload["cases"][0]["failure_category"] == "auth_or_permission"
    assert payload["recommended_next_tools"][0]["tool"] == "analyze_failure"


def test_query_failed_cases_filters_status_keyword_and_classname(tmp_path: Path) -> None:
    report = tmp_path / "junit.xml"
    _write_junit(report)

    payload = query_failed_cases_payload(
        report_path=str(report),
        project_root=str(tmp_path),
        statuses=["skipped"],
        keyword="dry run",
        classname="api_login",
    )

    assert payload["case_count"] == 1
    assert payload["cases"][0]["name"] == "step_04_wait"
    assert payload["cases"][0]["failure_category"] == "skipped"


def test_query_failed_cases_supports_limit_and_detail_omission(tmp_path: Path) -> None:
    report = tmp_path / "junit.xml"
    _write_junit(report)

    payload = query_failed_cases_payload(
        report_path=str(report),
        project_root=str(tmp_path),
        statuses=["failure", "error", "skipped"],
        limit=1,
        include_details=False,
    )

    assert payload["case_count"] == 3
    assert payload["returned_count"] == 1
    assert payload["truncated"] is True
    assert "details" not in payload["cases"][0]


def test_query_failed_cases_returns_not_found_for_missing_report(tmp_path: Path) -> None:
    payload = query_failed_cases_payload(
        run_id="missing-run",
        project_root=str(tmp_path),
    )

    assert payload["status"] == "not_found"
    assert payload["case_count"] == 0
    assert payload["cases"] == []
    assert "JUnit report not found" in payload["message"]


def test_query_failed_cases_rejects_unknown_status(tmp_path: Path) -> None:
    report = tmp_path / "junit.xml"
    _write_junit(report)

    with pytest.raises(ValueError, match="Unsupported status"):
        query_failed_cases_payload(
            report_path=str(report),
            project_root=str(tmp_path),
            statuses=["broken"],
        )


@pytest.mark.asyncio
async def test_query_failed_cases_handler_returns_json(tmp_path: Path) -> None:
    report = tmp_path / "junit.xml"
    _write_junit(report)

    result = await query_failed_cases_handler(
        report_path=str(report),
        project_root=str(tmp_path),
        keyword="invalid response",
    )

    assert result.isError is False
    payload = json.loads(result.content[0].text)
    assert payload["case_count"] == 1
    assert payload["cases"][0]["status"] == "error"
