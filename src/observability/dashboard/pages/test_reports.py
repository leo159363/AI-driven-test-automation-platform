"""Streamlit page for browsing local test execution reports."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.observability.dashboard.services.allure_report_service import (
    DEFAULT_ALLURE_REPORT_DIR,
    DEFAULT_ALLURE_RESULTS_DIR,
    build_allure_generate_command,
    generate_allure_html_report,
)
from src.observability.dashboard.services.test_report_service import (
    ReportArtifact,
    TestExecutionSummary,
    discover_report_artifacts,
    get_default_junit_report_path,
    load_execution_summary,
)


def _artifact_rows(artifacts: list[ReportArtifact]) -> list[dict[str, str]]:
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


def _render_allure_generation() -> None:
    st.subheader("Allure HTML Generation")
    st.markdown(
        "Generate a static Allure HTML report from existing Allure results. "
        "If the Allure CLI is not installed, this page returns a clear status "
        "instead of failing."
    )

    results_dir = st.text_input(
        "Allure results directory",
        value=str(DEFAULT_ALLURE_RESULTS_DIR),
        key="tr_allure_results_dir",
    )
    output_dir = st.text_input(
        "Allure HTML output directory",
        value=str(DEFAULT_ALLURE_REPORT_DIR),
        key="tr_allure_output_dir",
    )
    clean = st.checkbox("Clean output directory before generation", value=True, key="tr_allure_clean")

    command = build_allure_generate_command(results_dir, output_dir, clean=clean)
    st.code(" ".join(command), language="bash")

    if st.button("Generate Allure HTML", key="tr_generate_allure_html"):
        result = generate_allure_html_report(
            results_dir=results_dir,
            output_dir=output_dir,
            clean=clean,
        )
        if result.status == "generated":
            st.success(result.message)
        else:
            st.warning(result.message)
        st.json(result.to_dict())


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

    _render_allure_generation()

    st.subheader("推荐命令")
    st.code(
        "\n".join(
            [
                "pytest --junitxml=reports/junit.xml",
                "pytest --alluredir=reports/allure-results",
                "python scripts/generate_allure_report.py",
                "allure generate reports/allure-results -o reports/allure-report --clean",
            ]
        ),
        language="bash",
    )
    st.caption(
        "当前阶段仅做报告发现、解析和展示。后续自动化执行模块可以把输出统一沉淀到这些路径。"
    )
