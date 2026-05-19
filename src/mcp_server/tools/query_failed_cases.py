"""MCP Tool: query_failed_cases.

This tool filters failed/error/skipped cases from a parsed JUnit report so the
next MCP steps can analyze failures and generate bug reports.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Sequence

from mcp import types

from src.core.settings import Settings
from src.mcp_server.tools.get_test_report import get_test_report_payload

logger = logging.getLogger(__name__)


TOOL_NAME = "query_failed_cases"
TOOL_DESCRIPTION = """Query failed cases from a parsed JUnit/Allure test report.

Use this after get_test_report. The tool filters failure/error/skipped cases and
returns compact evidence for analyze_failure and generate_bug_report.
"""

VALID_STATUSES = ("failure", "error", "skipped")
DEFAULT_STATUSES = ("failure", "error")

TOOL_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "run_id": {
            "type": "string",
            "description": "Optional run id from run_api_tests. Used to infer reports/mcp-api-tests/{run_id}/junit.xml.",
        },
        "report_path": {
            "type": "string",
            "description": "Optional explicit JUnit XML path.",
        },
        "project_root": {
            "type": "string",
            "description": "Project root for default report discovery.",
            "default": ".",
        },
        "statuses": {
            "type": "array",
            "description": "Case statuses to return. Defaults to failure and error.",
            "items": {"type": "string", "enum": list(VALID_STATUSES)},
        },
        "keyword": {
            "type": "string",
            "description": "Optional keyword filter matched against classname, name, message, and details.",
        },
        "classname": {
            "type": "string",
            "description": "Optional classname substring filter.",
        },
        "case_name": {
            "type": "string",
            "description": "Optional testcase name substring filter.",
        },
        "limit": {
            "type": "integer",
            "description": "Maximum number of cases to return.",
            "default": 20,
            "minimum": 1,
            "maximum": 100,
        },
        "include_details": {
            "type": "boolean",
            "description": "Whether to include full failure/error/skipped details.",
            "default": True,
        },
    },
}


async def query_failed_cases_handler(
    run_id: Optional[str] = None,
    report_path: Optional[str] = None,
    project_root: str = ".",
    statuses: Optional[List[str]] = None,
    keyword: Optional[str] = None,
    classname: Optional[str] = None,
    case_name: Optional[str] = None,
    limit: int = 20,
    include_details: bool = True,
) -> types.CallToolResult:
    """Query failed cases and return JSON for MCP clients."""
    try:
        payload = query_failed_cases_payload(
            run_id=run_id,
            report_path=report_path,
            project_root=project_root,
            statuses=statuses,
            keyword=keyword,
            classname=classname,
            case_name=case_name,
            limit=limit,
            include_details=include_details,
        )
        return types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text=json.dumps(payload, ensure_ascii=False, indent=2),
                )
            ],
            isError=payload.get("status") == "not_found",
        )
    except ValueError as exc:
        return types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text=json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2),
                )
            ],
            isError=True,
        )
    except Exception:
        logger.exception("query_failed_cases handler error")
        return types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text=json.dumps(
                        {"error": "failed to query failed cases"},
                        ensure_ascii=False,
                        indent=2,
                    ),
                )
            ],
            isError=True,
        )


def query_failed_cases_payload(
    run_id: Optional[str] = None,
    report_path: Optional[str] = None,
    project_root: str = ".",
    statuses: Optional[Sequence[str]] = None,
    keyword: Optional[str] = None,
    classname: Optional[str] = None,
    case_name: Optional[str] = None,
    limit: int = 20,
    include_details: bool = True,
) -> Dict[str, Any]:
    """Build a structured failed-case query payload."""
    status_filter = _normalize_statuses(statuses)
    limit_value = _normalize_limit(limit)

    report = get_test_report_payload(
        run_id=run_id,
        report_path=report_path,
        project_root=project_root,
        include_failed_cases=True,
    )

    filters = {
        "statuses": status_filter,
        "keyword": (keyword or "").strip(),
        "classname": (classname or "").strip(),
        "case_name": (case_name or "").strip(),
        "limit": limit_value,
        "include_details": bool(include_details),
    }

    if report.get("status") == "not_found":
        return {
            "run_id": report.get("run_id", run_id or ""),
            "report_path": report.get("report_path", ""),
            "status": "not_found",
            "report_status": "not_found",
            "filters": filters,
            "summary": report.get("summary", {}),
            "case_count": 0,
            "returned_count": 0,
            "cases": [],
            "recommended_next_tools": [],
            "message": report.get("message", "JUnit report not found"),
        }

    cases = [
        case
        for case in report.get("failed_cases", [])
        if _matches_case(
            case,
            statuses=status_filter,
            keyword=keyword,
            classname=classname,
            case_name=case_name,
        )
    ]
    returned_cases = [
        _case_payload(index=index, case=case, include_details=bool(include_details))
        for index, case in enumerate(cases[:limit_value], start=1)
    ]

    return {
        "run_id": report.get("run_id", run_id or ""),
        "report_path": report.get("report_path", ""),
        "status": "cases_found" if cases else "no_cases",
        "report_status": report.get("status", ""),
        "filters": filters,
        "summary": report.get("summary", {}),
        "case_count": len(cases),
        "returned_count": len(returned_cases),
        "truncated": len(cases) > limit_value,
        "cases": returned_cases,
        "recommended_next_tools": _recommended_next_tools(returned_cases),
    }


def _normalize_statuses(statuses: Optional[Sequence[str]]) -> List[str]:
    if statuses is None:
        return list(DEFAULT_STATUSES)

    if isinstance(statuses, str):
        raw_statuses = [statuses]
    else:
        raw_statuses = list(statuses)

    normalized = []
    for status in raw_statuses:
        value = str(status).strip().lower()
        if not value:
            continue
        if value not in VALID_STATUSES:
            available = ", ".join(VALID_STATUSES)
            raise ValueError(f"Unsupported status: {value}. Available: {available}")
        if value not in normalized:
            normalized.append(value)

    return normalized or list(DEFAULT_STATUSES)


def _normalize_limit(limit: int) -> int:
    try:
        value = int(limit)
    except (TypeError, ValueError):
        value = 20
    return min(max(value, 1), 100)


def _matches_case(
    case: Dict[str, Any],
    statuses: Sequence[str],
    keyword: Optional[str],
    classname: Optional[str],
    case_name: Optional[str],
) -> bool:
    if str(case.get("status", "")).lower() not in statuses:
        return False

    if not _contains(case.get("classname", ""), classname):
        return False

    if not _contains(case.get("name", ""), case_name):
        return False

    if keyword and keyword.strip():
        haystack = " ".join(
            str(case.get(key, ""))
            for key in ("classname", "name", "message", "details")
        )
        return keyword.strip().lower() in haystack.lower()

    return True


def _contains(value: Any, needle: Optional[str]) -> bool:
    if not needle or not needle.strip():
        return True
    return needle.strip().lower() in str(value or "").lower()


def _case_payload(index: int, case: Dict[str, Any], include_details: bool) -> Dict[str, Any]:
    payload = {
        "case_id": f"FC-{index:03d}",
        "classname": case.get("classname", ""),
        "name": case.get("name", ""),
        "status": case.get("status", ""),
        "message": case.get("message", ""),
        "duration_seconds": case.get("duration_seconds", 0.0),
        "failure_category": _infer_failure_category(case),
        "failure_signature": _failure_signature(case),
        "recommended_usage": [
            "failure_analysis",
            "bug_report_generation",
        ],
    }
    if include_details:
        payload["details"] = case.get("details", "")
    return payload


def _infer_failure_category(case: Dict[str, Any]) -> str:
    status = str(case.get("status", "")).lower()
    text = " ".join(
        str(case.get(key, ""))
        for key in ("classname", "name", "message", "details")
    ).lower()

    if status == "skipped":
        return "skipped"
    if "timeout" in text or "timed out" in text:
        return "timeout"
    if any(token in text for token in ("connection", "refused", "dns", "network")):
        return "environment_or_network"
    if any(token in text for token in ("401", "403", "unauthorized", "forbidden", "token")):
        return "auth_or_permission"
    if any(token in text for token in ("assert", "expected", "actual", "does not contain")):
        return "assertion_mismatch"
    if status == "error":
        return "test_error"
    return "unknown"


def _failure_signature(case: Dict[str, Any]) -> str:
    message = str(case.get("message", "")).strip()
    details = str(case.get("details", "")).strip()
    candidate = message or _first_non_empty_line(details)
    if not candidate:
        candidate = f"{case.get('classname', '')}.{case.get('name', '')}".strip(".")
    return candidate[:200]


def _first_non_empty_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _recommended_next_tools(cases: Sequence[Dict[str, Any]]) -> List[Dict[str, str]]:
    if not cases:
        return []
    return [
        {
            "tool": "analyze_failure",
            "reason": "Combine failed-case evidence with RAG context to identify likely root cause.",
        },
        {
            "tool": "generate_bug_report",
            "reason": "Convert confirmed reproducible failures into a structured defect report.",
        },
    ]


def register_tool(protocol_handler, settings: Optional[Settings] = None) -> None:
    """Register query_failed_cases tool with the protocol handler."""
    protocol_handler.register_tool(
        name=TOOL_NAME,
        description=TOOL_DESCRIPTION,
        input_schema=TOOL_INPUT_SCHEMA,
        handler=query_failed_cases_handler,
    )
    logger.info("Registered MCP tool: %s", TOOL_NAME)
