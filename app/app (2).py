import os
import uuid
import aiofiles
import tempfile
import urllib.request
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import TranscriptionDocument, Sentiment
from app.sentiment import sentiment_from_text
from app.mongo import get_mongo_collection, check_mongo_connection
from app.transcribe import transcribe_local  # async function

# ==========================================================
#                  ALLOWED FORMATS
# ==========================================================

ALLOWED_EXTENSIONS = {"mp3", "wav"}

def _validate_filename(filename: str) -> bool:
    if not filename:
        return False
    ext = filename.lower().rsplit(".", 1)[-1]
    return ext in ALLOWED_EXTENSIONS

# ==========================================================
#                       WER CALCULATION
# ==========================================================
def calculate_wer(reference: str, hypothesis: str) -> float:
    """Compute Word Error Rate (WER) in percent."""
    ref_words = reference.strip().split()
    hyp_words = hypothesis.strip().split()
    N = len(ref_words)
    if N == 0:
        return 0.0

    dp = [[0] * (len(hyp_words)+1) for _ in range(len(ref_words)+1)]
    for i in range(len(ref_words)+1):
        dp[i][0] = i
    for j in range(len(hyp_words)+1):
        dp[0][j] = j

    for i in range(1, len(ref_words)+1):
        for j in range(1, len(hyp_words)+1):
            if ref_words[i-1] == hyp_words[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
    wer = dp[len(ref_words)][len(hyp_words)] / N
    return round(wer * 100, 2)

# ==========================================================
#                   FASTAPI APP SETUP
# ==========================================================

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="Transcription → Translation → Sentiment → WER → Store → JSON Output"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AUDIO_DIR = settings.AUDIO_DIR
os.makedirs(AUDIO_DIR, exist_ok=True)

@app.on_event("startup")
async def startup_event():
    ok = await check_mongo_connection()
    print("✅ MongoDB connected" if ok else "❌ MongoDB not connected!")

@app.get("/health")
async def health():
    mongo_ok = await check_mongo_connection()
    return {
        "service": settings.API_TITLE,
        "mongodb_status": "connected" if mongo_ok else "disconnected",
    }

# ==========================================================
#                    FILE HANDLING HELPERS
# ==========================================================

async def _save_uploaded_file(file: UploadFile) -> str:
    audio_id = uuid.uuid4().hex
    saved_path = os.path.join(AUDIO_DIR, f"{audio_id}_{file.filename}")
    size = 0
    async with aiofiles.open(saved_path, "wb") as out_file:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > settings.MAX_AUDIO_MB * 1024 * 1024:
                raise HTTPException(status_code=400, detail="File too large")
            await out_file.write(chunk)
    return saved_path

async def _fetch_file_from_url(url: str) -> str:
    ext = url.lower().rsplit(".", 1)[-1]
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="URL must end with .mp3 or .wav")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}")
    try:
        urllib.request.urlretrieve(url, tmp.name)
        return tmp.name
    except Exception:
        raise HTTPException(status_code=400, detail="Unable to download file")

# ==========================================================
#                        MAIN ROUTE
# ==========================================================

@app.post("/process")
async def process_audio(
    file: UploadFile = File(None),
    url: str = Form(None)
):
    if file is None and not url:
        raise HTTPException(status_code=400, detail="Provide either a file or a URL")

    if file:
        if not _validate_filename(file.filename):
            raise HTTPException(400, "Only .mp3 and .wav are allowed")
        filepath = await _save_uploaded_file(file)
        file_source = "upload"
        file_name = file.filename
    else:
        filepath = await _fetch_file_from_url(url)
        file_source = "url"
        file_name = url

    # ==========================================================
    #                TRANSCRIPTION (WHISPER)
    # ==========================================================
    try:
        result = await transcribe_local(filepath)
    except Exception as e:
        raise HTTPException(500, f"Transcription failed: {e}")

    # Handle tuple or dict return
    if isinstance(result, tuple):
        original_text = result[0].strip()
    else:
        original_text = result.get("text", "").strip()

    # Mock translation (replace with actual model if needed)
    translated_text = original_text

    # ==========================================================
    #                SENTIMENT ANALYSIS
    # ==========================================================
    sentiment_result = sentiment_from_text(original_text)
    if isinstance(sentiment_result, tuple):
        sentiment = Sentiment(score=sentiment_result[0], label=sentiment_result[1])
    else:
        sentiment = sentiment_result

    # ==========================================================
    #               WER CALCULATION
    # ==========================================================
    wer = calculate_wer(original_text, translated_text)

    # ==========================================================
    #               STORE IN MONGODB
    # ==========================================================
    col = get_mongo_collection()  # <-- no await here
    await col.insert_one(doc := TranscriptionDocument(
        transcription_id=str(uuid.uuid4()),
        file_source=file_source,
        file_name=file_name,
        created_at=datetime.utcnow(),
        original_text=original_text,
        translated_text=translated_text,
        sentiment=sentiment,
        wer=wer
    ).dict())

    # ==========================================================
    #                     RETURN JSON
    # ==========================================================
    return JSONResponse({
        "status": "success",
        "source": file_source,
        "file_or_url": file_name,
        "transcription_id": doc['transcription_id'],
        "original_text": original_text,
        "translated_text": translated_text,
        "sentiment": sentiment.dict(),
        "wer": wer
    })
