"""Shared test fixtures."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings


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
