"""FastAPI application factory."""

from __future__ import annotations

import asyncio
import contextlib
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes_documents, routes_formats, routes_health, routes_history
from app.api.errors import install_exception_handlers
from app.config import get_settings
from app.logging_config import configure_logging, log_stage
from app.storage.history import (
    HistoryStore,
    InMemoryHistoryStore,
    RemoteHistoryStore,
    SqliteHistoryStore,
)
from app.storage.memory import InMemoryDocumentStore
from app.storage.workspace import WorkspaceManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = app.state.settings
    configure_logging(settings.log_level, settings.log_format)
    removed = app.state.workspaces.sweep_expired(settings.workspace_ttl_min)
    if removed:
        log_stage("workspace_sweep", document_id="-", removed=removed)
    sweeper = None
    if settings.workspace_sweep_interval_min > 0:
        sweeper = asyncio.create_task(_sweep_forever(app))
    try:
        yield
    finally:
        if sweeper is not None:
            sweeper.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await sweeper


async def _sweep_forever(app: FastAPI) -> None:
    """Drop idle workspaces and their records so a shared server doesn't hoard uploads."""
    settings = app.state.settings
    while True:
        await asyncio.sleep(settings.workspace_sweep_interval_min * 60)
        expired = await asyncio.to_thread(
            app.state.workspaces.sweep_expired_ids, settings.workspace_ttl_min
        )
        for doc_id in expired:
            app.state.store.delete(doc_id)
        if expired:
            log_stage("workspace_sweep", document_id="-", removed=len(expired))


def _build_history(settings) -> HistoryStore:
    if not settings.history_enabled:
        return InMemoryHistoryStore()
    if settings.history_backend == "remote":
        if not (settings.history_api_url and settings.history_api_token):
            raise ValueError("HISTORY_BACKEND=remote needs HISTORY_API_URL and HISTORY_API_TOKEN")
        return RemoteHistoryStore(settings.history_api_url, settings.history_api_token)
    return SqliteHistoryStore(settings.history_db)


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
    app.state.history = _build_history(settings)

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
