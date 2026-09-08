"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes_documents, routes_formats, routes_health, routes_history
from app.api.errors import install_exception_handlers
from app.config import get_settings
from app.logging_config import configure_logging, log_stage
from app.storage.history import InMemoryHistoryStore, SqliteHistoryStore
from app.storage.memory import InMemoryDocumentStore
from app.storage.workspace import WorkspaceManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = app.state.settings
    configure_logging(settings.log_level, settings.log_format)
    removed = app.state.workspaces.sweep_expired(settings.workspace_ttl_min)
    if removed:
        log_stage("workspace_sweep", document_id="-", removed=removed)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="ManuScript AI",
        version=settings.version,
        summary="Local rule-based academic manuscript formatting.",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.store = InMemoryDocumentStore()
    app.state.workspaces = WorkspaceManager(settings.work_dir)
    app.state.history = (
        SqliteHistoryStore(settings.history_db)
        if settings.history_enabled
        else InMemoryHistoryStore()
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    install_exception_handlers(app)
    app.include_router(routes_health.router, prefix="/api")
    app.include_router(routes_formats.router, prefix="/api")
    app.include_router(routes_history.router, prefix="/api")
    app.include_router(routes_documents.router, prefix="/api")
    return app


app = create_app()
