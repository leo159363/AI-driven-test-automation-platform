"""Knowledge-base service for the Vue/FastAPI RAG page."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.mcp_server.tools.query_knowledge_hub import SUPPORTED_SOURCE_TYPES

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_STORAGE_DIR = Path("data") / "qualitypilot_knowledge"
DOCUMENTS_FILE = "documents.json"


@dataclass(frozen=True)
class KnowledgeChunk:
    """A searchable knowledge chunk."""

    chunk_id: str
    source_id: str
    source_type: str
    title: str
    content: str
    project: str
    module: str
    version: str
    score: float = 0.0
    metadata: dict[str, str] | None = None


@dataclass(frozen=True)
class KnowledgeSource:
    """A document/source visible in the knowledge-base page."""

    source_id: str
    title: str
    source_type: str
    project: str
    module: str
    version: str
    chunk_count: int
    origin: str
    created_at: str


BUILTIN_CHUNKS: tuple[KnowledgeChunk, ...] = (
    KnowledgeChunk(
        chunk_id="CTX-AUTH-001",
        source_id="api_authentication.md",
        source_type="api_doc",
        title="API Document: Authentication",
        content=(
            "POST /api/login expects username and password. Success returns 200 with token and user. "
            "Invalid credentials return 401. Missing required fields return 400."
        ),
        project="QualityPilot",
        module="登录鉴权",
        version="demo",
        score=0.92,
        metadata={"origin": "builtin_fixture"},
    ),
    KnowledgeChunk(
        chunk_id="CTX-STD-001",
        source_id="test_standard_api_error_handling.md",
        source_type="standard",
        title="Test Standard: API Error Handling",
        content=(
            "API tests should cover status code, response schema, error code, error message, trace id, "
            "authorization failures, boundary values, and sensitive information leakage."
        ),
        project="QualityPilot",
        module="测试规范",
        version="demo",
        score=0.88,
        metadata={"origin": "builtin_fixture"},
    ),
    KnowledgeChunk(
        chunk_id="CTX-BUG-001",
        source_id="defect_login_lockout.md",
        source_type="bug",
        title="Defect: Login Lockout Counter Reset",
        content=(
            "Regression checks: successful login resets failure counter; lockout is per account; "
            "audit logs include account id, client ip, and timestamp."
        ),
        project="QualityPilot",
        module="登录鉴权",
        version="demo",
        score=0.81,
        metadata={"origin": "builtin_fixture"},
    ),
    KnowledgeChunk(
        chunk_id="CTX-UPLOAD-001",
        source_id="api_upload_demo.md",
        source_type="api_doc",
        title="API Document: File Upload",
        content=(
            "POST /api/upload accepts binary body with X-Filename header. Success returns 201 with filename "
            "and size. Missing filename returns 400 missing_filename."
        ),
        project="QualityPilot",
        module="文件上传",
        version="demo",
        score=0.86,
        metadata={"origin": "builtin_fixture"},
    ),
)


def list_source_types() -> list[str]:
    """Return source types supported by the testing knowledge taxonomy."""
    return sorted(SUPPORTED_SOURCE_TYPES)


def list_knowledge_sources(
    *,
    project_root: Path | str = REPO_ROOT,
    project: str = "",
    module: str = "",
    version: str = "",
    source_types: list[str] | None = None,
) -> list[dict[str, Any]]:
    """List built-in and uploaded knowledge sources."""
    chunks = _all_chunks(project_root)
    chunks = _filter_chunks(
        chunks,
        project=project,
        module=module,
        version=version,
        source_types=source_types,
    )

    groups: dict[str, list[KnowledgeChunk]] = {}
    for chunk in chunks:
        groups.setdefault(chunk.source_id, []).append(chunk)

    sources = []
    for source_id, source_chunks in groups.items():
        first = source_chunks[0]
        origins = {str((chunk.metadata or {}).get("origin", "uploaded")) for chunk in source_chunks}
        created_at = str((first.metadata or {}).get("created_at", ""))
        sources.append(
            asdict(
                KnowledgeSource(
                    source_id=source_id,
                    title=first.title,
                    source_type=first.source_type,
                    project=first.project,
                    module=first.module,
                    version=first.version,
                    chunk_count=len(source_chunks),
                    origin="builtin" if "builtin_fixture" in origins else "uploaded",
                    created_at=created_at,
                )
            )
        )

    return sorted(sources, key=lambda item: (item["origin"], item["source_id"]))


def search_knowledge_contexts(
    *,
    query: str,
    project_root: Path | str = REPO_ROOT,
    project: str = "",
    module: str = "",
    version: str = "",
    source_types: list[str] | None = None,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Search knowledge chunks with deterministic keyword-overlap scoring."""
    query = _validate_query(query)
    chunks = _filter_chunks(
        _all_chunks(project_root),
        project=project,
        module=module,
        version=version,
        source_types=source_types,
    )

    query_tokens = _tokens(query + " " + module)
    scored: list[KnowledgeChunk] = []
    for chunk in chunks:
        text = " ".join([chunk.title, chunk.content, chunk.module, chunk.source_type])
        overlap = len(query_tokens.intersection(_tokens(text)))
        module_bonus = 2 if module and module in chunk.module else 0
        score = overlap + module_bonus + chunk.score
        if score <= 0:
            continue
        scored.append(
            KnowledgeChunk(
                **{
                    **asdict(chunk),
                    "score": round(score, 4),
                    "metadata": {
                        **(chunk.metadata or {}),
                        "retrieval_mode": "keyword_overlap_demo",
                    },
                }
            )
        )

    scored.sort(key=lambda item: item.score, reverse=True)
    return [_chunk_payload(chunk) for chunk in scored[: _clamp_top_k(top_k)]]


