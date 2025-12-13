import asyncio
from sqlalchemy import select
from app.models.session import AsyncSessionLocal
from app.models.transcript import Transcript

async def verify_db():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Transcript))
        transcripts = result.scalars().all()
        print(f"Found {len(transcripts)} transcripts:")
        for t in transcripts:
            print(f"- {t.text} (at {t.timestamp})")

if __name__ == "__main__":
    asyncio.run(verify_db())
