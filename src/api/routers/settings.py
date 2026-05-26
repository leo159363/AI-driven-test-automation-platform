"""System settings routes for platform capability configuration."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from src.api.services.platform_config_service import (
    PlatformConfigCreateRequest,
    PlatformConfigUpdateRequest,
    create_platform_config,
    delete_platform_config,
    list_platform_configs,
    update_platform_config,
)

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/platform-configs")
def get_platform_configs() -> dict[str, Any]:
    """Return built-in and custom platform capability configs."""
    items = list_platform_configs()
    return {
        "items": items,
        "summary": {
            "total": len(items),
            "builtin": sum(1 for item in items if item["builtin"]),
            "custom": sum(1 for item in items if not item["builtin"]),
        },
    }


@router.put("/platform-configs/{config_key}")
def put_platform_config(
    config_key: str,
    request: PlatformConfigUpdateRequest,
) -> dict[str, Any]:
    """Update a built-in or custom platform capability config."""
    return {"config": update_platform_config(config_key, request)}


@router.post("/platform-configs")
def post_platform_config(request: PlatformConfigCreateRequest) -> dict[str, Any]:
    """Create one custom platform capability config."""
    return {"config": create_platform_config(request)}


@router.delete("/platform-configs/{config_key}")
def remove_platform_config(config_key: str) -> dict[str, str]:
    """Delete one custom platform capability config."""
    return delete_platform_config(config_key)
