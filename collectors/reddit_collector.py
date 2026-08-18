"""
Reddit API collector using PRAW.
Searches subreddits for fashion shopping discussions and collects posts + comments.
"""

import logging
from typing import List, Dict, Any

from collectors.base_collector import BaseCollector

logger = logging.getLogger(__name__)


class RedditCollector(BaseCollector):
    """Collect posts and comments from Reddit via PRAW."""

    SOURCE_NAME = "Reddit"

    def __init__(self, client_id: str, client_secret: str,
                 user_agent: str, subreddits: List[str],
                 rate_limit: float = 1.0):
        super().__init__(rate_limit_seconds=rate_limit)
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent
        self.subreddits = subreddits
        self._reddit = None

    def is_available(self) -> bool:
        if not self.client_id or not self.client_secret:
            logger.warning(
                "Reddit API credentials not configured. "
                "Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET. Skipping Reddit."
            )
            return False
        try:
            import praw
            self._reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent,
            )
            # Quick auth check
            _ = self._reddit.read_only
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Reddit client: {e}")
            self.errors.append(str(e))
            return False

    def _infer_brand(self, text: str) -> str:
        """Infer brand/platform from text content."""
        text_lower = text.lower()
        if "myntra" in text_lower:
            return "Myntra"
        if "ajio" in text_lower:
            return "AJIO"
        if "flipkart" in text_lower:
            return "Flipkart"
        if "meesho" in text_lower:
            return "Meesho"
        if "tata cliq" in text_lower:
            return "Tata CLiQ"
        if "nykaa" in text_lower:
            return "Nykaa Fashion"
        return "General"

    def _format_date(self, utc_timestamp: float) -> str:
        """Convert Reddit UTC timestamp to ISO format."""
        from datetime import datetime, timezone
        return datetime.fromtimestamp(utc_timestamp, tz=timezone.utc).isoformat()

    def collect(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Collect Reddit posts and comments for all queries."""
        if not self.is_available():
            return []

        all_records = []
        seen_ids = set()

        logger.info(f"Reddit: Starting collection for {len(queries)} queries")

        # Strategy 1: Search specific subreddits
        for sub_name in self.subreddits:
            try:
                subreddit = self._reddit.subreddit(sub_name)
                for query in queries[:20]:  # Limit queries per subreddit
                    self._rate_limit()
                    try:
                        results = subreddit.search(query, limit=10, sort="relevance", time_filter="all")
                        for submission in results:
                            if submission.id in seen_ids:
                                continue
                            seen_ids.add(submission.id)

                            # Collect the submission itself if it has text
                            sub_text = submission.selftext or submission.title
                            if sub_text and len(sub_text.strip()) > 10:
                                brand = self._infer_brand(sub_text)
                                record = self.create_record(
                                    source_type="post",
                                    search_query=query,
                                    brand_or_platform=brand,
                                    title_or_context=submission.title,
                                    comment_text=sub_text,
                                    published_date=self._format_date(submission.created_utc),
                                    source_url=f"https://www.reddit.com{submission.permalink}",
                                    likes_or_upvotes=submission.score,
                                )
                                all_records.append(record)
                                self.records_collected += 1

                            # Collect top-level comments
                            submission.comments.replace_more(limit=0)
                            for comment in submission.comments[:20]:
                                if hasattr(comment, "body") and comment.body:
                                    c_id = comment.id
                                    if c_id in seen_ids:
                                        continue
                                    seen_ids.add(c_id)

                                    brand = self._infer_brand(comment.body)
                                    record = self.create_record(
                                        source_type="comment",
                                        search_query=query,
                                        brand_or_platform=brand,
                                        title_or_context=submission.title,
                                        comment_text=comment.body,
                                        published_date=self._format_date(comment.created_utc),
                                        source_url=f"https://www.reddit.com{comment.permalink}",
                                        likes_or_upvotes=comment.score,
                                    )
                                    all_records.append(record)
                                    self.records_collected += 1

                    except Exception as e:
                        logger.warning(f"Reddit: Error searching r/{sub_name} for '{query}': {e}")
                        self.errors.append(f"r/{sub_name} '{query}': {e}")

            except Exception as e:
                logger.warning(f"Reddit: Error accessing r/{sub_name}: {e}")
                self.errors.append(f"r/{sub_name}: {e}")

        # Strategy 2: Global search for remaining queries
        try:
            for query in queries:
                self._rate_limit()
                try:
                    results = self._reddit.subreddit("all").search(
                        query, limit=10, sort="relevance", time_filter="all"
                    )
                    for submission in results:
                        if submission.id in seen_ids:
                            continue
                        seen_ids.add(submission.id)

                        sub_text = submission.selftext or submission.title
                        if sub_text and len(sub_text.strip()) > 10:
                            brand = self._infer_brand(sub_text)
                            record = self.create_record(
                                source_type="post",
                                search_query=query,
                                brand_or_platform=brand,
                                title_or_context=submission.title,
                                comment_text=sub_text,
                                published_date=self._format_date(submission.created_utc),
                                source_url=f"https://www.reddit.com{submission.permalink}",
                                likes_or_upvotes=submission.score,
                            )
                            all_records.append(record)
                            self.records_collected += 1

                except Exception as e:
                    logger.warning(f"Reddit: Global search error for '{query}': {e}")
                    self.errors.append(f"Global '{query}': {e}")

        except Exception as e:
            logger.error(f"Reddit: Global search failed: {e}")
            self.errors.append(f"Global search: {e}")

        logger.info(f"Reddit: Collected {self.records_collected} records")
        return all_records
