"""AI testing assistant routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.api.services.assistant_service import (
    build_assistant_response,
    list_prompt_templates,
)

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


class AssistantRequest(BaseModel):
    """Request body for the AI testing assistant."""

    template_id: str = Field(default="test_case_generation")
    message: str = Field(..., min_length=1)
    project: str = Field(default="QualityPilot")
    module: str = Field(default="")
    version: str = Field(default="demo")
    use_knowledge: bool = Field(default=True)
    source_types: list[str] = Field(default_factory=list)
    top_k: int = Field(default=4, ge=1, le=8)


@router.get("/templates")
def get_prompt_templates() -> dict[str, Any]:
    """Return built-in assistant prompt templates."""
    templates = list_prompt_templates()
    return {
        "items": templates,
        "summary": {
            "total": len(templates),
            "categories": sorted({template["category"] for template in templates}),
        },
    }


@router.post("/chat")
async def assistant_chat(request: AssistantRequest) -> dict[str, Any]:
    """Generate assistant output for a selected test-development template."""
    try:
        return await build_assistant_response(
            template_id=request.template_id,
            message=request.message,
            project=request.project,
            module=request.module,
            version=request.version,
            use_knowledge=request.use_knowledge,
            source_types=request.source_types or None,
            top_k=request.top_k,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
