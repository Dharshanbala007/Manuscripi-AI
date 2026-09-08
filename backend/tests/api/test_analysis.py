import io
import time

from tests.fixtures.gen import academic_docx

_DOCX_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _upload(client, data=None, name="paper.docx"):
    payload = academic_docx() if data is None else data
    return client.post(
        "/api/documents/upload",
        files={"file": (name, io.BytesIO(payload), _DOCX_CT)},
    )


def _wait_analyzed(client, doc_id, tries=100):
    for _ in range(tries):
        data = client.get(f"/api/documents/{doc_id}/analysis").json()
        if data["state"] in ("analyzed", "error"):
            return data
        time.sleep(0.02)
    raise AssertionError("analysis did not finish")


def test_analyze_runs_all_stages_with_counts(client):
    doc_id = _upload(client).json()["id"]

    started = client.post(f"/api/documents/{doc_id}/analyze")
    assert started.status_code == 202
    assert started.json()["state"] == "analyzing"

    data = _wait_analyzed(client, doc_id)
    assert data["state"] == "analyzed"
    assert [s["status"] for s in data["stages"]] == ["done"] * 7
    assert [s["key"] for s in data["stages"]] == [
        "read",
        "extract",
        "metadata",
        "classify",
        "figures",
        "references",
        "structure",
    ]
    assert data["stats"]["paragraphs"] > 0
    assert data["stats"]["headings"] >= 6
    assert data["stats"]["references"] == 6
    assert any("references" in s["detail"] for s in data["stages"])
    assert data["metadata"]["title"]["value"].startswith("A Rule-Based Approach")


def test_outline_and_elements_after_analysis(client):
    doc_id = _upload(client).json()["id"]
    client.post(f"/api/documents/{doc_id}/analyze")
    _wait_analyzed(client, doc_id)

    outline = client.get(f"/api/documents/{doc_id}/outline").json()
    assert len(outline["nodes"]) >= 5
    assert any(n["canonical"] == "introduction" for n in outline["nodes"])

    page = client.get(f"/api/documents/{doc_id}/elements", params={"offset": 0, "limit": 5}).json()
    assert len(page["items"]) == 5
    assert page["total"] > 5
    assert {"id", "kind", "confidence", "text_preview", "needs_review"} <= page["items"][0].keys()


def test_outline_before_analysis_is_409(client):
    doc_id = _upload(client).json()["id"]
    resp = client.get(f"/api/documents/{doc_id}/outline")
    assert resp.status_code == 409
    assert resp.json()["error"] == "not_analyzed"


def test_analyze_rejected_when_busy(client):
    doc_id = _upload(client).json()["id"]
    record = client.app.state.store.get(doc_id)
    record.state = "formatting"

    resp = client.post(f"/api/documents/{doc_id}/analyze")
    assert resp.status_code == 409
    assert resp.json()["error"] == "busy"


def test_reanalyze_after_analyzed_is_allowed(client):
    doc_id = _upload(client).json()["id"]
    client.post(f"/api/documents/{doc_id}/analyze")
    _wait_analyzed(client, doc_id)

    again = client.post(f"/api/documents/{doc_id}/analyze")
    assert again.status_code == 202
    assert _wait_analyzed(client, doc_id)["state"] == "analyzed"
