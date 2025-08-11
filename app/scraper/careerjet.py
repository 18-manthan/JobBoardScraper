from __future__ import annotations

import argparse
import asyncio
import csv
import json
import re
import sys
from typing import Dict, List, Optional

import httpx
from bs4 import BeautifulSoup


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Connection": "keep-alive",
}


def _slugify(text: str) -> str:
    cleaned = re.sub(r"[,/]+", " ", text.strip().lower())
    cleaned = re.sub(r"\s+", "+", cleaned)
    return cleaned


def _first_text(el) -> str:
    if not el:
        return ""
    return el.get_text(strip=True)


def _normalize_url(href: Optional[str]) -> str:
    if not href:
        return ""
    if href.startswith("http"):
        return href
    return f"https://www.careerjet.com{href}"


def _extract_job_card(card) -> Dict[str, str]:
    # Title + URL
    title_el = (
        card.select_one("h2 a")
        or card.select_one("a.title")
        or card.select_one("a[data-ga-tag='job-title']")
        or card.select_one("a")
    )
    title = _first_text(title_el)
    url = _normalize_url(title_el.get("href") if title_el else "")

    # Company
    company_el = card.select_one(".company, .company_name, span.company, div.job header div a")
    company = _first_text(company_el) or "Unknown Company"

    # Location
    location_el = card.select_one(".locations, span.location, .job-location")
    location = _first_text(location_el) or "Remote"

    return {
        "title": title,
        "company": company,
        "location": location,
        "url": url,
    }


def scrape_careerjet_sync(query: str, location: str, limit: int = 10, timeout: float = 15.0) -> List[Dict[str, str]]:
    keyword_slug = _slugify(query)
    loc_input = (location or "").strip().lower()
    is_remote = loc_input in {"remote", "work from home", "wfh", "anywhere"}
    location_slug = _slugify(location) if not is_remote else ""

    # Build URL attempts: prioritize no-location when remote-like input is used
    url_candidates = []
    if is_remote:
        url_candidates += [
            f"https://www.careerjet.com/search/jobs?s={keyword_slug}",
            f"https://www.careerjet.co.in/search/jobs?s={keyword_slug}",
            f"https://www.careerjet.com/jobs?s={keyword_slug}",
            f"https://www.careerjet.co.in/jobs?s={keyword_slug}",
        ]
    # With location (when provided)
    if location_slug:
        url_candidates += [
            f"https://www.careerjet.co.in/search/jobs?s={keyword_slug}&l={location_slug}",
            f"https://www.careerjet.com/search/jobs?s={keyword_slug}&l={location_slug}",
            f"https://www.careerjet.com/jobs?l={location_slug}&s={keyword_slug}",
            f"https://www.careerjet.co.in/jobs?l={location_slug}&s={keyword_slug}",
        ]
    # Final fallback (no location)
    url_candidates += [
        f"https://www.careerjet.com/search/jobs?s={keyword_slug}",
        f"https://www.careerjet.co.in/search/jobs?s={keyword_slug}",
        f"https://www.careerjet.com/jobs?s={keyword_slug}",
        f"https://www.careerjet.co.in/jobs?s={keyword_slug}",
    ]

    client = httpx.Client(headers=DEFAULT_HEADERS, follow_redirects=True, timeout=timeout)
    last_error: Optional[Exception] = None
    results: List[Dict[str, str]] = []

    for candidate in url_candidates:
        try:
            resp = client.get(candidate)
            resp.raise_for_status()
            html = resp.text
        except Exception as e:  # noqa: BLE001
            last_error = e
            continue

        soup = BeautifulSoup(html, "html.parser")
        # Common wrappers: try several possibilities
        cards = (
            soup.select("article.job")
            or soup.select("section.job")
            or soup.select("div.job")
            or soup.select("li.job")
            or soup.select("div[id^='job_']")
            or soup.select(".job")
        )

        if not cards:
            cards = soup.select(".jobs .result, .job-list .result")

        if not cards:
            continue

        for card in cards:
            if len(results) >= limit:
                break
            try:
                data = _extract_job_card(card)
                if data.get("title") and data.get("url"):
                    results.append(data)
            except Exception:  # noqa: BLE001
                continue

        if results:
            break

    if not results and last_error is not None:
        print(f"[WARN] CareerJet fetched but no results; last error: {last_error}")

    return results[:limit]


async def scrape_careerjet(query: str = "python developer", location: str = "remote", limit: int = 10) -> List[Dict[str, str]]:
    """Scrape CareerJet job listings and return normalized results."""
    raw = await asyncio.to_thread(scrape_careerjet_sync, query, location, limit, 15.0)
    normalized: List[Dict[str, str]] = []
    for row in raw[:limit]:
        normalized.append(
            {
                "title": row.get("title", ""),
                "company": row.get("company", "Unknown Company"),
                "location": row.get("location", location or "Remote"),
                "description": "",
                "url": row.get("url", ""),
                "liked": False,
                "applied": False,
                "source": "CareerJet",
            }
        )
    return normalized


def _write_output(rows: List[Dict[str, str]], output: str) -> None:
    if output.lower().endswith(".json"):
        with open(output, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        print(f"[INFO] Wrote {len(rows)} records to {output}")
    elif output.lower().endswith(".csv"):
        fieldnames = ["title", "company", "location", "url"]
        with open(output, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow({k: (row.get(k) or "") for k in fieldnames})
        print(f"[INFO] Wrote {len(rows)} records to {output}")
    else:
        print(json.dumps(rows, ensure_ascii=False, indent=2))


def _parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Standalone CareerJet job scraper")
    parser.add_argument("--query", required=True, help="Job keywords, e.g. 'data scientist'")
    parser.add_argument("--location", required=True, help="Location, e.g. 'Noida, Uttar Pradesh'")
    parser.add_argument("--num-results", type=int, default=10, help="Total number of results to collect")
    parser.add_argument("--output", default="", help="Path to write output (.json or .csv). If omitted, prints JSON to stdout")
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = _parse_args(sys.argv[1:])
    print("[START] CareerJet Scraper Started")
    rows = scrape_careerjet_sync(args.query, args.location, args.num_results, 15.0)
    print(f"[RESULTS] Collected {len(rows)} records")
    if args.output:
        _write_output(rows, args.output)
    else:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    print("[END] Script Finished")


