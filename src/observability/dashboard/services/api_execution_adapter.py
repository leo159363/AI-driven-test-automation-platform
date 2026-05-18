"""API execution adapter for structured execution plans."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import time
from typing import Any, Dict, List, Mapping, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from src.observability.dashboard.services.execution_plan_service import (
    ExecutionPlan,
    ExecutionStep,
)


PASSED = "passed"
FAILED = "failed"
SKIPPED = "skipped"
DRY_RUN = "dry_run"


@dataclass(frozen=True)
class ExecutionStepResult:
    """Result for one execution-plan step."""

    index: int
    action: str
    status: str
    message: str
    request_method: str = ""
    request_url: str = ""
    response_status: Optional[int] = None
    response_preview: str = ""
    elapsed_ms: float = 0.0

    def to_row(self) -> Dict[str, str]:
        """Return a table-friendly row."""
        return {
            "Index": str(self.index),
            "Action": self.action,
            "Status": self.status,
            "Message": self.message,
            "Method": self.request_method,
            "URL": self.request_url,
            "HTTP": "" if self.response_status is None else str(self.response_status),
            "Elapsed ms": f"{self.elapsed_ms:.1f}",
        }


@dataclass(frozen=True)
class ExecutionResult:
    """Aggregated execution result for an execution plan."""

    plan_name: str
    adapter: str
    base_url: str
    dry_run: bool
    status: str
    total_steps: int
    passed_steps: int
    failed_steps: int
    skipped_steps: int
    dry_run_steps: int
    step_results: List[ExecutionStepResult]
    failure_reason: Optional[str] = None
    logs: List[str] = field(default_factory=list)
    artifacts: Dict[str, str] = field(default_factory=dict)

    def to_rows(self) -> List[Dict[str, str]]:
        """Return rows for dashboard rendering."""
        return [step.to_row() for step in self.step_results]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the result for debug-style preview."""
        payload = asdict(self)
        payload["step_results"] = [asdict(step) for step in self.step_results]
        return payload


