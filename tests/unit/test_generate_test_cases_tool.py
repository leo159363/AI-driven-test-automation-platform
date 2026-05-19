"""Unit tests for generate_test_cases MCP tool."""

from __future__ import annotations

import json
from typing import Any

import pytest

import src.mcp_server.tools.generate_test_cases as generate_module
from src.core.response.response_builder import MCPToolResponse


class FakeQueryTool:
    def __init__(self) -> None:
        self.kwargs: dict[str, Any] = {}

    async def execute(self, **kwargs: Any) -> MCPToolResponse:
        self.kwargs = kwargs
        return MCPToolResponse(
            content="markdown",
            structured_content={
                "collection": "knowledge_hub",
                "filters": {"project": "qualitypilot-demo"},
                "contexts": [
                    {
                        "chunk_id": "chunk-1",
                        "source_id": "auth-api-v1",
                        "source_type": "api_doc",
                        "title": "登录接口说明",
                        "content": "密码错误时返回 401。",
                        "score": 0.91,
                        "metadata": {"module": "auth"},
                    }
                ],
            },
        )


@pytest.mark.asyncio
async def test_generate_test_cases_handler_returns_structured_cases(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_tool = FakeQueryTool()
    monkeypatch.setattr(generate_module, "get_query_tool_instance", lambda: fake_tool)

    result = await generate_module.generate_test_cases_handler(
        requirement="登录接口密码错误时返回 401",
        project="qualitypilot-demo",
        module="auth",
        version="v1",
        source_types=["api_doc", "bug"],
        dimensions=["functional", "negative", "security"],
        case_count=3,
        top_k=4,
    )

    assert result.isError is False
    payload = json.loads(result.content[0].text)
    assert payload["requirement"] == "登录接口密码错误时返回 401"
    assert payload["generation_strategy"] == "rule_based_with_rag_context"
    assert payload["dimensions"] == ["functional", "negative", "security"]
    assert len(payload["test_cases"]) == 3
    assert payload["test_cases"][0]["case_id"] == "TC-001"
    assert payload["test_cases"][0]["priority"] == "P1"
    assert payload["test_cases"][0]["citations"][0]["source_id"] == "auth-api-v1"
    assert payload["test_cases"][0]["automation_hint"]["suggested_file"] == (
        "pytest_tests/api/test_qualitypilot_demo_auth.py"
    )
    assert payload["context_summary"]["source_type_distribution"] == {"api_doc": 1}

    assert fake_tool.kwargs["query"] == "登录接口密码错误时返回 401"
    assert fake_tool.kwargs["project"] == "qualitypilot-demo"
    assert fake_tool.kwargs["module"] == "auth"
    assert fake_tool.kwargs["version"] == "v1"
    assert fake_tool.kwargs["source_types"] == ["api_doc", "bug"]
    assert fake_tool.kwargs["top_k"] == 4


@pytest.mark.asyncio
async def test_generate_test_cases_falls_back_when_context_retrieval_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FailingQueryTool:
        async def execute(self, **kwargs: Any) -> MCPToolResponse:
            raise RuntimeError("embedding service unavailable")

    monkeypatch.setattr(
        generate_module,
        "get_query_tool_instance",
        lambda: FailingQueryTool(),
    )

    payload = await generate_module.generate_test_cases_payload(
        requirement="用户登录成功后进入首页",
        dimensions=["functional"],
        case_count=1,
    )

    assert payload["context_warning"] == (
        "RAG context retrieval failed: embedding service unavailable"
    )
    assert len(payload["test_cases"]) == 1
    assert payload["test_cases"][0]["citations"] == []


@pytest.mark.asyncio
async def test_generate_test_cases_handler_rejects_empty_requirement() -> None:
    result = await generate_module.generate_test_cases_handler(requirement="  ")

    assert result.isError is True
    payload = json.loads(result.content[0].text)
    assert payload["error"] == "requirement cannot be empty"


def test_generate_test_cases_normalizes_dimensions_and_limits_count() -> None:
    assert generate_module._normalize_dimensions(["FUNCTIONAL", "unknown", "security"]) == [
        "functional",
        "security",
    ]
    assert generate_module._clamp_int(99, minimum=1, maximum=12, default=6) == 12


@pytest.mark.asyncio
async def test_generate_test_cases_uses_pre_retrieved_contexts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class UnexpectedQueryTool:
        async def execute(self, **kwargs: Any) -> MCPToolResponse:
            raise AssertionError("live retrieval should be skipped")

    monkeypatch.setattr(
        generate_module,
        "get_query_tool_instance",
        lambda: UnexpectedQueryTool(),
    )

    payload = await generate_module.generate_test_cases_payload(
        requirement="login returns token",
        dimensions=["functional"],
        case_count=1,
        contexts=[
            {
                "context_id": "ctx-1",
                "source_id": "auth-api-v1",
                "source_type": "api_doc",
                "title": "Login API",
                "content": "Login should return token.",
                "score": 0.9,
            }
        ],
    )

    assert "context_warning" not in payload
    assert payload["context_summary"]["source_type_distribution"] == {"api_doc": 1}
    assert payload["test_cases"][0]["citations"][0]["chunk_id"] == "ctx-1"
