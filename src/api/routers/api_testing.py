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
