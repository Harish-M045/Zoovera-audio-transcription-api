from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional

class Sentiment(BaseModel):
    score: float = Field(..., description="Sentiment score (0..1)")
    label: str = Field(..., description="Positive / Negative / Neutral")

class TranscriptionDocument(BaseModel):
    transcription_id: str = Field(..., alias="_id")
    file_name: str
    original_text: str
    translated_text: str
    sentiment: Sentiment
    detected_language: Optional[str] = None
    processed_at: datetime = Field(default_factory=datetime.utcnow)

    # Pydantic v2 model config
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )
