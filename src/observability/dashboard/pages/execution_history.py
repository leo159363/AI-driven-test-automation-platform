"""Streamlit page for browsing execution history records."""

from __future__ import annotations

import json

import streamlit as st

from src.observability.dashboard.services import (
    DEFAULT_EXECUTION_HISTORY_PATH,
    build_execution_quality_trends,
    load_execution_history_records,
    summarize_execution_history,
)


def render() -> None:
    """Render local execution history."""
    st.header("Execution History")
    st.markdown(
        "Browse saved API / UI execution-plan records, including status, failure reason, "
        "artifacts, and linked report paths."
    )

    history_path = st.text_input(
        "History JSONL path",
        value=str(DEFAULT_EXECUTION_HISTORY_PATH),
        key="eh_history_path",
    )
    limit = st.number_input(
        "Record limit",
        min_value=1,
        max_value=500,
        value=100,
        step=10,
        key="eh_limit",
    )

    try:
        records = load_execution_history_records(history_path, limit=int(limit))
    except Exception as exc:
        st.error(f"Failed to load execution history: {exc}")
        return

    if not records:
        st.info("No execution history found. Save a record from the Execution Planner or run the CLI with --record-history.")
        st.code(
            (
                ".\\.venv\\Scripts\\python.exe scripts\\run_execution_plan.py "
                "--scenario ui_login_smoke --adapter browser --dry-run --record-history"
            ),
            language="powershell",
        )
        return

    summary = summarize_execution_history(records)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total", summary["total"])
    col2.metric("Passed", summary["passed"])
    col3.metric("Failed", summary["failed"])
    col4.metric("Dry-run", summary["dry_run"])

    trends = build_execution_quality_trends(records)
    trend_col1, trend_col2, trend_col3 = st.columns(3)
    trend_col1.metric("Pass rate", f"{trends['pass_rate'] * 100:.1f}%")
    trend_col2.metric("Failure rate", f"{trends['failure_rate'] * 100:.1f}%")
    trend_col3.metric("Dry-run rate", f"{trends['dry_run_rate'] * 100:.1f}%")

    st.subheader("Quality Trends")
    if trends["daily_rows"]:
        st.line_chart(
            trends["daily_rows"],
            x="date",
            y=["passed", "failed", "dry_run"],
            use_container_width=True,
        )
        st.dataframe(trends["daily_rows"], hide_index=True, use_container_width=True)

    trend_left, trend_right = st.columns(2)
    with trend_left:
        st.markdown("Status distribution")
        st.dataframe(trends["status_rows"], hide_index=True, use_container_width=True)
        st.markdown("Adapter distribution")
        st.dataframe(trends["adapter_rows"], hide_index=True, use_container_width=True)
    with trend_right:
        st.markdown("Top failure reasons")
        if trends["failure_rows"]:
            st.dataframe(trends["failure_rows"], hide_index=True, use_container_width=True)
        else:
            st.info("No failure reasons recorded.")

    st.subheader("Records")
    st.dataframe([record.to_row() for record in records], hide_index=True, use_container_width=True)

    st.subheader("Details")
    for record in records[:20]:
        title = f"{record.created_at} | {record.plan_name} | {record.status}"
        with st.expander(title):
            if record.failure_reason:
                st.error(record.failure_reason)
            if record.report_paths:
                st.markdown("Report paths")
                st.json(record.report_paths)
            if record.artifacts:
                st.markdown("Artifacts")
                st.json(record.artifacts)
            st.code(json.dumps(record.to_dict(), ensure_ascii=False, indent=2), language="json")
