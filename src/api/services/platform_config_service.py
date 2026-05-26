"""Runtime platform capability settings for the System Settings page."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Literal

from fastapi import HTTPException
from pydantic import BaseModel, Field, field_validator

ConfigType = Literal["rag", "mcp", "runner", "report", "experimental", "custom"]
ConfigStatus = Literal["enabled", "disabled", "experimental"]


class PlatformConfig(BaseModel):
    """Platform capability config returned to the frontend."""

    key: str
    name: str
    type: ConfigType
    builtin: bool
    enabled: bool
    status: ConfigStatus
    summary: str
    value: dict[str, Any]
    description: str


class PlatformConfigCreateRequest(BaseModel):
    """Create one custom platform config."""

    key: str = Field(..., min_length=1, pattern=r"^[a-zA-Z0-9_\-]+$")
    name: str = Field(..., min_length=1)
    type: ConfigType = Field(default="custom")
    enabled: bool = Field(default=True)
    value: dict[str, Any]
    description: str = Field(default="")

    @field_validator("value")
    @classmethod
    def validate_value_is_object(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError("value must be a JSON object")
        return value


class PlatformConfigUpdateRequest(BaseModel):
    """Update one platform config.

    Built-in configs only apply enabled and value. Custom configs may also update
    name, type, and description.
    """

    name: str | None = Field(default=None, min_length=1)
    type: ConfigType | None = Field(default=None)
    enabled: bool | None = Field(default=None)
    value: dict[str, Any] | None = Field(default=None)
    description: str | None = Field(default=None)

    @field_validator("value")
    @classmethod
    def validate_value_is_object(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if value is not None and not isinstance(value, dict):
            raise ValueError("value must be a JSON object")
        return value


DEFAULT_PLATFORM_CONFIGS: dict[str, PlatformConfig] = {
    "rag_knowledge_store": PlatformConfig(
        key="rag_knowledge_store",
        name="RAG Knowledge Store",
        type="rag",
        builtin=True,
        enabled=True,
        status="enabled",
        summary="local store · top_k=5 · chunk_size=800",
        value={
            "enabled": True,
            "store": "local",
            "top_k": 5,
            "chunk_size": 800,
            "source_type_filter": ["requirement", "api_doc", "bug", "log", "report"],
        },
        description=(
            "控制知识库检索参数。AI 生成测试用例、失败分析和 Bug 报告时，会优先从 RAG "
            "知识库检索相关需求、接口文档、历史缺陷和日志。"
        ),
    ),
    "mcp_server": PlatformConfig(
        key="mcp_server",
        name="MCP Server",
        type="mcp",
        builtin=True,
        enabled=True,
        status="enabled",
        summary="stdio transport · tools=6",
        value={
            "enabled": True,
            "transport": "stdio",
            "tools": [
                "retrieve_test_context",
                "generate_test_cases",
                "run_api_tests",
                "get_test_report",
                "analyze_failure",
                "generate_bug_report",
            ],
        },
        description=(
            "控制 MCP 工具服务。后续 Agent 编排中心会通过这些工具完成上下文检索、用例生成、"
            "测试执行、报告读取和失败分析。"
        ),
    ),
    "test_runner": PlatformConfig(
        key="test_runner",
        name="Test Runner",
        type="runner",
        builtin=True,
        enabled=True,
        status="enabled",
        summary="pytest · timeout=120s · artifacts=artifacts",
        value={
            "enabled": True,
            "framework": "pytest",
            "timeout_seconds": 120,
            "artifacts_dir": "artifacts",
            "junit_xml": "artifacts/junit.xml",
            "allure_results_dir": "artifacts/allure-results",
        },
        description=(
            "控制自动化测试执行器参数。平台执行 API 测试、自动化用例和回归任务时，会使用这里"
            "的 pytest 和报告目录配置。"
        ),
    ),
    "allure_report": PlatformConfig(
        key="allure_report",
        name="Allure Report",
        type="report",
        builtin=True,
        enabled=True,
        status="enabled",
        summary="results=artifacts/allure-results · auto_parse=true",
        value={
            "enabled": True,
            "results_dir": "artifacts/allure-results",
            "report_dir": "artifacts/allure-report",
            "auto_parse": True,
        },
        description=(
            "控制 Allure 报告解析。测试执行完成后，平台会读取 Allure results 并生成报告摘要、"
            "失败用例列表和趋势数据。"
        ),
    ),
    "agent_orchestration": PlatformConfig(
        key="agent_orchestration",
        name="Agent Orchestration",
        type="experimental",
        builtin=True,
        enabled=False,
        status="experimental",
        summary="planner=rule-based · executor=mock · max_steps=8",
        value={
            "enabled": False,
            "planner": "rule-based",
            "executor": "mock",
            "max_steps": 8,
            "human_review_required": True,
        },
        description=(
            "控制测试任务编排能力。当前可用于规则型测试计划生成，后续将接入 MCP tools，"
            "实现自然语言目标到测试执行链路的自动编排。"
        ),
    ),
}

PLATFORM_CONFIGS: dict[str, PlatformConfig] = deepcopy(DEFAULT_PLATFORM_CONFIGS)
CUSTOM_CONFIG_KEYS: set[str] = set()


def list_platform_configs() -> list[dict[str, Any]]:
    """Return all built-in and custom platform configs."""
    return [config.model_dump() for config in PLATFORM_CONFIGS.values()]


def create_platform_config(request: PlatformConfigCreateRequest) -> dict[str, Any]:
    """Create one custom platform config in memory."""
    key = request.key.strip()
    if key in PLATFORM_CONFIGS:
        raise HTTPException(status_code=400, detail="配置 key 已存在")
    config = PlatformConfig(
        key=key,
        name=request.name.strip(),
        type=request.type,
        builtin=False,
        enabled=request.enabled,
        status=_status_for(request.type, request.enabled),
        summary=_build_summary(request.type, request.value),
        value={**request.value, "enabled": request.enabled},
        description=request.description.strip() or "自定义平台能力配置。",
    )
    PLATFORM_CONFIGS[key] = config
    CUSTOM_CONFIG_KEYS.add(key)
    return config.model_dump()


def update_platform_config(
    config_key: str,
    request: PlatformConfigUpdateRequest,
) -> dict[str, Any]:
    """Update a built-in or custom platform config."""
    config = _get_config_or_404(config_key)
    next_enabled = request.enabled if request.enabled is not None else config.enabled
    next_value = request.value if request.value is not None else dict(config.value)
    next_value = {**next_value, "enabled": next_enabled}

    if config.builtin:
        updated = config.model_copy(
            update={
                "enabled": next_enabled,
                "status": _status_for(config.type, next_enabled),
                "summary": _build_summary(config.type, next_value),
                "value": next_value,
            }
        )
    else:
        next_type = request.type or config.type
        updated = config.model_copy(
            update={
                "name": request.name.strip() if request.name is not None else config.name,
                "type": next_type,
                "enabled": next_enabled,
                "status": _status_for(next_type, next_enabled),
                "summary": _build_summary(next_type, next_value),
                "value": next_value,
                "description": (
                    request.description.strip()
                    if request.description is not None
                    else config.description
                ),
            }
        )

    PLATFORM_CONFIGS[config_key] = updated
    return updated.model_dump()


def delete_platform_config(config_key: str) -> dict[str, str]:
    """Delete a custom config; built-in configs are protected."""
    config = _get_config_or_404(config_key)
    if config.builtin:
        raise HTTPException(status_code=400, detail="内置配置不允许删除")
    PLATFORM_CONFIGS.pop(config_key)
    CUSTOM_CONFIG_KEYS.discard(config_key)
    return {"message": "自定义配置已删除"}


def reset_platform_configs_for_tests() -> None:
    """Reset runtime configs. Intended for unit tests only."""
    PLATFORM_CONFIGS.clear()
    PLATFORM_CONFIGS.update(deepcopy(DEFAULT_PLATFORM_CONFIGS))
    CUSTOM_CONFIG_KEYS.clear()


def _get_config_or_404(config_key: str) -> PlatformConfig:
    config = PLATFORM_CONFIGS.get(config_key)
    if config is None:
        raise HTTPException(status_code=404, detail="平台配置不存在")
    return config


def _status_for(config_type: ConfigType, enabled: bool) -> ConfigStatus:
    if config_type == "experimental":
        return "experimental"
    return "enabled" if enabled else "disabled"


def _build_summary(config_type: ConfigType, value: dict[str, Any]) -> str:
    if config_type == "rag":
        return (
            f"{value.get('store', 'local')} store · top_k={value.get('top_k', '-')} · "
            f"chunk_size={value.get('chunk_size', '-')}"
        )
    if config_type == "mcp":
        tools = value.get("tools")
        tool_count = len(tools) if isinstance(tools, list) else 0
        return f"{value.get('transport', 'stdio')} transport · tools={tool_count}"
    if config_type == "runner":
        return (
            f"{value.get('framework', 'pytest')} · timeout={value.get('timeout_seconds', '-')}s · "
            f"artifacts={value.get('artifacts_dir', '-')}"
        )
    if config_type == "report":
        return (
            f"results={value.get('results_dir', '-')} · "
            f"auto_parse={value.get('auto_parse', '-')}"
        )
    if config_type == "experimental":
        return (
            f"planner={value.get('planner', '-')} · executor={value.get('executor', '-')} · "
            f"max_steps={value.get('max_steps', '-')}"
        )
    return _build_custom_summary(value)


def _build_custom_summary(value: dict[str, Any]) -> str:
    entries = list(value.items())[:3]
    if not entries:
        return "custom JSON config"
    return " · ".join(
        f"{key}={len(item) if isinstance(item, list) else item}" for key, item in entries
    )
