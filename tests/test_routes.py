import asyncio
import json

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_scrape_endpoint_per_source_limit(monkeypatch, client):
    # dummey aggregator to control output size
    async def fake_aggregate_jobs(query: str, location: str, limit: int, sources):
        results = []
        for s in sources:
            for i in range(limit):
                results.append({
                    "title": f"{s} {i}",
                    "company": "Co",
                    "location": location,
                    "description": "",
                    "url": f"https://example.com/{s}/{i}",
                    "liked": False,
                    "applied": False,
                    "source": s.capitalize(),
                })
        return results

    from app import scraper as scraper_pkg
    monkeypatch.setattr(scraper_pkg, "aggregate_jobs", fake_aggregate_jobs, raising=True)

    resp = client.get("/api/jobs/scrape", params={
        "query": "python developer",
        "location": "remote",
        "limit": 5,
        "sources": "linkedin,naukri,careerjet"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["per_source_limit"] == 5
    assert data["total_jobs"] == 15
    assert len(data["jobs"]) == 15


