from typing import List, Dict, Callable, Optional
import asyncio

from .linkedin import scrape_linkedin
from .careerjet import scrape_careerjet
from .timesjobs import scrape_timesjobs


SCRAPERS: Dict[str, Callable[..., asyncio.Future]] = {
    "linkedin": scrape_linkedin,
    "careerjet": scrape_careerjet,
    "timesjobs": scrape_timesjobs,
}

async def aggregate_jobs(
    query: str = "python developer",
    location: str = "remote",
    limit: int = 10,
    sources: Optional[List[str]] = None,
) -> List[dict]:
    """Run selected scrapers concurrently and combine results. Limit is per source."""
    selected_sources = [s.lower() for s in (sources or list(SCRAPERS.keys())) if s.lower() in SCRAPERS]
    if not selected_sources:
        return []

    # Apply the requested limit per source
    tasks = [SCRAPERS[name](query=query, location=location, limit=limit) for name in selected_sources]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    combined: List[dict] = []
    for res in results:
        if isinstance(res, Exception):
            continue
        if isinstance(res, list):
            combined.extend(res)

    return combined