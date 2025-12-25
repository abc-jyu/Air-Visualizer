# WebSocketのルーティングとメッセージ処理ロジック
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websockets.manager import manager
from app.models.session import AsyncSessionLocal
from app.models.transcript import Transcript
from app.services.analysis.sentiment import analyze_sentiment
import json
from datetime import datetime

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

                # Parse timestamp
                if timestamp_str:
                    timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                else:
                    timestamp = datetime.utcnow()

                # 1. Run sentiment analysis first
                sentiment_result = await analyze_sentiment(text)
                
                # Print dominant emotion in red
                if sentiment_result:
                    dominant_emotion = max(sentiment_result, key=sentiment_result.get)
                    dominant_score = sentiment_result[dominant_emotion]
                    # \033[31m is RED, \033[0m is RESET
                    print(f"\033[31m[Input] {text}\033[0m")
                    print(f"\033[31m[Emotion] {dominant_emotion} ({dominant_score:.1%})\033[0m")

                # 2. Save transcript AND sentiment to database
                async with AsyncSessionLocal() as session:
                    transcript = Transcript(
                        speaker=speaker,
                        text=text,
                        timestamp=timestamp,
                        sentiment_analysis=sentiment_result
                    )
                    session.add(transcript)
                    await session.commit()
                    await session.refresh(transcript)
                    transcript_id = transcript.id

                # 3. Prepare response
                response = {
                    "type": "analysis_result",
                    "transcript_id": transcript_id,
                    "speaker": speaker,
                    "text": text,
                    "timestamp": timestamp.isoformat(),
                    "sentiment": sentiment_result
                }

                # 4. Send results back to frontend
                await manager.broadcast(json.dumps(response))

                # 5. Optional: Check if coaching is needed
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
