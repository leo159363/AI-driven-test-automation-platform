"""Browser execution adapter for structured UI execution plans."""

from __future__ import annotations

from pathlib import Path
import re
import time
from typing import List, Optional, Protocol
from urllib.parse import urljoin

from src.observability.dashboard.services.api_execution_adapter import (
    DRY_RUN,
    FAILED,
    PASSED,
    SKIPPED,
    ExecutionResult,
    ExecutionStepResult,
)
from src.observability.dashboard.services.execution_plan_service import (
    ExecutionPlan,
    ExecutionStep,
)


UI_ACTIONS = {"open", "input", "click", "submit", "upload", "assert_text", "wait"}


class BrowserDependencyError(RuntimeError):
    """Raised when the optional browser automation runtime is unavailable."""


class BrowserRunner(Protocol):
    """Small protocol used by the adapter and by deterministic tests."""

    def open_url(self, url: str) -> None:
        """Open a URL in the browser."""

    def input_text(self, field: str, value: str) -> None:
        """Fill a field with text."""

    def click(self, target: str) -> None:
        """Click a visible target."""

    def submit(self) -> None:
        """Submit the current form."""

    def upload_file(self, file_path: str) -> None:
        """Upload a file through the first file input."""

    def wait(self, target: str) -> None:
        """Wait for a browser condition."""

    def assert_text(self, text: str) -> None:
        """Assert that visible page text is present."""

    def screenshot(self, path: Path) -> None:
        """Capture a screenshot to path."""

    def close(self) -> None:
        """Close browser resources."""


