"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes_health
from app.config import get_settings
from app.logging_config import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level, settings.log_format)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="ManuScript AI",
        version=settings.version,
        summary="Local rule-based academic manuscript formatting.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(routes_health.router, prefix="/api")
    return app


app = create_app()
