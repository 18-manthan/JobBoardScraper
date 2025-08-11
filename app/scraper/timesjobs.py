import argparse
import asyncio
import csv
import json
from typing import Dict, List, Optional

import httpx
from bs4 import BeautifulSoup


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Connection": "keep-alive",
    "Referer": "https://www.timesjobs.com/",
}


def _first_text(el) -> str:
    if not el:
        return ""
    return el.get_text(strip=True)


def _normalize_url(href: Optional[str]) -> str:
    if not href:
        return ""
    if href.startswith("http"):
        return href
    return f"https://www.timesjobs.com{href}"


def _extract_card(card) -> Dict[str, str]:
    title_el = (
        card.select_one("h2 a")
        or card.select_one("header h2 a")
        or card.select_one(".job-bx h2 a")
        or card.select_one("a[href*='jobid']")
    )
    title = _first_text(title_el)
    url = _normalize_url(title_el.get("href") if title_el else "")

    # Company
    company_el = (
        card.select_one("h3 .joblist-comp-name")
        or card.select_one(".joblist-comp-name")
        or card.select_one(".comp-name")
        or card.select_one("span.company")
    )
    company_text = _first_text(company_el)
    # TimesJobs often includes trailing "(More Jobs)" text, strip it
    company = company_text.replace("(More Jobs)", "").strip() or "Unknown Company"

    location_el = (
        card.select_one("ul.top-jd-dtl li span.loc")
        or card.select_one("span.location")
        or card.select_one("i.hiring_loc + span")
        or card.select_one(".job-location")
    )
    location = _first_text(location_el) or "Remote"

    return {
        "title": title,
        "company": company,
        "location": location,
        "url": url,
    }


async def _fetch_html(client: httpx.AsyncClient, params: dict) -> Optional[str]:
    try:
        resp = await client.get("https://www.timesjobs.com/candidate/job-search.html", params=params)
        resp.raise_for_status()
        return resp.text
    except Exception:
        return None


async def scrape_timesjobs(query: str = "python developer", location: str = "remote", limit: int = 10) -> List[Dict[str, str]]:
    """Scrape TimesJobs listings and return normalized results."""
    results: List[Dict[str, str]] = []
    async with httpx.AsyncClient(headers=DEFAULT_HEADERS, follow_redirects=True, timeout=15.0) as client:
        # Try a few pagination parameter patterns used on TimesJobs
        page = 1
        while len(results) < limit and page <= 5:
            params = {
                "searchType": "Home_Search",
                "from": "submit",
                "txtKeywords": query,
                "txtLocation": location,
                "sequence": page,
            }
            html = await _fetch_html(client, params)
            if not html and page == 1:
                # Try alternate parameter names
                params_alt = {
                    "searchType": "Home_Search",
                    "from": "submit",
                    "txtKeywords": query,
                    "txtLocation": location,
                    "curPg": page,
                }
                html = await _fetch_html(client, params_alt)
            
            if not html and page == 1:
                # Try without location parameter
                params_no_loc = {
                    "searchType": "Home_Search",
                    "from": "submit",
                    "txtKeywords": query,
                    "sequence": page,
                }
                html = await _fetch_html(client, params_no_loc)

            if not html:
                break

            soup = BeautifulSoup(html, "html.parser")
            cards = (
                soup.select("li.clearfix.job-bx, div.job-bx")
                or soup.select(".job-bx")
                or soup.select("article")
                or []
            )

            if not cards:
                break

            for card in cards:
                if len(results) >= limit:
                    break
                data = _extract_card(card)
                if data.get("title") and data.get("url"):
                    results.append(
                        {
                            "title": data["title"],
                            "company": data["company"],
                            "location": data["location"],
                            "description": "",
                            "url": data["url"],
                            "liked": False,
                            "applied": False,
                            "source": "TimesJobs",
                        }
                    )

            page += 1

    return results[:limit]


def _write_output(rows: List[Dict[str, str]], output: str) -> None:
    if output.lower().endswith(".json"):
        with open(output, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
    elif output.lower().endswith(".csv"):
        fieldnames = ["title", "company", "location", "url", "source"]
        with open(output, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow({k: row.get(k, "") for k in fieldnames})
    else:
        print(json.dumps(rows, ensure_ascii=False, indent=2))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Standalone TimesJobs scraper")
    parser.add_argument("--query", required=True, help="Job keywords, e.g. 'data scientist'")
    parser.add_argument("--location", required=True, help="Location, e.g. 'Noida, Uttar Pradesh'")
    parser.add_argument("--num-results", type=int, default=10, help="Total number of results to collect")
    parser.add_argument("--output", default="", help="Path to write output (.json or .csv). If omitted, prints JSON to stdout")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    rows = asyncio.run(scrape_timesjobs(args.query, args.location, args.num_results))
    if args.output:
        _write_output(rows, args.output)
    else:
        print(json.dumps(rows, ensure_ascii=False, indent=2))


