import asyncio
import types

import pytest

from app.scraper import aggregate_jobs


@pytest.mark.asyncio
async def test_aggregate_jobs_per_source_limit(monkeypatch):
    def make_fake_scraper(source_name: str):
        async def _scraper(query: str, location: str, limit: int):
            return [
                {
                    "title": f"{source_name} Title {i}",
                    "company": f"{source_name} Co",
                    "location": location,
                    "description": "",
                    "url": f"https://example.com/{source_name}/{i}",
                    "liked": False,
                    "applied": False,
                    "source": source_name.capitalize(),
                }
                for i in range(limit)
            ]
        return _scraper

    fake_map = {
        "linkedin": make_fake_scraper("linkedin"),
        "naukri": make_fake_scraper("naukri"),
        "careerjet": make_fake_scraper("careerjet"),
    }

    # Patch SCRAPERS with fakes
    monkeypatch.setattr("app.scraper.SCRAPERS", fake_map, raising=True)

    per_source_limit = 7
    sources = ["linkedin", "naukri", "careerjet"]
    jobs = await aggregate_jobs(
        query="python developer", location="remote", limit=per_source_limit, sources=sources
    )

    assert len(jobs) == per_source_limit * len(sources)
    counts = {}
    for j in jobs:
        counts[j["source"].lower()] = counts.get(j["source"].lower(), 0) + 1
    for s in sources:
        assert counts.get(s, 0) == per_source_limit


