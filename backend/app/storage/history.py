"""Document history — log-only summary rows. No manuscript content or model is stored."""

from __future__ import annotations

import sqlite3
from abc import ABC, abstractmethod
from contextlib import closing
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.storage.base import DocumentRecord

_COUNT_FIELDS = ("words", "paragraphs", "headings", "tables", "figures", "references", "sections")
_COLUMNS = (
    "id",
    "filename",
    "size",
    "created_at",
    "updated_at",
    "state",
    "profile_id",
    "health_total",
    "preservation_passed",
    *_COUNT_FIELDS,
)


@dataclass
class HistoryEntry:
    id: str
    filename: str
    size: int
    created_at: str
    updated_at: str
    state: str
    profile_id: str | None = None
    health_total: int | None = None
    preservation_passed: bool | None = None
    words: int = 0
    paragraphs: int = 0
    headings: int = 0
    tables: int = 0
    figures: int = 0
    references: int = 0
    sections: int = 0

    @classmethod
    def from_record(cls, record: DocumentRecord) -> HistoryEntry:
        stats = record.manuscript.stats if record.manuscript else None
        counts = (
            {f: int(getattr(stats, f, 0)) for f in _COUNT_FIELDS}
            if stats
            else dict.fromkeys(_COUNT_FIELDS, 0)
        )
        return cls(
            id=record.id,
            filename=record.filename,
            size=record.size,
            created_at=_iso(record.created_at),
            updated_at=_iso(record.updated_at),
            state=record.state,
            profile_id=record.profile_id,
            health_total=record.health.total if record.health else None,
            preservation_passed=(record.preservation.passed if record.preservation else None),
            **counts,
        )


def _iso(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat()


class HistoryStore(ABC):
    @abstractmethod
    def upsert(self, entry: HistoryEntry) -> None: ...

    @abstractmethod
    def get(self, entry_id: str) -> HistoryEntry | None: ...

    @abstractmethod
    def list(self, limit: int = 20) -> list[HistoryEntry]: ...

    @abstractmethod
    def delete(self, entry_id: str) -> None: ...


class InMemoryHistoryStore(HistoryStore):
    def __init__(self) -> None:
        self._items: dict[str, HistoryEntry] = {}

    def upsert(self, entry: HistoryEntry) -> None:
        self._items[entry.id] = entry

    def get(self, entry_id: str) -> HistoryEntry | None:
        return self._items.get(entry_id)

    def list(self, limit: int = 20) -> list[HistoryEntry]:
        rows = sorted(
            self._items.values(), key=lambda e: (e.updated_at, e.created_at), reverse=True
        )
        return rows[: max(0, limit)]

    def delete(self, entry_id: str) -> None:
        self._items.pop(entry_id, None)


_DDL = """
CREATE TABLE IF NOT EXISTS history (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    size INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    state TEXT NOT NULL,
    profile_id TEXT,
    health_total INTEGER,
    preservation_passed INTEGER,
    words INTEGER NOT NULL DEFAULT 0,
    paragraphs INTEGER NOT NULL DEFAULT 0,
    headings INTEGER NOT NULL DEFAULT 0,
    tables INTEGER NOT NULL DEFAULT 0,
    figures INTEGER NOT NULL DEFAULT 0,
    "references" INTEGER NOT NULL DEFAULT 0,
    sections INTEGER NOT NULL DEFAULT 0
);
"""


class SqliteHistoryStore(HistoryStore):
    # ponytail: one connection per call. Fine at this volume; add a pool only if
    # history writes ever show up in profiling.
    def __init__(self, db_path: Path | str) -> None:
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._conn()) as conn, conn:
            conn.executescript(_DDL)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path, timeout=5.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def upsert(self, entry: HistoryEntry) -> None:
        data = asdict(entry)
        data["preservation_passed"] = (
            None if entry.preservation_passed is None else int(entry.preservation_passed)
        )
        cols = ", ".join(f'"{c}"' for c in _COLUMNS)
        placeholders = ", ".join(f":{c}" for c in _COLUMNS)
        updates = ", ".join(f'"{c}"=excluded."{c}"' for c in _COLUMNS if c != "id")
        with closing(self._conn()) as conn, conn:
            conn.execute(
                f"INSERT INTO history ({cols}) VALUES ({placeholders}) "
                f"ON CONFLICT(id) DO UPDATE SET {updates}",
                data,
            )

    def get(self, entry_id: str) -> HistoryEntry | None:
        with closing(self._conn()) as conn:
            row = conn.execute("SELECT * FROM history WHERE id = ?", (entry_id,)).fetchone()
        return _row_to_entry(row) if row else None

    def list(self, limit: int = 20) -> list[HistoryEntry]:
        with closing(self._conn()) as conn:
            rows = conn.execute(
                "SELECT * FROM history ORDER BY updated_at DESC, created_at DESC LIMIT ?",
                (max(0, limit),),
            ).fetchall()
        return [_row_to_entry(r) for r in rows]

    def delete(self, entry_id: str) -> None:
        with closing(self._conn()) as conn, conn:
            conn.execute("DELETE FROM history WHERE id = ?", (entry_id,))


def _row_to_entry(row: sqlite3.Row) -> HistoryEntry:
    data = dict(row)
    pp = data.get("preservation_passed")
    data["preservation_passed"] = None if pp is None else bool(pp)
    return HistoryEntry(**data)
