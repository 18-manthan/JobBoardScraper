Job Aggregator API

FastAPI backend to scrape multiple job boards asynchronously, save jobs to Postgres, and export applied jobs to CSV. Includes optional Redis caching.

Features
- Async, per-source scraping (limit is per source)
- Sources: LinkedIn, CareerJet, TimesJobs
- Save jobs to DB with filters (search/company/location/source/liked/applied)
- Update liked/applied
- Export applied jobs to CSV
- Redis cache for scrape responses

In job scraping, if you set the limit to 3, it will fetch 9 jobs, 3 from each platform. Same logic applies for any limit.


