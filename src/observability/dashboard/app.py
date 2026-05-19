"""Streamlit dashboard entrypoint for the AI-driven test platform."""

from __future__ import annotations

import streamlit as st


def _page_overview() -> None:
    from src.observability.dashboard.pages.overview import render

    render()


def _page_test_workbench() -> None:
    from src.observability.dashboard.pages.test_workbench import render

    render()


def _page_automation_scenarios() -> None:
    from src.observability.dashboard.pages.automation_scenarios import render

    render()


def _page_execution_planner() -> None:
    from src.observability.dashboard.pages.execution_planner import render

    render()


def _page_execution_history() -> None:
    from src.observability.dashboard.pages.execution_history import render

    render()


def _page_test_reports() -> None:
    from src.observability.dashboard.pages.test_reports import render

    render()


def _page_test_design_evaluation() -> None:
    from src.observability.dashboard.pages.test_design_evaluation import render

    render()


def _page_test_design_review() -> None:
    from src.observability.dashboard.pages.test_design_review import render

    render()


def _page_traceability_matrix() -> None:
    from src.observability.dashboard.pages.traceability_matrix import render

    render()


def _page_data_browser() -> None:
    from src.observability.dashboard.pages.data_browser import render

    render()


def _page_ingestion_manager() -> None:
    from src.observability.dashboard.pages.ingestion_manager import render

    render()


def _page_ingestion_traces() -> None:
    from src.observability.dashboard.pages.ingestion_traces import render

    render()


def _page_query_traces() -> None:
    from src.observability.dashboard.pages.query_traces import render

    render()


def _page_evaluation_panel() -> None:
    from src.observability.dashboard.pages.evaluation_panel import render

    render()


pages = [
    st.Page(_page_overview, title="平台总览", icon="📊", default=True),
    st.Page(_page_test_workbench, title="测试工作台", icon="🧪"),
    st.Page(_page_automation_scenarios, title="自动化场景", icon="⚙️"),
    st.Page(_page_execution_planner, title="执行计划", icon="🗂️"),
    st.Page(_page_execution_history, title="执行历史", icon="🧾"),
    st.Page(_page_test_reports, title="测试报告", icon="📄"),
    st.Page(_page_test_design_evaluation, title="测试设计评估", icon="📏"),
    st.Page(_page_test_design_review, title="测试设计评审", icon="✅"),
    st.Page(_page_traceability_matrix, title="追踪矩阵", icon="🔗"),
    st.Page(_page_data_browser, title="知识库浏览", icon="📎"),
    st.Page(_page_ingestion_manager, title="测试资料入库", icon="📜"),
    st.Page(_page_ingestion_traces, title="入库日志", icon="📑"),
    st.Page(_page_query_traces, title="检索日志", icon="📷"),
    st.Page(_page_evaluation_panel, title="评估中心", icon="📻"),
]


def main() -> None:
    st.set_page_config(
        page_title="AI 驱动的自动化测试平台",
        page_icon="🧪",
        layout="wide",
    )

    nav = st.navigation(pages)
    nav.run()


if __name__ == "__main__":
    main()
else:
    main()
