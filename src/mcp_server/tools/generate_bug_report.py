"""MCP Tool: generate_bug_report.

This tool converts failure analysis results into structured defect report
drafts. It keeps the final stage of the QualityPilot workflow deterministic and
demo-friendly without requiring an external issue tracker or LLM.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Sequence

from mcp import types

from src.core.settings import Settings
from src.mcp_server.tools.analyze_failure import analyze_failure_payload

logger = logging.getLogger(__name__)


TOOL_NAME = "generate_bug_report"
TOOL_DESCRIPTION = """Generate structured bug report drafts from failure analysis.

Use this after analyze_failure. The tool returns JSON defect drafts plus
Markdown text that can be pasted into Jira, GitHub Issues, or a test report.
"""

VALID_SEVERITIES = ("critical", "high", "medium", "low")
VALID_PRIORITIES = ("P0", "P1", "P2", "P3")

TOOL_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "run_id": {
            "type": "string",
            "description": "Optional run id from run_api_tests. Used when analyses are not provided.",
        },
        "report_path": {
            "type": "string",
            "description": "Optional explicit JUnit XML path used when analyses are not provided.",
        },
        "project_root": {
            "type": "string",
            "description": "Project root for report discovery.",
            "default": ".",
        },
        "analyses": {
            "type": "array",
            "description": "Optional analyses from analyze_failure. If provided, report parsing is skipped.",
            "items": {"type": "object"},
        },
        "failed_cases": {
            "type": "array",
            "description": "Optional failed cases used when analyses are not provided.",
            "items": {"type": "object"},
        },
        "contexts": {
            "type": "array",
            "description": "Optional RAG contexts used when analyses are not provided.",
            "items": {"type": "object"},
        },
        "statuses": {
            "type": "array",
            "description": "Statuses to query when analyses and failed_cases are not provided.",
            "items": {"type": "string", "enum": ["failure", "error", "skipped"]},
        },
        "keyword": {
            "type": "string",
            "description": "Optional keyword filter used during internal failure analysis.",
        },
        "classname": {
            "type": "string",
            "description": "Optional classname filter used during internal failure analysis.",
        },
        "case_name": {
            "type": "string",
            "description": "Optional testcase name filter used during internal failure analysis.",
        },
        "limit": {
            "type": "integer",
            "description": "Maximum number of bug report drafts to generate.",
            "default": 5,
            "minimum": 1,
            "maximum": 20,
        },
        "project": {
            "type": "string",
            "description": "Project name in generated bug reports.",
        },
        "module": {
            "type": "string",
            "description": "Module name in generated bug reports.",
        },
        "version": {
            "type": "string",
            "description": "Affected version in generated bug reports.",
        },
        "environment": {
            "type": "string",
            "description": "Test environment, for example local, staging, or CI.",
            "default": "test",
        },
        "reporter": {
            "type": "string",
            "description": "Reporter name.",
            "default": "QualityPilot",
        },
        "severity": {
            "type": "string",
            "description": "Optional severity override.",
            "enum": list(VALID_SEVERITIES),
        },
        "priority": {
            "type": "string",
            "description": "Optional priority override.",
            "enum": list(VALID_PRIORITIES),
        },
        "include_non_bug_candidates": {
            "type": "boolean",
            "description": "Whether to also generate drafts for analyses not marked as product bug candidates.",
            "default": False,
        },
        "include_markdown": {
            "type": "boolean",
            "description": "Whether to include Markdown defect text.",
            "default": True,
        },
    },
}


async def generate_bug_report_handler(
    run_id: Optional[str] = None,
    report_path: Optional[str] = None,
    project_root: str = ".",
    analyses: Optional[List[Dict[str, Any]]] = None,
    failed_cases: Optional[List[Dict[str, Any]]] = None,
    contexts: Optional[List[Dict[str, Any]]] = None,
    statuses: Optional[List[str]] = None,
    keyword: Optional[str] = None,
    classname: Optional[str] = None,
    case_name: Optional[str] = None,
    limit: int = 5,
    project: Optional[str] = None,
    module: Optional[str] = None,
    version: Optional[str] = None,
    environment: str = "test",
    reporter: str = "QualityPilot",
    severity: Optional[str] = None,
    priority: Optional[str] = None,
    include_non_bug_candidates: bool = False,
    include_markdown: bool = True,
) -> types.CallToolResult:
    """Generate bug report drafts and return JSON for MCP clients."""
    try:
        payload = generate_bug_report_payload(
            run_id=run_id,
            report_path=report_path,
            project_root=project_root,
            analyses=analyses,
            failed_cases=failed_cases,
            contexts=contexts,
            statuses=statuses,
            keyword=keyword,
            classname=classname,
            case_name=case_name,
            limit=limit,
            project=project,
            module=module,
            version=version,
            environment=environment,
            reporter=reporter,
            severity=severity,
            priority=priority,
            include_non_bug_candidates=include_non_bug_candidates,
            include_markdown=include_markdown,
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
        logger.exception("generate_bug_report handler error")
        return types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text=json.dumps(
                        {"error": "failed to generate bug report"},
                        ensure_ascii=False,
                        indent=2,
                    ),
                )
            ],
            isError=True,
        )


def generate_bug_report_payload(
    run_id: Optional[str] = None,
    report_path: Optional[str] = None,
    project_root: str = ".",
    analyses: Optional[Sequence[Dict[str, Any]]] = None,
    failed_cases: Optional[Sequence[Dict[str, Any]]] = None,
    contexts: Optional[Sequence[Dict[str, Any]]] = None,
    statuses: Optional[Sequence[str]] = None,
    keyword: Optional[str] = None,
    classname: Optional[str] = None,
    case_name: Optional[str] = None,
    limit: int = 5,
    project: Optional[str] = None,
    module: Optional[str] = None,
    version: Optional[str] = None,
    environment: str = "test",
    reporter: str = "QualityPilot",
    severity: Optional[str] = None,
    priority: Optional[str] = None,
    include_non_bug_candidates: bool = False,
    include_markdown: bool = True,
) -> Dict[str, Any]:
    """Build structured bug report draft payload."""
    limit_value = _normalize_limit(limit)
    severity_override = _normalize_optional_enum(severity, VALID_SEVERITIES, "severity")
    priority_override = _normalize_optional_enum(priority, VALID_PRIORITIES, "priority")

    analysis_payload = _get_analysis_payload(
        run_id=run_id,
        report_path=report_path,
        project_root=project_root,
        analyses=analyses,
        failed_cases=failed_cases,
        contexts=contexts,
        statuses=statuses,
        keyword=keyword,
        classname=classname,
        case_name=case_name,
        limit=limit_value,
        project=project,
        module=module,
        version=version,
    )

    if analysis_payload.get("status") == "not_found":
        return {
            "status": "not_found",
            "run_id": analysis_payload.get("run_id", run_id or ""),
            "report_path": analysis_payload.get("report_path", ""),
            "project": project or analysis_payload.get("project", ""),
            "module": module or analysis_payload.get("module", ""),
            "version": version or analysis_payload.get("version", ""),
            "bug_count": 0,
            "bug_reports": [],
            "message": analysis_payload.get("message", "JUnit report not found"),
        }

    normalized_analyses = list(analysis_payload.get("analyses", []))
    candidates = [
        analysis
        for analysis in normalized_analyses
        if include_non_bug_candidates or analysis.get("should_create_bug")
    ][:limit_value]

    bug_reports = [
        _bug_report(
            index=index,
            analysis=analysis,
            run_id=str(analysis_payload.get("run_id", run_id or "")),
            report_path=str(analysis_payload.get("report_path", report_path or "")),
            project=project or analysis_payload.get("project", ""),
            module=module or analysis_payload.get("module", ""),
            version=version or analysis_payload.get("version", ""),
            environment=environment,
            reporter=reporter,
            severity_override=severity_override,
            priority_override=priority_override,
            include_markdown=include_markdown,
        )
        for index, analysis in enumerate(candidates, start=1)
    ]

    return {
        "status": "generated" if bug_reports else "no_bug_candidates",
        "run_id": analysis_payload.get("run_id", run_id or ""),
        "report_path": analysis_payload.get("report_path", report_path or ""),
        "project": project or analysis_payload.get("project", ""),
        "module": module or analysis_payload.get("module", ""),
        "version": version or analysis_payload.get("version", ""),
        "environment": environment or "test",
        "reporter": reporter or "QualityPilot",
        "source_analysis_status": analysis_payload.get("status", ""),
        "analysis_count": len(normalized_analyses),
        "bug_count": len(bug_reports),
        "bug_reports": bug_reports,
        "markdown": _combined_markdown(bug_reports) if include_markdown else "",
        "recommended_next_actions": _recommended_next_actions(bug_reports),
    }


def _get_analysis_payload(
    run_id: Optional[str],
    report_path: Optional[str],
    project_root: str,
    analyses: Optional[Sequence[Dict[str, Any]]],
    failed_cases: Optional[Sequence[Dict[str, Any]]],
    contexts: Optional[Sequence[Dict[str, Any]]],
    statuses: Optional[Sequence[str]],
    keyword: Optional[str],
    classname: Optional[str],
    case_name: Optional[str],
    limit: int,
    project: Optional[str],
    module: Optional[str],
    version: Optional[str],
) -> Dict[str, Any]:
    if analyses is not None:
        return {
            "status": "analyzed" if analyses else "no_cases",
            "run_id": run_id or "",
            "report_path": report_path or "",
            "project": project or "",
            "module": module or "",
            "version": version or "",
            "analyses": list(analyses)[:limit],
        }

    return analyze_failure_payload(
        run_id=run_id,
        report_path=report_path,
        project_root=project_root,
        failed_cases=failed_cases,
        contexts=contexts,
        statuses=statuses,
        keyword=keyword,
        classname=classname,
        case_name=case_name,
        limit=limit,
        project=project,
        module=module,
        version=version,
        analysis_depth="standard",
    )


def _bug_report(
    index: int,
    analysis: Dict[str, Any],
    run_id: str,
    report_path: str,
    project: str,
    module: str,
    version: str,
    environment: str,
    reporter: str,
    severity_override: Optional[str],
    priority_override: Optional[str],
    include_markdown: bool,
) -> Dict[str, Any]:
    severity = severity_override or _infer_severity(analysis)
    priority = priority_override or _infer_priority(severity, analysis)
    title = _title(analysis, module)
    bug = {
        "bug_id": f"BUG-{index:03d}",
        "status": "draft",
        "title": title,
        "severity": severity,
        "priority": priority,
        "project": project,
        "module": module,
        "version": version,
        "environment": environment or "test",
        "reporter": reporter or "QualityPilot",
        "source": {
            "run_id": run_id,
            "report_path": report_path,
            "analysis_id": analysis.get("analysis_id", ""),
            "case_id": analysis.get("case_id", ""),
            "classname": analysis.get("classname", ""),
            "case_name": analysis.get("name", ""),
        },
        "summary": _summary(analysis),
        "preconditions": _preconditions(environment),
        "reproduction_steps": _reproduction_steps(analysis),
        "expected_result": _expected_result(analysis),
        "actual_result": _actual_result(analysis),
        "evidence": analysis.get("evidence", []),
        "related_contexts": analysis.get("related_contexts", []),
        "suggested_fix": analysis.get("suggested_fix", []),
        "labels": _labels(analysis, module),
        "attachments": _attachments(report_path),
    }
    bug["markdown"] = _bug_markdown(bug) if include_markdown else ""
    return bug


def _normalize_limit(limit: int) -> int:
    try:
        value = int(limit)
    except (TypeError, ValueError):
        value = 5
    return min(max(value, 1), 20)


def _normalize_optional_enum(
    value: Optional[str],
    allowed: Sequence[str],
    field_name: str,
) -> Optional[str]:
    if value is None or not str(value).strip():
        return None
    normalized = str(value).strip()
    if normalized not in allowed:
        available = ", ".join(allowed)
        raise ValueError(f"Unsupported {field_name}: {normalized}. Available: {available}")
    return normalized


def _infer_severity(analysis: Dict[str, Any]) -> str:
    root_type = str(analysis.get("root_cause_type", ""))
    signature = str(analysis.get("failure_signature", "")).lower()
    if "payment" in signature or "data loss" in signature:
        return "critical"
    if root_type == "product_bug_or_contract_mismatch":
        return "high"
    if root_type == "environment_or_performance":
        return "medium"
    if root_type == "needs_manual_triage":
        return "medium"
    return "low"


def _infer_priority(severity: str, analysis: Dict[str, Any]) -> str:
    confidence = float(analysis.get("confidence", 0.0) or 0.0)
    if severity == "critical":
        return "P0"
    if severity == "high":
        return "P1" if confidence >= 0.65 else "P2"
    if severity == "medium":
        return "P2"
    return "P3"


def _title(analysis: Dict[str, Any], module: str) -> str:
    module_prefix = f"[{module}] " if module else ""
    name = analysis.get("name") or analysis.get("case_id") or "failed case"
    signature = analysis.get("failure_signature") or analysis.get("likely_root_cause", "")
    return f"{module_prefix}{name} failed: {signature}"[:160]


def _summary(analysis: Dict[str, Any]) -> str:
    cause = analysis.get("likely_root_cause") or "Failure analysis indicates a product or contract mismatch."
    confidence = analysis.get("confidence", 0.0)
    return f"{cause} Confidence: {confidence}."


def _preconditions(environment: str) -> List[str]:
    return [
        f"Test environment is {environment or 'test'}.",
        "The target service and required test data are available.",
        "The same automation scenario can be rerun with report artifacts enabled.",
    ]


def _reproduction_steps(analysis: Dict[str, Any]) -> List[str]:
    steps = analysis.get("reproduction_steps") or []
    if steps:
        return list(steps)
    classname = analysis.get("classname", "")
    name = analysis.get("name", "")
    return [
        f"Run testcase {classname}.{name}".strip("."),
        "Capture request, response, logs, and generated report artifacts.",
        "Compare the actual result with the expected API or requirement contract.",
    ]


def _expected_result(analysis: Dict[str, Any]) -> str:
    contexts = analysis.get("related_contexts", [])
    if contexts:
        source = contexts[0].get("title") or contexts[0].get("source_id") or "related RAG context"
        return f"Behavior should match the expected contract described by {source}."
    return "Behavior should match the requirement, API contract, and test case expected result."


def _actual_result(analysis: Dict[str, Any]) -> str:
    signature = analysis.get("failure_signature") or analysis.get("likely_root_cause", "")
    return str(signature or "The automation case failed.")[:500]


def _labels(analysis: Dict[str, Any], module: str) -> List[str]:
    labels = ["qualitypilot", "automated-test", "bug-candidate"]
    root_type = analysis.get("root_cause_type")
    category = analysis.get("failure_category")
    if root_type:
        labels.append(str(root_type))
    if category:
        labels.append(str(category))
    if module:
        labels.append(str(module))
    return labels


def _attachments(report_path: str) -> List[Dict[str, str]]:
    if not report_path:
        return []
    return [
        {
            "type": "junit_xml",
            "path": report_path,
            "description": "JUnit XML report used for failure analysis.",
        }
    ]


def _bug_markdown(bug: Dict[str, Any]) -> str:
    lines = [
        f"# {bug['title']}",
        "",
        f"- Severity: {bug['severity']}",
        f"- Priority: {bug['priority']}",
        f"- Project: {bug.get('project', '')}",
        f"- Module: {bug.get('module', '')}",
        f"- Version: {bug.get('version', '')}",
        f"- Environment: {bug.get('environment', '')}",
        "",
        "## Summary",
        bug.get("summary", ""),
        "",
        "## Preconditions",
    ]
    lines.extend(f"- {item}" for item in bug.get("preconditions", []))
    lines.extend(["", "## Steps To Reproduce"])
    lines.extend(f"{index}. {step}" for index, step in enumerate(bug.get("reproduction_steps", []), start=1))
    lines.extend(["", "## Expected Result", bug.get("expected_result", "")])
    lines.extend(["", "## Actual Result", bug.get("actual_result", "")])
    lines.extend(["", "## Evidence"])
    evidence = bug.get("evidence", [])
    if evidence:
        lines.extend(f"- {item.get('type', 'evidence')}: {item.get('value', '')}" for item in evidence)
    else:
        lines.append("- No structured evidence was provided.")
    lines.extend(["", "## Suggested Fix"])
    fixes = bug.get("suggested_fix", [])
    if fixes:
        lines.extend(f"- {item}" for item in fixes)
    else:
        lines.append("- Confirm reproducibility and compare with requirement/API documentation.")
    return "\n".join(lines).strip()


def _combined_markdown(bug_reports: Sequence[Dict[str, Any]]) -> str:
    return "\n\n---\n\n".join(
        bug.get("markdown", "")
        for bug in bug_reports
        if bug.get("markdown")
    )


def _recommended_next_actions(bug_reports: Sequence[Dict[str, Any]]) -> List[str]:
    if not bug_reports:
        return [
            "Confirm whether failures are product defects, test script issues, or environment issues.",
            "Rerun failed cases after collecting more RAG context and logs.",
        ]
    return [
        "Review generated bug drafts before filing them to an issue tracker.",
        "Attach JUnit XML, Allure results, request/response logs, and related requirement/API references.",
        "Rerun the failed scenario to confirm reproducibility.",
    ]


def register_tool(protocol_handler, settings: Optional[Settings] = None) -> None:
    """Register generate_bug_report tool with the protocol handler."""
    protocol_handler.register_tool(
        name=TOOL_NAME,
        description=TOOL_DESCRIPTION,
        input_schema=TOOL_INPUT_SCHEMA,
        handler=generate_bug_report_handler,
    )
    logger.info("Registered MCP tool: %s", TOOL_NAME)
