import io
import time

from tests.fixtures.gen import academic_docx, minimal_docx_bytes

_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _upload(client, data=None):
    payload = academic_docx() if data is None else data
    return client.post(
        "/api/documents/upload", files={"file": ("p.docx", io.BytesIO(payload), _CT)}
    ).json()["id"]


def _upload_analyze_format(client):
    doc_id = _upload(client)
    client.post(f"/api/documents/{doc_id}/analyze")
    for _ in range(150):
        if client.get(f"/api/documents/{doc_id}/analysis").json()["state"] in ("analyzed", "error"):
            break
        time.sleep(0.02)
    client.post(f"/api/documents/{doc_id}/format", json={"profile_id": "ieee"})
    return doc_id


def test_history_row_reflects_the_lifecycle(client):
    doc_id = _upload_analyze_format(client)

    rows = client.get("/api/history").json()
    assert len(rows) == 1
    row = rows[0]
    assert row["id"] == doc_id
    assert row["state"] == "formatted"
    assert row["profile_id"] == "ieee"
    assert isinstance(row["health_total"], int)
    assert row["preservation_passed"] is True
    assert row["paragraphs"] > 0
    assert row["session_active"] is True


def test_delete_history_row(client):
    doc_id = _upload_analyze_format(client)
    assert client.delete(f"/api/history/{doc_id}").status_code == 204
    assert client.get("/api/history").json() == []


def test_delete_document_keeps_the_history_row(client):
    doc_id = _upload_analyze_format(client)
    assert client.delete(f"/api/documents/{doc_id}").status_code == 204

    rows = client.get("/api/history").json()
    assert len(rows) == 1
    assert rows[0]["id"] == doc_id
    assert rows[0]["session_active"] is False


def test_history_respects_limit(client):
    for _ in range(3):
        client.post(
            "/api/documents/upload",
            files={"file": ("p.docx", io.BytesIO(minimal_docx_bytes()), _CT)},
        )
    rows = client.get("/api/history", params={"limit": 2}).json()
    assert len(rows) == 2
