"""Report writers for execution adapter results."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree

from src.observability.dashboard.services.api_execution_adapter import (
    DRY_RUN,
    FAILED,
    SKIPPED,
    ExecutionResult,
    ExecutionStepResult,
)


DEFAULT_EXECUTION_PLAN_JUNIT_PATH = Path("reports/execution-plan-junit.xml")


def write_execution_result_junit_xml(
    result: ExecutionResult,
    output_path: str | Path = DEFAULT_EXECUTION_PLAN_JUNIT_PATH,
) -> Path:
    """Write an execution result as JUnit XML and return the written path."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    suite = ElementTree.Element(
        "testsuite",
        {
            "name": _safe_suite_name(result.plan_name),
            "tests": str(result.total_steps),
            "failures": str(result.failed_steps),
            "errors": "0",
            "skipped": str(result.skipped_steps + result.dry_run_steps),
            "time": f"{_total_seconds(result):.3f}",
        },
    )
    suite.set("adapter", result.adapter)
    suite.set("base_url", result.base_url)
    suite.set("dry_run", str(result.dry_run).lower())

    for step in result.step_results:
        suite.append(_build_testcase(step, result))

    system_out = ElementTree.SubElement(suite, "system-out")
    system_out.text = "\n".join(result.logs)

    if result.failure_reason:
        system_err = ElementTree.SubElement(suite, "system-err")
        system_err.text = result.failure_reason

    tree = ElementTree.ElementTree(suite)
    ElementTree.indent(tree, space="  ")
    tree.write(path, encoding="utf-8", xml_declaration=True)
    return path


def _build_testcase(step: ExecutionStepResult, result: ExecutionResult) -> ElementTree.Element:
    testcase = ElementTree.Element(
        "testcase",
        {
            "classname": f"{result.adapter}.{_safe_suite_name(result.plan_name)}",
            "name": f"step_{step.index:02d}_{step.action}",
            "time": f"{step.elapsed_ms / 1000:.3f}",
        },
    )
    testcase.set("status", step.status)

    if step.request_method:
        testcase.set("method", step.request_method)
    if step.request_url:
        testcase.set("url", step.request_url)

    if step.status == FAILED:
        failure = ElementTree.SubElement(testcase, "failure", {"message": step.message})
        failure.text = _step_detail(step)
    elif step.status in {SKIPPED, DRY_RUN}:
        skipped = ElementTree.SubElement(testcase, "skipped", {"message": step.message})
        skipped.text = _step_detail(step)

    return testcase


def _step_detail(step: ExecutionStepResult) -> str:
    details = [
        f"status={step.status}",
        f"message={step.message}",
    ]
    if step.request_method:
        details.append(f"method={step.request_method}")
    if step.request_url:
        details.append(f"url={step.request_url}")
    if step.response_status is not None:
        details.append(f"http_status={step.response_status}")
    if step.response_preview:
        details.append(f"response={step.response_preview}")
    return "\n".join(details)


def _total_seconds(result: ExecutionResult) -> float:
    return sum(step.elapsed_ms for step in result.step_results) / 1000


def _safe_suite_name(name: str) -> str:
    normalized = name.strip() or "execution_plan"
    return normalized.replace(" ", "_")
