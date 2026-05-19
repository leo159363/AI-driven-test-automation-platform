"""Unit tests for execution history persistence."""

from __future__ import annotations

from pathlib import Path

from src.observability.dashboard.services.browser_execution_adapter import (
    BrowserExecutionAdapter,
)
from src.observability.dashboard.services.execution_history_service import (
    append_execution_history_record,
    build_execution_history_record,
    load_execution_history_records,
    summarize_execution_history,
)
from src.observability.dashboard.services.execution_plan_service import build_execution_plan


def _dry_run_result():
    plan = build_execution_plan(
        "UI Login",
        "\n".join(
            [
                "open /login",
                "input username = tester",
                "click Sign in",
                "assert text Welcome Test User",
            ]
        ),
    )
    return BrowserExecutionAdapter("http://127.0.0.1:8000").run(plan, dry_run=True)


class TestExecutionHistoryService:
    """Verify execution records can be built, stored, and summarized."""

    def test_build_record_from_execution_result(self) -> None:
        record = build_execution_history_record(
            _dry_run_result(),
            scenario_id="ui_login_smoke",
            trigger="unit",
            report_paths={"junitxml": "reports/execution-plan-junit.xml"},
        )

        assert record.plan_name == "UI Login"
        assert record.adapter == "ui_browser"
        assert record.status == "dry_run"
        assert record.scenario_id == "ui_login_smoke"
        assert record.trigger == "unit"
        assert record.report_paths["junitxml"] == "reports/execution-plan-junit.xml"
        assert record.to_row()["Status"] == "dry_run"

    def test_append_and_load_records_newest_first(self, tmp_path: Path) -> None:
        history_path = tmp_path / "records.jsonl"
        first = build_execution_history_record(_dry_run_result(), scenario_id="first")
        second = build_execution_history_record(_dry_run_result(), scenario_id="second")

        append_execution_history_record(first, history_path)
        append_execution_history_record(second, history_path)

        records = load_execution_history_records(history_path)

        assert [record.scenario_id for record in records] == ["second", "first"]
        assert records[0].record_id == second.record_id

    def test_summarize_execution_history(self) -> None:
        record = build_execution_history_record(_dry_run_result())

        summary = summarize_execution_history([record])

        assert summary == {
            "total": 1,
            "passed": 0,
            "failed": 0,
            "dry_run": 1,
        }
