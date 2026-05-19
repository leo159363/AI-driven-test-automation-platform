"""Unit tests for execution history persistence."""

from __future__ import annotations

from pathlib import Path

from src.observability.dashboard.services.browser_execution_adapter import (
    BrowserExecutionAdapter,
)
from src.observability.dashboard.services.execution_history_service import (
    append_execution_history_record,
    build_execution_quality_trends,
    build_execution_history_record,
    ExecutionHistoryRecord,
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

    def test_build_quality_trends(self) -> None:
        records = [
            ExecutionHistoryRecord(
                record_id="1",
                created_at="2026-05-19T01:00:00+00:00",
                plan_name="API Login",
                adapter="api_http",
                status="passed",
                base_url="http://127.0.0.1:8000",
                dry_run=False,
                total_steps=3,
                passed_steps=3,
                failed_steps=0,
                skipped_steps=0,
                dry_run_steps=0,
                duration_ms=120.0,
                scenario_id="api_login",
            ),
            ExecutionHistoryRecord(
                record_id="2",
                created_at="2026-05-19T02:00:00+00:00",
                plan_name="UI Login",
                adapter="ui_browser",
                status="failed",
                base_url="http://127.0.0.1:8000",
                dry_run=False,
                total_steps=5,
                passed_steps=3,
                failed_steps=1,
                skipped_steps=1,
                dry_run_steps=0,
                duration_ms=200.0,
                failure_reason="Button not found",
                scenario_id="ui_login_smoke",
            ),
            ExecutionHistoryRecord(
                record_id="3",
                created_at="2026-05-20T01:00:00+00:00",
                plan_name="UI Login Dry",
                adapter="ui_browser",
                status="dry_run",
                base_url="http://127.0.0.1:8000",
                dry_run=True,
                total_steps=5,
                passed_steps=0,
                failed_steps=0,
                skipped_steps=0,
                dry_run_steps=5,
                duration_ms=0.0,
                scenario_id="ui_login_smoke",
            ),
        ]

        trends = build_execution_quality_trends(records)

        assert trends["total"] == 3
        assert trends["pass_rate"] == 0.3333
        assert trends["failure_rate"] == 0.3333
        assert trends["dry_run_rate"] == 0.3333
        assert trends["daily_rows"][0]["date"] == "2026-05-19"
        assert trends["daily_rows"][0]["passed"] == 1
        assert trends["daily_rows"][0]["failed"] == 1
        assert trends["daily_rows"][1]["dry_run"] == 1
        assert trends["adapter_rows"][0] == {"adapter": "ui_browser", "count": 2}
        assert trends["failure_rows"][0] == {"failure_reason": "Button not found", "count": 1}
