"""Tests for mobile-first API features (v2.4)."""

from fastapi.testclient import TestClient


def test_dashboard_summary(client):
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "active_jobs" in data
    assert "recent_jobs" in data
    assert "success_rate" in data


def test_dashboard_summary_mobile(client):
    response = client.get("/api/dashboard/summary?mobile=true")
    assert response.status_code == 200
    assert len(response.json()["recent_jobs"]) <= 5


def test_jobs_pagination_mobile(client):
    for _ in range(3):
        client.post("/api/jobs", json={"mode": "quotes", "max_pages": 1})
    response = client.get("/api/jobs?mobile=true&limit=50")
    assert response.status_code == 200
    data = response.json()
    assert len(data["jobs"]) <= 10
    assert "total" in data


def test_jobs_pagination_offset(client):
    client.post("/api/jobs", json={"mode": "quotes", "max_pages": 1})
    response = client.get("/api/jobs?limit=1&offset=0")
    assert response.status_code == 200
    assert len(response.json()["jobs"]) == 1


def test_api_key_lifecycle(client):
    create = client.post("/api/api-keys?name=Test+Key")
    assert create.status_code == 201
    data = create.json()
    assert "api_key" in data
    assert data["api_key"].startswith("wsp_")

    listing = client.get("/api/api-keys")
    assert listing.status_code == 200
    assert len(listing.json()) >= 1

    revoke = client.delete(f"/api/api-keys/{data['id']}")
    assert revoke.status_code == 204


def test_schedule_crud(client):
    create = client.post(
        "/api/schedules",
        json={
            "name": "Hourly quotes",
            "mode": "quotes",
            "frequency": "hourly",
            "config": {"max_pages": 1, "check_robots": False},
        },
    )
    assert create.status_code == 201
    sched_id = create.json()["id"]

    listing = client.get("/api/schedules")
    assert any(s["id"] == sched_id for s in listing.json())

    pause = client.patch(f"/api/schedules/{sched_id}", json={"enabled": False})
    assert pause.status_code == 200
    assert pause.json()["enabled"] is False

    delete = client.delete(f"/api/schedules/{sched_id}")
    assert delete.status_code == 204


def test_webhook_crud(client):
    create = client.post(
        "/api/webhooks",
        json={
            "name": "Test hook",
            "url": "https://httpbin.org/post",
            "events": ["job.completed"],
        },
    )
    assert create.status_code == 201
    hook_id = create.json()["id"]

    listing = client.get("/api/webhooks")
    assert len(listing.json()) >= 1

    delete = client.delete(f"/api/webhooks/{hook_id}")
    assert delete.status_code == 204


def test_auth_status_open_by_default(client):
    response = client.get("/api/auth/status")
    assert response.status_code == 200
    data = response.json()
    assert data["auth_enabled"] is False
    assert data["authenticated"] is True


def test_auth_login_when_configured(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'auth.db'}")
    monkeypatch.setenv("ADMIN_USER", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "secret123")
    from app.core.config import get_settings
    from app.db.database import init_db, reset_db_engine
    from app.main import create_app

    get_settings.cache_clear()
    reset_db_engine()
    init_db()

    with TestClient(create_app()) as client:
        status = client.get("/api/auth/status")
        assert status.json()["auth_enabled"] is True
        assert status.json()["authenticated"] is False

        bad = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
        assert bad.status_code == 401

        good = client.post("/api/auth/login", json={"username": "admin", "password": "secret123"})
        assert good.status_code == 200

        me = client.get("/api/auth/me")
        assert me.json()["authenticated"] is True

    get_settings.cache_clear()
    reset_db_engine()


def test_serve_manifest(client):
    response = client.get("/static/manifest.json")
    assert response.status_code == 200


def test_serve_login_page(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert "Sign In" in response.text
