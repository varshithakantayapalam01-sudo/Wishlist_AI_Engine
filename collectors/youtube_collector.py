"""
YouTube Data API v3 collector.
Searches for videos matching fashion shopping queries and collects comments.
"""

import logging
from typing import List, Dict, Any, Optional

from collectors.base_collector import BaseCollector

logger = logging.getLogger(__name__)


class YouTubeCollector(BaseCollector):
    """Collect comments from YouTube videos via Data API v3."""

    SOURCE_NAME = "YouTube"

    def __init__(self, api_key: str, rate_limit: float = 0.5,
                 max_videos_per_query: int = 5,
                 max_comments_per_video: int = 100,
                 region_code: str = "IN"):
        super().__init__(rate_limit_seconds=rate_limit)
        self.api_key = api_key
        self.max_videos = max_videos_per_query
        self.max_comments = max_comments_per_video
        self.region_code = region_code
        self._youtube = None
        self._quota_used = 0

    def is_available(self) -> bool:
        if not self.api_key:
            logger.warning("YouTube API key not configured. Skipping YouTube collection.")
            return False
        try:
            from googleapiclient.discovery import build
            self._youtube = build("youtube", "v3", developerKey=self.api_key)
            return True
        except Exception as e:
            logger.error(f"Failed to initialize YouTube API client: {e}")
            self.errors.append(str(e))
            return False

    def _search_videos(self, query: str) -> List[Dict[str, str]]:
        """Search for videos matching the query. Returns list of {video_id, title}."""
        try:
            self._rate_limit()
            request = self._youtube.search().list(
                q=query,
                part="snippet",
                type="video",
                maxResults=self.max_videos,
                regionCode=self.region_code,
                relevanceLanguage="en",
                order="relevance",
            )
            response = request.execute()
            self._quota_used += 100  # search.list costs 100 units

            videos = []
            for item in response.get("items", []):
                videos.append({
                    "video_id": item["id"]["videoId"],
                    "title": item["snippet"]["title"],
                    "published_at": item["snippet"].get("publishedAt", ""),
                    "channel_title": item["snippet"].get("channelTitle", ""),
                })
            return videos
        except Exception as e:
            logger.error(f"YouTube search error for '{query}': {e}")
            self.errors.append(f"Search '{query}': {e}")
            return []

    def _get_comments(self, video_id: str) -> List[Dict[str, Any]]:
        """Fetch top-level comments for a video."""
        comments = []
        try:
            self._rate_limit()
            next_page_token = None
            fetched = 0

            while fetched < self.max_comments:
                request = self._youtube.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    maxResults=min(100, self.max_comments - fetched),
                    order="relevance",
                    textFormat="plainText",
                    pageToken=next_page_token,
                )
                response = request.execute()
                self._quota_used += 1  # commentThreads.list costs 1 unit

                for item in response.get("items", []):
                    snippet = item["snippet"]["topLevelComment"]["snippet"]
                    comments.append({
                        "text": snippet.get("textDisplay", ""),
                        "likes": snippet.get("likeCount", 0),
                        "published_at": snippet.get("publishedAt", ""),
                    })
                    fetched += 1

                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break
                self._rate_limit()

        except Exception as e:
            # Comments disabled or other error — skip silently
            if "commentsDisabled" not in str(e):
                logger.warning(f"Error fetching comments for video {video_id}: {e}")
        return comments

    def _infer_brand(self, query: str, title: str) -> str:
        """Infer brand/platform from query and video title."""
        combined = (query + " " + title).lower()
        if "myntra" in combined:
            return "Myntra"
        if "ajio" in combined:
            return "AJIO"
        if "flipkart" in combined:
            return "Flipkart"
        if "meesho" in combined:
            return "Meesho"
        if "tata cliq" in combined:
            return "Tata CLiQ"
        if "nykaa" in combined:
            return "Nykaa Fashion"
        return "General"

    def collect(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Collect YouTube comments for all queries."""
        if not self.is_available():
            return []

        all_records = []
        seen_video_ids = set()

        logger.info(f"YouTube: Starting collection for {len(queries)} queries")

        for i, query in enumerate(queries):
            logger.info(f"YouTube: [{i+1}/{len(queries)}] Searching: {query}")

            # Check quota budget (be conservative)
            if self._quota_used > 9000:
                logger.warning("YouTube: Approaching daily quota limit. Stopping.")
                self.skipped_queries.extend(queries[i:])
                break

            videos = self._search_videos(query)

            for video in videos:
                vid = video["video_id"]
                if vid in seen_video_ids:
                    continue
                seen_video_ids.add(vid)

                comments = self._get_comments(vid)
                brand = self._infer_brand(query, video["title"])
                video_url = f"https://www.youtube.com/watch?v={vid}"

                for comment in comments:
                    if not comment["text"].strip():
                        continue
                    record = self.create_record(
                        source_type="comment",
                        search_query=query,
                        brand_or_platform=brand,
                        title_or_context=video["title"],
                        comment_text=comment["text"],
                        published_date=comment.get("published_at"),
                        source_url=video_url,
                        likes_or_upvotes=comment.get("likes", 0),
                    )
                    all_records.append(record)
                    self.records_collected += 1

        logger.info(
            f"YouTube: Collected {self.records_collected} comments from "
            f"{len(seen_video_ids)} videos. Quota used: ~{self._quota_used} units."
        )
        return all_records
