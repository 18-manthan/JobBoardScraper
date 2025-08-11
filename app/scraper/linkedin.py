import httpx
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "DNT": "1",
    "Connection": "keep-alive"
}

async def scrape_linkedin(query: str = "python developer", location: str = "remote", limit: int = 10):
    """Scrape LinkedIn job listings and return normalized results."""
    base_url = "https://www.linkedin.com/jobs/search"
    params = {
        "keywords": query,
        "location": location,
        "f_TPR": "r86400",
        "position": 1,
        "pageNum": 0
    }
    
    url = f"{base_url}?{httpx.QueryParams(params)}"
    
    try:
        async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=15.0) as client:
            response = await client.get(url)
            response.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    jobs = []
    
    job_cards = (
        soup.select("li.base-card, .job-search-card, [data-job-id], div[data-job-id]")
        or []
    )
    
    for card in job_cards[:limit]:
        try:
            title_elem = card.select_one(".base-search-card__title, .job-search-card__title, h3, h2")
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            company_elem = card.select_one(
                ".base-search-card__subtitle, .job-search-card__subtitle, [data-testid='job-search-card__company-name']"
            )
            company = company_elem.get_text(strip=True) if company_elem else "Unknown Company"
            
            location_elem = card.select_one(
                ".job-search-card__location, .base-search-card__metadata, [data-testid='job-search-card__location']"
            )
            location = location_elem.get_text(strip=True) if location_elem else "Remote"
            
            link_elem = card.select_one("a") or card
            job_url = ""
            if link_elem:
                href = link_elem.get("href")
                if href:
                    if href.startswith("/"):
                        job_url = f"https://www.linkedin.com{href}"
                    else:
                        job_url = href
            
            job_id = card.get("data-job-id") or ""
            if job_id and not job_url:
                job_url = f"https://www.linkedin.com/jobs/view/{job_id}/"
            
            if title and job_url:
                job = {
                    "title": title,
                    "company": company,
                    "location": location,
                    "description": "",
                    "url": job_url,
                    "liked": False,
                    "applied": False,
                    "source": "LinkedIn"
                }
                jobs.append(job)
                
        except Exception:
            continue
    
    return jobs
