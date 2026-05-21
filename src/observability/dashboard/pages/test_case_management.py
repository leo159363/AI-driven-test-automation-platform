"""Streamlit page for test-case management and API automation entrypoints."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import streamlit as st

from src.observability.dashboard.services.automation_scenario_service import (
    list_automation_scenarios,
)
from src.observability.dashboard.services.test_case_library_service import (
    build_api_request_rows,
    build_case_catalog_rows,
    build_scenario_execution_command,
    list_test_cases,
    summarize_test_cases,
)

REPO_ROOT = Path(__file__).resolve().parents[4]


def _run_scenario_from_dashboard(scenario_id: str) -> subprocess.CompletedProcess[str]:
    """Run one built-in automation scenario and return the completed process."""
    cmd = [
        sys.executable,
        "scripts/run_automation_suite.py",
        "--scenario",
        scenario_id,
        "--junitxml",
        f"reports/dashboard-{scenario_id}-junit.xml",
        "--allure-results",
        f"reports/dashboard-{scenario_id}-allure-results",
    ]
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def render() -> None:
    """Render the test-case management page."""
    st.header("测试用例管理")
    st.markdown(
        "这个页面是更接近传统自动化测试平台的入口："
        "可以查看测试用例、接口测试请求、自动化状态、pytest 目标和报告产物。"
    )

    cases = list_test_cases()
    summary = summarize_test_cases(cases)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("测试用例数", summary["total"])
    col2.metric("接口测试", summary["api"])
    col3.metric("界面测试", summary["ui"])
    col4.metric("已接入自动化", summary["automated"])

    tab_cases, tab_api, tab_run = st.tabs(["测试用例列表", "接口测试", "执行与报告"])

    with tab_cases:
        st.subheader("测试用例列表")
        st.dataframe(build_case_catalog_rows(cases), hide_index=True, use_container_width=True)
        st.caption(
            "这里展示的是当前项目已经内置并可回归的用例。后续如果做成企业级平台，"
            "可以继续扩展用例新增、编辑、标签、负责人、环境和版本管理。"
        )

    with tab_api:
        st.subheader("接口测试用例")
        st.markdown(
            "当前内置接口测试覆盖登录鉴权和文件上传两个模块，"
            "这些用例背后对应 `tests/automation/` 下的 pytest 自动化脚本。"
        )
        st.dataframe(build_api_request_rows(), hide_index=True, use_container_width=True)
        st.code(
            ".\\.venv\\Scripts\\python.exe scripts\\run_automation_suite.py --scenario api_login",
            language="powershell",
        )
        st.code(
            ".\\.venv\\Scripts\\python.exe scripts\\run_automation_suite.py --scenario api_file_upload",
            language="powershell",
        )

    with tab_run:
        st.subheader("执行自动化场景")
        scenarios = list_automation_scenarios()
        scenario_labels = {scenario.scenario_id: scenario.name for scenario in scenarios}
        selected = st.selectbox(
            "选择要执行的场景",
            options=list(scenario_labels.keys()),
            format_func=lambda key: scenario_labels[key],
        )

        st.markdown("执行命令：")
        st.code(build_scenario_execution_command(selected), language="powershell")

        st.markdown("执行后会生成：")
        st.code(
            f"reports/dashboard-{selected}-junit.xml\n"
            f"reports/dashboard-{selected}-allure-results/",
            language="text",
        )

        run_clicked = st.button("运行所选自动化场景", type="primary")
        if run_clicked:
            with st.spinner("正在执行 pytest 自动化场景..."):
                try:
                    result = _run_scenario_from_dashboard(selected)
                except subprocess.TimeoutExpired:
                    st.error("执行超时：场景运行超过 120 秒。")
                    return

            if result.returncode == 0:
                st.success("自动化场景执行通过。")
            else:
                st.error(f"自动化场景执行失败，退出码：{result.returncode}")

            if result.stdout:
                st.subheader("stdout")
                st.code(result.stdout, language="text")
            if result.stderr:
                st.subheader("stderr")
                st.code(result.stderr, language="text")

        st.caption(
            "面试时可以说：平台不是只展示测试点，还把测试用例、接口测试、pytest 执行和报告产物串起来。"
        )
