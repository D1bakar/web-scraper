"""API endpoint tests."""

import time


def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_get_settings(client):
    response = client.get("/api/settings")
    assert response.status_code == 200
    data = response.json()
    assert "default_delay" in data
    assert "default_timeout" in data


def test_create_quotes_job(client):
    response = client.post("/api/jobs", json={"mode": "quotes", "max_pages": 1})
    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "pending"


def test_list_jobs(client):
    client.post("/api/jobs", json={"mode": "quotes", "max_pages": 1})
    response = client.get("/api/jobs")
    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    assert len(data["jobs"]) >= 1


def test_job_lifecycle(client):
    create = client.post("/api/jobs", json={"mode": "quotes", "max_pages": 1, "check_robots": False})
    job_id = create.json()["job_id"]

    for _ in range(30):
        job = client.get(f"/api/jobs/{job_id}").json()
        if job["status"] in ("completed", "failed"):
            break
        time.sleep(0.5)

    assert job["status"] == "completed"

    results = client.get(f"/api/jobs/{job_id}/results")
    assert results.status_code == 200
    assert results.json()["item_count"] > 0

    export = client.get(f"/api/jobs/{job_id}/export?format=json")
    assert export.status_code == 200
    assert export.headers["content-type"] == "application/json"


def test_meta_requires_url(client):
    response = client.post("/api/jobs", json={"mode": "meta"})
    assert response.status_code == 422


def test_serve_dashboard(client):
    response = client.get("/")
    assert response.status_code == 200
