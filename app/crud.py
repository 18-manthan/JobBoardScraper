
from app.models import Job
from app.db import AsyncSessionLocal
from sqlalchemy.future import select
import csv
import io
from datetime import datetime

async def save_job(job_data: dict):
    try:
        async with AsyncSessionLocal() as session:
            job = Job(**job_data)
            session.add(job)
            await session.commit()
            await session.refresh(job)
        return {"message": "Job saved successfully", "job_id": job.id}
    except Exception as e:
        raise Exception(f"Database error: {str(e)}")

async def update_job_status(job_id: int, liked: bool = None, applied: bool = None, title: str = None):
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Job).where(Job.id == job_id))
            job = result.scalar_one_or_none()
            
            if not job:
                raise Exception(f"Job with ID {job_id} not found")
            
            if title is not None and title != "":
                job.title = title
            if liked is not None:
                job.liked = liked
            if applied is not None:
                job.applied = applied
            
            await session.commit()
            await session.refresh(job)
            
            return {
                "message": "Job status updated successfully",
                "job_id": job.id,
                "title": job.title,
                "liked": job.liked,
                "applied": job.applied
            }
            
    except Exception as e:
        raise Exception(f"Update failed: {str(e)}")

async def get_saved_jobs(
    search: str = None,
    company: str = None,
    location: str = None,
    source: str = None,
    liked: bool = None,
    applied: bool = None,
    limit: int = 10,
    offset: int = 0
):
    async with AsyncSessionLocal() as session:
        query = select(Job)
        
        if search:
            search_filter = (
                Job.title.ilike(f"%{search}%") |
                Job.company.ilike(f"%{search}%") |
                Job.description.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
        
        if company:
            query = query.where(Job.company.ilike(f"%{company}%"))
        
        if location:
            query = query.where(Job.location.ilike(f"%{location}%"))
        
        if source:
            query = query.where(Job.source.ilike(f"%{source}%"))
        
        if liked is not None:
            query = query.where(Job.liked == liked)
        
        if applied is not None:
            query = query.where(Job.applied == applied)
        
        query = query.order_by(Job.created_at.desc()).offset(offset).limit(limit)
        
        result = await session.execute(query)
        jobs = result.scalars().all()
        
        count_query = select(Job)
        if search:
            count_query = count_query.where(search_filter)
        if company:
            count_query = count_query.where(Job.company.ilike(f"%{company}%"))
        if location:
            count_query = count_query.where(Job.location.ilike(f"%{location}%"))
        if source:
            count_query = count_query.where(Job.source.ilike(f"%{source}%"))
        if liked is not None:
            count_query = count_query.where(Job.liked == liked)
        if applied is not None:
            count_query = count_query.where(Job.applied == applied)
        
        count_result = await session.execute(count_query)
        total_count = len(count_result.scalars().all())
        
        return {
            "jobs": [job.__dict__ for job in jobs],
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_next": (offset + limit) < total_count,
                "has_prev": offset > 0
            }
        }
    
async def export_applied_jobs():
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Job).where(Job.applied == True).order_by(Job.created_at.desc())
            )
            jobs = result.scalars().all()
            
            if not jobs:
                return {"message": "No applied jobs found", "csv_data": ""}
            
            job_list = []
            for job in jobs:
                job_dict = {
                    "ID": job.id,
                    "Title": job.title,
                    "Company": job.company,
                    "Location": job.location,
                    "Description": job.description or "",
                    "URL": job.url,
                    "Source": job.source,
                    "Liked": "Yes" if job.liked else "No",
                    "Applied": "Yes" if job.applied else "No",
                    "Created At": job.created_at.strftime("%Y-%m-%d %H:%M:%S") if job.created_at else ""
                }
                job_list.append(job_dict)
            
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=job_list[0].keys())
            writer.writeheader()
            writer.writerows(job_list)
            
            csv_content = output.getvalue()
            output.close()
            
            return {
                "message": f"Successfully exported {len(jobs)} applied jobs",
                "csv_data": csv_content,
                "job_count": len(jobs),
                "filename": f"applied_jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            }
            
    except Exception as e:
        raise Exception(f"Export failed: {str(e)}")