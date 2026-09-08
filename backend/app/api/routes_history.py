"""Local document history — a lightweight log, separate from any manuscript content."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_history, get_store
from app.schemas.history import HistoryEntryOut
from app.storage.base import DocumentStore
from app.storage.history import HistoryStore

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=list[HistoryEntryOut])
def list_history(
    limit: int = Query(20, ge=1, le=100),
    history: HistoryStore = Depends(get_history),
    store: DocumentStore = Depends(get_store),
) -> list[HistoryEntryOut]:
    return [
        HistoryEntryOut.from_entry(entry, session_active=store.get(entry.id) is not None)
        for entry in history.list(limit)
    ]


@router.delete("/{entry_id}", status_code=204)
def delete_history(entry_id: str, history: HistoryStore = Depends(get_history)) -> None:
    history.delete(entry_id)
