# WebSocketのルーティングとメッセージ処理ロジック
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websockets.manager import manager
from app.models.session import AsyncSessionLocal
from app.models.transcript import Transcript
import json
from datetime import datetime

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Process data
            try:
                # Assume data is JSON string for now, or just text
                # In a real scenario, we'd parse JSON: data_json = json.loads(data)
                
                # 1. Save raw log to SQLite (async)
                try:
                    data_json = json.loads(data)
                    async with AsyncSessionLocal() as session:
                        # Handle both cases: if timestamp is present or not
                        # The extension sends: speaker, text, timestamp
                        transcript = Transcript(
                            speaker=data_json.get("speaker", "Unknown"),
                            text=data_json.get("text", ""),
                            timestamp=datetime.fromisoformat(data_json.get("timestamp").replace("Z", "+00:00")) if data_json.get("timestamp") else datetime.utcnow()
                        )
                        session.add(transcript)
                        await session.commit()
                except json.JSONDecodeError:
                    print(f"Failed to decode JSON: {data}")
                    # Fallback for non-JSON data (if any)
                    async with AsyncSessionLocal() as session:
                        transcript = Transcript(speaker="Unknown", text=data)
                        session.add(transcript)
                        await session.commit()
                
                # 2. Send to Analysis Service (Placeholder)
                # analysis_result = analyze_sentiment(data)
                
                # 3. If condition met, send to Coaching Service (Placeholder)
                # if analysis_result["score"] < -0.5:
                #     advice = generate_coaching([], analysis_result)
                
                # 4. Send result back to frontend
                await manager.broadcast(f"Saved: {data}")
            except Exception as e:
                print(f"Error processing data: {e}")
                await manager.broadcast(f"Error: {str(e)}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
