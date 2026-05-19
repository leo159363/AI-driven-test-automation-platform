"""MCP Tool: generate_test_cases.

This tool turns a requirement plus optional RAG context into structured test
cases. Stage 21 intentionally uses a deterministic generator so the platform can
run without a real LLM key while still producing interview-friendly outputs.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from mcp import types

from src.core.settings import Settings
from src.mcp_server.tools.query_knowledge_hub import SUPPORTED_SOURCE_TYPES
from src.mcp_server.tools.retrieve_test_context import RECOMMENDED_USAGE
from src.mcp_server.tools.retrieve_test_context import (
    get_query_tool_instance,
)

logger = logging.getLogger(__name__)


TOOL_NAME = "generate_test_cases"
TOOL_DESCRIPTION = """Generate structured test cases from a requirement and RAG context.

Use this after retrieve_test_context. The output is JSON and is designed to feed
pytest automation design, manual review, and later bug/failure analysis.
"""

SUPPORTED_DIMENSIONS = {
    "functional",
    "negative",
    "boundary",
    "security",
    "compatibility",
    "performance",
    "regression",
    "usability",
}

DEFAULT_DIMENSIONS = [
    "functional",
    "negative",
    "boundary",
    "security",
    "regression",
]

TOOL_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "requirement": {
            "type": "string",
            "description": "Requirement, user story, API behavior, or bug-fix requirement.",
        },
        "project": {
            "type": "string",
            "description": "Optional project metadata filter for RAG context retrieval.",
        },
        "module": {
            "type": "string",
            "description": "Optional module metadata filter for RAG context retrieval.",
        },
        "version": {
            "type": "string",
            "description": "Optional version metadata filter for RAG context retrieval.",
        },
        "source_types": {
            "type": "array",
            "description": "Optional RAG source types to retrieve before generation.",
            "items": {
                "type": "string",
                "enum": sorted(SUPPORTED_SOURCE_TYPES),
            },
        },
        "dimensions": {
            "type": "array",
            "description": "Test dimensions to cover.",
            "items": {
                "type": "string",
                "enum": sorted(SUPPORTED_DIMENSIONS),
            },
        },
        "case_count": {
            "type": "integer",
            "description": "Maximum number of test cases to generate.",
            "default": 6,
            "minimum": 1,
            "maximum": 12,
        },
        "top_k": {
            "type": "integer",
            "description": "Maximum number of RAG contexts to retrieve.",
            "default": 5,
            "minimum": 1,
            "maximum": 20,
        },
        "contexts": {
            "type": "array",
            "description": "Optional pre-retrieved RAG contexts. If provided, live retrieval is skipped.",
            "items": {"type": "object"},
        },
    },
    "required": ["requirement"],
}


async def generate_test_cases_handler(
    requirement: str,
    project: Optional[str] = None,
    module: Optional[str] = None,
    version: Optional[str] = None,
    source_types: Optional[List[str]] = None,
    dimensions: Optional[List[str]] = None,
    case_count: int = 6,
    top_k: int = 5,
    contexts: Optional[List[Dict[str, Any]]] = None,
) -> types.CallToolResult:
    """Generate structured test cases for MCP clients."""
    try:
        payload = await generate_test_cases_payload(
            requirement=requirement,
            project=project,
            module=module,
            version=version,
            source_types=source_types,
            dimensions=dimensions,
            case_count=case_count,
            top_k=top_k,
            contexts=contexts,
        )
        return types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text=json.dumps(payload, ensure_ascii=False, indent=2),
                )
            ],
            isError=False,
        )
    except ValueError as exc:
        return types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text=json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2),
                )
            ],
            isError=True,
        )
    except Exception:
        logger.exception("generate_test_cases handler error")
        return types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text=json.dumps(
                        {"error": "failed to generate test cases"},
                        ensure_ascii=False,
                        indent=2,
                    ),
                )
            ],
            isError=True,
        )


async def generate_test_cases_payload(
    requirement: str,
    project: Optional[str] = None,
    module: Optional[str] = None,
    version: Optional[str] = None,
    source_types: Optional[List[str]] = None,
    dimensions: Optional[List[str]] = None,
    case_count: int = 6,
    top_k: int = 5,
    contexts: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Build the JSON payload returned by generate_test_cases."""
    normalized_requirement = _validate_requirement(requirement)
    effective_dimensions = _normalize_dimensions(dimensions)
    effective_case_count = _clamp_int(case_count, minimum=1, maximum=12, default=6)
    effective_top_k = _clamp_int(top_k, minimum=1, maximum=20, default=5)
    effective_source_types = _normalize_source_types(source_types) or [
        "requirement",
        "api_doc",
        "test_case",
        "bug",
        "standard",
    ]

    if contexts is not None:
        contexts = _normalize_contexts(contexts)
        retrieval_error = None
    else:
        contexts, retrieval_error = await _retrieve_contexts(
            query=normalized_requirement,
            project=project,
            module=module,
            version=version,
            source_types=effective_source_types,
            top_k=effective_top_k,
        )

    cases = _generate_cases(
        requirement=normalized_requirement,
        dimensions=effective_dimensions,
        case_count=effective_case_count,
        contexts=contexts,
        project=project,
        module=module,
    )

    payload: Dict[str, Any] = {
        "requirement": normalized_requirement,
        "generation_strategy": "rule_based_with_rag_context",
        "dimensions": effective_dimensions,
        "test_cases": cases,
        "context_summary": _build_context_summary(contexts),
        "recommended_next_steps": [
            "review_test_cases",
            "map_cases_to_pytest",
            "run_api_tests",
            "get_test_report",
        ],
    }
    if retrieval_error:
        payload["context_warning"] = retrieval_error
    return payload


