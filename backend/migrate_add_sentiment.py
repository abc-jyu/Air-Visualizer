
import asyncio
from sqlalchemy import text
from app.models.session import engine

async def migrate():
    print("Starting migration: Add sentiment_analysis column to transcripts table...")
    async with engine.begin() as conn:
        try:
            # Check if column exists (simple way: select it, if fails, add it)
            # Or just try to add it and catch error if it exists (SQLite doesn't support IF NOT EXISTS for columns in all versions easily, 
            # but we can just run the ALTER TABLE command)
            
            # Using raw SQL for SQLite migration
            await conn.execute(text("ALTER TABLE transcripts ADD COLUMN sentiment_analysis JSON"))
            print("✓ Successfully added 'sentiment_analysis' column.")
        except Exception as e:
            if "duplicate column" in str(e) or "no such table" in str(e): # Adjust error check as needed for SQLite
                 print(f"? Migration might have already run or failed: {e}")
            else:
                 print(f"✗ Migration failed: {e}")

if __name__ == "__main__":
    asyncio.run(migrate())
