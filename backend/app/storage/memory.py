"""In-process DocumentStore. State lives for the lifetime of the server process."""

from __future__ import annotations

from datetime import UTC, datetime

from app.storage.base import DocumentRecord, DocumentStore


class InMemoryDocumentStore(DocumentStore):
    def __init__(self) -> None:
        self._items: dict[str, DocumentRecord] = {}

    def create(self, record: DocumentRecord) -> DocumentRecord:
        self._items[record.id] = record
        return record

    def get(self, doc_id: str) -> DocumentRecord | None:
        return self._items.get(doc_id)

    def update(self, record: DocumentRecord) -> DocumentRecord:
        record.updated_at = datetime.now(UTC)
        self._items[record.id] = record
        return record

    def delete(self, doc_id: str) -> None:
        self._items.pop(doc_id, None)

    def list(self) -> list[DocumentRecord]:
        return list(self._items.values())
