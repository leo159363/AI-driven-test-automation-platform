"""API testing routes for controlled request debugging."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.api.services.api_debug_service import (
    export_curl_command,
    generate_api_operation_plan,
    list_api_environments,
    run_api_debug_request,
    synthesize_api_test_cases,
)

router = APIRouter(prefix="/api/api-testing", tags=["api-testing"])


class JsonPathAssertionRequest(BaseModel):
    """One JSON path assertion from the API testing page."""

    path: str = Field(..., min_length=1)
    operator: str = Field(default="equals")
    expected: Any = None


class ApiDebugRequest(BaseModel):
    """Request body for controlled API debugging."""

    method: str = Field(default="POST")
    path: str = Field(..., min_length=1)
    base_url: str = Field(default="")
    headers: dict[str, str] = Field(default_factory=dict)
    params: dict[str, str] = Field(default_factory=dict)
    body: str = Field(default="")
    body_type: str = Field(default="json")
    environment: dict[str, Any] = Field(default_factory=dict)
    mock_config: dict[str, Any] = Field(default_factory=dict)
    expected_status: int | None = Field(default=None)
    json_assertions: list[JsonPathAssertionRequest] = Field(default_factory=list)
    timeout_seconds: int = Field(default=10, ge=1, le=30)


class ApiSynthesizeRequest(BaseModel):
    """Request body for deterministic API test data synthesis."""

    method: str = Field(default="POST")
    path: str = Field(..., min_length=1)
    headers: dict[str, str] = Field(default_factory=dict)
    body: str = Field(default="")
    count: int = Field(default=6, ge=1, le=12)


class ApiPlanRequest(BaseModel):
    """Request body for AI-orchestration style plan preview."""

    prompt: str = Field(..., min_length=1)
    context: dict[str, Any] = Field(default_factory=dict)


class ApiCaseSaveRequest(BaseModel):
    """Request body for saving an API test case draft."""

    name: str = Field(..., min_length=1)
    method: str = Field(default="POST")
    path: str = Field(..., min_length=1)
    collection_id: str = Field(default="auth")
    headers: dict[str, str] = Field(default_factory=dict)
    body: str = Field(default="")
    expected_status: int | None = Field(default=None)
    json_assertions: list[JsonPathAssertionRequest] = Field(default_factory=list)


class ApiEnvironmentSaveRequest(BaseModel):
    """Request body for creating or updating one API environment."""

    name: str = Field(..., min_length=1)
    base_url: str = Field(default="")
    description: str = Field(default="")
    variables: dict[str, str] = Field(default_factory=dict)
    headers: dict[str, str] = Field(default_factory=dict)
    is_default: bool = Field(default=False)


API_COLLECTIONS: list[dict[str, Any]] = [
    {
        "collection_id": "auth",
        "name": "登录鉴权",
        "description": "登录成功、登录失败和 token 相关接口用例。",
        "case_ids": ["api-login-success", "api-login-invalid-password"],
    },
    {
        "collection_id": "user",
        "name": "用户中心",
        "description": "用户资料、账号状态、权限角色和敏感字段校验接口用例。",
        "case_ids": [],
    },
    {
        "collection_id": "upload",
        "name": "文件上传",
        "description": "二进制上传和参数校验接口用例。",
        "case_ids": ["api-upload-success", "api-upload-missing-filename"],
    },
    {
        "collection_id": "order",
        "name": "订单流程",
        "description": "创建订单、订单状态流转、幂等提交和库存扣减接口用例。",
        "case_ids": [],
    },
    {
        "collection_id": "payment",
        "name": "支付回调",
        "description": "支付下单、回调验签、重复通知和金额一致性接口用例。",
        "case_ids": [],
    },
    {
        "collection_id": "system",
        "name": "系统公共接口",
        "description": "健康检查、配置读取、字典接口和错误码规范用例。",
        "case_ids": [],
    },
]

SAVED_API_CASES: list[dict[str, Any]] = []
USER_API_ENVIRONMENTS: list[dict[str, Any]] = []


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _environment_items() -> list[dict[str, Any]]:
    user_default_exists = any(item.get("is_default") for item in USER_API_ENVIRONMENTS)
    builtins = []
    for item in list_api_environments():
        builtins.append(
            {
                **item,
                "is_builtin": True,
                "is_default": item["environment_id"] == "mock-local" and not user_default_exists,
                "updated_at": "builtin",
            }
        )
    return [*builtins, *USER_API_ENVIRONMENTS]


def _normalize_environment_payload(
    request: ApiEnvironmentSaveRequest,
    *,
    environment_id: str,
) -> dict[str, Any]:
    return {
        "environment_id": environment_id,
        "name": request.name,
        "description": request.description,
        "base_url": request.base_url,
        "variables": {str(key): str(value) for key, value in request.variables.items()},
        "headers": {str(key): str(value) for key, value in request.headers.items()},
        "is_builtin": False,
        "is_default": request.is_default,
        "updated_at": _now(),
    }


def _apply_default_environment(environment_id: str) -> None:
    for item in USER_API_ENVIRONMENTS:
        item["is_default"] = item["environment_id"] == environment_id


@router.post("/debug")
def debug_api(request: ApiDebugRequest) -> dict[str, Any]:
    """Send one controlled API request and evaluate assertions."""
    try:
        return run_api_debug_request(
            method=request.method,
            path=request.path,
            base_url=request.base_url,
            headers=request.headers,
            params=request.params,
            body=request.body,
            body_type=request.body_type,
            environment=request.environment,
            mock_config=request.mock_config,
            expected_status=request.expected_status,
            json_assertions=[assertion.model_dump() for assertion in request.json_assertions],
            timeout_seconds=request.timeout_seconds,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/environments")
def get_api_environments() -> dict[str, Any]:
    """Return lightweight environment presets."""
    items = _environment_items()
    return {
        "items": items,
        "summary": {"total": len(items)},
    }


@router.post("/environments")
def create_api_environment(request: ApiEnvironmentSaveRequest) -> dict[str, Any]:
    """Create one API environment in the in-memory demo store."""
    environment_id = f"env-{len(USER_API_ENVIRONMENTS) + 1:03d}"
    environment = _normalize_environment_payload(request, environment_id=environment_id)
    USER_API_ENVIRONMENTS.append(environment)
    if environment["is_default"]:
        _apply_default_environment(environment_id)
    return {
        "environment": environment,
        "message": "环境已创建。当前为内存演示版，后续可替换为数据库持久化。",
    }


@router.put("/environments/{environment_id}")
def update_api_environment(
    environment_id: str,
    request: ApiEnvironmentSaveRequest,
) -> dict[str, Any]:
    """Update one user-created API environment."""
    for index, item in enumerate(USER_API_ENVIRONMENTS):
        if item["environment_id"] == environment_id:
            environment = _normalize_environment_payload(request, environment_id=environment_id)
            USER_API_ENVIRONMENTS[index] = environment
            if environment["is_default"]:
                _apply_default_environment(environment_id)
            return {"environment": environment, "message": "环境已更新。"}
    raise HTTPException(status_code=404, detail=f"Unknown environment_id: {environment_id}")


@router.delete("/environments/{environment_id}")
def delete_api_environment(environment_id: str) -> dict[str, str]:
    """Delete one user-created API environment."""
    for index, item in enumerate(USER_API_ENVIRONMENTS):
        if item["environment_id"] == environment_id:
            del USER_API_ENVIRONMENTS[index]
            return {"message": "环境已删除。"}
    if environment_id in {item["environment_id"] for item in list_api_environments()}:
        raise HTTPException(status_code=400, detail="Built-in environments cannot be deleted")
    raise HTTPException(status_code=404, detail=f"Unknown environment_id: {environment_id}")


@router.get("/collections")
def get_api_collections() -> dict[str, Any]:
    """Return API test collections."""
    return {
        "items": API_COLLECTIONS,
        "summary": {
            "total": len(API_COLLECTIONS),
            "case_total": sum(len(item["case_ids"]) for item in API_COLLECTIONS),
        },
    }


@router.get("/cases")
def get_api_cases() -> dict[str, Any]:
    """Return saved API test case drafts."""
    return {
        "items": SAVED_API_CASES,
        "summary": {"total": len(SAVED_API_CASES)},
    }


@router.post("/cases")
def save_api_case(request: ApiCaseSaveRequest) -> dict[str, Any]:
    """Save one API test case draft in an in-memory demo catalog."""
    case_id = f"saved-{len(SAVED_API_CASES) + 1:03d}"
    case = {
        "case_id": case_id,
        "name": request.name,
        "method": request.method,
        "path": request.path,
        "collection_id": request.collection_id,
        "headers": request.headers,
        "body": request.body,
        "expected_status": request.expected_status,
        "json_assertions": [assertion.model_dump() for assertion in request.json_assertions],
        "automation_status": "draft",
        "source": "api_workbench",
    }
    SAVED_API_CASES.append(case)
    return {
        "case": case,
        "message": "API 用例已保存为演示草稿，后续可扩展为数据库持久化。",
    }


@router.post("/collections/{collection_id}/run")
def run_api_collection(collection_id: str) -> dict[str, Any]:
    """Run one API collection in deterministic demo mode."""
    collection = next(
        (item for item in API_COLLECTIONS if item["collection_id"] == collection_id),
        None,
    )
    if collection is None:
        raise HTTPException(status_code=404, detail=f"Unknown collection_id: {collection_id}")
    total = len(collection["case_ids"])
    return {
        "run_id": f"api-collection-{collection_id}-demo",
        "target_id": collection_id,
        "collection_id": collection_id,
        "name": collection["name"],
        "module": collection["name"],
        "status": "passed",
        "started_at": "demo",
        "finished_at": "demo",
        "command": f"pytest tests/automation --scenario {collection_id}",
        "summary": {
            "total": total,
            "passed": total,
            "failed": 0,
            "duration_seconds": 1.4,
        },
        "artifacts": [
            "reports/api-runs/collection-demo/junit.xml",
            "reports/api-runs/collection-demo/allure-results",
        ],
        "ai_next_step": "可进入测试报告页查看 JUnit / Allure 产物，失败时进入 AI 失败分析。",
    }


@router.post("/synthesize")
def synthesize_api_cases(request: ApiSynthesizeRequest) -> dict[str, Any]:
    """Generate boundary, negative and security cases from one request."""
    try:
        return synthesize_api_test_cases(
            method=request.method,
            path=request.path,
            headers=request.headers,
            body=request.body,
            count=request.count,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/plan")
def plan_api_operations(request: ApiPlanRequest) -> dict[str, Any]:
    """Preview natural-language API test orchestration operations."""
    try:
        return generate_api_operation_plan(prompt=request.prompt, context=request.context)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/curl")
def export_api_curl(request: ApiDebugRequest) -> dict[str, str]:
    """Export the current request as a cURL command."""
    try:
        return export_curl_command(
            method=request.method,
            path=request.path,
            base_url=request.base_url,
            headers=request.headers,
            params=request.params,
            body=request.body,
            environment=request.environment,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
