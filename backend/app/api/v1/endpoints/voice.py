"""
Voice Endpoints — STT, TTS, and WebSocket streaming.
"""
import io
import uuid
from fastapi import APIRouter, UploadFile, File, Response, WebSocket, WebSocketDisconnect
from loguru import logger

from app.voice.stt import STTEngine
from app.voice.tts import TTSEngine

router = APIRouter(prefix="/voice", tags=["voice"])

# Typically we would instantiate these as dependencies or singletons on startup
stt = STTEngine()
# Coqui XTTSv2 (voice cloning). Model downloads automatically on first use.
tts = TTSEngine()

@router.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    """Transcribe uploaded audio file."""
    audio_bytes = await audio.read()
    # Write to a BytesIO object for faster-whisper
    audio_stream = io.BytesIO(audio_bytes)
    
    text = await stt.transcribe(audio_stream)
    return {"text": text}

@router.post("/speak")
async def speak(text: str):
    """Synthesize text to audio WAV."""
    audio_bytes = await tts.synthesize(text)
    return Response(content=audio_bytes, media_type="audio/wav")

@router.websocket("/stream")
async def voice_stream(websocket: WebSocket):
    """
    WebSocket endpoint for full-duplex voice conversation.
    Client sends audio frames, server responds with audio frames.
    """
    await websocket.accept()
    session_id = str(uuid.uuid4())
    logger.info(f"WebSocket voice connection opened: {session_id}")
    
    try:
        while True:
            data = await websocket.receive_bytes()
            # Stub: in a real implementation we accumulate bytes,
            # detect speech end via VAD, transcribe, run agent loop,
            # and stream back TTS bytes.
            pass
    except WebSocketDisconnect:
        logger.info(f"WebSocket voice connection closed: {session_id}")
