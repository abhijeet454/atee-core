"""
Speech-to-Text Module — local transcription using faster-whisper.
"""
import asyncio
from loguru import logger
from faster_whisper import WhisperModel

class STTEngine:
    def __init__(self, model_size="base", device="cpu"):
        # CPU is used by default for better compatibility unless specified
        # "cuda" with "float16" for GPU
        compute_type = "int8" if device == "cpu" else "float16"
        logger.info(f"Loading faster-whisper {model_size} on {device}")
        
        # We might want to defer loading until first use in a real app to save memory,
        # but for Jarvis we load it upfront for lower latency.
        try:
            self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        except Exception as e:
            logger.warning(f"Whisper initialization failed: {e}. STT may not be available.")
            self.model = None

    def transcribe_sync(self, audio_data) -> str:
        """Transcribe audio synchronously."""
        if not self.model:
            return ""
            
        # audio_data can be a numpy array, byte stream, or file path
        # Defaulting to Hindi for faster and more accurate recognition
        segments, info = self.model.transcribe(audio_data, language="hi", beam_size=5, vad_filter=True)
        
        text = "".join(segment.text for segment in segments)
        return text.strip()

    async def transcribe(self, audio_data) -> str:
        """Transcribe audio asynchronously."""
        return await asyncio.to_thread(self.transcribe_sync, audio_data)
