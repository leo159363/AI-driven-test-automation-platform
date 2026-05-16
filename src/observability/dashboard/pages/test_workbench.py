"""Streamlit page for a lightweight AI-assisted test workbench."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import streamlit as st


FOCUS_OPTIONS = ["功能", "边界", "异常", "安全", "并发", "回归"]


SCENARIO_BLUEPRINTS: Dict[str, Dict[str, Any]] = {
    "需求文档解析": {
        "summary": "适合从 PRD、Axure 说明、接口文档或文本需求中拆解测试对象。",
        "defaults": ["功能", "边界", "异常", "回归"],
        "sections": {
            "功能": [
                "识别需求中的业务目标、用户角色、功能入口和核心流程。",
                "拆分可测试模块，并明确每个模块的输入、处理和输出。",
                "补齐前置条件、测试步骤、预期结果和数据准备要求。",
            ],
            "边界": [
                "覆盖必填/选填字段、字段长度、枚举值、空值和格式约束。",
                "识别需求中未说明但影响测试的默认值、权限和状态限制。",
            ],
            "异常": [
                "补充接口失败、依赖服务不可用、网络超时和数据不一致场景。",
                "标记需求描述不清、规则冲突或验收标准缺失的风险点。",
            ],
            "回归": [
                "将本次需求影响到的已有功能、接口契约和关键业务链路加入回归范围。",
            ],
        },
        "automation": [
            "需求解析：从输入文本中提取模块、规则、字段和验收标准。",
            "用例生成：按功能、边界、异常、回归维度生成测试点草稿。",
            "评审辅助：输出需求疑问和风险列表，供测试评审使用。",
        ],
        "regression": [
            "需求主流程",
            "字段规则",
            "接口契约",
            "影响范围",
        ],
    },
    "接口测试设计": {
        "summary": "适合 REST API、RPC 接口、服务间调用和契约校验场景。",
        "defaults": ["功能", "边界", "异常", "安全", "回归"],
        "sections": {
            "功能": [
                "验证接口在合法请求下返回正确状态码、响应结构和业务数据。",
                "覆盖新增、查询、修改、删除等核心操作的正向路径。",
                "检查接口幂等性、分页、排序、过滤和状态流转行为。",
            ],
            "边界": [
                "覆盖缺失参数、非法类型、超长字段、边界数值和重复提交。",
                "验证空列表、无数据、最大分页、最小分页等边界响应。",
            ],
            "异常": [
                "模拟下游超时、数据库错误、第三方接口失败和重试失败。",
                "验证错误码、错误提示、日志字段和告警信息是否可定位。",
            ],
            "安全": [
                "校验未认证、权限不足、越权访问和敏感字段泄露风险。",
                "验证请求签名、token 过期、参数篡改和重放请求处理。",
            ],
            "回归": [
                "接口字段、状态码、错误码和兼容性契约不因迭代回退。",
            ],
        },
        "automation": [
            "接口自动化：生成 pytest/httpx 或 Postman/Newman 测试清单。",
            "契约测试：校验请求参数、响应 schema 和错误码规范。",
            "Mock 测试：隔离下游依赖，覆盖异常和超时分支。",
        ],
        "regression": [
            "核心接口",
            "参数校验",
            "错误码契约",
            "权限边界",
        ],
    },
    "Web UI 自动化": {
        "summary": "适合 Web 页面冒烟、端到端流程和自然语言步骤转自动化脚本。",
        "defaults": ["功能", "边界", "异常", "回归"],
        "sections": {
            "功能": [
                "覆盖页面入口、表单填写、按钮点击、跳转和结果展示。",
                "验证关键用户路径在桌面端和常用浏览器中可正常完成。",
                "检查页面状态、loading、空态、成功提示和失败提示。",
            ],
            "边界": [
                "覆盖表单空值、非法格式、超长输入、重复点击和刷新返回。",
                "检查弹窗、分页、筛选、搜索和批量操作的边界表现。",
            ],
            "异常": [
                "模拟接口 4xx/5xx、网络中断和超时，验证页面可恢复反馈。",
                "检查前端错误不会导致白屏，关键错误可被日志或监控捕获。",
            ],
            "回归": [
                "将核心页面冒烟、关键路径和高频操作加入自动化回归。",
            ],
        },
        "automation": [
            "UI E2E：将自然语言步骤拆解为 Playwright 执行动作。",
            "截图留痕：失败时保存截图、DOM 状态和执行日志。",
            "冒烟回归：围绕核心页面入口建立稳定的 smoke suite。",
        ],
        "regression": [
            "核心页面打开",
            "关键用户路径",
            "表单校验",
            "错误态展示",
        ],
    },
    "知识库增强": {
        "summary": "适合用历史缺陷、测试规范、业务规则和项目文档增强测试设计。",
        "defaults": ["功能", "异常", "回归"],
        "sections": {
            "功能": [
                "根据需求 query 检索相关规则、历史缺陷、测试规范和案例片段。",
                "在测试点中展示引用来源，便于测试人员复核依据。",
                "支持按 collection 限定知识范围，区分项目、模块或资料类型。",
            ],
            "异常": [
                "知识库为空、索引未构建、向量库不可用时给出可理解提示。",
                "召回结果为空或相关性不足时，不编造引用和结论。",
            ],
            "回归": [
                "对 Golden Test Set 的召回命中率、排序质量和引用覆盖持续回归。",
            ],
        },
        "automation": [
            "RAG 检索：混合检索召回测试知识片段。",
            "证据增强：将引用片段附加到测试设计草稿。",
            "质量评估：用 Hit Rate、MRR、Faithfulness 监控检索质量。",
        ],
        "regression": [
            "知识导入",
            "混合检索",
            "引用展示",
            "评估指标",
        ],
    },
    "回归评估": {
        "summary": "适合建立测试生成质量、检索质量和版本迭代质量的基准线。",
        "defaults": ["功能", "边界", "异常", "回归"],
        "sections": {
            "功能": [
                "定义标准需求输入、期望测试点和关联知识片段。",
                "生成测试设计后，对覆盖率、结构完整性和引用质量进行评分。",
                "输出可保存的评估报告，便于比较不同版本效果。",
            ],
            "边界": [
                "覆盖短需求、长需求、模糊需求、缺少上下文和混合语言输入。",
                "检查重复测试点、空输出、格式异常和引用数量异常。",
            ],
            "异常": [
                "LLM 不可用、检索失败或评估器异常时，保留可追踪错误信息。",
                "评估报告生成失败时，不影响测试草稿本身的导出。",
            ],
            "回归": [
                "每次修改生成逻辑、检索策略或模板后运行固定评估集。",
            ],
        },
        "automation": [
            "Golden Test Set：维护固定需求和期望结果。",
            "指标评估：计算覆盖率、命中率、排序质量和格式合规性。",
            "报告生成：输出 JSON/Markdown 评估报告。",
        ],
        "regression": [
            "固定测试集",
            "覆盖率指标",
            "检索指标",
            "报告生成",
        ],
    },
}


@dataclass
class KnowledgeHit:
    """Lightweight retrieval result for dashboard display."""

    chunk_id: str
    source_path: str
    score: float
    snippet: str


def _build_common_cases(requirement: str) -> List[str]:
    """Generate generic test cases from the requirement text."""
    requirement = requirement.strip()
    if not requirement:
        return []

    return [
        "基于当前需求梳理主成功流，补齐前置条件、核心步骤和预期结果。",
        "关注参数合法性、空值、越界值、特殊字符与重复提交场景。",
        "核对接口状态码、错误提示、日志记录与可观测字段是否齐全。",
        f"针对需求描述中的关键点“{requirement[:36]}{'...' if len(requirement) > 36 else ''}”补充业务回归。",
    ]


def _build_test_outline(
    scenario: str,
    requirement: str,
    focus_areas: List[str],
    evidence: List[KnowledgeHit],
) -> str:
    """Build a markdown draft that feels like a test platform output."""
    blueprint = SCENARIO_BLUEPRINTS[scenario]
    lines: List[str] = []
    lines.append(f"# {scenario} 测试设计草稿")
    lines.append("")
    lines.append("## 1. 测试背景")
    lines.append(f"- 场景说明：{blueprint['summary']}")
    lines.append(f"- 需求输入：{requirement.strip() or '未额外输入，使用场景模板生成。'}")
    lines.append(f"- 关注维度：{', '.join(focus_areas)}")
    lines.append("")
    lines.append("## 2. 推荐测试层级")
    for item in blueprint["automation"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## 3. 测试点")

    sections = blueprint["sections"]
    for focus in focus_areas:
        items = sections.get(focus, [])
        if not items:
            continue
        lines.append(f"### {focus}")
        for item in items:
            lines.append(f"- {item}")
        lines.append("")

    common_cases = _build_common_cases(requirement)
    if common_cases:
        lines.append("### 通用补充")
        for item in common_cases:
            lines.append(f"- {item}")
        lines.append("")

    lines.append("## 4. 回归建议")
    for item in blueprint["regression"]:
        lines.append(f"- {item}")
    lines.append("")

    if evidence:
        lines.append("## 5. 关联知识片段")
        for idx, hit in enumerate(evidence[:5], start=1):
            lines.append(
                f"- [{idx}] `{hit.source_path}` | score={hit.score:.3f} | {hit.snippet}"
            )
        lines.append("")

    lines.append("## 6. 说明")
    lines.append("- 当前草稿优先保证结构化输出，适合作为测试点初稿和回归清单。")
    lines.append("- 若配置了知识库与检索能力，可进一步结合真实文档做细化。")
    return "\n".join(lines)


def _fetch_knowledge_hits(
    query: str,
    collection: str,
    top_k: int,
) -> Tuple[List[KnowledgeHit], str | None]:
    """Retrieve context from the local RAG knowledge base when available."""
    try:
        from src.core.settings import load_settings
        from src.observability.dashboard.pages.evaluation_panel import (
            _try_create_hybrid_search,
        )

        settings = load_settings()
        hybrid_search = _try_create_hybrid_search(settings, collection=collection)
        if hybrid_search is None:
            return [], "知识库未就绪：当前无法创建 Hybrid Search，可先去“测试资料入库”页导入文档。"

        results = hybrid_search.search(query=query, top_k=top_k)
        hits = [
            KnowledgeHit(
                chunk_id=result.chunk_id,
                source_path=str(result.metadata.get("source_path", "unknown")),
                score=float(result.score),
                snippet=result.text.strip().replace("\n", " ")[:180],
            )
            for result in results
        ]
        if not hits:
            return [], "未检索到相关知识片段，可以换一个 query 或先导入资料。"
        return hits, None
    except Exception as exc:
        return [], f"知识检索暂不可用：{exc}"


def _render_hits(hits: List[KnowledgeHit]) -> None:
    """Render retrieval hits as expandable cards."""
    if not hits:
        st.info("暂无知识片段。可以先生成草稿，或去“测试资料入库”页上传 PRD / 测试文档。")
        return

    for idx, hit in enumerate(hits, start=1):
        with st.expander(
            f"[{idx}] {hit.source_path} | score={hit.score:.3f}",
            expanded=(idx == 1),
        ):
            st.caption(f"chunk_id: {hit.chunk_id}")
            st.write(hit.snippet)


def render() -> None:
    """Render the AI test workbench page."""
    st.header("AI 驱动的自动化测试平台 | 测试工作台")
    st.markdown(
        "把**需求描述、测试资产、知识检索和回归建议**放到一个工作台里。"
        "这页不是完整的 ALSys，而是基于现有 RAG Dashboard 做的测试平台原型。"
    )

    scenario = st.selectbox(
        "业务场景",
        options=list(SCENARIO_BLUEPRINTS.keys()),
        index=0,
        help="优先选择你当前要讲的业务场景，页面会给出对应的测试模板。",
    )
    blueprint = SCENARIO_BLUEPRINTS[scenario]

    col_left, col_right = st.columns([3, 2])
    with col_left:
        requirement = st.text_area(
            "需求 / 功能说明",
            height=160,
            placeholder="例如：用户上传一份需求文档后，系统需要解析模块、生成测试点，并引用相关历史缺陷或测试规范。",
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

    default_query = requirement.strip() or f"{scenario} 测试点"
    query = st.text_input(
        "知识检索 Query",
        value=default_query,
        key="tw_query",
            help="可直接问：接口错误码如何覆盖？需求里的边界条件如何补齐？UI 自动化步骤如何拆解？",
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
        if auto_retrieve and query.strip():
            hits, warning = _fetch_knowledge_hits(
                query=query.strip(),
                collection=collection.strip() or "default",
                top_k=int(top_k),
            )
        draft = _build_test_outline(
            scenario=scenario,
            requirement=requirement,
            focus_areas=focus_areas or blueprint["defaults"],
            evidence=hits,
        )
        st.session_state["tw_draft"] = draft
        st.session_state["tw_hits"] = hits
        st.session_state["tw_warning"] = warning

    if retrieve_clicked:
        hits, warning = _fetch_knowledge_hits(
            query=query.strip(),
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
                use_container_width=False,
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
### 这页能讲什么

- 需求录入：输入业务场景和功能说明，生成结构化测试点草稿。
- 知识辅助：对接本地 RAG 知识库，召回 PRD、缺陷单、历史测试资料。
- 回归建议：给出推荐测试层级和高风险回归范围。
- 结果导出：生成 Markdown 初稿，供测试人员继续补充。

### 这页不该硬讲什么

- 它不是完整的企业级用例管理系统。
- 它不是截图里那种已经做完登录、项目管理、XMind 流转的 SaaS 产品。
- 它更适合作为“智能测试工作台原型”来讲，重点在测试设计和知识复用。
            """.strip()
        )
