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
