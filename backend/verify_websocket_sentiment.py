
import asyncio
import json

import websockets
from datetime import datetime
from app.models.session import AsyncSessionLocal
from app.models.transcript import Transcript
from sqlalchemy import select, desc

async def verify_sentiment_storage():
    uri = "ws://localhost:8000/ws"
    
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected!")
            
            # Send test data
            test_text = "この機能が実装されて本当に嬉しいです！素晴らしい進捗だと思います。"
            data = {
                "speaker": "VerificationBot",
                "text": test_text,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            print(f"Sending data: {json.dumps(data, ensure_ascii=False)}")
            await websocket.send(json.dumps(data))
            
            # Receive response
            response = await websocket.recv()
            print(f"Received response: {response}")
            
            response_data = json.loads(response)
            if response_data.get("type") == "analysis_result":
                print("✓ Received analysis result")
                print(f"  Sentiment: {response_data.get('sentiment')}")
            
            # Check Database
            print("\nChecking Database...")
            async with AsyncSessionLocal() as session:
                # Get the latest transcript
                result = await session.execute(
                    select(Transcript).order_by(desc(Transcript.id)).limit(1)
                )
                transcript = result.scalar_one_or_none()
                
                if transcript and transcript.text == test_text:
                    print(f"✓ Found transcript in DB: ID={transcript.id}")
                    if transcript.sentiment_analysis:
                        print("✓ Sentiment analysis data is saved!")
                        print(f"  Saved Data: {transcript.sentiment_analysis}")
                    else:
                        print("✗ Sentiment analysis data is MISSING in DB.")
                else:
                    print("✗ Could not find the transcript in DB.")

    except Exception as e:
        print(f"Error during verification: {e}")

if __name__ == "__main__":
    asyncio.run(verify_sentiment_storage())
