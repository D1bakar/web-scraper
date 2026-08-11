"""Test configuration."""

import pytest
from fastapi.testclient import TestClient

from app.db.database import init_db, reset_db_engine
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    from app.core.config import get_settings

    get_settings.cache_clear()
    reset_db_engine()
    init_db()
    with TestClient(app) as c:
        yield c
    get_settings.cache_clear()
    reset_db_engine()
