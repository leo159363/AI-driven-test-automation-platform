"""Streamlit page for deterministic test-design quality evaluation."""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from src.observability.dashboard.services import (
    DEFAULT_TEST_DESIGN_GOLDEN_SET,
    DEFAULT_TEST_DESIGN_REPORT_DIR,
    load_test_design_golden_set,
    run_test_design_evaluation,
    write_test_design_evaluation_report,
)


def render() -> None:
    """Render the test-design evaluation dashboard page."""
    st.header("测试设计评估")
    st.markdown(
        "使用固定 Golden Test Set 评估测试点生成质量，重点看需求覆盖、维度覆盖、"
        "引用覆盖和空输出。这个页面用于证明平台输出不是只靠主观感觉判断。"
    )

    test_set_path = st.text_input(
        "Golden Test Set",
        value=str(DEFAULT_TEST_DESIGN_GOLDEN_SET),
        key="tde_golden_set_path",
        help="默认使用项目内置的通用测试设计评估集。",
    )
    path = Path(test_set_path)

    if not path.exists():
        st.warning(f"未找到 Golden Test Set：{path}")
        return

    try:
        cases = load_test_design_golden_set(path)
    except Exception as exc:
        st.error(f"无法加载 Golden Test Set：{exc}")
        return

    st.caption(f"已加载 {len(cases)} 个评估用例。")
    with st.expander("评估用例预览", expanded=False):
        rows = [
            {
                "Case": case.case_id,
                "Scenario": case.scenario,
                "Focus Areas": ", ".join(case.focus_areas),
                "Evidence": len(case.evidence),
            }
            for case in cases
        ]
        st.dataframe(rows, hide_index=True, use_container_width=True)

    col1, col2 = st.columns([1, 2])
    with col1:
        run_clicked = st.button("运行测试设计评估", type="primary", use_container_width=True)
    with col2:
        output_path = st.text_input(
            "可选 JSON 报告输出路径",
            value=str(DEFAULT_TEST_DESIGN_REPORT_DIR / "test_design_report.json"),
            key="tde_output_path",
            help="只有点击保存时才会写文件，路径必须位于 data/evaluation/ 下。",
        )

    if run_clicked:
        try:
            st.session_state["test_design_evaluation_report"] = run_test_design_evaluation(path)
        except Exception as exc:
            st.error(f"评估运行失败：{exc}")
            return

    report = st.session_state.get("test_design_evaluation_report")
    if not report:
        st.info("点击“运行测试设计评估”后，这里会展示聚合指标和逐用例结果。")
        return

    st.subheader("聚合指标")
    metric_cols = st.columns(5)
    for idx, (name, value) in enumerate(sorted(report.aggregate_metrics.items())):
        metric_cols[idx % 5].metric(name.replace("_", " ").title(), f"{value:.4f}")

    st.caption(
        f"Test Set: `{report.test_set_path}` | Version: `{report.version}` | "
        f"Cases: `{report.case_count}` | Time: `{report.total_elapsed_ms:.1f} ms`"
    )

    st.subheader("逐用例结果")
    st.dataframe(report.to_rows(), hide_index=True, use_container_width=True)

    for result in report.case_results:
        with st.expander(f"{result.case_id} | overall={result.metrics['overall_score']:.3f}"):
            if result.missing_keywords:
                st.warning("缺失关键词：" + ", ".join(result.missing_keywords))
            if result.missing_focus_areas:
                st.warning("缺失维度：" + ", ".join(result.missing_focus_areas))
            if result.missing_citation_sources:
                st.warning("缺失引用：" + ", ".join(result.missing_citation_sources))
            st.markdown(result.generated_markdown)

    save_clicked = st.button("保存 JSON 报告", key="tde_save_report")
    if save_clicked:
        try:
            written_path = write_test_design_evaluation_report(report, output_path)
            st.success(f"已保存：{written_path}")
        except Exception as exc:
            st.error(f"保存失败：{exc}")

    st.subheader("JSON 预览")
    st.code(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), language="json")
