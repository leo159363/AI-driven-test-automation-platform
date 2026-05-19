"""MCP Tool: retrieve_test_context.

This tool is a test-development oriented wrapper around query_knowledge_hub.
It returns structured contexts that can feed test case generation, failure
analysis, and bug report generation.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from mcp import types

from src.core.settings import Settings
from src.mcp_server.tools.query_knowledge_hub import (
    SUPPORTED_SOURCE_TYPES,
    get_tool_instance as get_query_tool_instance,
)

logger = logging.getLogger(__name__)


TOOL_NAME = "retrieve_test_context"
TOOL_DESCRIPTION = """Retrieve structured RAG context for test-development workflows.

Use this tool before generating test cases, analyzing failed tests, or drafting
bug reports. It supports project/module/version/source_type metadata filters.
"""

TOOL_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "Requirement, API behavior, failure symptom, or bug topic to retrieve context for.",
        },
        "project": {
            "type": "string",
            "description": "Optional project metadata filter.",
        },
        "module": {
            "type": "string",
            "description": "Optional module metadata filter.",
        },
        "version": {
            "type": "string",
            "description": "Optional version metadata filter.",
        },
        "source_types": {
            "type": "array",
            "description": "Optional source type filters.",
            "items": {
                "type": "string",
                "enum": sorted(SUPPORTED_SOURCE_TYPES),
            },
        },
        "top_k": {
            "type": "integer",
            "description": "Maximum number of contexts to return.",
            "default": 5,
            "minimum": 1,
            "maximum": 20,
        },
    },
    "required": ["query"],
}

RECOMMENDED_USAGE = [
    "test_case_generation",
    "failure_analysis",
    "bug_report_generation",
]


async def retrieve_test_context_handler(
    query: str,
    project: Optional[str] = None,
    module: Optional[str] = None,
    version: Optional[str] = None,
    source_types: Optional[List[str]] = None,
    top_k: int = 5,
) -> types.CallToolResult:
    """Retrieve structured test context from the knowledge hub."""
    query_tool = get_query_tool_instance()

    try:
        response = await query_tool.execute(
            query=query,
            top_k=top_k,
            project=project,
            module=module,
            version=version,
            source_types=source_types,
        )

        structured = response.structured_content or {}
        payload: Dict[str, Any] = {
            "query": query,
            "contexts": structured.get("contexts", []),
            "recommended_usage": RECOMMENDED_USAGE,
            "filters": structured.get("filters", {}),
            "collection": structured.get("collection"),
        }
        if "error" in response.metadata:
            payload["error"] = response.metadata["error"]

        return types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text=json.dumps(payload, ensure_ascii=False, indent=2),
                )
            ],
            isError=response.is_empty and "error" in response.metadata,
        )
    except ValueError as exc:
        return types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text=json.dumps(
                        {"query": query, "contexts": [], "error": str(exc)},
                        ensure_ascii=False,
                        indent=2,
                    ),
                )
            ],
            isError=True,
        )
    except Exception:
        logger.exception("retrieve_test_context handler error")
        return types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "query": query,
                            "contexts": [],
                            "error": "failed to retrieve test context",
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                )
            ],
            isError=True,
        )


def register_tool(protocol_handler, settings: Optional[Settings] = None) -> None:
    """Register retrieve_test_context tool with the protocol handler."""
    protocol_handler.register_tool(
        name=TOOL_NAME,
        description=TOOL_DESCRIPTION,
        input_schema=TOOL_INPUT_SCHEMA,
        handler=retrieve_test_context_handler,
    )
    logger.info("Registered MCP tool: %s", TOOL_NAME)
