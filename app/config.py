from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    # Mongo
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB: str = "zoveera_audio"
    MONGO_COLLECTION: str = "transcriptions"

    # Whisper
    WHISPER_MODEL: str = "small"
    WHISPER_DEVICE: str = "cpu"  # or "cuda"

    # API & app settings
    API_TITLE: str = "Zoveera Audio Transcription API"
    API_VERSION: str = "1.0"
    AUDIO_DIR: str = "uploaded_audio"
    MAX_AUDIO_MB: int = 25
    ALLOWED_EXTENSIONS: List[str] = ["mp3", "wav"]

    # Pydantic v2 settings
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # ignore unknown env vars
    )

settings = Settings()
