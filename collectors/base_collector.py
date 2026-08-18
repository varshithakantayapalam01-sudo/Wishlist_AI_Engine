"""
Abstract base class for all data collectors.
Provides shared logging, rate limiting, and record schema enforcement.
"""

import abc
import time
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional


logger = logging.getLogger(__name__)


class BaseCollector(abc.ABC):
    """Base class that all collectors inherit from."""

    SOURCE_NAME: str = "unknown"  # Override in subclasses

    def __init__(self, rate_limit_seconds: float = 1.0):
        self.rate_limit_seconds = rate_limit_seconds
        self._last_request_time = 0.0
        self.records_collected = 0
        self.errors = []
        self.skipped_queries = []

    def _rate_limit(self):
        """Enforce rate limiting between API calls."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit_seconds:
            time.sleep(self.rate_limit_seconds - elapsed)
        self._last_request_time = time.time()

    def create_record(
        self,
        source_type: str,
        search_query: str,
        brand_or_platform: str,
        title_or_context: str,
        comment_text: str,
        published_date: Optional[str] = None,
        source_url: Optional[str] = None,
        likes_or_upvotes: Optional[int] = None,
        product_category: Optional[str] = None,
        language: str = "en",
    ) -> Dict[str, Any]:
        """Create a standardized record dictionary."""
        return {
            "record_id": str(uuid.uuid4()),
            "source": self.SOURCE_NAME,
            "source_type": source_type,
            "search_query": search_query,
            "brand_or_platform": brand_or_platform,
            "title_or_context": title_or_context,
            "comment_text": comment_text.strip() if comment_text else "",
            "original_text": None,
            "translated_text": None,
            "published_date": published_date,
            "source_url": source_url,
            "likes_or_upvotes": likes_or_upvotes,
            "product_category": product_category,
            "language": language,
            "relevance_score": 0.0,
            "collection_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @abc.abstractmethod
    def is_available(self) -> bool:
        """Check if this collector can run (API keys present, etc.)."""
        ...

    @abc.abstractmethod
    def collect(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Run collection for given queries. Returns list of record dicts."""
        ...

    def get_status(self) -> Dict[str, Any]:
        """Return collection status summary."""
        return {
            "source": self.SOURCE_NAME,
            "available": self.is_available(),
            "records_collected": self.records_collected,
            "errors": len(self.errors),
            "skipped_queries": len(self.skipped_queries),
        }
