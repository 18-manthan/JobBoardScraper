import asyncio
import types

import pytest

from app.crud import get_saved_jobs


@pytest.mark.asyncio
async def test_get_saved_jobs_filters_build(monkeypatch):
    class FakeSession:
        async def execute(self, query):
            class Result:
                def scalars(self):
                    class Scalars:
                        def all(self):
                            return [types.SimpleNamespace(__dict__={"id": 1}), types.SimpleNamespace(__dict__={"id": 2})]
                    return Scalars()
            return Result()
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            return False

    class FakeSessionFactory:
        def __call__(self):
            return FakeSession()

    monkeypatch.setattr("app.crud.AsyncSessionLocal", FakeSessionFactory(), raising=True)

    result = await get_saved_jobs(
        search="python",
        company="ACME",
        location="Remote",
        source="LinkedIn",
        liked=True,
        applied=False,
        limit=10,
        offset=0,
    )

    assert "jobs" in result and isinstance(result["jobs"], list)
    assert "pagination" in result and result["pagination"]["limit"] == 10


