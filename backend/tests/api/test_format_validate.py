import io

from tests.fixtures.gen import minimal_docx_bytes

_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def test_format_ieee_returns_change_log_health_and_preservation(analyzed_doc):
    client, doc_id = analyzed_doc
    resp = client.post(f"/api/documents/{doc_id}/format", json={"profile_id": "ieee"})
    assert resp.status_code == 200
    body = resp.json()

    assert body["state"] == "formatted"
    assert body["profile_id"] == "ieee"
    assert body["change_log"]["formatting_changes"]
    assert body["change_log"]["content_changes"] == []
    assert 0 <= body["health"]["total"] <= 100
    assert set(body["health"]["categories"]) >= {"Structure", "Formatting", "References"}
    assert body["preservation"]["passed"] is True


def test_validate_after_format_sets_state_validated(analyzed_doc):
    client, doc_id = analyzed_doc
    client.post(f"/api/documents/{doc_id}/format", json={"profile_id": "ieee"})
    resp = client.post(f"/api/documents/{doc_id}/validate")
    assert resp.status_code == 200
    body = resp.json()
    assert body["state"] == "validated"
    assert "total" in body["health"]
    assert body["preservation"]["passed"] is True


def test_format_with_springer_is_422_planned(analyzed_doc):
    client, doc_id = analyzed_doc
    resp = client.post(f"/api/documents/{doc_id}/format", json={"profile_id": "springer"})
    assert resp.status_code == 422
    assert resp.json()["error"] == "profile_unavailable"
    assert "planned" in resp.json()["message"].lower()


def test_format_with_unknown_profile_is_422(analyzed_doc):
    client, doc_id = analyzed_doc
    resp = client.post(f"/api/documents/{doc_id}/format", json={"profile_id": "mla"})
    assert resp.status_code == 422


def test_format_before_analysis_is_409(client):
    doc_id = client.post(
        "/api/documents/upload",
        files={"file": ("x.docx", io.BytesIO(minimal_docx_bytes()), _CT)},
    ).json()["id"]
    resp = client.post(f"/api/documents/{doc_id}/format", json={"profile_id": "ieee"})
    assert resp.status_code == 409


def test_validate_before_format_is_409(analyzed_doc):
    client, doc_id = analyzed_doc
    resp = client.post(f"/api/documents/{doc_id}/validate")
    assert resp.status_code == 409