def upload_knowledge_document(
    *,
    filename: str,
    content: str,
    project_root: Path | str = REPO_ROOT,
    project: str = "QualityPilot",
    module: str = "",
    version: str = "demo",
    source_type: str = "requirement",
    title: str = "",
) -> dict[str, Any]:
    """Persist an uploaded text/markdown document as searchable chunks."""
    normalized_type = _validate_source_type(source_type)
    normalized_content = _validate_content(content)
    source_id = f"upload-{uuid.uuid4().hex[:8]}-{Path(filename or 'document.txt').name}"
    effective_title = title.strip() or Path(filename or source_id).stem
    created_at = datetime.now(timezone.utc).isoformat()
    chunks = []
    for index, text in enumerate(_split_text(normalized_content), start=1):
        chunks.append(
            KnowledgeChunk(
                chunk_id=f"{source_id}#chunk-{index:03d}",
                source_id=source_id,
                source_type=normalized_type,
                title=effective_title,
                content=text,
                project=project or "QualityPilot",
                module=module or "通用模块",
                version=version or "demo",
                score=0.0,
                metadata={
                    "origin": "uploaded",
                    "filename": filename or "",
                    "created_at": created_at,
                },
            )
        )

    records = _load_uploaded_chunks(project_root)
    records.extend(_chunk_payload(chunk) for chunk in chunks)
    _write_uploaded_chunks(project_root, records)

    return {
        "source_id": source_id,
        "title": effective_title,
        "source_type": normalized_type,
        "project": project or "QualityPilot",
        "module": module or "通用模块",
        "version": version or "demo",
        "chunk_count": len(chunks),
        "created_at": created_at,
    }


def _all_chunks(project_root: Path | str) -> list[KnowledgeChunk]:
    uploaded = [_chunk_from_payload(item) for item in _load_uploaded_chunks(project_root)]
    return list(BUILTIN_CHUNKS) + uploaded


def _filter_chunks(
    chunks: list[KnowledgeChunk],
    *,
    project: str = "",
    module: str = "",
    version: str = "",
    source_types: list[str] | None = None,
) -> list[KnowledgeChunk]:
    allowed_types = {_validate_source_type(item) for item in source_types or [] if item}
    return [
        chunk
        for chunk in chunks
        if (not project or chunk.project == project)
        and (not module or chunk.module == module)
        and (not version or chunk.version == version)
        and (not allowed_types or chunk.source_type in allowed_types)
    ]


def _chunk_payload(chunk: KnowledgeChunk) -> dict[str, Any]:
    return {
        "chunk_id": chunk.chunk_id,
        "source_id": chunk.source_id,
        "source_type": chunk.source_type,
        "title": chunk.title,
        "content": chunk.content,
        "score": chunk.score,
        "metadata": {
            "project": chunk.project,
            "module": chunk.module,
            "version": chunk.version,
            **(chunk.metadata or {}),
        },
    }


def _chunk_from_payload(payload: dict[str, Any]) -> KnowledgeChunk:
    metadata = payload.get("metadata") or {}
    return KnowledgeChunk(
        chunk_id=str(payload.get("chunk_id", "")),
        source_id=str(payload.get("source_id", "")),
        source_type=str(payload.get("source_type", "standard")),
        title=str(payload.get("title", "")),
        content=str(payload.get("content", "")),
        project=str(metadata.get("project", "QualityPilot")),
        module=str(metadata.get("module", "通用模块")),
        version=str(metadata.get("version", "demo")),
        score=float(payload.get("score", 0.0) or 0.0),
        metadata={key: str(value) for key, value in metadata.items()},
    )


def _load_uploaded_chunks(project_root: Path | str) -> list[dict[str, Any]]:
    path = _documents_path(project_root)
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return payload if isinstance(payload, list) else []


def _write_uploaded_chunks(project_root: Path | str, records: list[dict[str, Any]]) -> None:
    path = _documents_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


def _documents_path(project_root: Path | str) -> Path:
    return Path(project_root) / DEFAULT_STORAGE_DIR / DOCUMENTS_FILE


def _split_text(text: str, chunk_size: int = 900, overlap: int = 120) -> list[str]:
    paragraphs = [paragraph.strip() for paragraph in text.splitlines() if paragraph.strip()]
    normalized = "\n".join(paragraphs) or text.strip()
    if len(normalized) <= chunk_size:
        return [normalized]

    chunks = []
    start = 0
    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        chunks.append(normalized[start:end].strip())
        if end == len(normalized):
            break
        start = max(0, end - overlap)
    return [chunk for chunk in chunks if chunk]


def _validate_query(query: str) -> str:
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query cannot be empty")
    return query.strip()


def _validate_content(content: str) -> str:
    if not isinstance(content, str) or not content.strip():
        raise ValueError("document content cannot be empty")
    return content.strip()


def _validate_source_type(source_type: str) -> str:
    normalized = (source_type or "standard").strip().lower()
    if normalized not in SUPPORTED_SOURCE_TYPES:
        available = ", ".join(sorted(SUPPORTED_SOURCE_TYPES))
        raise ValueError(f"Unsupported source_type: {normalized}. Available: {available}")
    return normalized


def _clamp_top_k(top_k: int) -> int:
    try:
        value = int(top_k)
    except (TypeError, ValueError):
        value = 5
    return max(1, min(value, 20))


def _tokens(text: str) -> set[str]:
    normalized = []
    for char in text.lower():
        normalized.append(char if char.isalnum() else " ")
    tokens = {token for token in "".join(normalized).split() if len(token) >= 2}
    cjk_chars = [char for char in text if "\u4e00" <= char <= "\u9fff"]
    tokens.update("".join(cjk_chars[index : index + 2]) for index in range(len(cjk_chars) - 1))
    return tokens
