"""
Language detection and translation module.
Detects the language of each record, preserves original text,
and translates non-English content to English.
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class LanguageHandler:
    """Detect language and translate non-English content."""

    def __init__(self):
        self._detector_available = False
        self._translator_available = False
        self.total_processed = 0
        self.total_translated = 0
        self.total_english = 0
        self.translation_errors = 0
        self.language_distribution = {}

    def _init_detector(self):
        """Initialize language detector."""
        try:
            import langdetect
            self._detector_available = True
        except ImportError:
            logger.warning("langdetect not installed. Language detection disabled.")
            self._detector_available = False

    def _init_translator(self):
        """Initialize translator."""
        try:
            from deep_translator import GoogleTranslator
            self._translator_available = True
        except ImportError:
            logger.warning("deep-translator not installed. Translation disabled.")
            self._translator_available = False

    def detect_language(self, text: str) -> str:
        """Detect the language of the given text."""
        if not self._detector_available:
            return "en"  # Assume English if detector unavailable

        try:
            from langdetect import detect
            if len(text.strip()) < 10:
                return "en"  # Too short to detect reliably
            lang = detect(text)
            return lang
        except Exception:
            return "en"  # Default to English on error

    def translate_text(self, text: str, source_lang: str) -> str:
        """Translate text from source language to English."""
        if not self._translator_available:
            return text

        try:
            from deep_translator import GoogleTranslator

            # deep-translator has a character limit per request (~5000 chars)
            if len(text) > 4500:
                text = text[:4500]

            translator = GoogleTranslator(source=source_lang, target="en")
            translated = translator.translate(text)
            return translated if translated else text
        except Exception as e:
            logger.debug(f"Translation error for {source_lang}: {e}")
            self.translation_errors += 1
            return text

    def process(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process all records: detect language, translate non-English content.
        Updates records in-place and returns them.
        """
        self._init_detector()
        self._init_translator()

        logger.info(f"Language: Processing {len(records)} records")

        for record in records:
            self.total_processed += 1
            text = record.get("comment_text", "")

            # Detect language
            lang = self.detect_language(text)
            record["language"] = lang

            # Track distribution
            self.language_distribution[lang] = self.language_distribution.get(lang, 0) + 1

            if lang == "en":
                self.total_english += 1
                # No translation needed
                record["original_text"] = None
                record["translated_text"] = None
            else:
                # Store original and translate
                record["original_text"] = text

                # Common Indian languages to translate
                translatable_langs = {
                    "hi", "ta", "te", "bn", "mr", "gu", "kn", "ml",
                    "pa", "ur", "or", "as", "es", "fr", "de", "pt",
                }

                if lang in translatable_langs and self._translator_available:
                    translated = self.translate_text(text, lang)
                    if translated and translated != text:
                        record["translated_text"] = translated
                        record["comment_text"] = translated  # Use translated as primary
                        self.total_translated += 1
                    else:
                        record["translated_text"] = None
                else:
                    record["translated_text"] = None

        # Log summary
        logger.info(
            f"Language: {self.total_english} English, "
            f"{self.total_translated} translated, "
            f"{self.translation_errors} translation errors"
        )
        if self.language_distribution:
            top_langs = sorted(
                self.language_distribution.items(), key=lambda x: x[1], reverse=True
            )[:10]
            logger.info(f"Language: Top languages: {dict(top_langs)}")

        return records

    def get_stats(self) -> Dict[str, Any]:
        """Return language processing statistics."""
        return {
            "total_processed": self.total_processed,
            "total_english": self.total_english,
            "total_translated": self.total_translated,
            "translation_errors": self.translation_errors,
            "language_distribution": self.language_distribution,
            "percentage_translated": (
                round(self.total_translated / max(self.total_processed, 1) * 100, 2)
            ),
        }
