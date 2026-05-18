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
