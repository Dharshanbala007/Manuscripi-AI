import io

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app
from tests.fixtures.gen import minimal_docx_bytes

_DOCX_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _upload(client, data=None, name="paper.docx", ctype=_DOCX_CT):
    payload = minimal_docx_bytes() if data is None else data
    return client.post(
        "/api/documents/upload",
        files={"file": (name, io.BytesIO(payload), ctype)},
    )


def test_upload_returns_201_and_state_uploaded(client):
    resp = _upload(client)
    assert resp.status_code == 201
    body = resp.json()
    assert body["state"] == "uploaded"
    assert body["id"]
    assert body["filename"] == "paper.docx"
    assert body["size"] > 0


def test_get_document_roundtrip(client):
    doc_id = _upload(client).json()["id"]
    resp = client.get(f"/api/documents/{doc_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == doc_id


def test_get_unknown_document_404(client):
    resp = client.get("/api/documents/does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["error"] == "not_found"


def test_upload_non_docx_rejected_415(client):
    resp = _upload(client, data=b"just some text", name="notes.txt", ctype="text/plain")
    assert resp.status_code == 415
    assert resp.json()["error"] == "not_docx"


def test_upload_corrupt_docx_rejected_400(client):
    resp = _upload(client, data=minimal_docx_bytes()[:150])
    assert resp.status_code == 400
    assert resp.json()["error"] == "corrupt"


def test_upload_filename_is_basename_only(client):
    resp = _upload(client, name="../../secret/evil.docx")
    assert resp.status_code == 201
    assert resp.json()["filename"] == "evil.docx"


def test_upload_oversize_rejected_413(monkeypatch, tmp_path):
    monkeypatch.setenv("WORK_DIR", str(tmp_path / "ws_big"))
    monkeypatch.setenv("MAX_UPLOAD_MB", "0")
    get_settings.cache_clear()
    with TestClient(create_app()) as fresh:
        resp = _upload(fresh)
    assert resp.status_code == 413
    assert resp.json()["error"] == "too_large"
