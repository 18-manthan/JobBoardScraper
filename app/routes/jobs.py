from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from app.crud import save_job, get_saved_jobs, export_applied_jobs, update_job_status
from app.schemas import JobCreate, JobStatusUpdate
import io

router = APIRouter()

@router.get("/scrape")
async def scrape(request: Request, jobrole: str = "python developer", location: str = "pune", limit: int = 10, sources: str = "linkedin,careerjet,timesjobs"):
    from app.scraper import aggregate_jobs

    selected_sources = [s.strip().lower() for s in sources.split(",") if s.strip()]

    from app.cache import build_cache_key, get_cache, set_cache
    cache_key = build_cache_key(
        "scrape",
        query=jobrole,
        location=location,
        limit=limit,
        sources=",".join(selected_sources),
    )
    cached = await get_cache(request.app, cache_key)
    if cached is not None:
        return cached

    jobs = await aggregate_jobs(query=jobrole, location=location, limit=limit, sources=selected_sources)

    payload = {
        "total_jobs": len(jobs),
        "jobs": jobs,
        "query": jobrole,
        "location": location,
        "sources": selected_sources,
        "per_source_limit": limit,
    }
    await set_cache(request.app, cache_key, payload, ttl_seconds=300)
    return payload

@router.get("/saved")
async def saved_jobs(
    search: str = None,
    company: str = None,
    location: str = None,
    source: str = None,
    liked: bool = None,
    applied: bool = None,
    limit: int = 10,
    offset: int = 0
):
    return await get_saved_jobs(
        search=search,
        company=company,
        location=location,
        source=source,
        liked=liked,
        applied=applied,
        limit=limit,
        offset=offset
    )

@router.post("/save", response_model=dict)
async def save(job_data: JobCreate):
    try:
        job_dict = job_data.model_dump()
        result = await save_job(job_dict)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save job: {str(e)}")

@router.put("/{job_id}/status", response_model=dict)
async def update_status(job_id: int, status_update: JobStatusUpdate):
    try:
        result = await update_job_status(
            job_id=job_id,
            title=status_update.title,
            liked=status_update.liked,
            applied=status_update.applied
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update job status: {str(e)}")

@router.get("/export")
async def export_csv():
    try:
        result = await export_applied_jobs()
        
        if not result.get("csv_data"):
            return {"message": result["message"]}
        
        csv_data = result["csv_data"].encode('utf-8')
        
        return StreamingResponse(
            io.BytesIO(csv_data),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={result['filename']}",
                "Content-Type": "text/csv; charset=utf-8"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.get("/export/json")
async def export_csv_json():
    try:
        return await export_applied_jobs()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.get("/test-db")
async def test_database():
    try:
        from app.db import AsyncSessionLocal
        from sqlalchemy import text
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return {"message": "Database connection successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

