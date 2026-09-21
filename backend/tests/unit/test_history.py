import pytest

from app.storage.history import HistoryEntry, InMemoryHistoryStore, SqliteHistoryStore


def _entry(eid: str, updated: str, state: str = "uploaded") -> HistoryEntry:
    return HistoryEntry(
        id=eid,
        filename=f"{eid}.docx",
        size=100,
        created_at="2026-01-01T00:00:00+00:00",
        updated_at=updated,
        state=state,
    )


@pytest.fixture(params=["memory", "sqlite"])
def store(request, tmp_path):
    if request.param == "memory":
        return InMemoryHistoryStore()
    return SqliteHistoryStore(tmp_path / "h.db")


def test_upsert_and_get_roundtrip(store):
    store.upsert(_entry("d1", "2026-01-01T10:00:00+00:00"))
    got = store.get("d1")
    assert got is not None
    assert got.filename == "d1.docx"
    assert got.state == "uploaded"


def test_upsert_updates_in_place(store):
    store.upsert(_entry("d1", "2026-01-01T10:00:00+00:00", state="uploaded"))
    store.upsert(_entry("d1", "2026-01-01T11:00:00+00:00", state="formatted"))
    assert len(store.list(50)) == 1
    assert store.get("d1").state == "formatted"


def test_list_is_newest_first_and_respects_limit(store):
    store.upsert(_entry("a", "2026-01-01T09:00:00+00:00"))
    store.upsert(_entry("b", "2026-01-01T11:00:00+00:00"))
    store.upsert(_entry("c", "2026-01-01T10:00:00+00:00"))
    assert [e.id for e in store.list(2)] == ["b", "c"]


def test_delete(store):
    store.upsert(_entry("d1", "2026-01-01T10:00:00+00:00"))
    store.delete("d1")
    assert store.get("d1") is None
    store.delete("does-not-exist")  # no error


def test_unknown_get_returns_none(store):
    assert store.get("missing") is None


def test_sqlite_persists_across_instances(tmp_path):
    db = tmp_path / "h.db"
    SqliteHistoryStore(db).upsert(_entry("d1", "2026-01-01T10:00:00+00:00", state="analyzed"))
    reopened = SqliteHistoryStore(db)
    assert reopened.get("d1").state == "analyzed"


def test_from_record_reads_counts_health_and_preservation():
    from app.domain.issues import HealthScore, PreservationResult
    from app.domain.manuscript import DocumentStats, Manuscript, Metadata
    from app.storage.base import DocumentRecord

    record = DocumentRecord(
        id="d1", filename="p.docx", size=10, state="formatted", profile_id="ieee"
    )
    record.manuscript = Manuscript(
        id="d1",
        source_filename="p.docx",
        metadata=Metadata.empty(),
        stats=DocumentStats(words=100, paragraphs=8, tables=2, references=5),
    )
    record.health = HealthScore(total=91)
    record.preservation = PreservationResult(passed=True)

    entry = HistoryEntry.from_record(record)
    assert entry.state == "formatted"
    assert entry.profile_id == "ieee"
    assert entry.health_total == 91
    assert entry.preservation_passed is True
    assert entry.paragraphs == 8
    assert entry.tables == 2
    assert entry.references == 5


def test_from_record_without_manuscript_has_zero_counts():
    from app.storage.base import DocumentRecord

    entry = HistoryEntry.from_record(DocumentRecord(id="d1", filename="p.docx", size=10))
    assert entry.state == "uploaded"
    assert entry.health_total is None
    assert entry.preservation_passed is None
    assert entry.paragraphs == 0


# ---- owner scoping (shared/hosted server) ----


def _owned(eid: str, owner: str, updated: str = "2026-01-01T10:00:00+00:00") -> HistoryEntry:
    entry = _entry(eid, updated)
    entry.owner = owner
    return entry


def test_list_and_delete_can_be_scoped_to_an_owner(store):
    store.upsert(_owned("a1", "alice"))
    store.upsert(_owned("b1", "bob"))

    assert {e.id for e in store.list(50)} == {"a1", "b1"}  # owner=None -> everyone (local mode)
    assert [e.id for e in store.list(50, owner="alice")] == ["a1"]
    assert store.list(50, owner="nobody") == []

    store.delete("a1", owner="bob")  # someone else's row: untouched
    assert store.get("a1") is not None
    store.delete("a1", owner="alice")
    assert store.get("a1") is None


def test_owner_survives_upsert_and_roundtrip(store):
    store.upsert(_owned("a1", "alice"))
    store.upsert(_owned("a1", "alice", "2026-01-01T12:00:00+00:00"))
    assert store.get("a1").owner == "alice"


