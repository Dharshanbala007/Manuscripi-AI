"""Document history — log-only summary rows. No manuscript content or model is stored."""

from __future__ import annotations

import json
import logging
import sqlite3
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from collections.abc import Callable
from contextlib import closing
from dataclasses import asdict, dataclass, fields
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote, urlencode

from app.storage.base import DocumentRecord

logger = logging.getLogger("manuscript")

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
    "owner",
)


class HistoryError(Exception):
    """A history backend could not be reached or rejected a request."""


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
    # Anonymous per-browser id, used only to scope the list on a shared (hosted) server.
    owner: str = ""

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
            owner=record.owner,
            **counts,
        )


def _iso(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat()


def record_history(history: HistoryStore, record: DocumentRecord) -> None:
    """Log a lifecycle step. A history outage must never fail the request that caused it."""
    try:
        history.upsert(HistoryEntry.from_record(record))
    except HistoryError:
        logger.warning("history_write_failed", exc_info=True)


class HistoryStore(ABC):
    """`owner=None` means "every row" (single-user/local); a string filters to that owner."""

    @abstractmethod
    def upsert(self, entry: HistoryEntry) -> None: ...

    @abstractmethod
    def get(self, entry_id: str) -> HistoryEntry | None: ...

    @abstractmethod
    def list(self, limit: int = 20, owner: str | None = None) -> list[HistoryEntry]: ...

    @abstractmethod
    def delete(self, entry_id: str, owner: str | None = None) -> None: ...


class InMemoryHistoryStore(HistoryStore):
    def __init__(self) -> None:
        self._items: dict[str, HistoryEntry] = {}

    def upsert(self, entry: HistoryEntry) -> None:
        self._items[entry.id] = entry

    def get(self, entry_id: str) -> HistoryEntry | None:
        return self._items.get(entry_id)

    def list(self, limit: int = 20, owner: str | None = None) -> list[HistoryEntry]:
        rows = [e for e in self._items.values() if owner is None or e.owner == owner]
        rows.sort(key=lambda e: (e.updated_at, e.created_at), reverse=True)
        return rows[: max(0, limit)]

    def delete(self, entry_id: str, owner: str | None = None) -> None:
        entry = self._items.get(entry_id)
        if entry is not None and (owner is None or entry.owner == owner):
            del self._items[entry_id]


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
    sections INTEGER NOT NULL DEFAULT 0,
    owner TEXT NOT NULL DEFAULT ''
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
            # Databases created before owner scoping existed lack the column.
            existing = {row["name"] for row in conn.execute("PRAGMA table_info(history)")}
            if "owner" not in existing:
                conn.execute("ALTER TABLE history ADD COLUMN owner TEXT NOT NULL DEFAULT ''")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_history_owner ON history(owner, updated_at)"
            )

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

    def list(self, limit: int = 20, owner: str | None = None) -> list[HistoryEntry]:
        where, args = ("", ()) if owner is None else ("WHERE owner = ? ", (owner,))
        with closing(self._conn()) as conn:
            rows = conn.execute(
                f"SELECT * FROM history {where}ORDER BY updated_at DESC, created_at DESC LIMIT ?",
                (*args, max(0, limit)),
            ).fetchall()
        return [_row_to_entry(r) for r in rows]

    def delete(self, entry_id: str, owner: str | None = None) -> None:
        where, args = ("", ()) if owner is None else (" AND owner = ?", (owner,))
        with closing(self._conn()) as conn, conn:
            conn.execute(f"DELETE FROM history WHERE id = ?{where}", (entry_id, *args))


def _row_to_entry(row: sqlite3.Row) -> HistoryEntry:
    data = dict(row)
    pp = data.get("preservation_passed")
    data["preservation_passed"] = None if pp is None else bool(pp)
    return HistoryEntry(**data)


# (method, url, headers, body, timeout) -> (status, body)
Transport = Callable[[str, str, dict[str, str], bytes | None, float], tuple[int, bytes]]


def _urllib_transport(
    method: str, url: str, headers: dict[str, str], body: bytes | None, timeout: float
) -> tuple[int, bytes]:
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as err:
        return err.code, err.read()
    except (urllib.error.URLError, TimeoutError, OSError) as err:
        raise HistoryError(f"history service unreachable: {err}") from err


class RemoteHistoryStore(HistoryStore):
    """History kept in a Cloudflare D1 database behind a small authenticated Worker.

    A hosted backend (e.g. on Render) has no durable disk, so history lives off-box. The
    Worker (`cloudflare/history-worker`) owns the SQL; this class only speaks its JSON API.
    """

    def __init__(
        self,
        base_url: str,
        token: str,
        *,
        transport: Transport = _urllib_transport,
        timeout: float = 8.0,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._token = token
        self._transport = transport
        self._timeout = timeout

    def _call(
        self,
        method: str,
        path: str,
        params: dict[str, str | int] | None = None,
        body: dict | None = None,
    ) -> tuple[int, bytes]:
        url = self._base + path + (f"?{urlencode(params)}" if params else "")
        headers = {
            "authorization": f"Bearer {self._token}",
            "accept": "application/json",
            # Cloudflare's bot rules reject the default Python-urllib agent.
            "user-agent": "manuscript-ai-backend/1.0",
        }
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers["content-type"] = "application/json"
        return self._transport(method, url, headers, data, self._timeout)

    def upsert(self, entry: HistoryEntry) -> None:
        status, raw = self._call("PUT", f"/entries/{quote(entry.id, safe='')}", body=asdict(entry))
        if status >= 300:
            raise HistoryError(f"history upsert failed: HTTP {status} {raw[:120]!r}")

    def get(self, entry_id: str) -> HistoryEntry | None:
        status, raw = self._call("GET", f"/entries/{quote(entry_id, safe='')}")
        if status == 404:
            return None
        if status >= 300:
            raise HistoryError(f"history get failed: HTTP {status}")
        return _entry_from_json(json.loads(raw))

    def list(self, limit: int = 20, owner: str | None = None) -> list[HistoryEntry]:
        params: dict[str, str | int] = {"limit": max(0, limit)}
        if owner is not None:
            params["owner"] = owner
        status, raw = self._call("GET", "/entries", params=params)
        if status >= 300:
            raise HistoryError(f"history list failed: HTTP {status}")
        return [_entry_from_json(item) for item in json.loads(raw)]

    def delete(self, entry_id: str, owner: str | None = None) -> None:
        params = None if owner is None else {"owner": owner}
        status, _ = self._call("DELETE", f"/entries/{quote(entry_id, safe='')}", params=params)
        if status >= 300 and status != 404:
            raise HistoryError(f"history delete failed: HTTP {status}")


_ENTRY_FIELDS = {f.name for f in fields(HistoryEntry)}


def _entry_from_json(data: dict) -> HistoryEntry:
    entry = {k: v for k, v in data.items() if k in _ENTRY_FIELDS}
    pp = entry.get("preservation_passed")
    entry["preservation_passed"] = None if pp is None else bool(pp)
    return HistoryEntry(**entry)
