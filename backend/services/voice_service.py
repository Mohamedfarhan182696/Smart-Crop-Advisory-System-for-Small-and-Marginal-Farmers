"""
Voice Service
==============
Speech-to-text (Faster Whisper) and text-to-speech (gTTS) pipeline.
"""

import os
import tempfile
from pathlib import Path
from typing import Optional
from utils.logger import get_logger

logger = get_logger("voice")

_whisper_model = None


def _load_whisper():
    """Load Faster Whisper model."""
    global _whisper_model
    if _whisper_model is not None:
        return True

    try:
        from faster_whisper import WhisperModel
        from config.settings import get_settings
        
        settings = get_settings()
        model_size = settings.WHISPER_MODEL_SIZE or os.environ.get("WHISPER_MODEL_SIZE", "small")
        device = settings.WHISPER_DEVICE or os.environ.get("WHISPER_DEVICE", "cpu")
        compute_type = settings.WHISPER_COMPUTE_TYPE or os.environ.get("WHISPER_COMPUTE_TYPE", "int8")

        _whisper_model = WhisperModel(model_size, device=device, compute_type=compute_type)
        logger.info(f"Whisper model '{model_size}' loaded on {device}")
        return True
    except Exception as e:
        logger.error(f"Whisper load error: {e}")
        return False


def speech_to_text(audio_path: str, language: str = None) -> Optional[dict]:
    """
    Transcribe audio to text.

    Args:
        audio_path: Path to audio file
        language: Optional language code (en, ta, hi, te, ml)

    Returns:
        Dict with text, language, confidence
    """
    if not _load_whisper():
        return {"text": "", "language": "en", "error": "Whisper model not available"}

    try:
        kwargs = {"beam_size": 5}
        if language:
            kwargs["language"] = language

        segments, info = _whisper_model.transcribe(audio_path, **kwargs)
        text = " ".join([seg.text for seg in segments]).strip()

        result = {
            "text": text,
            "language": info.language,
            "language_probability": round(info.language_probability, 2),
        }
        logger.info(f"STT: '{text[:50]}...' (lang: {info.language})")
        return result

    except Exception as e:
        logger.error(f"STT error: {e}")
        return {"text": "", "language": "en", "error": str(e)}


def text_to_speech(text: str, language: str = "en", output_path: str = None) -> Optional[str]:
    """
    Convert text to speech audio file.

    Args:
        text: Text to speak
        language: Language code
        output_path: Optional output file path

    Returns:
        Path to generated audio file
    """
    if not text.strip():
        return None

    try:
        from gtts import gTTS

        lang_map = {"en": "en", "ta": "ta", "hi": "hi", "te": "te", "ml": "ml"}
        tts_lang = lang_map.get(language, "en")

        tts = gTTS(text=text, lang=tts_lang, slow=False)

        if output_path is None:
            fd, output_path = tempfile.mkstemp(suffix=".mp3")
            os.close(fd)

        tts.save(output_path)
        logger.info(f"TTS: Generated audio for '{text[:30]}...' in {tts_lang}")
        return output_path

    except Exception as e:
        logger.error(f"TTS error: {e}")
        return None
