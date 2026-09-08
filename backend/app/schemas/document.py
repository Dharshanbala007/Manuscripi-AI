from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.storage.base import DocumentRecord


class DocumentOut(BaseModel):
    id: str
    filename: str
    size: int
    state: str
    created_at: datetime

    @classmethod
    def from_record(cls, record: DocumentRecord) -> DocumentOut:
        return cls(
            id=record.id,
            filename=record.filename,
            size=record.size,
            state=record.state,
            created_at=record.created_at,
        )