class BrowserExecutionAdapter:
    """Execute UI-oriented plan steps through an optional Playwright runner."""

    adapter_name = "ui_browser"

    def __init__(
        self,
        base_url: str,
        timeout_seconds: float = 5.0,
        screenshot_dir: str | Path = "reports/screenshots",
        headless: bool = True,
        runner: Optional[BrowserRunner] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout_seconds = timeout_seconds
        self.screenshot_dir = Path(screenshot_dir)
        self.headless = headless
        self._runner = runner

    def run(self, plan: ExecutionPlan, dry_run: bool = False) -> ExecutionResult:
        """Execute a structured UI plan and return step-level results."""
        if dry_run:
            return self._run_dry(plan)

        try:
            runner = self._runner or _PlaywrightBrowserRunner(
                timeout_seconds=self.timeout_seconds,
                headless=self.headless,
            )
        except BrowserDependencyError as exc:
            return self._startup_failure(plan, str(exc))
        except Exception as exc:  # pragma: no cover - depends on local browser install
            return self._startup_failure(plan, f"Unable to start Playwright browser: {exc}")

        step_results: List[ExecutionStepResult] = []
        logs: List[str] = []
        artifacts: dict[str, str] = {}
        failure_reason: Optional[str] = None
        stop_after_failure = False

        try:
            for step in plan.steps:
                if stop_after_failure and step.action in UI_ACTIONS:
                    result = self._skipped(step, "Previous browser step failed")
                elif not step.supported:
                    result = self._skipped(step, step.note or "Unsupported step")
                elif step.action not in UI_ACTIONS:
                    result = self._skipped(
                        step,
                        f"Action '{step.action}' is not handled by browser adapter",
                    )
                else:
                    result = self._execute_step(plan, step, runner, artifacts)
                    if result.status == FAILED:
                        failure_reason = result.message
                        stop_after_failure = True

                step_results.append(result)
                logs.append(f"step {step.index} {step.action}: {result.status} - {result.message}")
        finally:
            runner.close()

        return _build_result(
            plan=plan,
            adapter=self.adapter_name,
            base_url=self.base_url.rstrip("/"),
            dry_run=False,
            step_results=step_results,
            failure_reason=failure_reason,
            logs=logs,
            artifacts=artifacts,
        )

    def _run_dry(self, plan: ExecutionPlan) -> ExecutionResult:
        step_results: List[ExecutionStepResult] = []
        logs: List[str] = []
        for step in plan.steps:
            if not step.supported:
                result = self._skipped(step, step.note or "Unsupported step")
            elif step.action in UI_ACTIONS:
                result = self._dry_run(step)
            else:
                result = self._skipped(
                    step,
                    f"Action '{step.action}' is not handled by browser adapter",
                )
            step_results.append(result)
            logs.append(f"step {step.index} {step.action}: {result.status} - {result.message}")

        return _build_result(
            plan=plan,
            adapter=self.adapter_name,
            base_url=self.base_url.rstrip("/"),
            dry_run=True,
            step_results=step_results,
            failure_reason=None,
            logs=logs,
            artifacts={},
        )

    def _execute_step(
        self,
        plan: ExecutionPlan,
        step: ExecutionStep,
        runner: BrowserRunner,
        artifacts: dict[str, str],
    ) -> ExecutionStepResult:
        started_at = time.perf_counter()
        request_url = ""
        try:
            if step.action == "open":
                request_url = self._build_url(step.target)
                runner.open_url(request_url)
                message = f"Opened URL: {request_url}"
            elif step.action == "input":
                runner.input_text(step.target, step.value)
                message = f"Filled field: {step.target}"
            elif step.action == "click":
                runner.click(step.target)
                message = f"Clicked target: {step.target}"
            elif step.action == "submit":
                runner.submit()
                message = "Submitted current form"
            elif step.action == "upload":
                runner.upload_file(step.target)
                message = f"Uploaded file: {step.target}"
            elif step.action == "wait":
                runner.wait(step.target)
                message = f"Wait condition accepted: {step.target}"
            elif step.action == "assert_text":
                runner.assert_text(step.target)
                message = f"Page contains expected text: {step.target}"
            else:
                return self._skipped(
                    step,
                    f"Action '{step.action}' is not handled by browser adapter",
                )
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - started_at) * 1000
            screenshot_path = self._capture_failure_screenshot(plan, step, runner)
            response_preview = ""
            if screenshot_path:
                artifacts["failure_screenshot"] = str(screenshot_path)
                response_preview = f"screenshot={screenshot_path}"
            return ExecutionStepResult(
                index=step.index,
                action=step.action,
                status=FAILED,
                message=f"Browser step failed: {exc}",
                request_url=request_url,
                response_preview=response_preview,
                elapsed_ms=elapsed_ms,
            )

        elapsed_ms = (time.perf_counter() - started_at) * 1000
        return ExecutionStepResult(
            index=step.index,
            action=step.action,
            status=PASSED,
            message=message,
            request_url=request_url,
            elapsed_ms=elapsed_ms,
        )

    def _dry_run(self, step: ExecutionStep) -> ExecutionStepResult:
        request_url = self._build_url(step.target) if step.action == "open" else ""
        return ExecutionStepResult(
            index=step.index,
            action=step.action,
            status=DRY_RUN,
            message="Dry run only; browser action was not executed",
            request_url=request_url,
        )

    def _skipped(self, step: ExecutionStep, message: str) -> ExecutionStepResult:
        return ExecutionStepResult(
            index=step.index,
            action=step.action,
            status=SKIPPED,
            message=message,
        )

    def _startup_failure(self, plan: ExecutionPlan, message: str) -> ExecutionResult:
        step_results: List[ExecutionStepResult] = []
        logs: List[str] = []
        failure_recorded = False
        for step in plan.steps:
            if not step.supported:
                result = self._skipped(step, step.note or "Unsupported step")
            elif step.action not in UI_ACTIONS:
                result = self._skipped(
                    step,
                    f"Action '{step.action}' is not handled by browser adapter",
                )
            elif not failure_recorded:
                result = ExecutionStepResult(
                    index=step.index,
                    action=step.action,
                    status=FAILED,
                    message=message,
                )
                failure_recorded = True
            else:
                result = self._skipped(step, "Browser session did not start")
            step_results.append(result)
            logs.append(f"step {step.index} {step.action}: {result.status} - {result.message}")

        return _build_result(
            plan=plan,
            adapter=self.adapter_name,
            base_url=self.base_url.rstrip("/"),
            dry_run=False,
            step_results=step_results,
            failure_reason=message if failure_recorded else None,
            logs=logs,
            artifacts={},
        )

    def _build_url(self, target: str) -> str:
        return urljoin(self.base_url, target.lstrip("/"))

    def _capture_failure_screenshot(
        self,
        plan: ExecutionPlan,
        step: ExecutionStep,
        runner: BrowserRunner,
    ) -> Optional[Path]:
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        path = self.screenshot_dir / f"{_safe_file_token(plan.name)}-step-{step.index:02d}.png"
        try:
            runner.screenshot(path)
        except Exception:
            return None
        return path


