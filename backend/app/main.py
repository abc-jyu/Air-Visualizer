# FastAPIアプリケーションのエントリーポイント
from fastapi import FastAPI
from app.core.config import settings
from app.websockets import router as ws_router
from app.schemas import TranscriptCreate
from app.models.transcript import Transcript
from app.models.session import AsyncSessionLocal, init_db
from app.services.analysis.sentiment import initialize_sentiment_model, shutdown_sentiment_model
import uvicorn


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)


@app.on_event("startup")
async def on_startup():
    # Initialize database
    await init_db()

    # Initialize sentiment analysis model
    try:
        await initialize_sentiment_model()
        print("✓ Sentiment analysis model initialized")
    except Exception as e:
        print(f"✗ Failed to initialize sentiment model: {e}")
        # Continue without sentiment analysis if it fails
        import traceback
        traceback.print_exc()


@app.on_event("shutdown")
async def on_shutdown():
    # Clean up sentiment model
    await shutdown_sentiment_model()

# Include routers
app.include_router(ws_router.router, tags=["websockets"])

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health_check():
    """Health check endpoint to verify services are running"""
    return {
        "status": "ok",
        "sentiment": "initialized"
    }




@app.post("/transcripts")
async def create_transcript(transcript: TranscriptCreate):
    async with AsyncSessionLocal() as session:
        db_transcript = Transcript(
            speaker=transcript.speaker,
            text=transcript.text,
            timestamp=transcript.timestamp
        )
        session.add(db_transcript)
        await session.commit()
        return {"status": "ok", "id": db_transcript.id}



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
