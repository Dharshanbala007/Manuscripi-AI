"""Request-scoped dependency accessors. Singletons live on `app.state`."""

from __future__ import annotations

import re

from fastapi import Request

from app.config import Settings
from app.storage.base import DocumentStore
from app.storage.history import HistoryStore
from app.storage.workspace import WorkspaceManager


def get_settings_dep(request: Request) -> Settings:
    return request.app.state.settings


def get_store(request: Request) -> DocumentStore:
    return request.app.state.store


def get_workspaces(request: Request) -> WorkspaceManager:
    return request.app.state.workspaces


def get_history(request: Request) -> HistoryStore:
    return request.app.state.history


_CLIENT_ID = re.compile(r"[A-Za-z0-9_-]{16,64}")


def get_owner(request: Request) -> str:
    """The caller's anonymous id from `X-Client-Id`, or "" if absent/malformed."""
    value = request.headers.get("x-client-id", "")
    return value if _CLIENT_ID.fullmatch(value) else ""
