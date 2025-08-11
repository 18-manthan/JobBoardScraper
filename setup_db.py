#!/usr/bin/env python3
import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.db import engine
from app.models import Base

async def setup_database():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database tables created successfully")
    except Exception as e:
        print(f"Database setup failed: {e}")
        return False
    return True

async def test_database_connection():
    try:
        async with engine.begin() as conn:
            from sqlalchemy import text
            await conn.execute(text("SELECT 1"))
        print("Database connection successful")
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

async def main():
    if not await test_database_connection():
        return
    if await setup_database():
        print("Setup completed")
    else:
        print("Setup failed")

if __name__ == "__main__":
    asyncio.run(main())
