"""Unit tests for analyze_failure MCP tool."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.mcp_server.tools.analyze_failure import (
    analyze_failure_handler,
    analyze_failure_payload,
)


def _write_junit(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """
<testsuite name="api_login" tests="3" failures="1" errors="1" skipped="0" time="0.420">
  <testcase classname="api_http.api_login" name="step_01_call_api" time="0.100" />
  <testcase classname="api_http.api_login" name="step_02_assert_token" time="0.050">
    <failure message="Response does not contain expected text: token">status=failed
message=Response does not contain expected text: token</failure>
  </testcase>
  <testcase classname="api_http.api_login" name="step_03_parse_json" time="0.020">
    <error message="JSONDecodeError: invalid response">Traceback: JSONDecodeError</error>
  </testcase>
</testsuite>
""".strip(),
        encoding="utf-8",
    )


def test_analyze_failure_payload_uses_report_and_contexts(tmp_path: Path) -> None:
    report = tmp_path / "junit.xml"
    _write_junit(report)

    payload = analyze_failure_payload(
        report_path=str(report),
        project_root=str(tmp_path),
        contexts=[
            {
                "chunk_id": "auth-api-v1_0001",
                "source_id": "auth-api-v1",
                "source_type": "api_doc",
                "title": "login token contract",
                "content": "The login API should return a token field after successful authentication.",
                "score": 0.91,
            }
        ],
        project="qualitypilot-demo",
        module="auth",
        version="v1",
    )

    assert payload["status"] == "analyzed"
    assert payload["project"] == "qualitypilot-demo"
    assert payload["case_count"] == 2
    assert payload["summary"]["bug_candidate_count"] == 2
    assert payload["analyses"][0]["root_cause_type"] == "product_bug_or_contract_mismatch"
    assert payload["analyses"][0]["should_create_bug"] is True
    assert payload["analyses"][0]["related_contexts"][0]["source_id"] == "auth-api-v1"
    assert payload["bug_report_candidates"][0]["case_id"] == "FC-001"


def test_analyze_failure_payload_accepts_failed_cases_directly() -> None:
    payload = analyze_failure_payload(
        failed_cases=[
            {
                "case_id": "FC-001",
                "classname": "tests.api.test_login",
                "name": "test_login_fixture",
                "status": "error",
                "message": "fixture 'token' not found",
                "details": "FixtureLookupError: fixture 'token' not found",
            }
        ],
        analysis_depth="quick",
    )

    assert payload["status"] == "analyzed"
    assert payload["analysis_depth"] == "quick"
    assert payload["summary"]["bug_candidate_count"] == 0
    assert payload["analyses"][0]["root_cause_type"] == "test_script_issue"
    assert "reproduction_steps" not in payload["analyses"][0]


def test_analyze_failure_payload_returns_not_found_for_missing_report(tmp_path: Path) -> None:
    payload = analyze_failure_payload(
        run_id="missing-run",
        project_root=str(tmp_path),
    )

    assert payload["status"] == "not_found"
    assert payload["case_count"] == 0
    assert payload["analyses"] == []
    assert "JUnit report not found" in payload["message"]


def test_analyze_failure_payload_returns_no_cases(tmp_path: Path) -> None:
    report = tmp_path / "junit.xml"
    report.write_text(
        """
<testsuite name="api_login" tests="1" failures="0" errors="0" skipped="0" time="0.100">
  <testcase classname="api_http.api_login" name="step_01_call_api" time="0.100" />
</testsuite>
""".strip(),
        encoding="utf-8",
    )

    payload = analyze_failure_payload(report_path=str(report), project_root=str(tmp_path))

    assert payload["status"] == "no_cases"
    assert payload["summary"]["total"] == 0
    assert payload["recommended_next_tools"] == []


def test_analyze_failure_payload_rejects_invalid_depth() -> None:
    with pytest.raises(ValueError, match="analysis_depth"):
        analyze_failure_payload(failed_cases=[], analysis_depth="deep")


@pytest.mark.asyncio
async def test_analyze_failure_handler_returns_json(tmp_path: Path) -> None:
    report = tmp_path / "junit.xml"
    _write_junit(report)

    result = await analyze_failure_handler(
        report_path=str(report),
        project_root=str(tmp_path),
        keyword="token",
    )

    assert result.isError is False
    payload = json.loads(result.content[0].text)
    assert payload["status"] == "analyzed"
    assert payload["case_count"] == 1
    assert payload["analyses"][0]["next_action"] == "confirm_reproducibility_then_generate_bug_report"
