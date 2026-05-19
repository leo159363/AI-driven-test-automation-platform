"""
MCP Server Tools.

This package contains the MCP tool definitions exposed to clients.
"""

from src.mcp_server.tools.query_knowledge_hub import (
    TOOL_NAME as QUERY_KNOWLEDGE_HUB_NAME,
    TOOL_DESCRIPTION as QUERY_KNOWLEDGE_HUB_DESCRIPTION,
    TOOL_INPUT_SCHEMA as QUERY_KNOWLEDGE_HUB_SCHEMA,
    QueryKnowledgeHubTool,
    query_knowledge_hub_handler,
    register_tool as register_query_knowledge_hub,
)
from src.mcp_server.tools.retrieve_test_context import (
    TOOL_NAME as RETRIEVE_TEST_CONTEXT_NAME,
    TOOL_DESCRIPTION as RETRIEVE_TEST_CONTEXT_DESCRIPTION,
    TOOL_INPUT_SCHEMA as RETRIEVE_TEST_CONTEXT_SCHEMA,
    retrieve_test_context_handler,
    register_tool as register_retrieve_test_context,
)

__all__ = [
    "QUERY_KNOWLEDGE_HUB_NAME",
    "QUERY_KNOWLEDGE_HUB_DESCRIPTION",
    "QUERY_KNOWLEDGE_HUB_SCHEMA",
    "QueryKnowledgeHubTool",
    "query_knowledge_hub_handler",
    "register_query_knowledge_hub",
    "RETRIEVE_TEST_CONTEXT_NAME",
    "RETRIEVE_TEST_CONTEXT_DESCRIPTION",
    "RETRIEVE_TEST_CONTEXT_SCHEMA",
    "retrieve_test_context_handler",
    "register_retrieve_test_context",
]
