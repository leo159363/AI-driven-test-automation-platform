"""Unit tests for AI test workbench draft-generation services."""

from __future__ import annotations

from src.observability.dashboard.services.test_design_service import (
    KnowledgeHit,
    generate_test_design_draft,
    get_default_query,
)
from src.observability.dashboard.services.test_design_templates import (
    SCENARIO_BLUEPRINTS,
)


class TestTestDesignService:
    """Verify test design generation behavior and fallbacks."""

    def test_generate_draft_includes_scenario_requirement_and_evidence(self) -> None:
        evidence = [
            KnowledgeHit(
                chunk_id="chunk-1",
                source_path="docs/api/login.md",
                score=0.91,
                snippet="登录接口需要覆盖 token 过期和权限不足场景。",
            )
        ]

        draft = generate_test_design_draft(
            scenario="接口测试设计",
            requirement="设计登录接口的异常和安全测试点。",
            focus_areas=["异常", "安全"],
            evidence=evidence,
        )

        assert draft.focus_areas == ["异常", "安全"]
        assert "# 接口测试设计 测试设计草稿" in draft.markdown
        assert "设计登录接口的异常和安全测试点。" in draft.markdown
        assert "## 5. 关联知识片段" in draft.markdown
        assert "docs/api/login.md" in draft.markdown

    def test_empty_requirement_falls_back_to_template_copy(self) -> None:
        draft = generate_test_design_draft(
            scenario="需求文档解析",
            requirement="",
            focus_areas=["功能"],
            evidence=[],
        )

        assert "未额外输入，使用场景模板生成。" in draft.markdown

    def test_empty_focus_areas_fall_back_to_scenario_defaults(self) -> None:
        draft = generate_test_design_draft(
            scenario="接口测试设计",
            requirement="补充用户查询接口测试点。",
            focus_areas=[],
            evidence=[],
        )

        assert draft.focus_areas == list(SCENARIO_BLUEPRINTS["接口测试设计"]["defaults"])

    def test_no_fake_citations_when_evidence_is_empty(self) -> None:
        draft = generate_test_design_draft(
            scenario="知识库增强",
            requirement="根据历史缺陷补充测试点。",
            focus_areas=["功能", "回归"],
            evidence=[],
        )

        assert "## 5. 关联知识片段" not in draft.markdown
        assert "score=" not in draft.markdown

    def test_default_query_uses_requirement_or_scenario_name(self) -> None:
        assert get_default_query("Web UI 自动化", "覆盖登录页面冒烟。") == "覆盖登录页面冒烟。"
        assert get_default_query("Web UI 自动化", "   ") == "Web UI 自动化 测试点"
