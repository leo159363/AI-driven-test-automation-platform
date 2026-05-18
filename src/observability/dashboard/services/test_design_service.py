"""Draft generation services for the AI test workbench."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from src.observability.dashboard.services.test_design_templates import (
    SCENARIO_BLUEPRINTS,
)

SOURCE_TYPE_LABELS: Dict[str, str] = {
    "requirement": "需求文档",
    "api_doc": "API 文档",
    "defect": "缺陷记录",
    "test_standard": "测试规范",
    "execution_log": "执行日志",
    "unknown": "未知来源",
}

SOURCE_TYPE_ALIASES: Dict[str, str] = {
    "requirement": "requirement",
    "requirements": "requirement",
    "prd": "requirement",
    "product_requirement": "requirement",
    "user_story": "requirement",
    "story": "requirement",
    "需求": "requirement",
    "需求文档": "requirement",
    "需求_文档": "requirement",
    "api": "api_doc",
    "api_doc": "api_doc",
    "api_document": "api_doc",
    "openapi": "api_doc",
    "swagger": "api_doc",
    "interface": "api_doc",
    "接口": "api_doc",
    "接口文档": "api_doc",
    "接口_文档": "api_doc",
    "api_文档": "api_doc",
    "defect": "defect",
    "bug": "defect",
    "issue": "defect",
    "jira": "defect",
    "缺陷": "defect",
    "缺陷记录": "defect",
    "缺陷_记录": "defect",
    "test_standard": "test_standard",
    "standard": "test_standard",
    "testing_standard": "test_standard",
    "guideline": "test_standard",
    "checklist": "test_standard",
    "测试规范": "test_standard",
    "测试_规范": "test_standard",
    "规范": "test_standard",
    "execution_log": "execution_log",
    "execution": "execution_log",
    "log": "execution_log",
    "report": "execution_log",
    "junit": "execution_log",
    "allure": "execution_log",
    "trace": "execution_log",
    "执行日志": "execution_log",
    "执行_日志": "execution_log",
    "测试报告": "execution_log",
    "测试_报告": "execution_log",
    "unknown": "unknown",
}

SOURCE_TYPE_METADATA_KEYS: Tuple[str, ...] = (
    "source_type",
    "document_type",
    "doc_type",
    "type",
    "category",
    "source_category",
)

SOURCE_TYPE_PATH_HINTS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    (
        "requirement",
        (
            "requirement",
            "requirements",
            "prd",
            "product_requirement",
            "user_story",
            "story",
            "需求",
        ),
    ),
    (
        "test_standard",
        (
            "test_standard",
            "testing_standard",
            "standard",
            "guideline",
            "checklist",
            "测试规范",
            "规范",
            "准入",
        ),
    ),
    (
        "api_doc",
        (
            "api_doc",
            "api",
            "openapi",
            "swagger",
            "interface",
            "接口",
        ),
    ),
    (
        "defect",
        (
            "defect",
            "bug",
            "issue",
            "jira",
            "incident",
            "缺陷",
            "故障",
        ),
    ),
    (
        "execution_log",
        (
            "execution_log",
            "execution",
            "log",
            "report",
            "junit",
            "allure",
            "trace",
            "执行日志",
            "测试报告",
        ),
    ),
)


@dataclass(frozen=True)
class KnowledgeHit:
    """Lightweight retrieval result for dashboard display."""

    chunk_id: str
    source_path: str
    score: float
    snippet: str
    source_type: str = "unknown"

    @property
    def source_type_label(self) -> str:
        """Return the human-readable source type label."""
        return SOURCE_TYPE_LABELS.get(self.source_type, SOURCE_TYPE_LABELS["unknown"])


@dataclass(frozen=True)
class TestDesignDraft:
    """Structured test-design draft returned by the service layer."""

    scenario: str
    requirement: str
    focus_areas: List[str]
    markdown: str
    evidence: List[KnowledgeHit]


def normalize_source_type(value: object) -> str:
    """Normalize user-provided or metadata-provided source type values."""
    if value is None:
        return "unknown"

    raw_value = str(value).strip()
    if not raw_value:
        return "unknown"

    normalized = (
        raw_value.lower()
        .replace("-", "_")
        .replace(" ", "_")
        .replace(".", "_")
        .replace("/", "_")
    )
    return SOURCE_TYPE_ALIASES.get(normalized) or SOURCE_TYPE_ALIASES.get(
        raw_value,
        "unknown",
    )


def infer_source_type(
    metadata: Mapping[str, Any] | None = None,
    source_path: str = "",
) -> str:
    """Infer source type from metadata first, then from path/title hints."""
    metadata = metadata or {}

    for key in SOURCE_TYPE_METADATA_KEYS:
        source_type = normalize_source_type(metadata.get(key))
        if source_type != "unknown":
            return source_type

    hint_parts: List[str] = [source_path]
    for key in ("source_path", "title", "summary", "tags"):
        value = metadata.get(key)
        if isinstance(value, (list, tuple, set)):
            hint_parts.extend(str(item) for item in value)
        elif value is not None:
            hint_parts.append(str(value))

    normalized_hints = " ".join(hint_parts).lower().replace("\\", "/")
    for source_type, hints in SOURCE_TYPE_PATH_HINTS:
        if any(_matches_source_hint(normalized_hints, hint) for hint in hints):
            return source_type
    return "unknown"


def _matches_source_hint(text: str, hint: str) -> bool:
    """Return whether a source hint is present without broad substring matches."""
    if any("\u4e00" <= char <= "\u9fff" for char in hint):
        return hint in text

    tokens = set(re.split(r"[^a-z0-9]+", text.replace("_", " ")))
    hint_tokens = [token for token in hint.replace("_", " ").split(" ") if token]
    return bool(hint_tokens) and all(token in tokens for token in hint_tokens)


def format_knowledge_hit_title(index: int, hit: KnowledgeHit) -> str:
    """Return the title used by the workbench retrieval result expander."""
    return (
        f"[{index}] {hit.source_type_label} | {hit.source_path} | "
        f"score={hit.score:.3f}"
    )


def get_scenario_blueprint(scenario: str) -> Dict[str, Any]:
    """Return the template for a scenario, raising on unknown keys."""
    try:
        return SCENARIO_BLUEPRINTS[scenario]
    except KeyError as exc:
        available = ", ".join(sorted(SCENARIO_BLUEPRINTS))
        raise ValueError(
            f"Unknown test-design scenario: {scenario}. Available scenarios: {available}"
        ) from exc


def get_focus_areas(scenario: str, focus_areas: Sequence[str]) -> List[str]:
    """Resolve requested focus areas, falling back to scenario defaults."""
    blueprint = get_scenario_blueprint(scenario)
    selected = [area for area in focus_areas if area]
    if selected:
        return selected
    return list(blueprint["defaults"])


def get_default_query(scenario: str, requirement: str) -> str:
    """Return the retrieval query shown in the UI."""
    requirement = requirement.strip()
    if requirement:
        return requirement
    return f"{scenario} 测试点"


def build_common_cases(requirement: str) -> List[str]:
    """Generate generic test cases from the requirement text."""
    requirement = requirement.strip()
    if not requirement:
        return []

    summary = requirement[:36]
    suffix = "..." if len(requirement) > 36 else ""
    return [
        "基于当前需求梳理主成功流，补齐前置条件、核心步骤和预期结果。",
        "关注参数合法性、空值、越界值、特殊字符与重复提交场景。",
        "核对状态码、错误提示、日志记录与可观测字段是否齐全。",
        f"针对需求描述中的关键点“{summary}{suffix}”补充业务回归。",
    ]


def build_test_outline(
    scenario: str,
    requirement: str,
    focus_areas: Sequence[str],
    evidence: Sequence[KnowledgeHit],
) -> str:
    """Build a markdown draft that feels like a test platform output."""
    blueprint = get_scenario_blueprint(scenario)
    resolved_focus_areas = get_focus_areas(scenario, focus_areas)
    sections = blueprint["sections"]
    lines: List[str] = [
        f"# {scenario} 测试设计草稿",
        "",
        "## 1. 测试背景",
        f"- 场景说明：{blueprint['summary']}",
        f"- 需求输入：{requirement.strip() or '未额外输入，使用场景模板生成。'}",
        f"- 关注维度：{', '.join(resolved_focus_areas)}",
        "",
        "## 2. 推荐测试层级",
    ]

    for item in blueprint["automation"]:
        lines.append(f"- {item}")

    lines.extend(["", "## 3. 测试点"])
    for focus in resolved_focus_areas:
        items = sections.get(focus, [])
        if not items:
            continue
        lines.append(f"### {focus}")
        for item in items:
            lines.append(f"- {item}")
        lines.append("")

    common_cases = build_common_cases(requirement)
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
                f"- [{idx}] `{hit.source_type_label}` | `{hit.source_path}` | "
                f"score={hit.score:.3f} | {hit.snippet}"
            )
        lines.append("")

    lines.extend(
        [
            "## 6. 说明",
            "- 当前草稿优先保证结构化输出，适合作为测试点初稿和回归清单。",
            "- 若已配置知识库与检索能力，可进一步结合真实文档做细化。",
        ]
    )
    return "\n".join(lines)


def generate_test_design_draft(
    scenario: str,
    requirement: str,
    focus_areas: Sequence[str],
    evidence: Sequence[KnowledgeHit],
) -> TestDesignDraft:
    """Generate a test-design draft with normalized focus areas."""
    resolved_focus_areas = get_focus_areas(scenario, focus_areas)
    markdown = build_test_outline(
        scenario=scenario,
        requirement=requirement,
        focus_areas=resolved_focus_areas,
        evidence=evidence,
    )
    return TestDesignDraft(
        scenario=scenario,
        requirement=requirement,
        focus_areas=resolved_focus_areas,
        markdown=markdown,
        evidence=list(evidence),
    )


def retrieve_knowledge_hits(
    query: str,
    collection: str,
    top_k: int,
) -> Tuple[List[KnowledgeHit], str | None]:
    """Retrieve context from the local RAG knowledge base when available."""
    query = query.strip()
    if not query:
        return [], "请输入检索 Query。"

    try:
        from src.core.settings import load_settings
        from src.observability.dashboard.pages.evaluation_panel import (
            _try_create_hybrid_search,
        )

        settings = load_settings()
        hybrid_search = _try_create_hybrid_search(settings, collection=collection)
        if hybrid_search is None:
            return (
                [],
                "知识库未就绪：当前无法创建 Hybrid Search，可先去“测试资料入库”页导入文档。",
            )

        results = hybrid_search.search(query=query, top_k=top_k)
        hits: List[KnowledgeHit] = []
        for result in results:
            metadata = result.metadata or {}
            source_path = str(metadata.get("source_path", "unknown"))
            hits.append(
                KnowledgeHit(
                    chunk_id=result.chunk_id,
                    source_path=source_path,
                    score=float(result.score),
                    snippet=result.text.strip().replace("\n", " ")[:180],
                    source_type=infer_source_type(metadata, source_path),
                )
            )
        if not hits:
            return [], "未检索到相关知识片段，可以换一个 Query 或先导入资料。"
        return hits, None
    except Exception as exc:
        return [], f"知识检索暂不可用：{exc}"
