"""Unit tests for the execution-plan CLI."""

from __future__ import annotations

from pathlib import Path

from scripts import run_execution_plan
from src.observability.dashboard.services.test_report_service import parse_junit_xml


class TestRunExecutionPlanScript:
    """Verify the CLI can produce a report in dry-run mode."""

    def test_main_writes_junit_for_dry_run(self, tmp_path: Path, monkeypatch) -> None:
        report_path = tmp_path / "execution-plan-junit.xml"
        monkeypatch.setattr(
            run_execution_plan,
            "parse_args",
            lambda: type(
                "Args",
                (),
                {
                    "scenario": "api_login",
                    "base_url": "http://127.0.0.1:1",
                    "dry_run": True,
                    "junitxml": str(report_path),
                    "json": False,
                },
            )(),
        )

        exit_code = run_execution_plan.main()
        summary = parse_junit_xml(report_path)

        assert exit_code == 0
        assert summary.total == 3
        assert summary.failed == 0
        assert summary.skipped == 3

    def test_main_runs_browser_plan_dry_run_with_allure(self, tmp_path: Path, monkeypatch) -> None:
        report_path = tmp_path / "ui-execution-plan-junit.xml"
        allure_dir = tmp_path / "allure-results"
        monkeypatch.setattr(
            run_execution_plan,
            "parse_args",
            lambda: type(
                "Args",
                (),
                {
                    "scenario": "ui_login_smoke",
                    "base_url": "http://127.0.0.1:8000",
                    "adapter": "auto",
                    "dry_run": True,
                    "junitxml": str(report_path),
                    "allure_results": str(allure_dir),
                    "screenshot_dir": str(tmp_path / "screenshots"),
                    "json": False,
                },
            )(),
        )

        exit_code = run_execution_plan.main()
        summary = parse_junit_xml(report_path)

        assert exit_code == 0
        assert summary.total == 5
        assert summary.failed == 0
        assert summary.skipped == 5
        assert any(allure_dir.glob("*-result.json"))
