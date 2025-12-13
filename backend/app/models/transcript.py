from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from app.models.session import Base

class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, index=True)
    speaker = Column(String, index=True)
    text = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
