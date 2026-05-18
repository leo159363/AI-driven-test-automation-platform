"""Streamlit page for the AI-assisted test workbench."""

from __future__ import annotations

from typing import List

import streamlit as st

from src.observability.dashboard.services import (
    FOCUS_OPTIONS,
    KnowledgeHit,
    SCENARIO_BLUEPRINTS,
    format_knowledge_hit_title,
    generate_test_design_draft,
    get_default_query,
    retrieve_knowledge_hits,
)


def _render_hits(hits: List[KnowledgeHit]) -> None:
    """Render retrieval hits as expandable cards."""
    if not hits:
        st.info(
            "暂无知识片段。可以先生成草稿，或去“测试资料入库”页上传 PRD、接口文档和测试资料。"
        )
        return

    for idx, hit in enumerate(hits, start=1):
        with st.expander(
            format_knowledge_hit_title(idx, hit),
            expanded=(idx == 1),
        ):
            st.caption(f"source_type: {hit.source_type} | chunk_id: {hit.chunk_id}")
            st.write(hit.snippet)


def render() -> None:
    """Render the AI test workbench page."""
    st.header("AI 驱动的自动化测试平台 | 测试工作台")
    st.markdown(
        "把 **需求描述、测试资产、知识检索和回归建议** 放到一个工作台里。"
        "这页不是完整的企业级测试平台，而是基于现有 RAG Dashboard 搭出的测试设计原型。"
    )

    scenario = st.selectbox(
        "业务场景",
        options=list(SCENARIO_BLUEPRINTS.keys()),
        index=0,
        help="优先选择你当前要演示的业务场景，页面会给出对应测试模板。",
    )
    blueprint = SCENARIO_BLUEPRINTS[scenario]

    col_left, col_right = st.columns([3, 2])
    with col_left:
        requirement = st.text_area(
            "需求 / 功能说明",
            height=160,
            placeholder=(
                "例如：用户上传一份需求文档后，系统需要解析模块、生成测试点，"
                "并引用相关历史缺陷或测试规范。"
            ),
            key="tw_requirement",
        )

    with col_right:
        st.info(blueprint["summary"])
        focus_areas = st.multiselect(
            "关注维度",
            options=FOCUS_OPTIONS,
            default=blueprint["defaults"],
            key="tw_focus",
        )
        collection = st.text_input(
            "知识库 Collection",
            value="default",
            key="tw_collection",
            help="用于指定检索范围；如果未做业务分库，可以保持 default。",
        )
        top_k = st.slider(
            "召回片段数量",
            min_value=1,
            max_value=8,
            value=4,
            key="tw_top_k",
        )
        auto_retrieve = st.checkbox(
            "生成草稿时同时检索知识片段",
            value=True,
            key="tw_auto_retrieve",
        )

    query = st.text_input(
        "知识检索 Query",
        value=get_default_query(scenario, requirement),
        key="tw_query",
        help=(
            "可直接问：接口错误码如何覆盖？需求里的边界条件如何补齐？"
            "UI 自动化步骤如何拆解？"
        ),
    )

    action_col1, action_col2 = st.columns(2)
    with action_col1:
        generate_clicked = st.button(
            "生成测试点草稿",
            type="primary",
            use_container_width=True,
        )
    with action_col2:
        retrieve_clicked = st.button(
            "仅检索知识片段",
            use_container_width=True,
        )

    if generate_clicked:
        hits: List[KnowledgeHit] = []
        warning: str | None = None
        if auto_retrieve:
            hits, warning = retrieve_knowledge_hits(
                query=query,
                collection=collection.strip() or "default",
                top_k=int(top_k),
            )

        draft = generate_test_design_draft(
            scenario=scenario,
            requirement=requirement,
            focus_areas=focus_areas,
            evidence=hits,
        )
        st.session_state["tw_draft"] = draft.markdown
        st.session_state["tw_hits"] = hits
        st.session_state["tw_warning"] = warning

    if retrieve_clicked:
        hits, warning = retrieve_knowledge_hits(
            query=query,
            collection=collection.strip() or "default",
            top_k=int(top_k),
        )
        st.session_state["tw_hits"] = hits
        st.session_state["tw_warning"] = warning

    tabs = st.tabs(["测试点草稿", "知识片段", "平台定位"])

    with tabs[0]:
        draft = st.session_state.get("tw_draft")
        if draft:
            st.markdown(draft)
            st.download_button(
                "导出 Markdown",
                data=draft,
                file_name="test_design_draft.md",
                mime="text/markdown",
            )
        else:
            st.info("点击“生成测试点草稿”后，这里会展示结构化测试设计结果。")

    with tabs[1]:
        warning = st.session_state.get("tw_warning")
        if warning:
            st.warning(warning)
        _render_hits(st.session_state.get("tw_hits", []))

    with tabs[2]:
        st.markdown(
            """
### 这页能讲什么？
- 需求录入：输入业务场景和功能说明，生成结构化测试点草稿。
- 知识辅助：对接本地 RAG 知识库，召回 PRD、缺陷单、历史测试资料。
- 回归建议：给出推荐测试层级和高风险回归范围。
- 结果导出：生成 Markdown 初稿，供测试人员继续补充。

### 这页不该硬讲什么？
- 它不是完整的企业级用例管理系统。
- 它不是已经做完项目管理、权限体系和多租户流程的 SaaS 产品。
- 它更适合作为“智能测试工作台原型”来讲，重点在测试设计和知识复用。
            """.strip()
        )
