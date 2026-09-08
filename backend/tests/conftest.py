"""Shared test fixtures."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings


@pytest.fixture(scope="session")
def sample_dir():
    from pathlib import Path

    return Path(__file__).parents[2] / "sample_documents"


@pytest.fixture(params=["sample_basic", "sample_complex", "sample_messy"])
def sample_docx(request, sample_dir):
    path = sample_dir / f"{request.param}.docx"
    if not path.exists():
        pytest.skip(f"{path.name} not generated; run scripts/gen_samples.py")
    return path


@pytest.fixture(autouse=True)
def _isolated_settings(tmp_path, monkeypatch):
    """Every test gets a fresh Settings bound to a throwaway work dir."""
    monkeypatch.setenv("WORK_DIR", str(tmp_path / "ws"))
    monkeypatch.setenv("WORKSPACE_TTL_MIN", "120")
    monkeypatch.setenv("MAX_UPLOAD_MB", "25")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def client():
    from app.main import create_app

    app = create_app()
    with TestClient(app) as c:
        yield c


@pytest.fixture
def analyzed_doc(client):
    """(client, doc_id) for a document that has finished analysis."""
    import io
    import time

    from tests.fixtures.gen import academic_docx

    ct = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    doc_id = client.post(
        "/api/documents/upload",
        files={"file": ("paper.docx", io.BytesIO(academic_docx()), ct)},
    ).json()["id"]
    client.post(f"/api/documents/{doc_id}/analyze")

    state = "analyzing"
    for _ in range(100):
        state = client.get(f"/api/documents/{doc_id}/analysis").json()["state"]
        if state in ("analyzed", "error"):
            break
        time.sleep(0.02)
    assert state == "analyzed"
    return client, doc_id
