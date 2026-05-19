"""Unit tests for the browser execution adapter."""

from __future__ import annotations

from pathlib import Path

from src.observability.dashboard.services.api_execution_adapter import (
    DRY_RUN,
    FAILED,
    PASSED,
    SKIPPED,
)
from src.observability.dashboard.services.browser_execution_adapter import (
    BrowserExecutionAdapter,
)
from src.observability.dashboard.services.execution_plan_service import build_execution_plan


class _FakeBrowserRunner:
    def __init__(self, fail_on: str = "") -> None:
        self.fail_on = fail_on
        self.actions: list[str] = []
        self.closed = False

    def open_url(self, url: str) -> None:
        self._record("open", url)

    def input_text(self, field: str, value: str) -> None:
        self._record("input", f"{field}={value}")

    def click(self, target: str) -> None:
        self._record("click", target)

    def submit(self) -> None:
        self._record("submit", "")

    def upload_file(self, file_path: str) -> None:
        self._record("upload", file_path)

    def wait(self, target: str) -> None:
        self._record("wait", target)

    def assert_text(self, text: str) -> None:
        self._record("assert_text", text)

    def screenshot(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"fake-png")

    def close(self) -> None:
        self.closed = True

    def _record(self, action: str, value: str) -> None:
        self.actions.append(f"{action}:{value}")
        if self.fail_on == action:
            raise AssertionError(f"{action} failed")


def _ui_plan():
    return build_execution_plan(
        "UI Login",
        "\n".join(
            [
                "open /login",
                "input username = tester",
                "input password = Passw0rd!",
                "click Sign in",
                "assert text Welcome Test User",
            ]
        ),
    )


class TestBrowserExecutionAdapter:
    """Verify deterministic browser adapter behavior without launching Playwright."""

    def test_dry_run_does_not_launch_browser(self) -> None:
        result = BrowserExecutionAdapter("http://127.0.0.1:8000").run(
            _ui_plan(),
            dry_run=True,
        )

        assert result.status == DRY_RUN
        assert result.dry_run_steps == 5
        assert result.failed_steps == 0
        assert result.step_results[0].request_url == "http://127.0.0.1:8000/login"

    def test_executes_ui_plan_with_runner(self) -> None:
        runner = _FakeBrowserRunner()

        result = BrowserExecutionAdapter(
            "http://127.0.0.1:8000",
            runner=runner,
        ).run(_ui_plan())

        assert result.status == PASSED
        assert result.passed_steps == 5
        assert result.failed_steps == 0
        assert runner.closed is True
        assert runner.actions[:2] == [
            "open:http://127.0.0.1:8000/login",
            "input:username=tester",
        ]

    def test_failure_captures_screenshot_and_skips_remaining_steps(self, tmp_path: Path) -> None:
        runner = _FakeBrowserRunner(fail_on="click")

        result = BrowserExecutionAdapter(
            "http://127.0.0.1:8000",
            runner=runner,
            screenshot_dir=tmp_path,
        ).run(_ui_plan())

        assert result.status == FAILED
        assert result.failed_steps == 1
        assert result.skipped_steps == 1
        assert result.step_results[3].status == FAILED
        assert result.step_results[4].status == SKIPPED
        assert "failure_screenshot" in result.artifacts
        assert Path(result.artifacts["failure_screenshot"]).exists()
