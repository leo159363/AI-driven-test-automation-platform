"""Streamlit page for natural-language execution-plan preview."""

from __future__ import annotations

import json

import streamlit as st

from src.observability.dashboard.services import (
    build_execution_plan,
    get_execution_preset_steps,
    list_automation_scenarios,
)


def _scenario_options() -> dict[str, str]:
    options = {"custom": "自定义"}
    for scenario in list_automation_scenarios():
        options[scenario.scenario_id] = scenario.name
    return options


def render() -> None:
    """Render the execution-plan preview page."""
    st.header("执行计划预览")
    st.markdown(
        "把**自然语言测试步骤**解析成结构化执行计划。"
        "当前只做预览，不直接驱动浏览器或接口执行。"
    )

    options = _scenario_options()
    selected_scenario = st.selectbox(
        "预设场景",
        options=list(options.keys()),
        format_func=lambda key: options[key],
        index=0,
        help="可以直接选择平台内置示例场景，也可以手工输入自定义步骤。",
    )

    default_steps = get_execution_preset_steps(selected_scenario)
    plan_name = st.text_input(
        "计划名称",
        value=options[selected_scenario] if selected_scenario != "custom" else "自定义执行计划",
        key="ep_name",
    )
    step_text = st.text_area(
        "自然语言步骤",
        value=default_steps,
        height=220,
        key=f"ep_steps_{selected_scenario}",
        placeholder=(
            "例如：\n"
            "打开 /login\n"
            "输入 用户名 = tester\n"
            "输入 密码 = Passw0rd!\n"
            "点击 Sign in\n"
            "断言看到 Welcome Test User"
        ),
    )

    parse_clicked = st.button("生成执行计划", type="primary")

    if parse_clicked:
        plan = build_execution_plan(plan_name, step_text)
        st.session_state["execution_plan_preview"] = plan

    plan = st.session_state.get("execution_plan_preview")
    if not plan:
        st.info("点击“生成执行计划”后，这里会展示结构化步骤、适配器类型和警告信息。")
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("步骤数", len(plan.steps))
    col2.metric("支持步骤", sum(1 for step in plan.steps if step.supported))
    col3.metric("未支持步骤", len(plan.warnings))

    st.caption(f"Adapter: `{plan.adapter}` | Target: `{plan.target}`")

    if plan.warnings:
        st.warning("以下步骤尚未支持：\n- " + "\n- ".join(plan.warnings))

    st.subheader("步骤明细")
    st.dataframe(plan.to_rows(), hide_index=True, use_container_width=True)

    st.subheader("结构化预览")
    st.code(json.dumps(plan.to_dict(), ensure_ascii=False, indent=2), language="json")

    st.caption("执行适配器会在后续阶段接入；当前页面只负责把测试意图解析成稳定的执行计划。")
