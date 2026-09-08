def test_formats_lists_ieee_available_and_springer_planned(client):
    resp = client.get("/api/formats")
    assert resp.status_code == 200
    by_id = {f["id"]: f for f in resp.json()}

    assert by_id["ieee"]["status"] == "available"
    assert by_id["ieee"]["features"]
    assert by_id["springer"]["status"] == "planned"
