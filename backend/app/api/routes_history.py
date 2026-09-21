"""Document history — a lightweight log, separate from any manuscript content."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_history, get_owner, get_settings_dep, get_store
from app.config import Settings
from app.schemas.history import HistoryEntryOut
from app.storage.base import DocumentStore
from app.storage.history import HistoryError, HistoryStore

logger = logging.getLogger("manuscript")

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=list[HistoryEntryOut])
def list_history(
    limit: int = Query(20, ge=1, le=100),
    history: HistoryStore = Depends(get_history),
    store: DocumentStore = Depends(get_store),
    settings: Settings = Depends(get_settings_dep),
    owner: str = Depends(get_owner),
) -> list[HistoryEntryOut]:
    if settings.history_scope_by_owner and not owner:
        return []  # a shared server never lists other visitors' documents
    try:
        rows = history.list(limit, owner=owner if settings.history_scope_by_owner else None)
    except HistoryError:
        logger.warning("history_read_failed", exc_info=True)
        return []
    return [
        HistoryEntryOut.from_entry(entry, session_active=store.get(entry.id) is not None)
        for entry in rows
    ]


@router.delete("/{entry_id}", status_code=204)
def delete_history(
    entry_id: str,
    history: HistoryStore = Depends(get_history),
    settings: Settings = Depends(get_settings_dep),
    owner: str = Depends(get_owner),
) -> None:
    if settings.history_scope_by_owner and not owner:
        return
    try:
        history.delete(entry_id, owner=owner if settings.history_scope_by_owner else None)
    except HistoryError:
        logger.warning("history_delete_failed", exc_info=True)
