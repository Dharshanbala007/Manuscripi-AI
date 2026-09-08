import io
import time

import pytest

from tests.fixtures.gen import academic_docx

_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _analyze(client, data):
    doc_id = client.post(
        "/api/documents/upload",
        files={"file": ("paper.docx", io.BytesIO(data), _CT)},
    ).json()["id"]
    client.post(f"/api/documents/{doc_id}/analyze")
    for _ in range(150):
        if client.get(f"/api/documents/{doc_id}/analysis").json()["state"] in ("analyzed", "error"):
            break
        time.sleep(0.02)
    return doc_id


@pytest.mark.parametrize("messy", [False, True])
def test_upload_analyze_format_validate_end_to_end(client, messy):
    doc_id = _analyze(client, academic_docx(messy=messy))

    fmt = client.post(f"/api/documents/{doc_id}/format", json={"profile_id": "ieee"})
    assert fmt.status_code == 200
    fmt_body = fmt.json()
    assert fmt_body["state"] == "formatted"
    assert fmt_body["change_log"]["content_changes"] == []

    val = client.post(f"/api/documents/{doc_id}/validate")
    assert val.status_code == 200
    val_body = val.json()
    assert val_body["state"] == "validated"
    assert val_body["preservation"]["passed"] is True
    assert 0 <= val_body["health"]["total"] <= 100

    if messy:
        assert any(i["severity"] in ("warning", "info") for i in val_body["issues"])
