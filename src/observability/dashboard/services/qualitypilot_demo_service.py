"""Dashboard helpers for the QualityPilot workflow demo artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_QUALITYPILOT_DEMO_DIR = Path("reports/qualitypilot-demo")
DEFAULT_QUALITYPILOT_DEMO_SUMMARY_PATH = DEFAULT_QUALITYPILOT_DEMO_DIR / "demo_summary.json"


TOOL_PURPOSES = {
    "generate_test_cases": "Generate structured test cases from requirement and RAG context.",
    "run_api_tests": "Execute the API scenario and write JUnit/Allure artifacts.",
    "get_test_report": "Parse the generated JUnit report into a test summary.",
    "query_failed_cases": "Extract failed cases as compact triage evidence.",
    "analyze_failure": "Classify the failure and suggest root-cause evidence.",
    "generate_bug_report": "Create a structured defect draft from failure analysis.",
}


def load_qualitypilot_demo_summary(
    summary_path: str | Path = DEFAULT_QUALITYPILOT_DEMO_SUMMARY_PATH,
) -> tuple[dict[str, Any] | None, str | None]:
    """Load the persisted QualityPilot demo summary JSON for dashboard display."""
    path = Path(summary_path)
    if not path.exists():
        return None, f"QualityPilot demo summary not found: {path}"

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, f"QualityPilot demo summary is not valid JSON: {exc}"
    except OSError as exc:
        return None, f"Failed to read QualityPilot demo summary: {exc}"

    if not isinstance(data, dict):
        return None, "QualityPilot demo summary must be a JSON object."
    return data, None


def build_headline_metrics(summary: dict[str, Any]) -> dict[str, Any]:
    """Return top-level numbers used by the Dashboard metric cards."""
    headline = _as_dict(summary.get("headline"))
    return {
        "Run ID": _text(summary.get("run_id")),
        "Execution": _text(headline.get("execution_status")),
        "Report": _text(headline.get("report_status")),
        "Failed Cases": headline.get("failed_case_count", 0),
        "Bug Drafts": headline.get("bug_count", 0),
    }


def build_workflow_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    """Build table rows for the MCP workflow timeline."""
    workflow = _as_list(summary.get("workflow"))
    stages = _as_dict(summary.get("stages"))
    rows: list[dict[str, Any]] = []

    for index, tool_name in enumerate(workflow, start=1):
        tool = _text(tool_name)
        rows.append(
            {
                "Step": index,
                "MCP Tool": tool,
                "Purpose": TOOL_PURPOSES.get(tool, ""),
                "Result": _tool_result(tool, stages),
            }
        )
    return rows


def build_context_rows(summary: dict[str, Any], limit: int = 20) -> list[dict[str, Any]]:
    """Build rows for RAG contexts used by the demo."""
    stages = _as_dict(summary.get("stages"))
    rag_contexts = _as_dict(stages.get("rag_contexts"))
    contexts = _as_list(rag_contexts.get("contexts"))[:limit]

    rows: list[dict[str, Any]] = []
    for context in contexts:
        item = _as_dict(context)
        rows.append(
            {
                "Source ID": _text(item.get("source_id")),
                "Type": _text(item.get("source_type")),
                "Title": _text(item.get("title")),
                "Score": item.get("score", ""),
                "Content": _shorten(item.get("content"), 220),
            }
        )
    return rows


def build_test_case_rows(summary: dict[str, Any], limit: int = 20) -> list[dict[str, Any]]:
    """Build rows for generated test cases."""
    stages = _as_dict(summary.get("stages"))
    test_cases_payload = _as_dict(stages.get("test_cases"))
    cases = _as_list(test_cases_payload.get("test_cases"))[:limit]

    rows: list[dict[str, Any]] = []
    for case in cases:
        item = _as_dict(case)
        automation_hint = _as_dict(item.get("automation_hint"))
        rows.append(
            {
                "Case ID": _text(item.get("case_id")),
                "Title": _text(item.get("title")),
                "Dimension": _text(item.get("dimension")),
                "Priority": _text(item.get("priority")),
                "Automation File": _text(automation_hint.get("suggested_file")),
            }
        )
    return rows


def build_failed_case_rows(summary: dict[str, Any], limit: int = 20) -> list[dict[str, Any]]:
    """Build rows for failed cases parsed from the report."""
    stages = _as_dict(summary.get("stages"))
    failed_payload = _as_dict(stages.get("failed_cases"))
    cases = _as_list(failed_payload.get("cases"))[:limit]

    rows: list[dict[str, Any]] = []
    for case in cases:
        item = _as_dict(case)
        rows.append(
            {
                "Case ID": _text(item.get("case_id")),
                "Status": _text(item.get("status")),
                "Class": _text(item.get("classname")),
                "Name": _text(item.get("name")),
                "Category": _text(item.get("failure_category")),
                "Signature": _shorten(item.get("failure_signature") or item.get("message"), 220),
            }
        )
    return rows


def build_failure_analysis_rows(summary: dict[str, Any], limit: int = 20) -> list[dict[str, Any]]:
    """Build rows for root-cause analysis results."""
    stages = _as_dict(summary.get("stages"))
    analysis_payload = _as_dict(stages.get("failure_analysis"))
    analyses = _as_list(analysis_payload.get("analyses"))[:limit]

    rows: list[dict[str, Any]] = []
    for analysis in analyses:
        item = _as_dict(analysis)
        rows.append(
            {
                "Analysis ID": _text(item.get("analysis_id")),
                "Case ID": _text(item.get("case_id")),
                "Root Cause Type": _text(item.get("root_cause_type")),
                "Confidence": item.get("confidence", ""),
                "Create Bug": bool(item.get("should_create_bug")),
                "Likely Root Cause": _shorten(item.get("likely_root_cause"), 260),
            }
        )
    return rows


def build_bug_report_rows(summary: dict[str, Any], limit: int = 20) -> list[dict[str, Any]]:
    """Build rows for generated bug-report drafts."""
    stages = _as_dict(summary.get("stages"))
    bug_payload = _as_dict(stages.get("bug_report"))
    bugs = _as_list(bug_payload.get("bug_reports"))[:limit]

    rows: list[dict[str, Any]] = []
    for bug in bugs:
        item = _as_dict(bug)
        rows.append(
            {
                "Bug ID": _text(item.get("bug_id")),
                "Title": _text(item.get("title")),
                "Severity": _text(item.get("severity")),
                "Priority": _text(item.get("priority")),
                "Status": _text(item.get("status")),
                "Attachments": len(_as_list(item.get("attachments"))),
            }
        )
    return rows


def extract_bug_report_markdown(summary: dict[str, Any]) -> str:
    """Return bug Markdown from the persisted file when available, then JSON payload."""
    outputs = _as_dict(summary.get("outputs"))
    markdown_path = _text(outputs.get("bug_report_md"))
    if markdown_path:
        path = Path(markdown_path)
        try:
            if path.exists():
                return path.read_text(encoding="utf-8")
        except OSError:
            pass

    stages = _as_dict(summary.get("stages"))
    bug_payload = _as_dict(stages.get("bug_report"))
    return _text(bug_payload.get("markdown"))


def _tool_result(tool_name: str, stages: dict[str, Any]) -> str:
    if tool_name == "generate_test_cases":
        payload = _as_dict(stages.get("test_cases"))
        return f"{len(_as_list(payload.get('test_cases')))} cases"
    if tool_name == "run_api_tests":
        payload = _as_dict(stages.get("execution"))
        return _text(payload.get("status"))
    if tool_name == "get_test_report":
        payload = _as_dict(stages.get("report"))
        summary = _as_dict(payload.get("summary"))
        total = summary.get("total", "")
        failed = summary.get("failed", "")
        status = _text(payload.get("status"))
        return f"{status} | total={total} failed={failed}".strip()
    if tool_name == "query_failed_cases":
        payload = _as_dict(stages.get("failed_cases"))
        return f"{payload.get('case_count', 0)} failed cases"
    if tool_name == "analyze_failure":
        payload = _as_dict(stages.get("failure_analysis"))
        return f"{payload.get('case_count', 0)} analyses"
    if tool_name == "generate_bug_report":
        payload = _as_dict(stages.get("bug_report"))
        return f"{payload.get('bug_count', 0)} bug drafts"
    return ""


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _shorten(value: Any, limit: int) -> str:
    text = " ".join(_text(value).split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."
