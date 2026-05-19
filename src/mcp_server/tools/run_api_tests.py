"""MCP Tool: run_api_tests.

This tool runs API-oriented test scenarios and emits structured execution
results plus report paths. It supports a stable execution-plan mode and an
optional pytest mode for built-in demo automation scenarios.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import uuid

from mcp import types

from src.core.settings import Settings
from src.observability.dashboard.services.api_execution_adapter import (
    ApiExecutionAdapter,
)
from src.observability.dashboard.services.automation_scenario_service import (
    get_pytest_targets,
)
from src.observability.dashboard.services.execution_history_service import (
    append_execution_history_record,
    build_execution_history_record,
)
from src.observability.dashboard.services.execution_plan_service import (
    build_execution_plan,
    get_execution_preset_steps,
)
from src.observability.dashboard.services.execution_result_report_service import (
    write_execution_result_allure_results,
    write_execution_result_junit_xml,
)
from src.observability.dashboard.services.test_report_service import parse_junit_xml
from scripts.run_automation_suite import build_pytest_args

logger = logging.getLogger(__name__)


TOOL_NAME = "run_api_tests"
TOOL_DESCRIPTION = """Run API automation scenarios and return structured results.

Use this after generate_test_cases. In plan mode it executes parsed API steps
through the API adapter and writes JUnit/Allure-compatible reports. In pytest
mode it runs the built-in API pytest automation scenario.
"""

API_SCENARIO_IDS = ["api_login", "api_file_upload"]
EXECUTION_MODES = ["plan", "pytest"]

TOOL_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "scenario_id": {
            "type": "string",
            "description": "Built-in API scenario id.",
            "enum": API_SCENARIO_IDS,
            "default": "api_login",
        },
        "base_url": {
            "type": "string",
            "description": "Base URL for real API adapter execution.",
            "default": "http://127.0.0.1:8000",
        },
        "dry_run": {
            "type": "boolean",
            "description": "Preview execution without network requests in plan mode.",
            "default": True,
        },
        "execution_mode": {
            "type": "string",
            "description": "Execution backend: plan adapter or pytest runner.",
            "enum": EXECUTION_MODES,
            "default": "plan",
        },
        "step_text": {
            "type": "string",
            "description": "Optional natural-language/API steps. Overrides built-in scenario steps in plan mode.",
        },
        "junitxml": {
            "type": "string",
            "description": "Optional JUnit XML output path.",
        },
        "allure_results": {
            "type": "string",
            "description": "Optional Allure results output directory.",
        },
        "record_history": {
            "type": "boolean",
            "description": "Append execution result to local execution history.",
            "default": False,
        },
    },
}


async def run_api_tests_handler(
    scenario_id: str = "api_login",
    base_url: str = "http://127.0.0.1:8000",
    dry_run: bool = True,
    execution_mode: str = "plan",
    step_text: Optional[str] = None,
    junitxml: Optional[str] = None,
    allure_results: Optional[str] = None,
    record_history: bool = False,
) -> types.CallToolResult:
    """Run API tests and return JSON for MCP clients."""
    try:
        payload = run_api_tests_payload(
            scenario_id=scenario_id,
            base_url=base_url,
            dry_run=dry_run,
            execution_mode=execution_mode,
            step_text=step_text,
            junitxml=junitxml,
            allure_results=allure_results,
            record_history=record_history,
        )
        return types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text=json.dumps(payload, ensure_ascii=False, indent=2),
                )
            ],
            isError=False,
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
        logger.exception("run_api_tests handler error")
        return types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text=json.dumps(
                        {"error": "failed to run API tests"},
                        ensure_ascii=False,
                        indent=2,
                    ),
                )
            ],
            isError=True,
        )


def run_api_tests_payload(
    scenario_id: str = "api_login",
    base_url: str = "http://127.0.0.1:8000",
    dry_run: bool = True,
    execution_mode: str = "plan",
    step_text: Optional[str] = None,
    junitxml: Optional[str] = None,
    allure_results: Optional[str] = None,
    record_history: bool = False,
) -> Dict[str, Any]:
    """Build run_api_tests payload and write reports."""
    scenario_id = _validate_api_scenario(scenario_id)
    execution_mode = _validate_execution_mode(execution_mode)
    run_id = f"api-{scenario_id}-{uuid.uuid4().hex[:8]}"

    if execution_mode == "pytest":
        return _run_pytest_mode(
            run_id=run_id,
            scenario_id=scenario_id,
            dry_run=dry_run,
            junitxml=junitxml,
            allure_results=allure_results,
        )

    return _run_plan_mode(
        run_id=run_id,
        scenario_id=scenario_id,
        base_url=base_url,
        dry_run=bool(dry_run),
        step_text=step_text,
        junitxml=junitxml,
        allure_results=allure_results,
        record_history=record_history,
    )


def _run_plan_mode(
    run_id: str,
    scenario_id: str,
    base_url: str,
    dry_run: bool,
    step_text: Optional[str],
    junitxml: Optional[str],
    allure_results: Optional[str],
    record_history: bool,
) -> Dict[str, Any]:
    steps = (step_text or get_execution_preset_steps(scenario_id)).strip()
    if not steps:
        raise ValueError(f"No API execution steps found for scenario_id={scenario_id}")

    plan = build_execution_plan(scenario_id, steps)
    if not any(step.action == "call_api" for step in plan.steps):
        raise ValueError("run_api_tests only supports API execution plans")

    result = ApiExecutionAdapter(base_url=base_url).run(plan, dry_run=dry_run)
    report_paths = _write_plan_reports(
        result=result,
        run_id=run_id,
        junitxml=junitxml,
        allure_results=allure_results,
    )

    if record_history:
        history_path = append_execution_history_record(
            build_execution_history_record(
                result,
                scenario_id=scenario_id,
                trigger="mcp",
                report_paths=report_paths,
            )
        )
        report_paths["history"] = str(history_path)

    return {
        "run_id": run_id,
        "scenario_id": scenario_id,
        "execution_mode": "plan",
        "adapter": result.adapter,
        "base_url": result.base_url,
        "dry_run": result.dry_run,
        "status": result.status,
        "summary": {
            "total": result.total_steps,
            "passed": result.passed_steps,
            "failed": result.failed_steps,
            "skipped": result.skipped_steps,
            "dry_run": result.dry_run_steps,
        },
        "steps": [_step_result_payload(step) for step in result.step_results],
        "failure_reason": result.failure_reason,
        "logs": result.logs,
        "report_paths": report_paths,
    }


def _run_pytest_mode(
    run_id: str,
    scenario_id: str,
    dry_run: bool,
    junitxml: Optional[str],
    allure_results: Optional[str],
) -> Dict[str, Any]:
    report_paths = _default_report_paths(run_id, junitxml, allure_results)
    pytest_args = build_pytest_args(
        scenario_id=scenario_id,
        junitxml_path=report_paths["junitxml"],
        allure_results_path=report_paths.get("allure_results", ""),
        use_allure=bool(report_paths.get("allure_results")),
    )

    if dry_run:
        return {
            "run_id": run_id,
            "scenario_id": scenario_id,
            "execution_mode": "pytest",
            "dry_run": True,
            "status": "dry_run",
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "dry_run": len(get_pytest_targets(scenario_id)),
            },
            "pytest_args": pytest_args,
            "report_paths": report_paths,
        }

    exit_code = _run_pytest(pytest_args)
    summary = parse_junit_xml(report_paths["junitxml"])
    status = "passed" if exit_code == 0 and summary.failed == 0 else "failed"
    return {
        "run_id": run_id,
        "scenario_id": scenario_id,
        "execution_mode": "pytest",
        "dry_run": False,
        "status": status,
        "summary": {
            "total": summary.total,
            "passed": summary.passed,
            "failed": summary.failed,
            "skipped": summary.skipped,
            "dry_run": 0,
        },
        "pytest_exit_code": exit_code,
        "pytest_args": pytest_args,
        "report_paths": report_paths,
    }


def _write_plan_reports(
    result,
    run_id: str,
    junitxml: Optional[str],
    allure_results: Optional[str],
) -> Dict[str, str]:
    report_paths = _default_report_paths(run_id, junitxml, allure_results)
    junit_path = write_execution_result_junit_xml(result, report_paths["junitxml"])
    report_paths["junitxml"] = str(junit_path)

    if report_paths.get("allure_results"):
        allure_path = write_execution_result_allure_results(result, report_paths["allure_results"])
        report_paths["allure_result"] = str(allure_path)
    return report_paths


def _default_report_paths(
    run_id: str,
    junitxml: Optional[str],
    allure_results: Optional[str],
) -> Dict[str, str]:
    base_dir = Path("reports") / "mcp-api-tests" / run_id
    paths = {
        "junitxml": str(Path(junitxml) if junitxml else base_dir / "junit.xml"),
    }
    if allure_results:
        paths["allure_results"] = str(Path(allure_results))
    return paths


def _step_result_payload(step) -> Dict[str, Any]:
    return {
        "index": step.index,
        "action": step.action,
        "status": step.status,
        "message": step.message,
        "request_method": step.request_method,
        "request_url": step.request_url,
        "response_status": step.response_status,
        "response_preview": step.response_preview,
        "elapsed_ms": round(float(step.elapsed_ms), 2),
    }


def _validate_api_scenario(scenario_id: str) -> str:
    scenario_id = (scenario_id or "api_login").strip()
    if scenario_id not in API_SCENARIO_IDS:
        available = ", ".join(API_SCENARIO_IDS)
        raise ValueError(f"Unsupported API scenario_id: {scenario_id}. Available: {available}")
    return scenario_id


def _validate_execution_mode(execution_mode: str) -> str:
    execution_mode = (execution_mode or "plan").strip().lower()
    if execution_mode not in EXECUTION_MODES:
        available = ", ".join(EXECUTION_MODES)
        raise ValueError(f"Unsupported execution_mode: {execution_mode}. Available: {available}")
    return execution_mode


def _run_pytest(pytest_args: list[str]) -> int:
    import pytest

    return int(pytest.main(pytest_args))


def register_tool(protocol_handler, settings: Optional[Settings] = None) -> None:
    """Register run_api_tests tool with the protocol handler."""
    protocol_handler.register_tool(
        name=TOOL_NAME,
        description=TOOL_DESCRIPTION,
        input_schema=TOOL_INPUT_SCHEMA,
        handler=run_api_tests_handler,
    )
    logger.info("Registered MCP tool: %s", TOOL_NAME)