async def _retrieve_contexts(
    query: str,
    project: Optional[str],
    module: Optional[str],
    version: Optional[str],
    source_types: List[str],
    top_k: int,
) -> tuple[List[Dict[str, Any]], Optional[str]]:
    """Retrieve RAG contexts and gracefully fall back to empty context."""
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
    except Exception as exc:
        return [], f"RAG context retrieval failed: {exc}"

    structured = response.structured_content or {}
    contexts = structured.get("contexts", [])
    if not isinstance(contexts, list):
        contexts = []

    if "error" in response.metadata:
        return contexts, str(response.metadata["error"])
    return contexts, None


def _generate_cases(
    requirement: str,
    dimensions: List[str],
    case_count: int,
    contexts: List[Dict[str, Any]],
    project: Optional[str],
    module: Optional[str],
) -> List[Dict[str, Any]]:
    """Generate deterministic test cases from dimensions and contexts."""
    cases = []
    for index in range(case_count):
        dimension = dimensions[index % len(dimensions)]
        cases.append(
            _build_case(
                index=index + 1,
                requirement=requirement,
                dimension=dimension,
                contexts=contexts,
                project=project,
                module=module,
            )
        )
    return cases


def _build_case(
    index: int,
    requirement: str,
    dimension: str,
    contexts: List[Dict[str, Any]],
    project: Optional[str],
    module: Optional[str],
) -> Dict[str, Any]:
    """Build one test case for a specific dimension."""
    case_id = f"TC-{index:03d}"
    summary = _shorten(requirement, 32)
    citations = _select_citations(contexts, limit=2)
    title_map = {
        "functional": f"{summary} 主流程验证",
        "negative": f"{summary} 异常输入验证",
        "boundary": f"{summary} 边界值验证",
        "security": f"{summary} 鉴权与越权验证",
        "compatibility": f"{summary} 兼容性验证",
        "performance": f"{summary} 响应时间验证",
        "regression": f"{summary} 回归验证",
        "usability": f"{summary} 提示信息验证",
    }
    priority_map = {
        "functional": "P1",
        "negative": "P1",
        "security": "P1",
        "boundary": "P2",
        "regression": "P2",
        "performance": "P2",
        "compatibility": "P3",
        "usability": "P3",
    }

    return {
        "case_id": case_id,
        "title": title_map.get(dimension, f"{summary} 测试验证"),
        "dimension": dimension,
        "priority": priority_map.get(dimension, "P2"),
        "preconditions": _preconditions_for(dimension),
        "steps": _steps_for(dimension, requirement),
        "expected_results": _expected_results_for(dimension),
        "test_data": _test_data_for(dimension),
        "automation_hint": _automation_hint_for(dimension, project, module),
        "citations": citations,
    }