class ApiExecutionAdapter:
    """Execute API-oriented plan steps against a base URL."""

    adapter_name = "api_http"

    def __init__(self, base_url: str, timeout_seconds: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout_seconds = timeout_seconds

    def run(self, plan: ExecutionPlan, dry_run: bool = False) -> ExecutionResult:
        """Execute a structured plan and return step-level results."""
        step_results: List[ExecutionStepResult] = []
        logs: List[str] = []
        failure_reason: Optional[str] = None
        last_response_text = ""
        pending_upload: Optional[str] = None

        for step in plan.steps:
            if not step.supported:
                result = self._skipped(step, step.note or "Unsupported step")
            elif dry_run:
                result = self._dry_run(step)
            elif step.action == "call_api":
                result, last_response_text = self._call_api(step, pending_upload)
                pending_upload = None
            elif step.action == "wait":
                result = ExecutionStepResult(
                    index=step.index,
                    action=step.action,
                    status=PASSED,
                    message=f"Wait condition accepted: {step.target}",
                )
            elif step.action == "upload":
                pending_upload = step.target or "demo.txt"
                result = ExecutionStepResult(
                    index=step.index,
                    action=step.action,
                    status=PASSED,
                    message=f"Prepared upload fixture: {pending_upload}",
                )
            elif step.action == "assert_text":
                result = self._assert_text(step, last_response_text)
            else:
                result = self._skipped(step, f"Action '{step.action}' is not handled by API adapter")

            step_results.append(result)
            logs.append(f"step {step.index} {step.action}: {result.status} - {result.message}")
            if result.status == FAILED and failure_reason is None:
                failure_reason = result.message

        passed_steps = sum(1 for result in step_results if result.status == PASSED)
        failed_steps = sum(1 for result in step_results if result.status == FAILED)
        skipped_steps = sum(1 for result in step_results if result.status == SKIPPED)
        dry_run_steps = sum(1 for result in step_results if result.status == DRY_RUN)

        if dry_run:
            status = DRY_RUN
        elif failed_steps:
            status = FAILED
        else:
            status = PASSED

        return ExecutionResult(
            plan_name=plan.name,
            adapter=self.adapter_name,
            base_url=self.base_url.rstrip("/"),
            dry_run=dry_run,
            status=status,
            total_steps=len(step_results),
            passed_steps=passed_steps,
            failed_steps=failed_steps,
            skipped_steps=skipped_steps,
            dry_run_steps=dry_run_steps,
            step_results=step_results,
            failure_reason=failure_reason,
            logs=logs,
            artifacts={},
        )

    def _dry_run(self, step: ExecutionStep) -> ExecutionStepResult:
        method = step.value if step.action == "call_api" else ""
        request_url = self._build_url(step.target) if step.action == "call_api" else ""
        return ExecutionStepResult(
            index=step.index,
            action=step.action,
            status=DRY_RUN,
            message="Dry run only; no network request was sent",
            request_method=method,
            request_url=request_url,
        )

    def _skipped(self, step: ExecutionStep, message: str) -> ExecutionStepResult:
        return ExecutionStepResult(
            index=step.index,
            action=step.action,
            status=SKIPPED,
            message=message,
        )

    def _call_api(
        self, step: ExecutionStep, pending_upload: Optional[str]
    ) -> Tuple[ExecutionStepResult, str]:
        method = (step.value or "GET").upper()
        url = self._build_url(step.target)
        body, headers = self._build_request_body(method, step.target, pending_upload)
        started_at = time.perf_counter()
        request = Request(url, data=body, headers=headers, method=method)

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                response_body = response.read().decode("utf-8", errors="replace")
                elapsed_ms = (time.perf_counter() - started_at) * 1000
                status_code = response.status
        except HTTPError as exc:
            response_body = exc.read().decode("utf-8", errors="replace")
            elapsed_ms = (time.perf_counter() - started_at) * 1000
            return (
                ExecutionStepResult(
                    index=step.index,
                    action=step.action,
                    status=FAILED,
                    message=f"HTTP request failed with status {exc.code}",
                    request_method=method,
                    request_url=url,
                    response_status=exc.code,
                    response_preview=_preview(response_body),
                    elapsed_ms=elapsed_ms,
                ),
                response_body,
            )
        except URLError as exc:
            elapsed_ms = (time.perf_counter() - started_at) * 1000
            return (
                ExecutionStepResult(
                    index=step.index,
                    action=step.action,
                    status=FAILED,
                    message=f"Network error: {exc.reason}",
                    request_method=method,
                    request_url=url,
                    elapsed_ms=elapsed_ms,
                ),
                "",
            )

        status = PASSED if status_code < 400 else FAILED
        message = f"HTTP {status_code}"
        return (
            ExecutionStepResult(
                index=step.index,
                action=step.action,
                status=status,
                message=message,
                request_method=method,
                request_url=url,
                response_status=status_code,
                response_preview=_preview(response_body),
                elapsed_ms=elapsed_ms,
            ),
            response_body,
        )

    def _assert_text(self, step: ExecutionStep, response_text: str) -> ExecutionStepResult:
        expected = step.target
        if expected and expected in response_text:
            return ExecutionStepResult(
                index=step.index,
                action=step.action,
                status=PASSED,
                message=f"Response contains expected text: {expected}",
                response_preview=_preview(response_text),
            )
        return ExecutionStepResult(
            index=step.index,
            action=step.action,
            status=FAILED,
            message=f"Response does not contain expected text: {expected}",
            response_preview=_preview(response_text),
        )

    def _build_url(self, target: str) -> str:
        return urljoin(self.base_url, target.lstrip("/"))

    def _build_request_body(
        self, method: str, target: str, pending_upload: Optional[str]
    ) -> Tuple[Optional[bytes], Mapping[str, str]]:
        headers: Dict[str, str] = {"User-Agent": "ai-test-platform-api-adapter/1.0"}
        normalized_target = "/" + target.lstrip("/")

        if method in {"GET", "DELETE"}:
            return None, headers

        if normalized_target == "/api/login":
            headers["Content-Type"] = "application/json"
            return _json_body({"username": "tester", "password": "Passw0rd!"}), headers

        if normalized_target == "/api/upload":
            filename = pending_upload or "demo.txt"
            headers["Content-Type"] = "application/octet-stream"
            headers["X-Filename"] = filename
            return b"demo upload content", headers

        headers["Content-Type"] = "application/json"
        return _json_body({}), headers


def execute_plan_with_api_adapter(
    plan: ExecutionPlan, base_url: str, dry_run: bool = False
) -> ExecutionResult:
    """Convenience function used by the dashboard page."""
    return ApiExecutionAdapter(base_url=base_url).run(plan, dry_run=dry_run)


def _json_body(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload).encode("utf-8")


def _preview(text: str, max_length: int = 240) -> str:
    normalized = text.replace("\r", " ").replace("\n", " ").strip()
    if len(normalized) <= max_length:
        return normalized
    return normalized[: max_length - 3] + "..."
