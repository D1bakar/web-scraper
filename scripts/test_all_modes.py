"""End-to-end API test for all 11 scrape modes."""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000/api"


def req(method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(
        BASE + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


def wait_job(job_id: str, timeout: int = 90) -> dict:
    job: dict = {}
    for _ in range(timeout * 2):
        _, job = req("GET", f"/jobs/{job_id}")
        if job["status"] in ("completed", "failed"):
            return job
        time.sleep(0.5)
    return job


MODES: dict[str, dict] = {
    "price_compare": {
        "mode": "price_compare",
        "urls": [
            "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
            "https://books.toscrape.com/catalogue/tipping-the-velvet_999/index.html",
        ],
        "price_selector": ".price_color",
        "check_robots": False,
        "delay": 0,
    },
    "quotes": {"mode": "quotes", "max_pages": 1, "check_robots": False, "delay": 0},
    "meta": {
        "mode": "meta",
        "url": "https://quotes.toscrape.com",
        "check_robots": False,
        "delay": 0,
    },
    "links": {
        "mode": "links",
        "url": "https://quotes.toscrape.com",
        "same_domain": True,
        "check_robots": False,
        "delay": 0,
    },
    "tables": {
        "mode": "tables",
        "url": "https://quotes.toscrape.com/tableful",
        "check_robots": False,
        "delay": 0,
    },
    "selectors": {
        "mode": "selectors",
        "url": "https://quotes.toscrape.com",
        "selectors": ["div.quote span.text", "small.author"],
        "check_robots": False,
        "delay": 0,
    },
    "sitemap": {
        "mode": "sitemap",
        "url": "https://wordpress.org/sitemap.xml",
        "max_urls": 50,
        "check_robots": False,
        "delay": 0,
    },
    "email_extract": {
        "mode": "email_extract",
        "url": "https://www.w3.org/People/Berners-Lee/",
        "check_robots": False,
        "delay": 0,
    },
    "json_ld": {
        "mode": "json_ld",
        "url": "https://wordpress.org/",
        "check_robots": False,
        "delay": 0,
    },
    "social_meta": {
        "mode": "social_meta",
        "url": "https://quotes.toscrape.com",
        "check_robots": False,
        "delay": 0,
    },
    "readability": {
        "mode": "readability",
        "url": "https://quotes.toscrape.com",
        "check_robots": False,
        "delay": 0,
    },
}


def main() -> int:
    health_code, health = req("GET", "/health")
    print(f"Health {health_code}: {health}")
    if health_code != 200:
        print("Server not reachable")
        return 1

    results: dict[str, dict] = {}
    for mode, body in MODES.items():
        code, created = req("POST", "/jobs", body)
        if code != 202:
            results[mode] = {"pass": False, "stage": "create", "code": code, "detail": created}
            continue

        job = wait_job(created["job_id"])
        ok = job["status"] == "completed" and job.get("total_items", 0) > 0
        if job["status"] == "completed":
            _, res = req("GET", f"/jobs/{created['job_id']}/results")
            ok = res.get("item_count", 0) > 0
        results[mode] = {
            "pass": ok,
            "status": job["status"],
            "items": job.get("total_items", 0),
            "error": job.get("error"),
        }

    print(json.dumps(results, indent=2))
    failed = [m for m, r in results.items() if not r.get("pass")]
    if failed:
        print(f"FAILED modes: {failed}")
        return 1
    print("All 11 modes passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
