"""
Data cleaner module.
Handles deduplication, spam removal, PII stripping, whitespace normalization,
and generic comment filtering.
"""

import re
import logging
from typing import List, Dict, Any, Set

from rapidfuzz import fuzz

logger = logging.getLogger(__name__)


class DataCleaner:
    """Clean raw collected data by removing duplicates, spam, PII, and junk."""

    def __init__(self, spam_patterns: List[str], min_length: int = 20,
                 near_dupe_threshold: float = 85.0):
        """
        Args:
            spam_patterns: list of regex patterns to identify spam
            min_length: minimum character length to keep a comment
            near_dupe_threshold: fuzzy match ratio threshold for near-duplicates
        """
        self.spam_patterns = [re.compile(p, re.IGNORECASE) for p in spam_patterns]
        self.min_length = min_length
        self.near_dupe_threshold = near_dupe_threshold

        # Counters for reporting
        self.total_input = 0
        self.removed_exact_dupes = 0
        self.removed_near_dupes = 0
        self.removed_spam = 0
        self.removed_too_short = 0
        self.removed_generic = 0
        self.removed_pii = 0

        # PII patterns
        self._email_re = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        self._phone_re = re.compile(
            r'(?:\+91[\-\s]?)?(?:\d[\-\s]?){10,13}'
        )
        # Generic / low-value comment patterns
        self._generic_patterns = [
            re.compile(r'^(nice|good|great|awesome|amazing|love it|loved it|love this|wow|cool|best|superb|fantastic|excellent|beautiful|lovely)[\s.!]*$', re.IGNORECASE),
            re.compile(r'^(thanks|thank you|thankyou|thnx|thnks|ty)[\s.!]*$', re.IGNORECASE),
            re.compile(r'^(first|first comment|first!|hi|hello|hey|hii|hiii)[\s.!]*$', re.IGNORECASE),
            re.compile(r'^(please|pls|plz)\s+(subscribe|like|share).*$', re.IGNORECASE),
            re.compile(r'^(subscribed|liked|shared)[\s.!]*$', re.IGNORECASE),
            re.compile(r'^\W+$'),  # Only special characters
        ]

    def _normalize_text(self, text: str) -> str:
        """Normalize whitespace and clean text for comparison."""
        if not text:
            return ""
        # Collapse multiple spaces/newlines
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _is_spam(self, text: str) -> bool:
        """Check if text matches any spam pattern."""
        for pattern in self.spam_patterns:
            if pattern.search(text):
                return True
        return False

    def _is_generic(self, text: str) -> bool:
        """Check if comment is a generic low-value response."""
        stripped = text.strip()
        for pattern in self._generic_patterns:
            if pattern.match(stripped):
                return True

        # Check if it's mostly emojis
        # Remove all emoji characters and see what's left
        non_emoji = re.sub(
            r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF'
            r'\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251'
            r'\U0000200D\U0000FE0F\U00002640\U00002642\U00002764]+',
            '', stripped
        )
        if len(non_emoji.strip()) < 5 and len(stripped) > 0:
            return True

        return False

    def _strip_pii(self, text: str) -> str:
        """Remove personally identifying information."""
        original = text
        text = self._email_re.sub('[EMAIL]', text)
        text = self._phone_re.sub('[PHONE]', text)
        if text != original:
            self.removed_pii += 1
        return text

    def _remove_exact_duplicates(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove records with identical comment text."""
        seen_texts: Set[str] = set()
        unique = []
        for record in records:
            normalized = self._normalize_text(record.get("comment_text", "")).lower()
            if normalized in seen_texts:
                self.removed_exact_dupes += 1
                continue
            seen_texts.add(normalized)
            unique.append(record)
        return unique

    def _remove_near_duplicates(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove near-duplicate records using fuzzy matching."""
        if len(records) < 2:
            return records

        unique = []
        kept_texts = []

        for record in records:
            text = self._normalize_text(record.get("comment_text", "")).lower()
            is_near_dupe = False

            # Only compare against recent records for performance (sliding window)
            compare_window = kept_texts[-200:] if len(kept_texts) > 200 else kept_texts

            for existing_text in compare_window:
                ratio = fuzz.ratio(text, existing_text)
                if ratio >= self.near_dupe_threshold:
                    is_near_dupe = True
                    break

            if is_near_dupe:
                self.removed_near_dupes += 1
            else:
                unique.append(record)
                kept_texts.append(text)

        return unique

    def clean(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Run the full cleaning pipeline on records.
        Returns cleaned records list.
        """
        self.total_input = len(records)
        logger.info(f"Cleaner: Starting with {self.total_input} raw records")

        # Step 1: Normalize whitespace in all texts
        for record in records:
            record["comment_text"] = self._normalize_text(record.get("comment_text", ""))

        # Step 2: Remove too-short comments
        before = len(records)
        records = [r for r in records if len(r.get("comment_text", "")) >= self.min_length]
        self.removed_too_short = before - len(records)
        logger.info(f"Cleaner: Removed {self.removed_too_short} too-short comments")

        # Step 3: Remove spam
        before = len(records)
        records = [r for r in records if not self._is_spam(r.get("comment_text", ""))]
        self.removed_spam = before - len(records)
        logger.info(f"Cleaner: Removed {self.removed_spam} spam comments")

        # Step 4: Remove generic/low-value comments
        before = len(records)
        records = [r for r in records if not self._is_generic(r.get("comment_text", ""))]
        self.removed_generic = before - len(records)
        logger.info(f"Cleaner: Removed {self.removed_generic} generic comments")

        # Step 5: Strip PII
        for record in records:
            record["comment_text"] = self._strip_pii(record["comment_text"])
        logger.info(f"Cleaner: Stripped PII from {self.removed_pii} records")

        # Step 6: Remove exact duplicates
        records = self._remove_exact_duplicates(records)
        logger.info(f"Cleaner: Removed {self.removed_exact_dupes} exact duplicates")

        # Step 7: Remove near-duplicates
        records = self._remove_near_duplicates(records)
        logger.info(f"Cleaner: Removed {self.removed_near_dupes} near-duplicates")

        total_removed = (
            self.removed_too_short + self.removed_spam + self.removed_generic +
            self.removed_exact_dupes + self.removed_near_dupes
        )
        logger.info(
            f"Cleaner: {len(records)} records remaining "
            f"(removed {total_removed} total)"
        )

        return records

    def get_stats(self) -> Dict[str, int]:
        """Return cleaning statistics."""
        return {
            "total_input": self.total_input,
            "removed_too_short": self.removed_too_short,
            "removed_spam": self.removed_spam,
            "removed_generic": self.removed_generic,
            "removed_exact_duplicates": self.removed_exact_dupes,
            "removed_near_duplicates": self.removed_near_dupes,
            "removed_pii_stripped": self.removed_pii,
            "total_removed": (
                self.removed_too_short + self.removed_spam + self.removed_generic +
                self.removed_exact_dupes + self.removed_near_dupes
            ),
        }
