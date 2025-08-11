import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.db import engine
from sqlalchemy import text

async def migrate_database():
    """Add missing columns to database"""
    try:
        async with engine.begin() as conn:
            # Check if source column exists
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'jobs' AND column_name = 'source'
            """))
            
            if not result.fetchone():
                # Add the missing source column
                await conn.execute(text("""
                    ALTER TABLE jobs 
                    ADD COLUMN source VARCHAR DEFAULT 'Unknown'
                """))
            
            # Check if all required columns exist
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'jobs'
            """))
            
        print("Migration completed")
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return False

async def reset_database():
    """Drop and recreate the jobs table (WARNING: This will delete all data)"""
    try:
        async with engine.begin() as conn:
            # Drop the table
            await conn.execute(text("DROP TABLE IF EXISTS jobs CASCADE"))
            
            # Recreate the table with all columns
            await conn.execute(text("""
                CREATE TABLE jobs (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR NOT NULL,
                    company VARCHAR NOT NULL,
                    location VARCHAR NOT NULL,
                    description VARCHAR,
                    url VARCHAR NOT NULL,
                    source VARCHAR DEFAULT 'Unknown',
                    liked BOOLEAN DEFAULT FALSE,
                    applied BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
        print("Database reset completed")
        return True
        
    except Exception as e:
        print(f"Reset failed: {e}")
        return False

async def main():
    """Main migration function"""
    choice = input("1) Migrate  2) Reset  > ")
    
    if choice == "1":
        await migrate_database()
    elif choice == "2":
        await reset_database()
    else:
        print("Invalid choice")

if __name__ == "__main__":
    asyncio.run(main())
