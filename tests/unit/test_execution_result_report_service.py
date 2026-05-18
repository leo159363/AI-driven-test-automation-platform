"""Unit tests for execution-result report writers."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree

from src.observability.dashboard.services.api_execution_adapter import (
    DRY_RUN,
    FAILED,
    PASSED,
    SKIPPED,
    ExecutionResult,
    ExecutionStepResult,
)
from src.observability.dashboard.services.execution_result_report_service import (
    write_execution_result_junit_xml,
)
from src.observability.dashboard.services.test_report_service import parse_junit_xml


def _sample_result() -> ExecutionResult:
    steps = [
        ExecutionStepResult(
            index=1,
            action="call_api",
            status=PASSED,
            message="HTTP 200",
            request_method="POST",
            request_url="http://127.0.0.1:8000/api/login",
            response_status=200,
            response_preview='{"token":"demo"}',
            elapsed_ms=12.5,
        ),
        ExecutionStepResult(
            index=2,
            action="assert_text",
            status=FAILED,
            message="Response does not contain expected text: missing-token",
            response_preview='{"token":"demo"}',
            elapsed_ms=0.0,
        ),
        ExecutionStepResult(
            index=3,
            action="unsupported",
            status=SKIPPED,
            message="Unsupported step",
        ),
        ExecutionStepResult(
            index=4,
            action="call_api",
            status=DRY_RUN,
            message="Dry run only; no network request was sent",
            request_method="GET",
            request_url="http://127.0.0.1:8000/api/status",
        ),
    ]
    return ExecutionResult(
        plan_name="API Login",
        adapter="api_http",
        base_url="http://127.0.0.1:8000",
        dry_run=False,
        status=FAILED,
        total_steps=len(steps),
        passed_steps=1,
        failed_steps=1,
        skipped_steps=1,
        dry_run_steps=1,
        step_results=steps,
        failure_reason="Response does not contain expected text: missing-token",
        logs=["step 1 call_api: passed - HTTP 200"],
        artifacts={},
    )


class TestExecutionResultReportService:
    """Verify JUnit conversion for execution adapter results."""

    def test_write_execution_result_junit_xml(self, tmp_path: Path) -> None:
        path = write_execution_result_junit_xml(
            _sample_result(),
            tmp_path / "execution-plan-junit.xml",
        )

        root = ElementTree.parse(path).getroot()

        assert root.tag == "testsuite"
        assert root.attrib["name"] == "API_Login"
        assert root.attrib["tests"] == "4"
        assert root.attrib["failures"] == "1"
        assert root.attrib["skipped"] == "2"
        assert root.attrib["adapter"] == "api_http"
        assert root.find("system-out") is not None
        assert root.find("system-err") is not None

        failure = root.find(".//failure")
        assert failure is not None
        assert "missing-token" in failure.attrib["message"]

        skipped = root.findall(".//skipped")
        assert len(skipped) == 2

    def test_written_junit_is_parseable_by_report_center(self, tmp_path: Path) -> None:
        path = write_execution_result_junit_xml(
            _sample_result(),
            tmp_path / "execution-plan-junit.xml",
        )

        summary = parse_junit_xml(path)

        assert summary.total == 4
        assert summary.passed == 1
        assert summary.failed == 1
        assert summary.skipped == 2
        assert summary.errors == 0
