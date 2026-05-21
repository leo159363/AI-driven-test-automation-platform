"""Knowledge-base and RAG demo routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from src.api.services.knowledge_service import (
    list_knowledge_sources,
    list_source_types,
    search_knowledge_contexts,
    upload_knowledge_document,
)

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


class KnowledgeSearchRequest(BaseModel):
    """Request body for retrieval testing."""

    query: str = Field(..., min_length=1)
    project: str = Field(default="")
    module: str = Field(default="")
    version: str = Field(default="")
    source_types: list[str] = Field(default_factory=list)
    top_k: int = Field(default=5, ge=1, le=20)


def _split_source_types(source_types: list[str] | None) -> list[str]:
    values: list[str] = []
    for item in source_types or []:
        values.extend(part.strip() for part in item.split(",") if part.strip())
    return values


@router.get("/source-types")
def get_source_types() -> dict[str, Any]:
    """Return supported testing knowledge source types."""
    items = list_source_types()
    return {
        "items": items,
        "summary": {"total": len(items)},
    }


@router.get("/sources")
def get_knowledge_sources(
    project: str = "",
    module: str = "",
    version: str = "",
    source_types: list[str] | None = Query(default=None),
) -> dict[str, Any]:
    """Return visible knowledge sources with optional filters."""
    try:
        items = list_knowledge_sources(
            project=project,
            module=module,
            version=version,
            source_types=_split_source_types(source_types),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "items": items,
        "summary": {
            "total": len(items),
            "source_types": sorted({item["source_type"] for item in items}),
            "modules": sorted({item["module"] for item in items}),
        },
    }


@router.post("/search")
def search_knowledge(request: KnowledgeSearchRequest) -> dict[str, Any]:
    """Retrieve knowledge chunks for testing design and failure analysis."""
    try:
        contexts = search_knowledge_contexts(
            query=request.query,
            project=request.project,
            module=request.module,
            version=request.version,
            source_types=request.source_types,
            top_k=request.top_k,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "query": request.query,
        "contexts": contexts,
        "retrieval_mode": "keyword_overlap_demo",
        "filters": {
            "project": request.project,
            "module": request.module,
            "version": request.version,
            "source_types": request.source_types,
            "top_k": request.top_k,
        },
    }


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    project: str = Form(default="QualityPilot"),
    module: str = Form(default="通用模块"),
    version: str = Form(default="demo"),
    source_type: str = Form(default="requirement"),
    title: str = Form(default=""),
) -> dict[str, Any]:
    """Upload a text or markdown document into the demo knowledge base."""
    raw = await file.read()
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        content = raw.decode("utf-8", errors="replace")

    try:
        source = upload_knowledge_document(
            filename=file.filename or "document.txt",
            content=content,
            project=project,
            module=module,
            version=version,
            source_type=source_type,
            title=title,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "source": source,
        "message": "document indexed",
    }
