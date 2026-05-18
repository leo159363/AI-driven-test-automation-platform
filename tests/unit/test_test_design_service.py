"""Unit tests for AI test workbench draft-generation services."""

from __future__ import annotations

from pathlib import Path

from src.observability.dashboard.services.test_design_service import (
    KnowledgeHit,
    format_knowledge_hit_title,
    generate_test_design_draft,
    get_default_query,
    infer_source_type,
    normalize_source_type,
)
from src.observability.dashboard.services.test_design_templates import (
    SCENARIO_BLUEPRINTS,
)


FIXTURE_SOURCE_DIR = Path("tests/fixtures/test_knowledge_sources")


class TestTestDesignService:
    """Verify test design generation behavior and fallbacks."""

    def test_generate_draft_includes_scenario_requirement_and_evidence(self) -> None:
        evidence = [
            KnowledgeHit(
                chunk_id="chunk-1",
                source_path="docs/api/login.md",
                score=0.91,
                snippet="登录接口需要覆盖 token 过期和权限不足场景。",
                source_type="api_doc",
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
        assert "API 文档" in draft.markdown
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

    def test_source_type_normalization_supports_expected_taxonomy(self) -> None:
        assert normalize_source_type("prd") == "requirement"
        assert normalize_source_type("openapi") == "api_doc"
        assert normalize_source_type("bug") == "defect"
        assert normalize_source_type("testing-standard") == "test_standard"
        assert normalize_source_type("junit") == "execution_log"
        assert normalize_source_type("") == "unknown"

    def test_source_type_prefers_metadata_then_path_fallback(self) -> None:
        assert infer_source_type(
            {"source_type": "defect"},
            "docs/api/login.md",
        ) == "defect"
        assert infer_source_type({}, "fixtures/requirements/login_prd.md") == "requirement"
        assert infer_source_type({}, "fixtures/api/auth_openapi.yaml") == "api_doc"
        assert infer_source_type({}, "fixtures/standards/api_test_standard.md") == "test_standard"
        assert infer_source_type({}, "reports/junit.xml") == "execution_log"
        assert infer_source_type({}, "docs/general_notes.md") == "unknown"
        assert infer_source_type({}, "sample_documents/blogger_intro.pdf") == "unknown"

    def test_knowledge_hit_title_renders_source_type_label(self) -> None:
        hit = KnowledgeHit(
            chunk_id="chunk-2",
            source_path="fixtures/defects/login_lockout.md",
            score=0.82,
            snippet="连续登录失败后需要锁定账户。",
            source_type="defect",
        )

        assert (
            format_knowledge_hit_title(1, hit)
            == "[1] 缺陷记录 | fixtures/defects/login_lockout.md | score=0.820"
        )

    def test_generic_test_knowledge_fixtures_cover_source_taxonomy(self) -> None:
        detected_source_types = set()
        for path in FIXTURE_SOURCE_DIR.glob("*.md"):
            content = path.read_text(encoding="utf-8")
            for line in content.splitlines():
                if line.startswith("source_type:"):
                    detected_source_types.add(normalize_source_type(line.split(":", 1)[1]))

        assert detected_source_types == {
            "requirement",
            "api_doc",
            "defect",
            "test_standard",
            "execution_log",
        }
