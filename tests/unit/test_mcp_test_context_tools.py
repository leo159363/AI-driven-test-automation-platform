"""Unit tests for test-development MCP tool behavior."""

from __future__ import annotations

import json
from typing import Any

import pytest

from src.core.response.response_builder import MCPToolResponse
from src.core.types import RetrievalResult
from src.mcp_server.tools import retrieve_test_context as retrieve_module
from src.mcp_server.tools.query_knowledge_hub import QueryKnowledgeHubTool


def test_query_knowledge_hub_builds_test_metadata_filters() -> None:
    tool = QueryKnowledgeHubTool()

    filters = tool._build_metadata_filters(
        project="qualitypilot-demo",
        module="auth",
        version="v1",
        source_types=["API_DOC", "bug", "unknown", "bug"],
    )

    assert filters == {
        "project": "qualitypilot-demo",
        "module": "auth",
        "version": "v1",
        "source_type": ["api_doc", "bug"],
    }


def test_query_knowledge_hub_structured_payload_contains_context_fields() -> None:
    tool = QueryKnowledgeHubTool()
    result = RetrievalResult(
        chunk_id="chunk-1",
        score=0.87654,
        text="Password error returns 401.",
        metadata={
            "source_id": "auth-api-v1",
            "source_type": "api_doc",
            "title": "Auth API",
            "project": "qualitypilot-demo",
        },
    )

    payload = tool._build_structured_payload(
        query="login failure",
        results=[result],
        collection="knowledge_hub",
        filters={"project": "qualitypilot-demo"},
    )

    assert payload["query"] == "login failure"
    assert payload["collection"] == "knowledge_hub"
    assert payload["contexts"][0]["source_id"] == "auth-api-v1"
    assert payload["contexts"][0]["source_type"] == "api_doc"
    assert payload["contexts"][0]["title"] == "Auth API"
    assert payload["contexts"][0]["content"] == "Password error returns 401."
    assert payload["contexts"][0]["score"] == 0.8765


@pytest.mark.asyncio
async def test_retrieve_test_context_returns_structured_json(monkeypatch: pytest.MonkeyPatch) -> None:
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
                            "title": "Auth API",
                            "content": "Wrong password returns 401.",
                            "score": 0.91,
                            "metadata": {},
                        }
                    ],
                },
            )

    fake_tool = FakeQueryTool()
    monkeypatch.setattr(
        retrieve_module,
        "get_query_tool_instance",
        lambda: fake_tool,
    )

    result = await retrieve_module.retrieve_test_context_handler(
        query="wrong password",
        project="qualitypilot-demo",
        module="auth",
        version="v1",
        source_types=["api_doc"],
        top_k=3,
    )

    assert result.isError is False
    payload = json.loads(result.content[0].text)
    assert payload["query"] == "wrong password"
    assert payload["contexts"][0]["source_id"] == "auth-api-v1"
    assert payload["recommended_usage"] == [
        "test_case_generation",
        "failure_analysis",
        "bug_report_generation",
    ]
    assert fake_tool.kwargs["project"] == "qualitypilot-demo"
    assert fake_tool.kwargs["source_types"] == ["api_doc"]
    assert fake_tool.kwargs["top_k"] == 3
