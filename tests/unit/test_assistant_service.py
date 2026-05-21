"""Unit tests for the AI testing assistant service."""

from __future__ import annotations

import pytest

from src.api.services.assistant_service import (
    build_assistant_response,
    get_prompt_template,
    list_prompt_templates,
    retrieve_local_contexts,
)


def test_list_prompt_templates_contains_core_testing_tasks() -> None:
    templates = list_prompt_templates()
    template_ids = {template["template_id"] for template in templates}

    assert {
        "test_case_generation",
        "api_test_design",
        "failure_analysis",
        "bug_report",
        "testability_review",
    }.issubset(template_ids)
    assert all(template["recommended_tools"] for template in templates)


def test_get_prompt_template_rejects_unknown_template() -> None:
    with pytest.raises(ValueError):
        get_prompt_template("missing")


def test_retrieve_local_contexts_filters_by_source_type_and_module() -> None:
    contexts = retrieve_local_contexts(
        query="登录接口 token 401",
        source_types=["api_doc", "standard"],
        module="登录鉴权",
        top_k=3,
    )

    assert contexts
    assert all(context["source_type"] in {"api_doc", "standard"} for context in contexts)
    assert contexts[0]["score"] >= contexts[-1]["score"]


@pytest.mark.asyncio
async def test_assistant_generates_test_cases_with_contexts() -> None:
    response = await build_assistant_response(
        template_id="test_case_generation",
        message="登录接口成功返回 token，错误密码返回 401",
        module="登录鉴权",
        use_knowledge=True,
    )

    assert response["result_type"] == "test_cases"
    assert response["contexts"]
    assert response["result"]["test_cases"]
    assert "测试用例草稿" in response["markdown"]


@pytest.mark.asyncio
async def test_assistant_generates_failure_analysis() -> None:
    response = await build_assistant_response(
        template_id="failure_analysis",
        message="test_api_login_success failed: AssertionError token missing",
        module="登录鉴权",
        use_knowledge=True,
    )

    assert response["result_type"] == "failure_analysis"
    assert response["result"]["analyses"]
    assert "失败分析草稿" in response["markdown"]


@pytest.mark.asyncio
async def test_assistant_generates_bug_report() -> None:
    response = await build_assistant_response(
        template_id="bug_report",
        message="登录成功接口返回 200 但是缺少 token 字段",
        module="登录鉴权",
        use_knowledge=True,
    )

    assert response["result_type"] == "bug_report"
    assert response["result"]["bug_reports"]
    assert "# " in response["markdown"]
