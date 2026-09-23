import io

from docx import Document

from app.export.pdf_export import pdf_available
from tests.fixtures.gen import minimal_docx_bytes

_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _formatted(analyzed_doc):
    client, doc_id = analyzed_doc
    client.post(f"/api/documents/{doc_id}/format", json={"profile_id": "ieee"})
    return client, doc_id


def test_export_docx_is_a_real_openable_docx(analyzed_doc):
    client, doc_id = _formatted(analyzed_doc)
    resp = client.get(f"/api/documents/{doc_id}/export/docx")

    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/vnd.openxml")
    assert "manuscript_ieee_formatted.docx" in resp.headers.get("content-disposition", "")
    assert resp.content[:4] == b"PK\x03\x04"

    doc = Document(io.BytesIO(resp.content))
    assert len(doc.paragraphs) > 5


def test_export_pdf_is_real_pdf_or_503(analyzed_doc):
    client, doc_id = _formatted(analyzed_doc)
    resp = client.get(f"/api/documents/{doc_id}/export/pdf")

    if pdf_available(client.app.state.settings):
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content[:5] == b"%PDF-"
        page_count = client.get(f"/api/documents/{doc_id}/analysis").json()["page_count"]
        assert isinstance(page_count, int) and page_count >= 1
    else:
        assert resp.status_code == 503
        assert resp.json()["error"] == "pdf_unavailable"


def test_page_count_is_null_before_any_pdf(analyzed_doc):
    client, doc_id = _formatted(analyzed_doc)
    assert client.get(f"/api/documents/{doc_id}/analysis").json()["page_count"] is None


def test_preview_returns_pdf_or_labelled_structured_html(analyzed_doc):
    client, doc_id = _formatted(analyzed_doc)
    resp = client.get(f"/api/documents/{doc_id}/preview")
    assert resp.status_code == 200

    if resp.headers["content-type"].startswith("application/pdf"):
        assert resp.content[:5] == b"%PDF-"
    else:
        assert "text/html" in resp.headers["content-type"]
        assert "Structural preview" in resp.text


def test_export_before_format_is_409(analyzed_doc):
    client, doc_id = analyzed_doc
    assert client.get(f"/api/documents/{doc_id}/export/docx").status_code == 409


def test_preview_falls_back_to_structured_html_on_an_unexpected_pdf_failure(
    analyzed_doc, monkeypatch
):
    """A crash or timeout in the PDF converter must never surface as a blank/500 iframe."""
    import app.api.routes_documents as routes

    def _boom(*args, **kwargs):
        raise RuntimeError("simulated LibreOffice crash")

    monkeypatch.setattr(routes, "pdf_available", lambda settings: True)
    monkeypatch.setattr(routes, "export_pdf", _boom)

    client, doc_id = _formatted(analyzed_doc)
    resp = client.get(f"/api/documents/{doc_id}/preview")

    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "Structural preview" in resp.text


def test_delete_removes_the_document(client):
    doc_id = client.post(
        "/api/documents/upload",
        files={"file": ("x.docx", io.BytesIO(minimal_docx_bytes()), _CT)},
    ).json()["id"]

    assert client.delete(f"/api/documents/{doc_id}").status_code == 204
    assert client.get(f"/api/documents/{doc_id}").status_code == 404
