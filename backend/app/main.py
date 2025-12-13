from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from app.core.config import settings
from app.websockets import router as ws_router
from app.schemas import TranscriptCreate
from app.models.transcript import Transcript
from app.models.session import AsyncSessionLocal
import uvicorn


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

from app.models.session import init_db

@app.on_event("startup")
async def on_startup():
    await init_db()

# Include routers
app.include_router(ws_router.router, tags=["websockets"])

@app.get("/")
async def root():
    return {"message": "Hello World"}




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
