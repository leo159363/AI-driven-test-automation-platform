"""Report writers for execution adapter results."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import time
import uuid
from xml.etree import ElementTree

from src.observability.dashboard.services.api_execution_adapter import (
    DRY_RUN,
    FAILED,
    PASSED,
    SKIPPED,
    ExecutionResult,
    ExecutionStepResult,
)


DEFAULT_EXECUTION_PLAN_JUNIT_PATH = Path("reports/execution-plan-junit.xml")
DEFAULT_EXECUTION_PLAN_ALLURE_RESULTS_DIR = Path("reports/execution-plan-allure-results")


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


def write_execution_result_allure_results(
    result: ExecutionResult,
    output_dir: str | Path = DEFAULT_EXECUTION_PLAN_ALLURE_RESULTS_DIR,
) -> Path:
    """Write an execution result as minimal Allure-compatible result JSON."""
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)

    result_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{result.adapter}:{result.plan_name}"))
    start_ms = int(time.time() * 1000)
    log_source = f"{result_uuid}-execution.log"
    (directory / log_source).write_text("\n".join(result.logs), encoding="utf-8")

    attachments = [
        {
            "name": "execution logs",
            "source": log_source,
            "type": "text/plain",
        }
    ]
    attachments.extend(_copy_artifact_attachments(result, directory, result_uuid))

    payload = {
        "uuid": result_uuid,
        "name": result.plan_name,
        "fullName": f"{result.adapter}.{_safe_suite_name(result.plan_name)}",
        "status": _allure_status(result.status),
        "stage": "finished",
        "statusDetails": {"message": result.failure_reason or ""},
        "steps": [_build_allure_step(step, start_ms) for step in result.step_results],
        "attachments": attachments,
        "parameters": [
            {"name": "adapter", "value": result.adapter},
            {"name": "base_url", "value": result.base_url},
            {"name": "dry_run", "value": str(result.dry_run).lower()},
        ],
        "labels": [
            {"name": "suite", "value": "execution_plan"},
            {"name": "adapter", "value": result.adapter},
        ],
        "start": start_ms,
        "stop": start_ms + int(_total_seconds(result) * 1000),
    }

    output_path = directory / f"{result_uuid}-result.json"
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


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


def _build_allure_step(step: ExecutionStepResult, suite_start_ms: int) -> dict[str, object]:
    elapsed_ms = int(step.elapsed_ms)
    started_at = suite_start_ms
    return {
        "name": f"step {step.index:02d} {step.action}",
        "status": _allure_status(step.status),
        "stage": "finished",
        "statusDetails": {"message": step.message},
        "parameters": _allure_step_parameters(step),
        "start": started_at,
        "stop": started_at + elapsed_ms,
    }


def _allure_step_parameters(step: ExecutionStepResult) -> list[dict[str, str]]:
    parameters = [{"name": "status", "value": step.status}]
    if step.request_method:
        parameters.append({"name": "method", "value": step.request_method})
    if step.request_url:
        parameters.append({"name": "url", "value": step.request_url})
    if step.response_status is not None:
        parameters.append({"name": "http_status", "value": str(step.response_status)})
    if step.response_preview:
        parameters.append({"name": "preview", "value": step.response_preview})
    return parameters


def _copy_artifact_attachments(
    result: ExecutionResult,
    directory: Path,
    result_uuid: str,
) -> list[dict[str, str]]:
    attachments: list[dict[str, str]] = []
    for artifact_name, artifact_path in result.artifacts.items():
        source_path = Path(artifact_path)
        if not source_path.exists() or not source_path.is_file():
            continue
        attachment_source = f"{result_uuid}-{source_path.name}"
        shutil.copy2(source_path, directory / attachment_source)
        attachments.append(
            {
                "name": artifact_name.replace("_", " "),
                "source": attachment_source,
                "type": _guess_attachment_type(source_path),
            }
        )
    return attachments


def _allure_status(status: str) -> str:
    if status == PASSED:
        return "passed"
    if status == FAILED:
        return "failed"
    if status in {SKIPPED, DRY_RUN}:
        return "skipped"
    return "broken"


def _guess_attachment_type(path: Path) -> str:
    if path.suffix.lower() == ".png":
        return "image/png"
    if path.suffix.lower() in {".jpg", ".jpeg"}:
        return "image/jpeg"
    return "text/plain"


def _total_seconds(result: ExecutionResult) -> float:
    return sum(step.elapsed_ms for step in result.step_results) / 1000


def _safe_suite_name(name: str) -> str:
    normalized = name.strip() or "execution_plan"
    return normalized.replace(" ", "_")
