"""
Google Play Store review collector.
Uses the google-play-scraper package (no API key required).
Fetches reviews for Myntra, AJIO, and other fashion apps.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime, timezone

from collectors.base_collector import BaseCollector

logger = logging.getLogger(__name__)


class PlayStoreCollector(BaseCollector):
    """Collect app reviews from Google Play Store."""

    SOURCE_NAME = "Google Play Store"

    def __init__(self, app_ids: Dict[str, str], rate_limit: float = 2.0,
                 reviews_per_app: int = 500):
        """
        Args:
            app_ids: dict mapping app name -> Play Store package ID
            rate_limit: seconds between requests
            reviews_per_app: max reviews to fetch per app
        """
        super().__init__(rate_limit_seconds=rate_limit)
        self.app_ids = app_ids
        self.reviews_per_app = reviews_per_app
        self._scraper_available = False

    def is_available(self) -> bool:
        try:
            import google_play_scraper
            self._scraper_available = True
            return True
        except ImportError:
            logger.warning(
                "google-play-scraper not installed. "
                "Run: pip install google-play-scraper"
            )
            return False

    def _filter_fashion_review(self, text: str) -> bool:
        """Check if review is fashion/clothing related (for general apps like Flipkart)."""
        fashion_keywords = [
            "clothes", "clothing", "fashion", "dress", "shirt", "jeans",
            "kurta", "kurti", "saree", "lehenga", "top", "tshirt", "t-shirt",
            "shoes", "sneakers", "size", "sizing", "fit", "fitting",
            "outfit", "wear", "fabric", "material", "style", "styled",
            "ethnic", "western", "formal", "casual", "color", "colour",
            "design", "quality", "return", "exchange", "wishlist",
        ]
        text_lower = text.lower()
        return any(kw in text_lower for kw in fashion_keywords)

    def collect(self, queries: List[str] = None) -> List[Dict[str, Any]]:
        """
        Collect Play Store reviews. The `queries` parameter is not used
        directly here; instead we fetch reviews for configured apps and
        filter for fashion relevance.
        """
        if not self.is_available():
            return []

        from google_play_scraper import reviews, Sort

        all_records = []
        fashion_only_apps = {
            "Myntra", "AJIO", "Nykaa Fashion", "Bewakoof",
            "Limeroad", "H&M", "Max Fashion",
        }

        logger.info(f"PlayStore: Starting collection for {len(self.app_ids)} apps")

        for app_name, app_id in self.app_ids.items():
            logger.info(f"PlayStore: Fetching reviews for {app_name} ({app_id})")
            try:
                self._rate_limit()

                # Fetch reviews in both sort orders to get different sets
                result = []
                seen_review_ids = set()

                for sort_order in [Sort.MOST_RELEVANT, Sort.NEWEST]:
                    continuation_token = None
                    fetched = 0
                    per_sort_limit = self.reviews_per_app // 2

                    while fetched < per_sort_limit:
                        batch_size = min(200, per_sort_limit - fetched)
                        try:
                            batch, continuation_token = reviews(
                                app_id,
                                lang="en",
                                country="in",
                                sort=sort_order,
                                count=batch_size,
                                continuation_token=continuation_token,
                            )
                            if not batch:
                                break

                            for rev in batch:
                                rev_id = rev.get("reviewId", "")
                                if rev_id and rev_id not in seen_review_ids:
                                    seen_review_ids.add(rev_id)
                                    result.append(rev)

                            fetched += len(batch)
                            self._rate_limit()

                            if not continuation_token:
                                break
                        except Exception as e:
                            logger.warning(
                                f"PlayStore: Batch fetch error for {app_name} "
                                f"({sort_order}): {e}"
                            )
                            break

                logger.info(f"PlayStore: Got {len(result)} unique reviews for {app_name}")

                for rev in result:
                    text = rev.get("content", "")
                    if not text or len(text.strip()) < 15:
                        continue

                    # For non-fashion-specific apps, filter reviews
                    if app_name not in fashion_only_apps:
                        if not self._filter_fashion_review(text):
                            continue

                    # Format the published date
                    pub_date = rev.get("at")
                    if pub_date:
                        if isinstance(pub_date, datetime):
                            pub_date = pub_date.replace(tzinfo=timezone.utc).isoformat()
                        else:
                            pub_date = str(pub_date)

                    record = self.create_record(
                        source_type="review",
                        search_query=f"{app_name} app review",
                        brand_or_platform=app_name,
                        title_or_context=f"{app_name} - Google Play Store Review",
                        comment_text=text,
                        published_date=pub_date,
                        source_url=f"https://play.google.com/store/apps/details?id={app_id}",
                        likes_or_upvotes=rev.get("thumbsUpCount", 0),
                    )
                    all_records.append(record)
                    self.records_collected += 1

            except Exception as e:
                logger.error(f"PlayStore: Error collecting reviews for {app_name}: {e}")
                self.errors.append(f"{app_name}: {e}")

        logger.info(f"PlayStore: Collected {self.records_collected} reviews total")
        return all_records