class _PlaywrightBrowserRunner:
    """Thin Playwright wrapper imported only when real browser execution is requested."""

    def __init__(self, timeout_seconds: float, headless: bool) -> None:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise BrowserDependencyError(
                "Playwright is not installed. Install the optional browser extra and run "
                "`python -m playwright install chromium`, or use dry-run mode."
            ) from exc

        self.timeout_ms = timeout_seconds * 1000
        self._playwright = sync_playwright().start()
        try:
            self._browser = self._playwright.chromium.launch(headless=headless)
            self._page = self._browser.new_page()
        except Exception:
            self._playwright.stop()
            raise

    def open_url(self, url: str) -> None:
        self._page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)

    def input_text(self, field: str, value: str) -> None:
        locator = self._page.get_by_label(field)
        if locator.count() == 0:
            locator = self._page.get_by_placeholder(field)
        if locator.count() == 0:
            locator = self._page.locator(f"[name='{field}']")
        locator.first.fill(value, timeout=self.timeout_ms)

    def click(self, target: str) -> None:
        locator = self._page.get_by_role("button", name=target)
        if locator.count() == 0:
            locator = self._page.get_by_text(target, exact=False)
        locator.first.click(timeout=self.timeout_ms)

    def submit(self) -> None:
        self._page.keyboard.press("Enter")

    def upload_file(self, file_path: str) -> None:
        self._page.locator("input[type=file]").first.set_input_files(file_path)

    def wait(self, target: str) -> None:
        milliseconds = _parse_wait_milliseconds(target)
        if milliseconds:
            self._page.wait_for_timeout(milliseconds)
        else:
            self._page.wait_for_load_state("networkidle", timeout=self.timeout_ms)

    def assert_text(self, text: str) -> None:
        self._page.get_by_text(text, exact=False).first.wait_for(timeout=self.timeout_ms)

    def screenshot(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._page.screenshot(path=str(path), full_page=True)

    def close(self) -> None:
        try:
            self._browser.close()
        finally:
            self._playwright.stop()


def execute_plan_with_browser_adapter(
    plan: ExecutionPlan,
    base_url: str,
    dry_run: bool = False,
    screenshot_dir: str | Path = "reports/screenshots",
    headless: bool = True,
) -> ExecutionResult:
    """Convenience function used by the dashboard page and CLI."""
    return BrowserExecutionAdapter(
        base_url=base_url,
        screenshot_dir=screenshot_dir,
        headless=headless,
    ).run(plan, dry_run=dry_run)


def _build_result(
    plan: ExecutionPlan,
    adapter: str,
    base_url: str,
    dry_run: bool,
    step_results: List[ExecutionStepResult],
    failure_reason: Optional[str],
    logs: List[str],
    artifacts: dict[str, str],
) -> ExecutionResult:
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
        adapter=adapter,
        base_url=base_url,
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
        artifacts=artifacts,
    )


def _parse_wait_milliseconds(target: str) -> Optional[float]:
    match = re.search(r"(\d+(?:\.\d+)?)\s*(ms|millisecond|milliseconds|s|sec|second|seconds)?", target)
    if not match:
        return None
    value = float(match.group(1))
    unit = (match.group(2) or "ms").lower()
    if unit in {"s", "sec", "second", "seconds"}:
        value *= 1000
    return value


def _safe_file_token(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip())
    return normalized.strip("-") or "execution-plan"
