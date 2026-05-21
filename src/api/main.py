"""FastAPI entrypoint for the QualityPilot full-stack backend."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import assistant, automation, health, knowledge, reports, test_cases


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
    app.include_router(test_cases.router)
    app.include_router(automation.router)
    app.include_router(reports.router)
    return app


app = create_app()
