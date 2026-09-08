import io

from tests.fixtures.gen import minimal_docx_bytes

_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _flatten_block_ids(nodes):
    out = []
    for n in nodes:
        out.append(n["block_id"])
        out.extend(_flatten_block_ids(n["children"]))
    return out


def test_put_metadata_marks_field_edited(analyzed_doc):
    client, doc_id = analyzed_doc
    resp = client.put(
        f"/api/documents/{doc_id}/metadata",
        json={"title": "My Corrected Title", "keywords": ["alpha", "beta"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"]["value"] == "My Corrected Title"
    assert body["title"]["edited_by_user"] is True
    assert body["title"]["confidence"] == 1.0
    assert body["keywords"]["value"] == ["alpha", "beta"]


def test_patch_element_to_heading_updates_outline(analyzed_doc):
    client, doc_id = analyzed_doc
    page = client.get(f"/api/documents/{doc_id}/elements", params={"limit": 300}).json()
    para = next(i for i in page["items"] if i["kind"] == "paragraph")

    resp = client.patch(
        f"/api/documents/{doc_id}/elements/{para['id']}",
        json={"kind": "heading", "level": 2},
    )
    assert resp.status_code == 200
    assert resp.json()["kind"] == "heading"
    assert resp.json()["needs_review"] is False

    outline = client.get(f"/api/documents/{doc_id}/outline").json()
    assert para["id"] in _flatten_block_ids(outline["nodes"])


def test_patch_unknown_element_is_404(analyzed_doc):
    client, doc_id = analyzed_doc
    resp = client.patch(f"/api/documents/{doc_id}/elements/bZZZ", json={"kind": "heading"})
    assert resp.status_code == 404


def test_patch_bad_kind_is_422(analyzed_doc):
    client, doc_id = analyzed_doc
    page = client.get(f"/api/documents/{doc_id}/elements", params={"limit": 5}).json()
    resp = client.patch(
        f"/api/documents/{doc_id}/elements/{page['items'][0]['id']}",
        json={"kind": "totally-not-a-kind"},
    )
    assert resp.status_code == 422
    assert resp.json()["error"] == "bad_kind"


def test_metadata_edit_before_analysis_is_409(client):
    doc_id = client.post(
        "/api/documents/upload",
        files={"file": ("x.docx", io.BytesIO(minimal_docx_bytes()), _CT)},
    ).json()["id"]
    resp = client.put(f"/api/documents/{doc_id}/metadata", json={"title": "x"})
    assert resp.status_code == 409
