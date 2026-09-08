from __future__ import annotations

from pydantic import BaseModel

from app.storage.history import HistoryEntry


class HistoryEntryOut(BaseModel):
    id: str
    filename: str
    size: int
    created_at: str
    updated_at: str
    state: str
    profile_id: str | None
    health_total: int | None
    preservation_passed: bool | None
    words: int
    paragraphs: int
    headings: int
    tables: int
    figures: int
    references: int
    sections: int
    session_active: bool

    @classmethod
    def from_entry(cls, entry: HistoryEntry, *, session_active: bool) -> HistoryEntryOut:
        return cls(**vars(entry), session_active=session_active)
