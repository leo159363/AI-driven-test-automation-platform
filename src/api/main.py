"""FastAPI entrypoint for the QualityPilot full-stack backend."""

from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from src.api.routers import (
    api_testing,
    assistant,
    automation,
    health,
    knowledge,
    platform,
    reports,
    test_cases,
)

FRONTEND_ROUTES = {
    "/",
    "/api-testing",
    "/api-environments",
    "/test-cases",
    "/automation",
    "/reports",
    "/assistant",
    "/knowledge",
    "/web-testing",
    "/app-testing",
    "/performance",
    "/cicd",
    "/documents",
    "/settings",
}


def create_app() -> FastAPI:
    """Create the QualityPilot API application."""
    app = FastAPI(
        title="QualityPilot API",
        description=(
            "Backend APIs for the MCP + RAG based intelligent automation testing platform."
        ),
        version="0.1.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(assistant.router)
    app.include_router(knowledge.router)
    app.include_router(platform.router)
    app.include_router(api_testing.router)
    app.include_router(test_cases.router)
    app.include_router(automation.router)
    app.include_router(reports.router)

    @app.get("/", include_in_schema=False)
    @app.get("/{frontend_path:path}", include_in_schema=False)
    def redirect_frontend_route(frontend_path: str = "") -> RedirectResponse:
        """Redirect common Vue routes when users open the FastAPI port directly."""
        normalized_path = f"/{frontend_path}".rstrip("/") or "/"
        if normalized_path == "/api" or normalized_path.startswith("/api/"):
            raise HTTPException(status_code=404, detail="Not Found")
        if normalized_path not in FRONTEND_ROUTES:
            raise HTTPException(status_code=404, detail="Not Found")
        frontend_base_url = os.getenv("QUALITYPILOT_WEB_URL", "http://127.0.0.1:5173").rstrip("/")
        return RedirectResponse(f"{frontend_base_url}{normalized_path}", status_code=307)

    return app


app = create_app()
