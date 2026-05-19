"""Streamlit page for requirement-test-execution traceability."""

from __future__ import annotations

import json

import streamlit as st

from src.observability.dashboard.services import (
    DEFAULT_EXECUTION_HISTORY_PATH,
    build_traceability_report,
    load_execution_history_records,
)


SAMPLE_REQUIREMENTS = """登录接口需要支持用户名密码认证，成功后返回 token。
连续五次登录失败后需要临时锁定账户。
错误提示不能泄露账号是否存在。"""

SAMPLE_TEST_DESIGN = """# 接口测试设计 测试设计草稿

## 3. 测试点
### 功能
- 验证登录接口在正确用户名和密码下返回 200、token 和用户信息。
- 验证连续五次密码错误后账户被锁定并返回明确错误码。

### 安全
- 验证登录失败提示不暴露账号是否存在，避免用户枚举风险。
- 验证 token 过期和无权限访问会被拒绝。

### 回归
- 验证登录响应 schema 和错误码兼容旧客户端。
"""


def render() -> None:
    """Render the traceability matrix page."""
    st.header("Traceability Matrix")
    st.markdown(
        "Map requirement items to generated test points, built-in automation scenarios, "
        "and the latest saved execution result."
    )

    history_path = st.text_input(
        "Execution history JSONL path",
        value=str(DEFAULT_EXECUTION_HISTORY_PATH),
        key="tm_history_path",
    )
    limit = st.number_input(
        "Execution record limit",
        min_value=1,
        max_value=500,
        value=100,
        step=10,
        key="tm_limit",
    )

    default_requirement = st.session_state.get("tw_requirement", SAMPLE_REQUIREMENTS)
    default_draft = st.session_state.get("tw_draft", SAMPLE_TEST_DESIGN)

    col_left, col_right = st.columns(2)
    with col_left:
        requirement_text = st.text_area(
            "Requirement items",
            value=default_requirement,
            height=260,
            key="tm_requirements",
        )
    with col_right:
        test_design_markdown = st.text_area(
            "Test-design Markdown",
            value=default_draft,
            height=260,
            key="tm_markdown",
        )

    try:
        records = load_execution_history_records(history_path, limit=int(limit))
    except Exception as exc:
        st.error(f"Failed to load execution history: {exc}")
        records = []

    if st.button("Build Matrix", type="primary", key="tm_build"):
        st.session_state["tm_report"] = build_traceability_report(
            requirement_text=requirement_text,
            test_design_markdown=test_design_markdown,
            execution_records=records,
        )

    report = st.session_state.get("tm_report")
    if not report:
        st.info("Build the matrix to see coverage, automation linkage, and execution gaps.")
        return

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Requirements", report.requirement_count)
    col2.metric("Covered", f"{report.coverage_rate * 100:.1f}%")
    col3.metric("Automated", f"{report.automation_rate * 100:.1f}%")
    col4.metric("Passed", f"{report.passed_rate * 100:.1f}%")

    st.subheader("Matrix")
    st.dataframe(report.to_rows(), hide_index=True, use_container_width=True)

    st.subheader("Requirement Details")
    for row in report.rows:
        title = f"{row.requirement_id} | {row.risk_level} | {row.requirement}"
        with st.expander(title):
            if row.gaps:
                st.warning(", ".join(row.gaps))
            st.markdown("Test points")
            if row.test_points:
                st.dataframe(
                    [point.to_dict() for point in row.test_points],
                    hide_index=True,
                    use_container_width=True,
                )
            else:
                st.info("No matched test points.")

            st.markdown("Automation")
            if row.automation:
                st.dataframe(
                    [link.to_dict() for link in row.automation],
                    hide_index=True,
                    use_container_width=True,
                )
            else:
                st.info("No matched automation scenario.")

    st.subheader("JSON")
    st.code(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), language="json")
