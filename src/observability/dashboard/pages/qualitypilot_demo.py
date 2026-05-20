"""Streamlit page for the QualityPilot end-to-end workflow demo."""

from __future__ import annotations

import asyncio
import json
import threading
from pathlib import Path
from typing import Any

import streamlit as st

from scripts.run_qualitypilot_demo import DEFAULT_REQUIREMENT, run_demo
from src.observability.dashboard.services.qualitypilot_demo_service import (
    DEFAULT_QUALITYPILOT_DEMO_DIR,
    build_bug_report_rows,
    build_context_rows,
    build_failed_case_rows,
    build_failure_analysis_rows,
    build_headline_metrics,
    build_test_case_rows,
    build_workflow_rows,
    extract_bug_report_markdown,
    load_qualitypilot_demo_summary,
)


def render() -> None:
    """Render a visual dashboard for the deterministic QualityPilot demo."""
    st.header("QualityPilot Workflow Demo")
    st.markdown(
        "Visualize the MCP + RAG testing loop: context retrieval, test case generation, "
        "pytest execution, report parsing, failure analysis, and bug report drafting."
    )

    output_dir = st.text_input(
        "Demo output directory",
        value=str(DEFAULT_QUALITYPILOT_DEMO_DIR),
        key="qpd_output_dir",
    )
    requirement = st.text_area(
        "Requirement used by the demo",
        value=DEFAULT_REQUIREMENT,
        height=110,
        key="qpd_requirement",
    )

    action_col, command_col = st.columns([1, 2])
    with action_col:
        run_clicked = st.button("Run demo", key="qpd_run_demo", type="primary")
    with command_col:
        st.code(
            f".\\.venv\\Scripts\\python.exe scripts\\run_qualitypilot_demo.py --output-dir {output_dir}",
            language="powershell",
        )

    if run_clicked:
        try:
            with st.spinner("Running QualityPilot demo workflow..."):
                summary = _run_demo_sync(output_dir=output_dir, requirement=requirement)
            st.session_state["qualitypilot_demo_summary"] = summary
            st.success("QualityPilot demo completed.")
        except Exception as exc:
            st.error(f"QualityPilot demo failed: {exc}")
            return

    summary = _get_current_summary(output_dir)
    if summary is None:
        st.info(
            "No demo summary has been generated yet. Run the command above or click Run demo "
            "to create JUnit XML, Allure results, JSON summary, and a bug report draft."
        )
        return

    _render_headline(summary)
    _render_workflow(summary)
    _render_stage_details(summary)


def _get_current_summary(output_dir: str) -> dict[str, Any] | None:
    session_summary = st.session_state.get("qualitypilot_demo_summary")
    if isinstance(session_summary, dict):
        return session_summary

    summary_path = Path(output_dir) / "demo_summary.json"
    summary, warning = load_qualitypilot_demo_summary(summary_path)
    if warning:
        st.caption(warning)
    return summary


def _render_headline(summary: dict[str, Any]) -> None:
    metrics = build_headline_metrics(summary)
    cols = st.columns(5)
    cols[0].metric("Run ID", metrics["Run ID"] or "-")
    cols[1].metric("Execution", metrics["Execution"] or "-")
    cols[2].metric("Report", metrics["Report"] or "-")
    cols[3].metric("Failed Cases", metrics["Failed Cases"])
    cols[4].metric("Bug Drafts", metrics["Bug Drafts"])


def _render_workflow(summary: dict[str, Any]) -> None:
    st.subheader("MCP Workflow")
    rows = build_workflow_rows(summary)
    if rows:
        st.dataframe(rows, hide_index=True, use_container_width=True)
    else:
        st.info("No workflow rows found in the demo summary.")


def _render_stage_details(summary: dict[str, Any]) -> None:
    st.subheader("RAG Contexts")
    context_rows = build_context_rows(summary)
    if context_rows:
        st.dataframe(context_rows, hide_index=True, use_container_width=True)
    else:
        st.info("No RAG contexts were recorded.")

    st.subheader("Generated Test Cases")
    case_rows = build_test_case_rows(summary)
    if case_rows:
        st.dataframe(case_rows, hide_index=True, use_container_width=True)
    else:
        st.info("No generated test cases were recorded.")

    left, right = st.columns(2)
    with left:
        st.subheader("Failed Cases")
        failed_rows = build_failed_case_rows(summary)
        if failed_rows:
            st.dataframe(failed_rows, hide_index=True, use_container_width=True)
        else:
            st.info("No failed cases were recorded.")
    with right:
        st.subheader("Failure Analysis")
        analysis_rows = build_failure_analysis_rows(summary)
        if analysis_rows:
            st.dataframe(analysis_rows, hide_index=True, use_container_width=True)
        else:
            st.info("No failure analysis was recorded.")

    st.subheader("Bug Report Draft")
    bug_rows = build_bug_report_rows(summary)
    if bug_rows:
        st.dataframe(bug_rows, hide_index=True, use_container_width=True)
    else:
        st.info("No bug report drafts were generated.")

    markdown = extract_bug_report_markdown(summary)
    if markdown:
        st.code(markdown, language="markdown")
        st.download_button(
            "Download bug report markdown",
            data=markdown,
            file_name="qualitypilot_bug_report.md",
            mime="text/markdown",
            key="qpd_download_bug_markdown",
        )

    with st.expander("Raw demo summary JSON"):
        st.code(json.dumps(summary, ensure_ascii=False, indent=2), language="json")


def _run_demo_sync(output_dir: str, requirement: str) -> dict[str, Any]:
    """Run the async demo in a worker thread to avoid nested event loops."""
    result: dict[str, Any] = {}
    error: dict[str, BaseException] = {}

    def _target() -> None:
        try:
            result["summary"] = asyncio.run(
                run_demo(output_dir=output_dir, requirement=requirement)
            )
        except BaseException as exc:
            error["exception"] = exc

    thread = threading.Thread(target=_target, daemon=True)
    thread.start()
    thread.join()

    if error:
        raise error["exception"]
    summary = result.get("summary")
    if not isinstance(summary, dict):
        raise RuntimeError("QualityPilot demo did not return a summary object.")
    return summary
