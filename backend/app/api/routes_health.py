"""Liveness + runtime capability probe."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.export.pdf_export import pdf_available

router = APIRouter(tags=["health"])


@router.get("/health")
def health(settings: Settings = Depends(get_settings)) -> dict:
    return {
        "status": "ok",
        "version": settings.version,
        "capabilities": {"pdf_export": pdf_available(settings)},
    }
