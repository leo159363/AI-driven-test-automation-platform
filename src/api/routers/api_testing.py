"""API testing routes for controlled request debugging."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.api.services.api_debug_service import run_api_debug_request

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
    body: str = Field(default="")
    expected_status: int | None = Field(default=None)
    json_assertions: list[JsonPathAssertionRequest] = Field(default_factory=list)
    timeout_seconds: int = Field(default=10, ge=1, le=30)


@router.post("/debug")
def debug_api(request: ApiDebugRequest) -> dict[str, Any]:
    """Send one controlled API request and evaluate assertions."""
    try:
        return run_api_debug_request(
            method=request.method,
            path=request.path,
            base_url=request.base_url,
            headers=request.headers,
            body=request.body,
            expected_status=request.expected_status,
            json_assertions=[assertion.model_dump() for assertion in request.json_assertions],
            timeout_seconds=request.timeout_seconds,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
