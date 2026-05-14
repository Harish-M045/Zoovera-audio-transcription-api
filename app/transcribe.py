import asyncio
from typing import Tuple
from app.config import settings

_model = None

def _load_model():
    global _model
    if _model is not None:
        return _model
    try:
        import whisper
    except Exception as e:
        raise RuntimeError("Install 'whisper' first: " + str(e))
    _model = whisper.load_model(settings.WHISPER_MODEL, device=settings.WHISPER_DEVICE)
    return _model

def _transcribe_blocking(path: str) -> Tuple[str, str, str]:
    model = _load_model()
    detect = model.transcribe(path, task="transcribe")
    original_text = detect.get("text", "").strip()
    language = detect.get("language", "unknown")
    translated = model.transcribe(path, task="translate")
    translated_text = translated.get("text", "").strip()
    return original_text, translated_text, language

async def transcribe_local(path: str) -> Tuple[str, str, str]:
    return await asyncio.to_thread(_transcribe_blocking, path)
