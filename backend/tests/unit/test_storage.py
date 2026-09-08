import os
import time

import pytest

from app.storage.base import DocumentRecord
from app.storage.memory import InMemoryDocumentStore
from app.storage.workspace import WorkspaceManager


def test_store_roundtrip():
    store = InMemoryDocumentStore()
    rec = DocumentRecord(id="d1", filename="a.docx", size=10)
    store.create(rec)
    assert store.get("d1") is rec

    rec.state = "analyzed"
    store.update(rec)
    assert store.get("d1").state == "analyzed"
    assert [r.id for r in store.list()] == ["d1"]

    store.delete("d1")
    assert store.get("d1") is None


def test_store_unknown_get_returns_none():
    assert InMemoryDocumentStore().get("missing") is None


def test_workspace_create_and_path(tmp_path):
    wm = WorkspaceManager(tmp_path / "ws")
    d = wm.create("doc-1")
    assert d.is_dir()
    p = wm.path("doc-1", "source.docx")
    assert p.name == "source.docx"
    assert str(d) in str(p)


def test_workspace_path_rejects_traversal(tmp_path):
    wm = WorkspaceManager(tmp_path / "ws")
    wm.create("doc-1")
    with pytest.raises(ValueError):
        wm.path("doc-1", "..", "escape.txt")


def test_workspace_sweep_expired(tmp_path):
    wm = WorkspaceManager(tmp_path / "ws")
    fresh = wm.create("fresh")
    old = wm.create("old")
    past = time.time() - 3 * 3600
    os.utime(old, (past, past))

    removed = wm.sweep_expired(ttl_minutes=120)

    assert removed == 1
    assert fresh.is_dir()
    assert not old.exists()
