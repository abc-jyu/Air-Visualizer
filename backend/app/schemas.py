# Pydanticを使用したデータバリデーションスキーマ
from pydantic import BaseModel
from datetime import datetime

class TranscriptCreate(BaseModel):
    speaker: str
    text: str
    timestamp: datetime
