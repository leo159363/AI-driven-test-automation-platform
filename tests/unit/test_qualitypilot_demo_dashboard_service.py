"""Tests for QualityPilot dashboard demo artifact helpers."""

from __future__ import annotations

import json
from pathlib import Path

from src.observability.dashboard.services.qualitypilot_demo_service import (
    build_bug_report_rows,
    build_context_rows,
    build_failed_case_rows,
    build_failure_analysis_rows,
    build_headline_metrics,
    build_test_case_rows,
    build_workflow_rows,
    extract_bug_report_markdown,
    load_qualitypilot_demo_summary,
)


def _sample_summary(tmp_path: Path) -> dict:
    bug_markdown = tmp_path / "bug_report.md"
    bug_markdown.write_text("# Demo bug\n\nFailure evidence.", encoding="utf-8")
    return {
        "workflow": [
            "generate_test_cases",
            "run_api_tests",
            "get_test_report",
            "query_failed_cases",
            "analyze_failure",
            "generate_bug_report",
        ],
        "run_id": "api-api_login-demo",
        "outputs": {"bug_report_md": str(bug_markdown)},
        "headline": {
            "execution_status": "failed",
            "report_status": "failed",
            "failed_case_count": 1,
            "bug_count": 1,
        },
        "stages": {
            "rag_contexts": {
                "contexts": [
                    {
                        "source_id": "auth-api-v1",
                        "source_type": "api_doc",
                        "title": "Login API contract",
                        "score": 0.96,
                        "content": "POST /api/login must return token.",
                    }
                ]
            },
            "test_cases": {
                "test_cases": [
                    {
                        "case_id": "TC-001",
                        "title": "Login token check",
                        "dimension": "functional",
                        "priority": "P1",
                        "automation_hint": {
                            "suggested_file": "pytest_tests/api/test_qualitypilot_auth.py"
                        },
                    }
                ]
            },
            "execution": {"status": "failed"},
            "report": {"status": "failed", "summary": {"total": 1, "failed": 1}},
            "failed_cases": {
                "case_count": 1,
                "cases": [
                    {
                        "case_id": "FC-001",
                        "status": "failure",
                        "classname": "api_login",
                        "name": "assert_token",
                        "failure_category": "auth_or_permission",
                        "failure_signature": "Response does not contain token",
                    }
                ],
            },
            "failure_analysis": {
                "case_count": 1,
                "analyses": [
                    {
                        "analysis_id": "FA-001",
                        "case_id": "FC-001",
                        "root_cause_type": "product_bug_or_contract_mismatch",
                        "confidence": 0.7,
                        "should_create_bug": True,
                        "likely_root_cause": "The login response misses token.",
                    }
                ],
            },
            "bug_report": {
                "bug_count": 1,
                "bug_reports": [
                    {
                        "bug_id": "BUG-001",
                        "title": "[auth] token missing",
                        "severity": "high",
                        "priority": "P1",
                        "status": "draft",
                        "attachments": [{"type": "junit_xml", "path": "reports/junit.xml"}],
                    }
                ],
                "markdown": "# Inline bug",
            },
        },
    }


def test_load_qualitypilot_demo_summary_reads_json(tmp_path: Path) -> None:
    path = tmp_path / "demo_summary.json"
    path.write_text(json.dumps({"run_id": "demo"}), encoding="utf-8")

    summary, warning = load_qualitypilot_demo_summary(path)

    assert warning is None
    assert summary == {"run_id": "demo"}


def test_load_qualitypilot_demo_summary_handles_missing_file(tmp_path: Path) -> None:
    summary, warning = load_qualitypilot_demo_summary(tmp_path / "missing.json")

    assert summary is None
    assert warning
    assert "not found" in warning


def test_build_qualitypilot_demo_rows(tmp_path: Path) -> None:
    summary = _sample_summary(tmp_path)

    metrics = build_headline_metrics(summary)
    assert metrics["Execution"] == "failed"
    assert metrics["Bug Drafts"] == 1

    workflow_rows = build_workflow_rows(summary)
    assert len(workflow_rows) == 6
    assert workflow_rows[-1]["Result"] == "1 bug drafts"

    assert build_context_rows(summary)[0]["Source ID"] == "auth-api-v1"
    assert build_test_case_rows(summary)[0]["Case ID"] == "TC-001"
    assert build_failed_case_rows(summary)[0]["Category"] == "auth_or_permission"
    assert build_failure_analysis_rows(summary)[0]["Create Bug"] is True
    assert build_bug_report_rows(summary)[0]["Severity"] == "high"
    assert extract_bug_report_markdown(summary).startswith("# Demo bug")
