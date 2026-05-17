"""Streamlit page for browsing local test execution reports."""

from __future__ import annotations

from pathlib import Path
from typing import List

import streamlit as st

from src.observability.dashboard.services.test_report_service import (
    ReportArtifact,
    TestExecutionSummary,
    discover_report_artifacts,
    get_default_junit_report_path,
    load_execution_summary,
)


def _artifact_rows(artifacts: List[ReportArtifact]) -> List[dict[str, str]]:
    return [
        {
            "Type": artifact.label,
            "Status": "Found" if artifact.exists else "Missing",
            "Path": str(artifact.path),
            "Details": artifact.detail,
        }
        for artifact in artifacts
    ]


def _render_summary(summary: TestExecutionSummary) -> None:
    cols = st.columns(5)
    cols[0].metric("Total", summary.total)
    cols[1].metric("Passed", summary.passed)
    cols[2].metric("Failed", summary.failed)
    cols[3].metric("Skipped", summary.skipped)
    cols[4].metric("Errors", summary.errors)

    st.caption(
        f"Suite: `{summary.suite_name}` | Duration: `{summary.duration_seconds:.2f}s` | "
        f"Source: `{summary.source_path}`"
    )


def render() -> None:
    """Render the Test Reports page."""
    st.header("测试报告")
    st.markdown(
        "集中查看 **pytest 执行结果摘要** 与 **Allure 报告工件状态**。"
        "这一页关注的是自动化执行结果，不替代检索评估面板。"
    )

    project_root = Path(".")
    artifacts = discover_report_artifacts(project_root)

    st.subheader("执行摘要")
    junit_path = st.text_input(
        "JUnit XML 路径",
        value=get_default_junit_report_path(project_root),
        help="支持 pytest 通过 --junitxml 生成的 XML 报告。",
        key="tr_junit_path",
    )

    summary, warning = load_execution_summary(junit_path)
    if summary is not None:
        _render_summary(summary)
    else:
        st.info(
            warning
            or "当前还没有可解析的执行报告。你可以先运行 pytest 生成 JUnit XML 或 Allure 结果目录。"
        )

    st.subheader("报告工件")
    st.dataframe(_artifact_rows(artifacts), hide_index=True, use_container_width=True)

    st.subheader("推荐命令")
    st.code(
        "\n".join(
            [
                "pytest --junitxml=reports/junit.xml",
                "pytest --alluredir=reports/allure-results",
                "allure generate reports/allure-results -o reports/allure-report --clean",
            ]
        ),
        language="bash",
    )
    st.caption(
        "当前阶段仅做报告发现、解析和展示。后续自动化执行模块可以把输出统一沉淀到这些路径。"
    )
