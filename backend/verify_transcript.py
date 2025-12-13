# /transcripts エンドポイントに対してPOSTリクエストを送信し、APIの動作確認を行うためのスクリプト
import requests
import datetime

url = "http://localhost:8000/transcripts"
data = {
    "speaker": "Test Speaker",
    "text": "This is a test transcript.",
    "timestamp": datetime.datetime.utcnow().isoformat()
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
