"""MCP Tool: analyze_failure.

This tool turns failed test cases into structured failure analysis. It is
rule-based by default so the testing workflow works without an external LLM key,
while still accepting RAG contexts from retrieve_test_context.
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from typing import Any, Dict, List, Optional, Sequence

from mcp import types

from src.core.settings import Settings
from src.mcp_server.tools.query_failed_cases import query_failed_cases_payload

logger = logging.getLogger(__name__)


TOOL_NAME = "analyze_failure"
TOOL_DESCRIPTION = """Analyze failed test cases and produce root-cause hints.

Use this after query_failed_cases. The tool combines failed-case evidence with
optional RAG contexts and returns likely cause, confidence, evidence, suggested
fixes, and bug-report candidates.
"""

VALID_STATUSES = ("failure", "error", "skipped")

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
        "failed_cases": {
            "type": "array",
            "description": "Optional cases from query_failed_cases. If provided, report parsing is skipped.",
            "items": {"type": "object"},
        },
        "contexts": {
            "type": "array",
            "description": "Optional RAG contexts from retrieve_test_context.",
            "items": {"type": "object"},
        },
        "statuses": {
            "type": "array",
            "description": "Statuses to query when failed_cases is not provided.",
            "items": {"type": "string", "enum": list(VALID_STATUSES)},
        },
        "keyword": {
            "type": "string",
            "description": "Optional keyword filter used when querying failed cases from a report.",
        },
        "classname": {
            "type": "string",
            "description": "Optional classname filter used when querying failed cases from a report.",
        },
        "case_name": {
            "type": "string",
            "description": "Optional testcase name filter used when querying failed cases from a report.",
        },
        "limit": {
            "type": "integer",
            "description": "Maximum number of failed cases to analyze.",
            "default": 10,
            "minimum": 1,
            "maximum": 50,
        },
        "project": {
            "type": "string",
            "description": "Optional project metadata for analysis output.",
        },
        "module": {
            "type": "string",
            "description": "Optional module metadata for analysis output.",
        },
        "version": {
            "type": "string",
            "description": "Optional version metadata for analysis output.",
        },
        "analysis_depth": {
            "type": "string",
            "description": "Analysis detail level.",
            "enum": ["quick", "standard"],
            "default": "standard",
        },
    },
}


async def analyze_failure_handler(
    run_id: Optional[str] = None,
    report_path: Optional[str] = None,
    project_root: str = ".",
    failed_cases: Optional[List[Dict[str, Any]]] = None,
    contexts: Optional[List[Dict[str, Any]]] = None,
    statuses: Optional[List[str]] = None,
    keyword: Optional[str] = None,
    classname: Optional[str] = None,
    case_name: Optional[str] = None,
    limit: int = 10,
    project: Optional[str] = None,
    module: Optional[str] = None,
    version: Optional[str] = None,
    analysis_depth: str = "standard",
) -> types.CallToolResult:
    """Analyze failed cases and return JSON for MCP clients."""
    try:
        payload = analyze_failure_payload(
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
            analysis_depth=analysis_depth,
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
        logger.exception("analyze_failure handler error")
        return types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text=json.dumps(
                        {"error": "failed to analyze failure"},
                        ensure_ascii=False,
                        indent=2,
                    ),
                )
            ],
            isError=True,
        )


def analyze_failure_payload(
    run_id: Optional[str] = None,
    report_path: Optional[str] = None,
    project_root: str = ".",
    failed_cases: Optional[Sequence[Dict[str, Any]]] = None,
    contexts: Optional[Sequence[Dict[str, Any]]] = None,
    statuses: Optional[Sequence[str]] = None,
    keyword: Optional[str] = None,
    classname: Optional[str] = None,
    case_name: Optional[str] = None,
    limit: int = 10,
    project: Optional[str] = None,
    module: Optional[str] = None,
    version: Optional[str] = None,
    analysis_depth: str = "standard",
) -> Dict[str, Any]:
    """Build structured failure analysis payload."""
    limit_value = _normalize_limit(limit)
    depth = _normalize_analysis_depth(analysis_depth)
    context_items = _normalize_contexts(contexts)

    if failed_cases is not None:
        case_query = {
            "run_id": run_id or "",
            "report_path": report_path or "",
            "status": "cases_found" if failed_cases else "no_cases",
            "report_status": "",
            "summary": {},
            "case_count": len(failed_cases),
            "returned_count": min(len(failed_cases), limit_value),
            "cases": list(failed_cases)[:limit_value],
        }
    else:
        case_query = query_failed_cases_payload(
            run_id=run_id,
            report_path=report_path,
            project_root=project_root,
            statuses=statuses,
            keyword=keyword,
            classname=classname,
            case_name=case_name,
            limit=limit_value,
            include_details=True,
        )

    if case_query.get("status") == "not_found":
        return {
            "status": "not_found",
            "run_id": case_query.get("run_id", run_id or ""),
            "report_path": case_query.get("report_path", ""),
            "analysis_depth": depth,
            "project": project or "",
            "module": module or "",
            "version": version or "",
            "case_count": 0,
            "analyses": [],
            "summary": _empty_summary(),
            "message": case_query.get("message", "JUnit report not found"),
        }

    cases = _normalize_cases(case_query.get("cases", []), limit=limit_value)
    analyses = [
        _analyze_case(
            index=index,
            case=case,
            contexts=context_items,
            analysis_depth=depth,
        )
        for index, case in enumerate(cases, start=1)
    ]

    return {
        "status": "analyzed" if analyses else "no_cases",
        "run_id": case_query.get("run_id", run_id or ""),
        "report_path": case_query.get("report_path", report_path or ""),
        "analysis_depth": depth,
        "project": project or "",
        "module": module or "",
        "version": version or "",
        "report_status": case_query.get("report_status", ""),
        "report_summary": case_query.get("summary", {}),
        "context_count": len(context_items),
        "case_count": len(analyses),
        "analyses": analyses,
        "summary": _build_summary(analyses),
        "bug_report_candidates": _bug_report_candidates(analyses),
        "recommended_next_tools": _recommended_next_tools(analyses),
    }


def _normalize_limit(limit: int) -> int:
    try:
        value = int(limit)
    except (TypeError, ValueError):
        value = 10
    return min(max(value, 1), 50)


def _normalize_analysis_depth(analysis_depth: str) -> str:
    value = (analysis_depth or "standard").strip().lower()
    if value not in {"quick", "standard"}:
        raise ValueError("analysis_depth must be quick or standard")
    return value


def _normalize_contexts(contexts: Optional[Sequence[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    if not contexts:
        return []
    normalized = []
    for index, context in enumerate(contexts, start=1):
        metadata = context.get("metadata") or {}
        normalized.append(
            {
                "context_id": context.get("chunk_id") or context.get("context_id") or f"CTX-{index:03d}",
                "source_id": context.get("source_id") or metadata.get("source_id", ""),
                "source_type": context.get("source_type") or metadata.get("source_type", ""),
                "title": context.get("title") or metadata.get("title", ""),
                "content": context.get("content") or context.get("text", ""),
                "score": context.get("score", 0.0),
                "metadata": metadata,
            }
        )
    return normalized


def _normalize_cases(cases: Sequence[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    normalized = []
    for index, case in enumerate(cases[:limit], start=1):
        normalized.append(
            {
                "case_id": case.get("case_id") or f"FC-{index:03d}",
                "classname": case.get("classname", ""),
                "name": case.get("name", ""),
                "status": case.get("status", ""),
                "message": case.get("message", ""),
                "details": case.get("details", ""),
                "duration_seconds": case.get("duration_seconds", 0.0),
                "failure_category": case.get("failure_category", ""),
                "failure_signature": case.get("failure_signature", ""),
            }
        )
    return normalized


def _analyze_case(
    index: int,
    case: Dict[str, Any],
    contexts: Sequence[Dict[str, Any]],
    analysis_depth: str,
) -> Dict[str, Any]:
    text = _case_text(case)
    root = _infer_root_cause(text=text, status=str(case.get("status", "")))
    related_contexts = _related_contexts(case, contexts)
    evidence = _build_evidence(case, related_contexts)
    suggested_fix = _suggested_fix(root["root_cause_type"], related_contexts)
    reproduction_steps = _reproduction_steps(case)

    analysis = {
        "analysis_id": f"FA-{index:03d}",
        "case_id": case.get("case_id") or f"FC-{index:03d}",
        "classname": case.get("classname", ""),
        "name": case.get("name", ""),
        "status": case.get("status", ""),
        "failure_category": case.get("failure_category") or root["failure_category"],
        "failure_signature": case.get("failure_signature") or _failure_signature(case),
        "root_cause_type": root["root_cause_type"],
        "likely_root_cause": root["likely_root_cause"],
        "confidence": root["confidence"],
        "evidence": evidence,
        "suggested_fix": suggested_fix,
        "next_action": _next_action(root["root_cause_type"]),
        "should_create_bug": _should_create_bug(root["root_cause_type"]),
        "related_contexts": related_contexts,
    }

    if analysis_depth == "standard":
        analysis["reproduction_steps"] = reproduction_steps
        analysis["triage_notes"] = _triage_notes(root["root_cause_type"], related_contexts)

    return analysis


def _case_text(case: Dict[str, Any]) -> str:
    return " ".join(
        str(case.get(key, ""))
        for key in ("classname", "name", "status", "message", "details", "failure_category")
    ).lower()


def _infer_root_cause(text: str, status: str) -> Dict[str, Any]:
    status_value = status.lower()
    if status_value == "skipped":
        return {
            "failure_category": "skipped",
            "root_cause_type": "not_executed",
            "likely_root_cause": "The case was skipped, so there is no executable failure evidence yet.",
            "confidence": 0.95,
        }

    if any(token in text for token in ("connection refused", "dns", "network", "no route", "host")):
        return {
            "failure_category": "environment_or_network",
            "root_cause_type": "environment_issue",
            "likely_root_cause": "The failure is likely caused by environment, service availability, or network connectivity.",
            "confidence": 0.82,
        }

    if any(token in text for token in ("timeout", "timed out", "read timeout")):
        return {
            "failure_category": "timeout",
            "root_cause_type": "environment_or_performance",
            "likely_root_cause": "The request or assertion timed out; check service latency, test timeout settings, and resource pressure.",
            "confidence": 0.72,
        }

    if any(token in text for token in ("fixture", "importerror", "modulenotfounderror", "nameerror", "typeerror")):
        return {
            "failure_category": "test_script_error",
            "root_cause_type": "test_script_issue",
            "likely_root_cause": "The failure points to a test script, dependency, or fixture problem rather than a product defect.",
            "confidence": 0.78,
        }

    if any(token in text for token in ("401", "403", "unauthorized", "forbidden", "token")):
        return {
            "failure_category": "auth_or_permission",
            "root_cause_type": "product_bug_or_contract_mismatch",
            "likely_root_cause": "Authentication or permission behavior differs from the expected API contract or test data setup.",
            "confidence": 0.7,
        }

    if any(token in text for token in ("jsondecodeerror", "invalid response", "content-type", "schema")):
        return {
            "failure_category": "response_format",
            "root_cause_type": "product_bug_or_contract_mismatch",
            "likely_root_cause": "The response format does not match the expected contract.",
            "confidence": 0.68,
        }

    if any(token in text for token in ("assert", "expected", "actual", "does not contain")):
        return {
            "failure_category": "assertion_mismatch",
            "root_cause_type": "product_bug_or_contract_mismatch",
            "likely_root_cause": "Actual behavior does not match the assertion; compare product behavior with requirement and API documentation.",
            "confidence": 0.66,
        }

    if status_value == "error":
        return {
            "failure_category": "test_error",
            "root_cause_type": "needs_manual_triage",
            "likely_root_cause": "The test raised an error, but current evidence is insufficient to determine whether it is product or script related.",
            "confidence": 0.5,
        }

    return {
        "failure_category": "unknown",
        "root_cause_type": "needs_manual_triage",
        "likely_root_cause": "Current failure evidence is not enough for a confident classification.",
        "confidence": 0.45,
    }


def _related_contexts(
    case: Dict[str, Any],
    contexts: Sequence[Dict[str, Any]],
    max_items: int = 3,
) -> List[Dict[str, Any]]:
    if not contexts:
        return []

    case_tokens = _significant_tokens(_case_text(case))
    scored_contexts = []
    for context in contexts:
        content = " ".join(
            str(context.get(key, ""))
            for key in ("source_id", "source_type", "title", "content")
        ).lower()
        overlap = len(case_tokens.intersection(_significant_tokens(content)))
        if overlap <= 0:
            continue
        scored_contexts.append((overlap, context))

    scored_contexts.sort(key=lambda item: item[0], reverse=True)
    return [
        {
            "context_id": context.get("context_id", ""),
            "source_id": context.get("source_id", ""),
            "source_type": context.get("source_type", ""),
            "title": context.get("title", ""),
            "score": context.get("score", 0.0),
            "matched_terms": score,
        }
        for score, context in scored_contexts[:max_items]
    ]


def _significant_tokens(text: str) -> set[str]:
    tokens = []
    current = []
    for char in text.lower():
        if char.isalnum() or char in {"_", "-"}:
            current.append(char)
        elif current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    return {token for token in tokens if len(token) >= 4}


def _build_evidence(case: Dict[str, Any], related_contexts: Sequence[Dict[str, Any]]) -> List[Dict[str, str]]:
    evidence = []
    message = str(case.get("message", "")).strip()
    if message:
        evidence.append({"type": "junit_message", "value": message[:300]})

    signature = case.get("failure_signature") or _failure_signature(case)
    if signature:
        evidence.append({"type": "failure_signature", "value": str(signature)[:300]})

    details = _first_non_empty_line(str(case.get("details", "")))
    if details and details != message:
        evidence.append({"type": "junit_details", "value": details[:300]})

    for context in related_contexts:
        title = context.get("title") or context.get("source_id") or context.get("context_id")
        evidence.append({"type": "rag_context", "value": str(title)[:300]})

    return evidence


def _suggested_fix(root_cause_type: str, related_contexts: Sequence[Dict[str, Any]]) -> List[str]:
    if root_cause_type == "environment_issue":
        return [
            "Check base_url, service process, network route, and test environment health.",
            "Rerun the same case after confirming the target API is reachable.",
        ]
    if root_cause_type == "environment_or_performance":
        return [
            "Compare response time with SLA and inspect backend logs around the failed timestamp.",
            "Increase timeout only after proving the service latency is expected.",
        ]
    if root_cause_type == "test_script_issue":
        return [
            "Fix test dependency, fixture, or assertion setup before filing a product bug.",
            "Run the failed test locally with verbose logs to confirm the script path.",
        ]
    if root_cause_type == "product_bug_or_contract_mismatch":
        fixes = [
            "Compare actual response with requirement/API documentation.",
            "Confirm test data and authentication state, then rerun to check reproducibility.",
        ]
        if related_contexts:
            fixes.append("Use the related RAG context as expected-behavior evidence in the bug report.")
        return fixes
    if root_cause_type == "not_executed":
        return [
            "Find why the case was skipped and decide whether it should be enabled for this scenario.",
        ]
    return [
        "Collect response body, request parameters, server logs, and related requirement context for manual triage.",
    ]


def _next_action(root_cause_type: str) -> str:
    if root_cause_type in {"product_bug_or_contract_mismatch", "environment_or_performance"}:
        return "confirm_reproducibility_then_generate_bug_report"
    if root_cause_type == "environment_issue":
        return "fix_environment_then_rerun"
    if root_cause_type == "test_script_issue":
        return "fix_test_script_then_rerun"
    if root_cause_type == "not_executed":
        return "review_skip_reason"
    return "collect_more_evidence"


def _should_create_bug(root_cause_type: str) -> bool:
    return root_cause_type in {
        "product_bug_or_contract_mismatch",
        "environment_or_performance",
    }


def _reproduction_steps(case: Dict[str, Any]) -> List[str]:
    classname = case.get("classname", "")
    name = case.get("name", "")
    return [
        f"Run testcase {classname}.{name}".strip("."),
        "Capture request, response, logs, and generated report artifacts.",
        "Compare actual result with expected behavior from RAG context or test case design.",
    ]


def _triage_notes(root_cause_type: str, related_contexts: Sequence[Dict[str, Any]]) -> List[str]:
    notes = []
    if related_contexts:
        notes.append("Related RAG contexts are available and should be cited during triage.")
    else:
        notes.append("No RAG context was supplied; retrieve requirement/API/log context before final bug filing.")
    if root_cause_type == "product_bug_or_contract_mismatch":
        notes.append("Do not file the bug until test data and expected contract are confirmed.")
    if root_cause_type == "test_script_issue":
        notes.append("This should be fixed in automation code before product-side escalation.")
    return notes


def _failure_signature(case: Dict[str, Any]) -> str:
    message = str(case.get("message", "")).strip()
    if message:
        return message[:200]
    details = _first_non_empty_line(str(case.get("details", "")))
    if details:
        return details[:200]
    return f"{case.get('classname', '')}.{case.get('name', '')}".strip(".")[:200]


def _first_non_empty_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _build_summary(analyses: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    if not analyses:
        return _empty_summary()
    distribution = Counter(item.get("root_cause_type", "unknown") for item in analyses)
    return {
        "total": len(analyses),
        "root_cause_distribution": dict(distribution),
        "bug_candidate_count": sum(1 for item in analyses if item.get("should_create_bug")),
        "high_confidence_count": sum(1 for item in analyses if float(item.get("confidence", 0)) >= 0.75),
    }


def _empty_summary() -> Dict[str, Any]:
    return {
        "total": 0,
        "root_cause_distribution": {},
        "bug_candidate_count": 0,
        "high_confidence_count": 0,
    }


def _bug_report_candidates(analyses: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    candidates = []
    for analysis in analyses:
        if not analysis.get("should_create_bug"):
            continue
        candidates.append(
            {
                "analysis_id": analysis.get("analysis_id", ""),
                "case_id": analysis.get("case_id", ""),
                "title": _bug_title(analysis),
                "root_cause_type": analysis.get("root_cause_type", ""),
                "confidence": analysis.get("confidence", 0.0),
                "evidence_count": len(analysis.get("evidence", [])),
            }
        )
    return candidates


def _bug_title(analysis: Dict[str, Any]) -> str:
    name = analysis.get("name") or analysis.get("case_id") or "failed case"
    signature = analysis.get("failure_signature") or analysis.get("likely_root_cause", "")
    return f"{name} failed: {signature}"[:160]


def _recommended_next_tools(analyses: Sequence[Dict[str, Any]]) -> List[Dict[str, str]]:
    if not analyses:
        return []
    tools = [
        {
            "tool": "retrieve_test_context",
            "reason": "Retrieve requirement, API document, bug, and log context before final triage.",
        }
    ]
    if any(item.get("should_create_bug") for item in analyses):
        tools.append(
            {
                "tool": "generate_bug_report",
                "reason": "Convert confirmed bug candidates into a structured defect report.",
            }
        )
    return tools


def register_tool(protocol_handler, settings: Optional[Settings] = None) -> None:
    """Register analyze_failure tool with the protocol handler."""
    protocol_handler.register_tool(
        name=TOOL_NAME,
        description=TOOL_DESCRIPTION,
        input_schema=TOOL_INPUT_SCHEMA,
        handler=analyze_failure_handler,
    )
    logger.info("Registered MCP tool: %s", TOOL_NAME)