def _preconditions_for(dimension: str) -> List[str]:
    base = ["测试环境可访问", "基础测试数据已准备"]
    if dimension in {"security", "negative"}:
        return base + ["准备有效账号、无效账号和低权限账号"]
    if dimension == "performance":
        return base + ["准备可重复执行的压测或计时脚本"]
    return base


def _steps_for(dimension: str, requirement: str) -> List[str]:
    if dimension == "functional":
        return [
            "按需求描述准备合法输入数据",
            "执行目标接口或页面操作",
            "检查业务状态、响应字段和持久化结果",
        ]
    if dimension == "negative":
        return [
            "准备空值、非法格式、缺失必填字段等输入",
            "执行目标接口或页面操作",
            "检查错误码、错误提示和日志记录",
        ]
    if dimension == "boundary":
        return [
            "识别需求中的长度、数量、金额、时间等边界条件",
            "分别输入最小值、最大值、越界值和临界值",
            "检查系统是否按边界规则处理",
        ]
    if dimension == "security":
        return [
            "使用未登录、过期 token、低权限账号访问目标功能",
            "尝试越权访问或篡改关键参数",
            "检查系统是否拒绝请求且不泄露敏感信息",
        ]
    if dimension == "performance":
        return [
            "准备稳定测试数据和重复执行脚本",
            "连续执行目标接口或关键流程",
            "统计响应时间、失败率和异常日志",
        ]
    if dimension == "compatibility":
        return [
            "选择不同浏览器、分辨率或客户端环境",
            "执行核心业务流程",
            "检查页面布局、交互和接口兼容性",
        ]
    if dimension == "usability":
        return [
            "触发成功、失败和等待中的典型状态",
            "观察页面提示、按钮状态和错误文案",
            "确认用户能理解下一步操作",
        ]
    return [
        f"围绕需求“{_shorten(requirement, 40)}”准备回归数据",
        "执行历史核心路径和本次变更路径",
        "对比本次结果和历史预期结果",
    ]


def _expected_results_for(dimension: str) -> List[str]:
    if dimension == "security":
        return ["非法访问被拒绝", "无敏感字段泄露", "审计日志可追踪"]
    if dimension == "negative":
        return ["返回明确错误码", "错误提示可理解", "不产生脏数据"]
    if dimension == "performance":
        return ["响应时间满足阈值", "失败率在可接受范围内", "无明显资源异常"]
    if dimension == "compatibility":
        return ["核心流程可完成", "页面元素无错位", "关键接口行为一致"]
    return ["实际结果符合需求描述", "关键字段和状态正确", "相关日志可追踪"]


def _test_data_for(dimension: str) -> Dict[str, Any]:
    if dimension == "negative":
        return {"invalid_values": ["", None, "illegal_format", "duplicated_value"]}
    if dimension == "boundary":
        return {"boundary_values": ["min", "max", "min-1", "max+1"]}
    if dimension == "security":
        return {"accounts": ["anonymous", "expired_token", "low_privilege_user"]}
    if dimension == "performance":
        return {"threshold": {"p95_ms": 1000, "error_rate": "1%"}}
    return {"data_policy": "use valid baseline data and isolate side effects"}


