"""Streamlit page for browsing execution history records."""

from __future__ import annotations

import json

import streamlit as st

from src.observability.dashboard.services import (
    DEFAULT_EXECUTION_HISTORY_PATH,
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
