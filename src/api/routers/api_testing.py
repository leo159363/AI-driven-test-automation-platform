"""API testing routes for controlled request debugging."""

from __future__ import annotations

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


API_COLLECTIONS: list[dict[str, Any]] = [
    {
        "collection_id": "auth",
        "name": "登录鉴权",
        "description": "登录成功、登录失败和 token 相关接口用例。",
        "case_ids": ["api-login-success", "api-login-invalid-password"],
    },
    {
        "collection_id": "upload",
        "name": "文件上传",
        "description": "二进制上传和参数校验接口用例。",
        "case_ids": ["api-upload-success", "api-upload-missing-filename"],
    },
]

SAVED_API_CASES: list[dict[str, Any]] = []


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
    items = list_api_environments()
    return {
        "items": items,
        "summary": {"total": len(items)},
    }


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
