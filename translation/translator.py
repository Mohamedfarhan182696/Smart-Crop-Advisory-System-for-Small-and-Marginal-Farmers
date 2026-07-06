"""
Translation Service
====================
Deep Translator wrapper for multilingual support.
"""

from typing import Optional
from cachetools import TTLCache
from utils.logger import get_logger

logger = get_logger("translation")

# Cache translations (24h TTL, max 1000 entries)
_translation_cache = TTLCache(maxsize=1000, ttl=86400)

SUPPORTED_LANGS = {"en": "english", "ta": "tamil", "hi": "hindi", "te": "telugu", "ml": "malayalam"}


def translate_text(text: str, target_lang: str, source_lang: str = "en") -> str:
    """
    Translate text to the target language.

    Args:
        text: Text to translate
        target_lang: Target language code (en, ta, hi, te, ml)
        source_lang: Source language code

    Returns:
        Translated text, or original if translation fails
    """
    if not text or target_lang == source_lang:
        return text

    if target_lang not in SUPPORTED_LANGS:
        return text

    cache_key = f"{source_lang}:{target_lang}:{text[:100]}"
    if cache_key in _translation_cache:
        return _translation_cache[cache_key]

    try:
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        result = translator.translate(text)

        if result:
            _translation_cache[cache_key] = result
            return result
        return text

    except Exception as e:
        logger.error(f"Translation error ({source_lang}→{target_lang}): {e}")
        return text


def translate_batch(texts: list[str], target_lang: str, source_lang: str = "en") -> list[str]:
    """Translate a batch of texts."""
    return [translate_text(t, target_lang, source_lang) for t in texts]
