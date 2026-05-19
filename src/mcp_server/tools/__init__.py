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
from src.mcp_server.tools.generate_test_cases import (
    TOOL_NAME as GENERATE_TEST_CASES_NAME,
    TOOL_DESCRIPTION as GENERATE_TEST_CASES_DESCRIPTION,
    TOOL_INPUT_SCHEMA as GENERATE_TEST_CASES_SCHEMA,
    generate_test_cases_handler,
    register_tool as register_generate_test_cases,
)
from src.mcp_server.tools.run_api_tests import (
    TOOL_NAME as RUN_API_TESTS_NAME,
    TOOL_DESCRIPTION as RUN_API_TESTS_DESCRIPTION,
    TOOL_INPUT_SCHEMA as RUN_API_TESTS_SCHEMA,
    run_api_tests_handler,
    register_tool as register_run_api_tests,
)
from src.mcp_server.tools.get_test_report import (
    TOOL_NAME as GET_TEST_REPORT_NAME,
    TOOL_DESCRIPTION as GET_TEST_REPORT_DESCRIPTION,
    TOOL_INPUT_SCHEMA as GET_TEST_REPORT_SCHEMA,
    get_test_report_handler,
    register_tool as register_get_test_report,
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
    "GENERATE_TEST_CASES_NAME",
    "GENERATE_TEST_CASES_DESCRIPTION",
    "GENERATE_TEST_CASES_SCHEMA",
    "generate_test_cases_handler",
    "register_generate_test_cases",
    "RUN_API_TESTS_NAME",
    "RUN_API_TESTS_DESCRIPTION",
    "RUN_API_TESTS_SCHEMA",
    "run_api_tests_handler",
    "register_run_api_tests",
    "GET_TEST_REPORT_NAME",
    "GET_TEST_REPORT_DESCRIPTION",
    "GET_TEST_REPORT_SCHEMA",
    "get_test_report_handler",
    "register_get_test_report",
]
