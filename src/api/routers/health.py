"""Health-check endpoints."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    """Return API liveness information for Vue and CI smoke checks."""
    return {
        "status": "ok",
        "service": "qualitypilot-api",
        "version": "0.1.0",
        "docs": "/docs",
    }

