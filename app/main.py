from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routes import jobs
from app.db import engine
from app.models import Base
from app.cache import init_redis, close_redis

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await init_redis(app)
    yield
    await close_redis(app)
   

app = FastAPI(
    title="Job Aggregator API",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])