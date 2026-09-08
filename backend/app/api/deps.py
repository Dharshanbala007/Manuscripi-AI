"""Request-scoped dependency accessors. Singletons live on `app.state`."""

from __future__ import annotations

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
