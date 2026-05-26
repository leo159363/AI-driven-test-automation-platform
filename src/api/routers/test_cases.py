"""Test-case and API endpoint catalog routes."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.observability.dashboard.services.test_case_library_service import (
    list_api_request_examples,
    list_test_cases,
)

router = APIRouter(prefix="/api", tags=["test-cases"])


class TestCaseSaveRequest(BaseModel):
    """Request body for creating or updating one test case."""

    title: str = Field(..., min_length=1)
    test_type: str = Field(default="接口测试")
    module: str = Field(default="登录鉴权")
    priority: str = Field(default="P1")
    method: str = Field(default="POST")
    path: str = Field(default="/api/login")
    collection_id: str = Field(default="auth")
    description: str = Field(default="")
    scenario_id: str = Field(default="api_login")
    scenario_name: str = Field(default="API: 登录接口")
    automation_status: str = Field(default="草稿")
    pytest_target: str = Field(default="")
    assertion: str = Field(default="")
    related_report: str = Field(default="")


USER_TEST_CASES: list[dict[str, Any]] = []


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _api_request_index() -> dict[str, dict[str, Any]]:
    return {item.related_case_id: asdict(item) for item in list_api_request_examples()}


def _builtin_case_rows() -> list[dict[str, Any]]:
    api_index = _api_request_index()
    rows: list[dict[str, Any]] = []
    for case in list_test_cases():
        row = asdict(case)
        api_request = api_index.get(case.case_id, {})
        row.update(
            {
                "method": api_request.get("method", ""),
                "path": api_request.get("path", ""),
                "collection_id": "upload" if case.module == "文件上传" else "auth",
                "description": case.assertion,
                "is_builtin": True,
                "source": "builtin_catalog",
                "updated_at": "builtin",
            }
        )
        rows.append(row)
    return rows


def _all_case_rows() -> list[dict[str, Any]]:
    return [*_builtin_case_rows(), *USER_TEST_CASES]


def _summarize_rows(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "total": len(rows),
        "api": sum(1 for case in rows if case["test_type"] == "接口测试"),
        "ui": sum(1 for case in rows if case["test_type"] == "界面测试"),
        "automated": sum(1 for case in rows if "已" in case["automation_status"]),
    }


def _case_from_request(
    request: TestCaseSaveRequest,
    *,
    case_id: str,
) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "title": request.title,
        "test_type": request.test_type,
        "module": request.module,
        "priority": request.priority,
        "method": request.method,
        "path": request.path,
        "collection_id": request.collection_id,
        "description": request.description,
        "scenario_id": request.scenario_id,
        "scenario_name": request.scenario_name,
        "automation_status": request.automation_status,
        "pytest_target": request.pytest_target,
        "assertion": request.assertion,
        "related_report": request.related_report,
        "is_builtin": False,
        "source": "manual_created",
        "updated_at": _now(),
    }


@router.get("/test-cases")
def get_test_cases() -> dict[str, object]:
    """Return the current test-case catalog for platform pages."""
    cases = _all_case_rows()
    return {
        "items": cases,
        "summary": _summarize_rows(cases),
    }


@router.post("/test-cases")
def create_test_case(request: TestCaseSaveRequest) -> dict[str, object]:
    """Create one user-defined test case in the demo catalog."""
    case_id = f"TC-CUSTOM-{len(USER_TEST_CASES) + 1:03d}"
    test_case = _case_from_request(request, case_id=case_id)
    USER_TEST_CASES.append(test_case)
    return {"case": test_case, "message": "测试用例已创建。当前为内存演示版。"}


@router.put("/test-cases/{case_id}")
def update_test_case(case_id: str, request: TestCaseSaveRequest) -> dict[str, object]:
    """Update one user-defined test case."""
    if case_id in {case.case_id for case in list_test_cases()}:
        raise HTTPException(status_code=400, detail="Built-in test cases cannot be edited")
    for index, item in enumerate(USER_TEST_CASES):
        if item["case_id"] == case_id:
            test_case = _case_from_request(request, case_id=case_id)
            USER_TEST_CASES[index] = test_case
            return {"case": test_case, "message": "测试用例已更新。"}
    raise HTTPException(status_code=404, detail=f"Unknown case_id: {case_id}")


@router.delete("/test-cases/{case_id}")
def delete_test_case(case_id: str) -> dict[str, str]:
    """Delete one user-defined test case."""
    if case_id in {case.case_id for case in list_test_cases()}:
        raise HTTPException(status_code=400, detail="Built-in test cases cannot be deleted")
    for index, item in enumerate(USER_TEST_CASES):
        if item["case_id"] == case_id:
            del USER_TEST_CASES[index]
            return {"message": "测试用例已删除。"}
    raise HTTPException(status_code=404, detail=f"Unknown case_id: {case_id}")


@router.get("/api-endpoints")
def get_api_endpoints() -> dict[str, object]:
    """Return API request examples linked to automated test cases."""
    endpoints = [asdict(endpoint) for endpoint in list_api_request_examples()]
    methods = Counter(endpoint["method"] for endpoint in endpoints)
    modules = sorted({endpoint["module"] for endpoint in endpoints})
    scenarios = sorted({endpoint["scenario_id"] for endpoint in endpoints})
    return {
        "items": endpoints,
        "summary": {
            "total": len(endpoints),
            "methods": dict(sorted(methods.items())),
            "modules": modules,
            "scenarios": scenarios,
        },
    }
