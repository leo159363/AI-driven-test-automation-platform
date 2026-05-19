"""Unit tests for generate_bug_report MCP tool."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.mcp_server.tools.generate_bug_report import (
    generate_bug_report_handler,
    generate_bug_report_payload,
)


def _write_junit(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """
<testsuite name="api_login" tests="2" failures="1" errors="0" skipped="0" time="0.250">
  <testcase classname="api_http.api_login" name="step_01_call_api" time="0.100" />
  <testcase classname="api_http.api_login" name="step_02_assert_token" time="0.050">
    <failure message="Response does not contain expected text: token">status=failed
message=Response does not contain expected text: token</failure>
  </testcase>
</testsuite>
""".strip(),
        encoding="utf-8",
    )


def _analysis(should_create_bug: bool = True) -> dict:
    return {
        "analysis_id": "FA-001",
        "case_id": "FC-001",
        "classname": "api_http.api_login",
        "name": "step_02_assert_token",
        "status": "failure",
        "failure_category": "auth_or_permission",
        "failure_signature": "Response does not contain expected text: token",
        "root_cause_type": "product_bug_or_contract_mismatch",
        "likely_root_cause": "Authentication behavior differs from the expected API contract.",
        "confidence": 0.7,
        "evidence": [
            {
                "type": "junit_message",
                "value": "Response does not contain expected text: token",
            }
        ],
        "suggested_fix": ["Compare actual response with requirement/API documentation."],
        "next_action": "confirm_reproducibility_then_generate_bug_report",
        "should_create_bug": should_create_bug,
        "related_contexts": [
            {
                "context_id": "auth-api-v1_0001",
                "source_id": "auth-api-v1",
                "source_type": "api_doc",
                "title": "login token contract",
                "score": 0.91,
                "matched_terms": 2,
            }
        ],
        "reproduction_steps": [
            "Run testcase api_http.api_login.step_02_assert_token",
            "Capture request, response, logs, and generated report artifacts.",
        ],
    }


def test_generate_bug_report_payload_from_analysis() -> None:
    payload = generate_bug_report_payload(
        analyses=[_analysis()],
        run_id="api-api_login-demo",
        report_path="reports/demo/junit.xml",
        project="qualitypilot-demo",
        module="auth",
        version="v1",
        environment="staging",
        reporter="tester",
    )

    assert payload["status"] == "generated"
    assert payload["bug_count"] == 1
    bug = payload["bug_reports"][0]
    assert bug["bug_id"] == "BUG-001"
    assert bug["severity"] == "high"
    assert bug["priority"] == "P1"
    assert bug["project"] == "qualitypilot-demo"
    assert bug["module"] == "auth"
    assert bug["source"]["analysis_id"] == "FA-001"
    assert bug["attachments"][0]["path"] == "reports/demo/junit.xml"
    assert "# [auth] step_02_assert_token failed" in bug["markdown"]
    assert "## Steps To Reproduce" in payload["markdown"]


def test_generate_bug_report_payload_can_analyze_report_internally(tmp_path: Path) -> None:
    report = tmp_path / "junit.xml"
    _write_junit(report)

    payload = generate_bug_report_payload(
        report_path=str(report),
        project_root=str(tmp_path),
        project="qualitypilot-demo",
        module="auth",
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
    )

    assert payload["status"] == "generated"
    assert payload["analysis_count"] == 1
    assert payload["bug_reports"][0]["source"]["case_name"] == "step_02_assert_token"
    assert payload["bug_reports"][0]["related_contexts"][0]["source_id"] == "auth-api-v1"


def test_generate_bug_report_filters_non_bug_candidates() -> None:
    analysis = _analysis(should_create_bug=False)
    analysis["root_cause_type"] = "test_script_issue"

    payload = generate_bug_report_payload(analyses=[analysis])

    assert payload["status"] == "no_bug_candidates"
    assert payload["bug_count"] == 0
    assert payload["bug_reports"] == []

    included = generate_bug_report_payload(
        analyses=[analysis],
        include_non_bug_candidates=True,
        include_markdown=False,
    )

    assert included["status"] == "generated"
    assert included["bug_count"] == 1
    assert included["markdown"] == ""


def test_generate_bug_report_returns_not_found_for_missing_report(tmp_path: Path) -> None:
    payload = generate_bug_report_payload(
        run_id="missing-run",
        project_root=str(tmp_path),
    )

    assert payload["status"] == "not_found"
    assert payload["bug_count"] == 0
    assert "JUnit report not found" in payload["message"]


def test_generate_bug_report_rejects_invalid_severity() -> None:
    with pytest.raises(ValueError, match="Unsupported severity"):
        generate_bug_report_payload(analyses=[_analysis()], severity="urgent")


@pytest.mark.asyncio
async def test_generate_bug_report_handler_returns_json() -> None:
    result = await generate_bug_report_handler(
        analyses=[_analysis()],
        project="qualitypilot-demo",
        module="auth",
        severity="critical",
        priority="P0",
    )

    assert result.isError is False
    payload = json.loads(result.content[0].text)
    assert payload["status"] == "generated"
    assert payload["bug_reports"][0]["severity"] == "critical"
    assert payload["bug_reports"][0]["priority"] == "P0"