def test_sqlite_adds_the_owner_column_to_an_existing_database(tmp_path):
    import sqlite3

    db = tmp_path / "old.db"
    with sqlite3.connect(db) as conn:  # the pre-owner schema
        conn.execute(
            "CREATE TABLE history (id TEXT PRIMARY KEY, filename TEXT NOT NULL,"
            " size INTEGER NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,"
            " state TEXT NOT NULL, profile_id TEXT, health_total INTEGER,"
            " preservation_passed INTEGER, words INTEGER NOT NULL DEFAULT 0,"
            " paragraphs INTEGER NOT NULL DEFAULT 0, headings INTEGER NOT NULL DEFAULT 0,"
            " tables INTEGER NOT NULL DEFAULT 0, figures INTEGER NOT NULL DEFAULT 0,"
            ' "references" INTEGER NOT NULL DEFAULT 0, sections INTEGER NOT NULL DEFAULT 0)'
        )
        conn.execute(
            "INSERT INTO history (id, filename, size, created_at, updated_at, state)"
            " VALUES ('old', 'old.docx', 1, 'x', 'y', 'exported')"
        )
    reopened = SqliteHistoryStore(db)
    assert reopened.get("old").owner == ""
    reopened.upsert(_owned("new", "alice"))
    assert [e.id for e in reopened.list(10, owner="alice")] == ["new"]


# ---- RemoteHistoryStore (Cloudflare D1 Worker) against a fake transport ----


class _FakeWorker:
    """Speaks the Worker's JSON API in memory, and records what it was sent."""

    def __init__(self):
        self.rows: dict[str, dict] = {}
        self.calls: list[tuple[str, str, dict, bytes | None]] = []
        self.fail_with: int | None = None

    def __call__(self, method, url, headers, body, timeout):
        import json
        from urllib.parse import parse_qs, urlparse

        self.calls.append((method, url, headers, body))
        if self.fail_with:
            return self.fail_with, b"nope"
        parts = urlparse(url)
        query = {k: v[0] for k, v in parse_qs(parts.query).items()}
        entry_id = parts.path.rsplit("/", 1)[-1]
        if method == "PUT":
            self.rows[entry_id] = json.loads(body)
            return 200, b'{"ok":true}'
        if method == "GET" and parts.path == "/entries":
            rows = [
                r
                for r in self.rows.values()
                if "owner" not in query or r["owner"] == query["owner"]
            ]
            rows.sort(key=lambda r: r["updated_at"], reverse=True)
            return 200, json.dumps(rows[: int(query["limit"])]).encode()
        if method == "GET":
            row = self.rows.get(entry_id)
            return (200, json.dumps(row).encode()) if row else (404, b"{}")
        if method == "DELETE":
            row = self.rows.get(entry_id)
            if row and ("owner" not in query or row["owner"] == query["owner"]):
                del self.rows[entry_id]
            return 200, b'{"ok":true}'
        return 405, b""


@pytest.fixture
def remote():
    from app.storage.history import RemoteHistoryStore

    worker = _FakeWorker()
    return RemoteHistoryStore("https://history.example.dev/", "s3cret", transport=worker), worker


def test_remote_roundtrips_an_entry_and_maps_preservation_to_bool(remote):
    store, _ = remote
    entry = _owned("d1", "alice")
    entry.preservation_passed = True
    entry.profile_id = "ieee"
    store.upsert(entry)

    assert store.get("d1") == entry
    assert store.get("missing") is None


def test_remote_sends_the_bearer_token_a_user_agent_and_hits_the_right_urls(remote):
    store, worker = remote
    store.upsert(_owned("d1", "alice"))
    store.list(5, owner="alice")

    method, url, headers, _ = worker.calls[0]
    assert (method, url) == ("PUT", "https://history.example.dev/entries/d1")
    assert headers["authorization"] == "Bearer s3cret"
    assert "python-urllib" not in headers["user-agent"].lower()
    assert worker.calls[1][1] == "https://history.example.dev/entries?limit=5&owner=alice"


def test_remote_scopes_list_and_delete_by_owner(remote):
    store, _ = remote
    store.upsert(_owned("a1", "alice"))
    store.upsert(_owned("b1", "bob"))
    assert [e.id for e in store.list(10, owner="bob")] == ["b1"]
    assert len(store.list(10)) == 2
    store.delete("a1", owner="bob")
    assert store.get("a1") is not None
    store.delete("a1", owner="alice")
    assert store.get("a1") is None


def test_remote_raises_history_error_on_a_failed_call(remote):
    from app.storage.history import HistoryError

    store, worker = remote
    worker.fail_with = 500
    with pytest.raises(HistoryError):
        store.upsert(_owned("d1", "alice"))
    with pytest.raises(HistoryError):
        store.list(5)


def test_record_history_swallows_backend_failures(remote):
    from app.storage.base import DocumentRecord
    from app.storage.history import record_history

    store, worker = remote
    worker.fail_with = 503
    record_history(store, DocumentRecord(id="d1", filename="p.docx", size=1))  # must not raise