def _automation_hint_for(
    dimension: str,
    project: Optional[str],
    module: Optional[str],
) -> Dict[str, str]:
    layer = "api" if dimension in {"functional", "negative", "boundary", "security"} else "e2e"
    marker = "automation" if layer == "api" else "e2e"
    return {
        "suggested_layer": layer,
        "pytest_marker": marker,
        "suggested_file": _suggested_file_name(project, module, layer),
    }


def _suggested_file_name(
    project: Optional[str],
    module: Optional[str],
    layer: str,
) -> str:
    project_part = _slug(project or "qualitypilot")
    module_part = _slug(module or "general")
    return f"pytest_tests/{layer}/test_{project_part}_{module_part}.py"


def _select_citations(
    contexts: List[Dict[str, Any]],
    limit: int,
) -> List[Dict[str, Any]]:
    citations = []
    for context in contexts[:limit]:
        citations.append(
            {
                "chunk_id": context.get("chunk_id", ""),
                "source_id": context.get("source_id", ""),
                "source_type": context.get("source_type", ""),
                "title": context.get("title", ""),
                "score": context.get("score", 0),
            }
        )
    return citations


def _build_context_summary(contexts: List[Dict[str, Any]]) -> Dict[str, Any]:
    source_types: Dict[str, int] = {}
    for context in contexts:
        source_type = str(context.get("source_type") or "unknown")
        source_types[source_type] = source_types.get(source_type, 0) + 1
    return {
        "context_count": len(contexts),
        "source_type_distribution": source_types,
        "recommended_usage": RECOMMENDED_USAGE,
    }


def _validate_requirement(requirement: str) -> str:
    if not isinstance(requirement, str) or not requirement.strip():
        raise ValueError("requirement cannot be empty")
    return requirement.strip()


def _normalize_dimensions(dimensions: Optional[List[str]]) -> List[str]:
    if not dimensions:
        return list(DEFAULT_DIMENSIONS)
    normalized = []
    for dimension in dimensions:
        if not isinstance(dimension, str):
            continue
        value = dimension.strip().lower()
        if value in SUPPORTED_DIMENSIONS and value not in normalized:
            normalized.append(value)
    return normalized or list(DEFAULT_DIMENSIONS)


def _normalize_source_types(source_types: Optional[List[str]]) -> List[str]:
    if not source_types:
        return []
    normalized = []
    for source_type in source_types:
        if not isinstance(source_type, str):
            continue
        value = source_type.strip().lower()
        if value in SUPPORTED_SOURCE_TYPES and value not in normalized:
            normalized.append(value)
    return normalized


def _normalize_contexts(contexts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized = []
    for index, context in enumerate(contexts, start=1):
        metadata = context.get("metadata") or {}
        normalized.append(
            {
                "chunk_id": context.get("chunk_id") or context.get("context_id") or f"CTX-{index:03d}",
                "source_id": context.get("source_id") or metadata.get("source_id", ""),
                "source_type": context.get("source_type") or metadata.get("source_type", ""),
                "title": context.get("title") or metadata.get("title", ""),
                "content": context.get("content") or context.get("text", ""),
                "score": context.get("score", 0),
                "metadata": metadata,
            }
        )
    return normalized


def _clamp_int(value: int, minimum: int, maximum: int, default: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return max(minimum, min(maximum, number))


def _shorten(text: str, max_length: int) -> str:
    text = " ".join(text.split())
    if len(text) <= max_length:
        return text
    return text[:max_length].rstrip() + "..."


def _slug(value: str) -> str:
    lowered = value.strip().lower()
    chars = [char if char.isalnum() else "_" for char in lowered]
    slug = "".join(chars).strip("_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug or "default"


def register_tool(protocol_handler, settings: Optional[Settings] = None) -> None:
    """Register generate_test_cases tool with the protocol handler."""
    protocol_handler.register_tool(
        name=TOOL_NAME,
        description=TOOL_DESCRIPTION,
        input_schema=TOOL_INPUT_SCHEMA,
        handler=generate_test_cases_handler,
    )
    logger.info("Registered MCP tool: %s", TOOL_NAME)
