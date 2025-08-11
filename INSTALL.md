Install and Run

Two supported setups: with Docker, and without Docker (native).

Option A: Docker (API + Postgres + Redis)
- Prerequisites: Docker Desktop running
- Steps:
  1) git clone https://github.com/18-manthan/JobBoardScraper.git && cd JobBoardScraper
  2) docker compose up --build
  3) API: http://127.0.0.1:8000 (docs at /docs)
  4) API: http://127.0.0.1:8000/docs (swagger)
- What it starts:
  - API on 8000, Postgres in-network on 5432, Redis on 6379
  - Tables auto-create on API startup
- Useful:
  - Stop: Ctrl+C or `docker compose down`
  - Clean DB volume: `docker compose down --volumes`
  - Tests: `docker compose run --rm api pytest -q`
- Troubleshooting:
  - Port in use: edit the `8000:8000` mapping in docker-compose.yml
  - Orphan warning: add `--remove-orphans`

Option B: Native (no Docker)
- Prereqs: Python 3.11+, Postgres
- Steps:
  1) python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
  2) Start Postgres and create DB, e.g. `createdb jobdb`
  3) export DATABASE_URL="postgresql+asyncpg://postgres@localhost/jobdb"; export SQL_ECHO=false
  4) uvicorn app.main:app --reload
  5) Open http://127.0.0.1:8000/docs
- Optional caching:
  - Redis local: export REDIS_URL="redis://localhost:6379/0"

Verification
- DB check: GET /api/jobs/test-db → {"message":"Database connection successful"}
- Scrape sample:
  curl "http://127.0.0.1:8000/api/jobs/scrape?query=python%20developer&location=remote&limit=5&sources=linkedin,careerjet,timesjobs"

Tests
- pytest -q

Notes
- Tables are created at startup
- If Redis is unreachable, caching is skipped
- Public job boards change markup, selectors may need occasional tweaks


