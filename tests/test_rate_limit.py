"""Rate limit middleware tests."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.middleware import RateLimitMiddleware


def _client(limit: int = 5) -> TestClient:
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, requests_per_minute=limit, localhost_multiplier=1)

    @app.get("/api/health")
    def health():
        return {"ok": True}

    @app.get("/api/jobs/{job_id}")
    def job_status(job_id: str):
        return {"id": job_id}

    @app.get("/api/jobs/{job_id}/results")
    def job_results(job_id: str):
        return {"data": [], "item_count": 0}

    @app.post("/api/jobs")
    def create_job():
        return {"ok": True}

    return TestClient(app)


def test_health_exempt_from_rate_limit():
    client = _client(limit=2)
    for _ in range(10):
        assert client.get("/api/health").status_code == 200


def test_job_polling_exempt_from_rate_limit():
    client = _client(limit=2)
    for _ in range(10):
        assert client.get("/api/jobs/abc").status_code == 200


def test_job_results_exempt_from_rate_limit():
    client = _client(limit=2)
    for _ in range(10):
        assert client.get("/api/jobs/abc/results").status_code == 200


def test_job_create_is_rate_limited():
    client = _client(limit=2)
    assert client.post("/api/jobs").status_code == 200
    assert client.post("/api/jobs").status_code == 200
    assert client.post("/api/jobs").status_code == 429
