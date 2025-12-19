# WebSocketのルーティングとメッセージ処理ロジック
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websockets.manager import manager
from app.models.session import AsyncSessionLocal
from app.models.transcript import Transcript
from app.services.analysis.sentiment import analyze_sentiment
from app.services.analysis.audio import analyze_audio
import json
from datetime import datetime
import base64

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()

            try:
                data_json = json.loads(data)

                # Extract data
                speaker = data_json.get("speaker", "Unknown")
                text = data_json.get("text", "")
                timestamp_str = data_json.get("timestamp")
                audio_base64 = data_json.get("audio")  # Optional audio data
                audio_format = data_json.get("audio_format", "webm")

                # Parse timestamp
                if timestamp_str:
                    timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                else:
                    timestamp = datetime.utcnow()

                # 1. Save transcript to database
                async with AsyncSessionLocal() as session:
                    transcript = Transcript(
                        speaker=speaker,
                        text=text,
                        timestamp=timestamp
                    )
                    session.add(transcript)
                    await session.commit()
                    await session.refresh(transcript)
                    transcript_id = transcript.id

                # 2. Run sentiment analysis
                sentiment_result = await analyze_sentiment(text)

                # 3. Run audio analysis if audio data provided
                audio_result = None
                if audio_base64:
                    try:
                        audio_bytes = base64.b64decode(audio_base64)
                        audio_result = await analyze_audio(audio_bytes, audio_format)
                    except Exception as e:
                        print(f"Audio analysis failed: {e}")
                        import traceback
                        traceback.print_exc()
                        audio_result = {"volume": 0.0, "pitch": 0.0}

                # 4. Prepare response
                response = {
                    "type": "analysis_result",
                    "transcript_id": transcript_id,
                    "speaker": speaker,
                    "text": text,
                    "timestamp": timestamp.isoformat(),
                    "sentiment": sentiment_result,
                    "audio": audio_result
                }

                # 5. Send results back to frontend
                await manager.broadcast(json.dumps(response))

                # 6. Optional: Check if coaching is needed
                # dominant_emotion = max(sentiment_result, key=sentiment_result.get)
                # if dominant_emotion in ["怒り", "恐れ", "嫌悪"] and sentiment_result[dominant_emotion] > 0.5:
                #     # Trigger coaching service
                #     pass

            except json.JSONDecodeError:
                print(f"Failed to decode JSON: {data}")
                await manager.broadcast(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))

            except Exception as e:
                print(f"Error processing data: {e}")
                import traceback
                traceback.print_exc()
                await manager.broadcast(json.dumps({
                    "type": "error",
                    "message": str(e)
                }))

    except WebSocketDisconnect:
        manager.disconnect(websocket)
