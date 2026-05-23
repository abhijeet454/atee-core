"""
Text-to-Speech Module — local synthesis using Coqui XTTSv2 for voice cloning.

Requires TTS package and a reference wav file.
"""
import asyncio
import io
import os
import wave
from loguru import logger
import numpy as np
import scipy.io.wavfile

try:
    from TTS.api import TTS
    HAS_TTS = True
except ImportError:
    HAS_TTS = False


class TTSEngine:
    def __init__(self, model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2"):
        self.tts = None
        self.reference_wav = "./data/voices/friend_sample.wav"
        
        if not HAS_TTS:
            logger.warning("Coqui TTS not installed. TTS will be unavailable.")
            return
            
        logger.info(f"Loading Coqui TTS model: {model_name}...")
        try:
            # Initialize TTS (will download the model if not present)
            # Use gpu=True if CUDA is available, else False
            import torch
            use_gpu = torch.cuda.is_available()
            self.tts = TTS(model_name=model_name, progress_bar=False).to("cuda" if use_gpu else "cpu")
            logger.info("XTTSv2 model loaded successfully!")
        except Exception as e:
            logger.error(f"TTS initialization failed: {e}")

    def synthesize_sync(self, text: str) -> bytes:
        """Synthesize text to WAV bytes synchronously."""
        if not self.tts:
            logger.error("TTS engine not initialized.")
            return b""
            
        if not os.path.exists(self.reference_wav):
            logger.warning(f"Reference wav not found at {self.reference_wav}. Please add it to clone the voice.")
            return b""

        try:
            # Generate audio
            logger.debug(f"Synthesizing voice clone for text: {text}")
            wav_array = self.tts.tts(
                text=text,
                speaker_wav=self.reference_wav,
                language="hi"  # Hindi
            )
            
            # Convert float list to numpy array (16-bit PCM)
            audio_array = np.array(wav_array)
            audio_array = np.int16(audio_array * 32767)
            
            # Create an in-memory byte buffer
            out_buf = io.BytesIO()
            scipy.io.wavfile.write(out_buf, 24000, audio_array) # XTTSv2 outputs at 24kHz
            
            return out_buf.getvalue()
        except Exception as e:
            logger.error(f"Voice cloning failed: {e}")
            return b""

    async def synthesize(self, text: str) -> bytes:
        """Synthesize text to WAV bytes asynchronously."""
        return await asyncio.to_thread(self.synthesize_sync, text)
