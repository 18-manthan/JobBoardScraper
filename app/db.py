from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres@localhost/jobdb")
ECHO_SQL = os.getenv("SQL_ECHO", "false").lower() in {"1", "true", "yes"}

engine = create_async_engine(DATABASE_URL, echo=ECHO_SQL)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


