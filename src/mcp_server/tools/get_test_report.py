"""MCP Tool: get_test_report.

This tool parses JUnit XML and discovers report artifacts so MCP clients can
consume test execution results after run_api_tests.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

from mcp import types

from src.core.settings import Settings
from src.observability.dashboard.services.test_report_service import (
    ReportArtifact,
    discover_report_artifacts,
    get_default_junit_report_path,
    parse_junit_xml,
)

logger = logging.getLogger(__name__)


TOOL_NAME = "get_test_report"
TOOL_DESCRIPTION = """Parse a JUnit/Allure test report into structured JSON.

Use this after run_api_tests. The tool returns summary counts, failed cases,
suite details, and discovered report artifact paths.
"""

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
        "allure_results": {
            "type": "string",
            "description": "Optional explicit Allure results directory.",
        },
        "include_failed_cases": {
            "type": "boolean",
            "description": "Whether to include failed/error/skipped testcase details.",
            "default": True,
        },
    },
}


async def get_test_report_handler(
    run_id: Optional[str] = None,
    report_path: Optional[str] = None,
    project_root: str = ".",
    allure_results: Optional[str] = None,
    include_failed_cases: bool = True,
) -> types.CallToolResult:
    """Parse a test report and return JSON for MCP clients."""
    try:
        payload = get_test_report_payload(
            run_id=run_id,
            report_path=report_path,
            project_root=project_root,
            allure_results=allure_results,
            include_failed_cases=include_failed_cases,
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
        logger.exception("get_test_report handler error")
        return types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text=json.dumps(
                        {"error": "failed to parse test report"},
                        ensure_ascii=False,
                        indent=2,
                    ),
                )
            ],
            isError=True,
        )


def get_test_report_payload(
    run_id: Optional[str] = None,
    report_path: Optional[str] = None,
    project_root: str = ".",
    allure_results: Optional[str] = None,
    include_failed_cases: bool = True,
) -> Dict[str, Any]:
    """Build structured test report payload."""
    root = Path(project_root or ".")
    junit_path = _resolve_junit_path(root, run_id, report_path)
    artifacts = _discover_artifacts(root, allure_results)

    if not junit_path.exists():
        return {
            "run_id": run_id or "",
            "report_path": str(junit_path),
            "status": "not_found",
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "errors": 0,
                "skipped": 0,
                "duration_seconds": 0.0,
            },
            "suites": [],
            "failed_cases": [],
            "artifacts": [_artifact_payload(artifact) for artifact in artifacts],
            "message": f"JUnit report not found: {junit_path}",
        }

    summary = parse_junit_xml(junit_path)
    junit_details = _parse_junit_details(junit_path, include_failed_cases=include_failed_cases)
    status = "failed" if summary.failed or summary.errors else "passed"
    if summary.total == 0:
        status = "empty"

    return {
        "run_id": run_id or _infer_run_id(junit_path),
        "report_path": str(junit_path),
        "status": status,
        "summary": {
            "suite_name": summary.suite_name,
            "total": summary.total,
            "passed": summary.passed,
            "failed": summary.failed,
            "errors": summary.errors,
            "skipped": summary.skipped,
            "duration_seconds": round(summary.duration_seconds, 4),
            "pass_rate": _ratio(summary.passed, summary.total),
        },
        "suites": junit_details["suites"],
        "failed_cases": junit_details["failed_cases"],
        "artifacts": [_artifact_payload(artifact) for artifact in artifacts],
    }


def _resolve_junit_path(root: Path, run_id: Optional[str], report_path: Optional[str]) -> Path:
    if report_path and report_path.strip():
        return Path(report_path)
    if run_id and run_id.strip():
        return root / "reports" / "mcp-api-tests" / run_id.strip() / "junit.xml"
    return Path(get_default_junit_report_path(root))


def _discover_artifacts(root: Path, allure_results: Optional[str]) -> List[ReportArtifact]:
    artifacts = discover_report_artifacts(root)
    if allure_results and allure_results.strip():
        path = Path(allure_results)
        artifacts.append(
            ReportArtifact(
                artifact_type="allure_results",
                label="Allure Results",
                path=path,
                exists=path.exists(),
                detail=_describe_explicit_allure(path),
            )
        )
    return artifacts


def _describe_explicit_allure(path: Path) -> str:
    if not path.exists():
        return "Not found"
    if path.is_file():
        return "Allure result file"
    json_count = sum(1 for item in path.rglob("*.json") if item.is_file())
    return f"{json_count} result files"


def _parse_junit_details(
    report_path: Path,
    include_failed_cases: bool,
) -> Dict[str, Any]:
    root = ElementTree.parse(report_path).getroot()
    suites = _collect_suites(root)
    suite_payloads = []
    failed_cases: List[Dict[str, Any]] = []

    for suite in suites:
        suite_payloads.append(_suite_payload(suite))
        if include_failed_cases:
            failed_cases.extend(_collect_failed_cases(suite))

    return {
        "suites": suite_payloads,
        "failed_cases": failed_cases,
    }


def _collect_suites(root: ElementTree.Element) -> List[ElementTree.Element]:
    if root.tag == "testsuite":
        return [root]
    if root.tag == "testsuites":
        return [suite for suite in root if suite.tag == "testsuite"]
    raise ValueError(f"Unsupported JUnit root tag: {root.tag}")


def _suite_payload(suite: ElementTree.Element) -> Dict[str, Any]:
    total = _int_attr(suite, "tests")
    failed = _int_attr(suite, "failures")
    errors = _int_attr(suite, "errors")
    skipped = _int_attr(suite, "skipped")
    if total == 0:
        total = len(suite.findall(".//testcase"))
    passed = max(total - failed - errors - skipped, 0)
    return {
        "name": suite.attrib.get("name", "pytest"),
        "total": total,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "skipped": skipped,
        "duration_seconds": _float_attr(suite, "time"),
    }


def _collect_failed_cases(suite: ElementTree.Element) -> List[Dict[str, Any]]:
    cases = []
    for testcase in suite.findall(".//testcase"):
        child, status = _first_status_child(testcase)
        if child is None:
            continue
        cases.append(
            {
                "classname": testcase.attrib.get("classname", ""),
                "name": testcase.attrib.get("name", ""),
                "status": status,
                "message": child.attrib.get("message", ""),
                "details": (child.text or "").strip(),
                "duration_seconds": _float_attr(testcase, "time"),
            }
        )
    return cases


def _first_status_child(testcase: ElementTree.Element) -> tuple[Optional[ElementTree.Element], str]:
    for status in ("failure", "error", "skipped"):
        child = testcase.find(status)
        if child is not None:
            return child, status
    return None, ""


def _artifact_payload(artifact: ReportArtifact) -> Dict[str, Any]:
    return {
        "artifact_type": artifact.artifact_type,
        "label": artifact.label,
        "path": str(artifact.path),
        "exists": artifact.exists,
        "detail": artifact.detail,
    }


def _infer_run_id(junit_path: Path) -> str:
    parts = list(junit_path.parts)
    if "mcp-api-tests" in parts:
        index = parts.index("mcp-api-tests")
        if index + 1 < len(parts):
            return parts[index + 1]
    return ""


def _int_attr(element: ElementTree.Element, name: str) -> int:
    return int(element.attrib.get(name, "0") or 0)


def _float_attr(element: ElementTree.Element, name: str) -> float:
    return float(element.attrib.get(name, "0") or 0.0)


def _ratio(value: int, total: int) -> float:
    return round(value / total, 4) if total else 0.0


def register_tool(protocol_handler, settings: Optional[Settings] = None) -> None:
    """Register get_test_report tool with the protocol handler."""
    protocol_handler.register_tool(
        name=TOOL_NAME,
        description=TOOL_DESCRIPTION,
        input_schema=TOOL_INPUT_SCHEMA,
        handler=get_test_report_handler,
    )
    logger.info("Registered MCP tool: %s", TOOL_NAME)
