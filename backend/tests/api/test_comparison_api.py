def test_comparison_before_format_is_409(analyzed_doc):
    client, doc_id = analyzed_doc
    resp = client.get(f"/api/documents/{doc_id}/comparison")
    assert resp.status_code == 409
    assert resp.json()["error"] == "not_formatted"


def test_comparison_after_format(analyzed_doc):
    client, doc_id = analyzed_doc
    client.post(f"/api/documents/{doc_id}/format", json={"profile_id": "ieee"})

    body = client.get(f"/api/documents/{doc_id}/comparison").json()

    assert body["original"]["stats"]["references"] == body["formatted"]["stats"]["references"]
    assert body["deltas"]["tables"] == 0
    assert body["deltas"]["figures"] == 0
    assert body["summary"]["preservation_passed"] is True
    assert body["summary"]["formatting_changes"] > 0
    assert isinstance(body["original"]["sections"], list)
    assert body["original"]["sections"]
    assert body["original"]["metadata"]["title"].startswith("A Rule-Based Approach")
