import io

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from tests.fixtures.gen import minimal_docx_bytes

_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
ALICE = {"x-client-id": "alice-client-id-0001"}
BOB = {"x-client-id": "bob-client-id-000002"}


def _upload(client, headers=None) -> str:
    response = client.post(
        "/api/documents/upload",
        files={"file": ("p.docx", io.BytesIO(minimal_docx_bytes()), _CT)},
        headers=headers or {},
    )
    return response.json()["id"]


@pytest.fixture
def shared_client(monkeypatch):
    """A server that scopes history per visitor, as in a hosted deployment."""
    monkeypatch.setenv("HISTORY_SCOPE_BY_OWNER", "true")
    get_settings.cache_clear()
    from app.main import create_app

    with TestClient(create_app()) as client:
        yield client


def test_each_visitor_only_sees_their_own_documents(shared_client):
    alice_doc = _upload(shared_client, ALICE)
    bob_doc = _upload(shared_client, BOB)

    assert [r["id"] for r in shared_client.get("/api/history", headers=ALICE).json()] == [alice_doc]
    assert [r["id"] for r in shared_client.get("/api/history", headers=BOB).json()] == [bob_doc]


def test_no_client_id_lists_nothing(shared_client):
    _upload(shared_client, ALICE)
    assert shared_client.get("/api/history").json() == []
    assert shared_client.get("/api/history", headers={"x-client-id": "short"}).json() == []


def test_a_visitor_cannot_delete_someone_elses_row(shared_client):
    alice_doc = _upload(shared_client, ALICE)
    assert shared_client.delete(f"/api/history/{alice_doc}", headers=BOB).status_code == 204
    assert len(shared_client.get("/api/history", headers=ALICE).json()) == 1
    assert shared_client.delete(f"/api/history/{alice_doc}", headers=ALICE).status_code == 204
    assert shared_client.get("/api/history", headers=ALICE).json() == []


def test_local_mode_is_unscoped_and_needs_no_header(client):
    doc_id = _upload(client)
    rows = client.get("/api/history").json()
    assert [r["id"] for r in rows] == [doc_id]
    assert "owner" not in rows[0]  # the anonymous id is never exposed


def test_a_history_outage_does_not_fail_uploads_or_the_list():
    from app.main import create_app
    from app.storage.history import HistoryError, HistoryStore

    class Down(HistoryStore):
        def upsert(self, entry):
            raise HistoryError("down")

        def get(self, entry_id):
            raise HistoryError("down")

        def list(self, limit=20, owner=None):
            raise HistoryError("down")

        def delete(self, entry_id, owner=None):
            raise HistoryError("down")

    app = create_app()
    app.state.history = Down()
    with TestClient(app) as client:
        assert _upload(client)  # 201, not a 500
        assert client.get("/api/history").json() == []
        assert client.delete("/api/history/whatever").status_code == 204


def test_remote_backend_requires_url_and_token(monkeypatch):
    monkeypatch.setenv("HISTORY_BACKEND", "remote")
    get_settings.cache_clear()
    from app.main import create_app

    with pytest.raises(ValueError, match="HISTORY_API_URL"):
        create_app()
