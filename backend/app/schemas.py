# Pydanticを使用したデータバリデーションスキーマ
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TranscriptCreate(BaseModel):
    speaker: str
    text: str
    timestamp: datetime


class SentimentAnalysisResult(BaseModel):
    """Sentiment analysis result with 8 WRIME emotions"""
    喜び: float      # joy
    悲しみ: float    # sadness
    期待: float      # anticipation
    驚き: float      # surprise
    怒り: float      # anger
    恐れ: float      # fear
    嫌悪: float      # disgust
    信頼: float      # trust


class AudioAnalysisResult(BaseModel):
    """Audio features extracted from voice"""
    volume: float  # 0.0 - 1.0
    pitch: float   # Hz (typically 50-500 for human speech)


class CombinedAnalysisResult(BaseModel):
    """Combined analysis result for transcript with audio"""
    transcript_id: int
    speaker: str
    text: str
    timestamp: datetime
    sentiment: SentimentAnalysisResult
    audio: Optional[AudioAnalysisResult] = None
