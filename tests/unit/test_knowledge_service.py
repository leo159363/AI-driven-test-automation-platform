"""Unit tests for the QualityPilot knowledge-base service."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.api.services.knowledge_service import (
    list_knowledge_sources,
    list_source_types,
    search_knowledge_contexts,
    upload_knowledge_document,
)


def test_list_source_types_contains_testing_taxonomy() -> None:
    source_types = set(list_source_types())

    assert {"requirement", "api_doc", "bug", "test_report", "log", "standard"}.issubset(
        source_types
    )


def test_list_knowledge_sources_includes_builtin_sources() -> None:
    sources = list_knowledge_sources(project="QualityPilot", version="demo")

    source_ids = {source["source_id"] for source in sources}
    assert "api_authentication.md" in source_ids
    assert "test_standard_api_error_handling.md" in source_ids
    assert all(source["chunk_count"] >= 1 for source in sources)


def test_search_knowledge_contexts_filters_by_source_type() -> None:
    contexts = search_knowledge_contexts(
        query="login token 401",
        project="QualityPilot",
        version="demo",
        source_types=["api_doc"],
        top_k=3,
    )

    assert contexts
    assert all(context["source_type"] == "api_doc" for context in contexts)
    assert contexts[0]["metadata"]["retrieval_mode"] == "keyword_overlap_demo"


def test_upload_knowledge_document_persists_chunks(tmp_path: Path) -> None:
    source = upload_knowledge_document(
        filename="payment_api.md",
        content=(
            "# Payment API\n\n"
            "POST /api/pay creates an order payment. Invalid amount returns 400 invalid_amount."
        ),
        project_root=tmp_path,
        project="QualityPilot",
        module="payment",
        version="v1",
        source_type="api_doc",
        title="Payment API",
    )

    assert source["source_type"] == "api_doc"
    assert source["chunk_count"] == 1
    sources = list_knowledge_sources(project_root=tmp_path, project="QualityPilot", version="v1")
    assert any(item["title"] == "Payment API" for item in sources)


def test_search_knowledge_contexts_can_find_uploaded_document(tmp_path: Path) -> None:
    upload_knowledge_document(
        filename="upload_requirement.md",
        content="File upload should reject missing X-Filename header with 400 missing_filename.",
        project_root=tmp_path,
        project="QualityPilot",
        module="file_upload",
        version="v2",
        source_type="requirement",
        title="Upload Requirement",
    )

    contexts = search_knowledge_contexts(
        query="missing_filename",
        project_root=tmp_path,
        project="QualityPilot",
        module="file_upload",
        version="v2",
        source_types=["requirement"],
    )

    assert contexts
    assert contexts[0]["title"] == "Upload Requirement"
    assert contexts[0]["metadata"]["origin"] == "uploaded"


def test_upload_knowledge_document_rejects_unknown_source_type(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unsupported source_type"):
        upload_knowledge_document(
            filename="bad.md",
            content="content",
            project_root=tmp_path,
            source_type="unknown",
        )
