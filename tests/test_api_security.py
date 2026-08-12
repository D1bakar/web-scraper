"""API security and retry tests."""


def test_health_detail(client):
    response = client.get("/api/health/detail")
    assert response.status_code == 200
    data = response.json()
    assert "uptime_seconds" in data
    assert "active_jobs" in data
    assert "ssrf_protection" in data


def test_retry_requires_failed_job(client):
    create = client.post("/api/jobs", json={"mode": "quotes", "max_pages": 1, "check_robots": False})
    job_id = create.json()["job_id"]
    response = client.post(f"/api/jobs/{job_id}/retry")
    assert response.status_code == 409


def test_block_ssrf_in_job(client):
    response = client.post(
        "/api/jobs",
        json={"mode": "meta", "url": "http://127.0.0.1/admin"},
    )
    assert response.status_code == 422


def test_settings_includes_security_fields(client):
    response = client.get("/api/settings")
    assert response.status_code == 200
    data = response.json()
    assert "rate_limit_per_minute" in data
    assert "api_key_required" in data
