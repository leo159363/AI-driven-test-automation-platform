"""Streamlit page for browsing built-in demo automation scenarios."""

from __future__ import annotations

import streamlit as st

from src.observability.dashboard.services.automation_scenario_service import (
    build_runner_command,
    list_automation_scenarios,
)


def render() -> None:
    """Render the built-in automation scenario catalog."""
    st.header("自动化场景")
    st.markdown(
        "平台支持很多测试场景，但第一版先内置 **可稳定跑通的示例场景**。"
        "这样可以先把执行约定、报告产物和展示链路跑通，再逐步扩展更多业务场景。"
    )

    scenarios = list_automation_scenarios()
    rows = [
        {
            "ID": scenario.scenario_id,
            "Name": scenario.name,
            "Category": scenario.category,
            "Labels": ", ".join(scenario.labels),
            "Description": scenario.description,
            "Pytest Targets": ", ".join(scenario.pytest_targets),
            "Command": build_runner_command(scenario.scenario_id),
        }
        for scenario in scenarios
    ]

    st.subheader("内置示例场景")
    st.dataframe(rows, hide_index=True, use_container_width=True)

    st.subheader("统一执行命令")
    st.code(build_runner_command("all"), language="powershell")
    st.caption(
        "当前阶段通过 CLI runner 统一执行并产出 JUnit / Allure 工件。"
        "Dashboard 负责展示场景目录和报告结果，不在页面里直接跑测试。"
    )
