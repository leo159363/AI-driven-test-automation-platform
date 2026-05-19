"""Pure unit tests for Chroma metadata filter translation."""

from __future__ import annotations

from src.libs.vector_store.chroma_store import ChromaStore


def test_build_where_clause_single_exact_filter() -> None:
    store = ChromaStore.__new__(ChromaStore)

    assert store._build_where_clause({"project": "qualitypilot-demo"}) == {
        "project": "qualitypilot-demo"
    }


def test_build_where_clause_multiple_filters_uses_and() -> None:
    store = ChromaStore.__new__(ChromaStore)

    where = store._build_where_clause(
        {
            "project": "qualitypilot-demo",
            "module": "auth",
            "source_type": ["requirement", "api_doc"],
        }
    )

    assert where == {
        "$and": [
            {"project": "qualitypilot-demo"},
            {"module": "auth"},
            {"source_type": {"$in": ["requirement", "api_doc"]}},
        ]
    }
