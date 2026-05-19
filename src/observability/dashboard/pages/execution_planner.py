"""Streamlit page for natural-language execution-plan preview."""

from __future__ import annotations

import json

import streamlit as st

from src.observability.dashboard.services import (
    DEFAULT_EXECUTION_PLAN_ALLURE_RESULTS_DIR,
    DEFAULT_EXECUTION_PLAN_JUNIT_PATH,
    build_execution_plan,
    execute_plan_with_browser_adapter,
    execute_plan_with_api_adapter,
    get_execution_preset_steps,
    list_automation_scenarios,
    write_execution_result_allure_results,
    write_execution_result_junit_xml,
)


def _scenario_options() -> dict[str, str]:
    options = {"custom": "自定义"}
    for scenario in list_automation_scenarios():
        options[scenario.scenario_id] = scenario.name
    return options


def _render_execution_result(result, key_prefix: str) -> None:
    result_col1, result_col2, result_col3, result_col4 = st.columns(4)
    result_col1.metric("Status", result.status)
    result_col2.metric("Passed", result.passed_steps)
    result_col3.metric("Failed", result.failed_steps)
    result_col4.metric("Skipped / Dry-run", result.skipped_steps + result.dry_run_steps)

    if result.failure_reason:
        st.error(result.failure_reason)

    st.dataframe(result.to_rows(), hide_index=True, use_container_width=True)
    st.code(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), language="json")

    report_path = st.text_input(
        "JUnit XML output path",
        value=str(DEFAULT_EXECUTION_PLAN_JUNIT_PATH),
        key=f"{key_prefix}_junit_path",
        help="Saved reports can be viewed on the Test Reports page.",
    )
    if st.button("Save JUnit XML", key=f"{key_prefix}_save_junit"):
        try:
            written_path = write_execution_result_junit_xml(result, report_path)
            st.success(f"Saved: {written_path}")
        except Exception as exc:
            st.error(f"Save failed: {exc}")

    allure_dir = st.text_input(
        "Allure results directory",
        value=str(DEFAULT_EXECUTION_PLAN_ALLURE_RESULTS_DIR),
        key=f"{key_prefix}_allure_dir",
        help="Writes minimal Allure result JSON and attachments for the execution plan.",
    )
    if st.button("Save Allure Results", key=f"{key_prefix}_save_allure"):
        try:
            written_path = write_execution_result_allure_results(result, allure_dir)
            st.success(f"Saved: {written_path}")
        except Exception as exc:
            st.error(f"Save failed: {exc}")


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
        st.session_state.pop("execution_plan_result", None)

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

    if plan.adapter == "api_http_preview":
        st.subheader("API 执行适配器")
        api_base_url = st.text_input(
            "API Base URL",
            value="http://127.0.0.1:8000",
            key="ep_api_base_url",
            help="真实执行时指向本地稳定 API；只预览请求步骤时保持 dry-run。",
        )
        dry_run = st.checkbox(
            "Dry run",
            value=True,
            key="ep_api_dry_run",
            help="只生成执行结果，不发送真实网络请求。",
        )

        if st.button("执行 API 计划", key="ep_run_api_plan"):
            if not api_base_url.strip():
                st.error("API Base URL 不能为空。")
            else:
                st.session_state["execution_plan_result"] = execute_plan_with_api_adapter(
                    plan,
                    api_base_url,
                    dry_run=dry_run,
                )

        result = st.session_state.get("execution_plan_result")
        if result:
            _render_execution_result(result, "ep_api")
    elif plan.adapter == "ui_browser_preview":
        st.subheader("Browser UI execution adapter")
        ui_base_url = st.text_input(
            "UI Base URL",
            value="http://127.0.0.1:8000",
            key="ep_ui_base_url",
            help="Dry-run does not open the browser. Real execution requires optional Playwright setup.",
        )
        dry_run = st.checkbox(
            "Dry run",
            value=True,
            key="ep_ui_dry_run",
            help="Preview browser execution without launching Playwright.",
        )
        screenshot_dir = st.text_input(
            "Failure screenshot directory",
            value="reports/screenshots",
            key="ep_ui_screenshot_dir",
        )

        if st.button("Execute UI plan", key="ep_run_ui_plan"):
            if not ui_base_url.strip():
                st.error("UI Base URL cannot be empty.")
            else:
                st.session_state["execution_plan_result"] = execute_plan_with_browser_adapter(
                    plan,
                    ui_base_url,
                    dry_run=dry_run,
                    screenshot_dir=screenshot_dir,
                )

        result = st.session_state.get("execution_plan_result")
        if result:
            _render_execution_result(result, "ep_ui")
    else:
        st.info("当前计划类型暂未绑定可执行适配器。请使用 API 或 UI 预设步骤。")

    st.caption("执行适配器现在支持 API HTTP 与 Browser UI 计划；UI 真执行需要可选 Playwright 环境，dry-run 可直接演示。")
