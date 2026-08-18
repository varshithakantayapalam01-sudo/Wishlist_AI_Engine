"""
Web discussion collector (fallback).
Fetches publicly accessible fashion discussion pages, Q&A threads,
and forum posts. Respects robots.txt.
"""

import re
import logging
import time
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, urljoin
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from collectors.base_collector import BaseCollector

logger = logging.getLogger(__name__)

# Common headers to appear as a normal browser
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


class WebCollector(BaseCollector):
    """Collect public fashion discussions from accessible web pages."""

    SOURCE_NAME = "Web"

    def __init__(self, rate_limit: float = 3.0, timeout: int = 15):
        super().__init__(rate_limit_seconds=rate_limit)
        self.timeout = timeout
        self._robots_cache = {}

    def is_available(self) -> bool:
        """Web collector is always available as a fallback."""
        return True

    def _check_robots(self, url: str) -> bool:
        """Check if we're allowed to access this URL per robots.txt."""
        try:
            from urllib.robotparser import RobotFileParser
            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

            if robots_url not in self._robots_cache:
                rp = RobotFileParser()
                rp.set_url(robots_url)
                try:
                    rp.read()
                except Exception:
                    # If we can't read robots.txt, allow access
                    self._robots_cache[robots_url] = None
                    return True
                self._robots_cache[robots_url] = rp

            rp = self._robots_cache[robots_url]
            if rp is None:
                return True
            return rp.can_fetch("*", url)
        except Exception:
            return True

    def _fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a web page."""
        if not self._check_robots(url):
            logger.info(f"Web: Blocked by robots.txt: {url}")
            return None

        try:
            self._rate_limit()
            response = requests.get(url, headers=HEADERS, timeout=self.timeout)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Web: Failed to fetch {url}: {e}")
            self.errors.append(f"Fetch {url}: {e}")
            return None

    def _extract_discussions_from_search(self, query: str) -> List[Dict[str, Any]]:
        """
        Use a search-result approach to find public discussions.
        We search for discussions on fashion forums and Q&A sites.
        """
        records = []

        # Build search URLs for publicly accessible discussion aggregators
        search_targets = [
            {
                "url": f"https://www.google.com/search?q={requests.utils.quote(query + ' site:quora.com')}&num=10",
                "name": "Quora",
            },
            {
                "url": f"https://www.google.com/search?q={requests.utils.quote(query + ' fashion forum India')}&num=10",
                "name": "Fashion Forum",
            },
        ]

        for target in search_targets:
            soup = self._fetch_page(target["url"])
            if not soup:
                continue

            # Extract search result snippets — these contain useful text
            # from public discussions even if we can't access the pages directly
            for result in soup.select("div.g, div[data-sokoban-container]"):
                # Extract the snippet text
                snippet_el = result.select_one(
                    "div.VwiC3b, span.aCOpRe, div[data-sncf], div.IsZvec"
                )
                link_el = result.select_one("a[href]")
                title_el = result.select_one("h3")

                if not snippet_el:
                    continue

                snippet_text = snippet_el.get_text(strip=True)
                if len(snippet_text) < 30:
                    continue

                source_url = ""
                if link_el:
                    href = link_el.get("href", "")
                    if href.startswith("/url?q="):
                        source_url = href.split("/url?q=")[1].split("&")[0]
                    elif href.startswith("http"):
                        source_url = href

                title_text = title_el.get_text(strip=True) if title_el else query

                record = self.create_record(
                    source_type="discussion",
                    search_query=query,
                    brand_or_platform=self._infer_brand(snippet_text),
                    title_or_context=title_text,
                    comment_text=snippet_text,
                    published_date=None,
                    source_url=source_url,
                    likes_or_upvotes=None,
                )
                records.append(record)
                self.records_collected += 1

        return records

    def _collect_from_public_forums(self, query: str) -> List[Dict[str, Any]]:
        """
        Attempt to collect from known public fashion discussion pages.
        These are openly accessible pages without login requirements.
        """
        records = []
        forum_search_urls = [
            # IndiaFashionForum and similar publicly indexed pages
            f"https://www.google.com/search?q={requests.utils.quote(query + ' review discussion India')}&num=5",
        ]

        for search_url in forum_search_urls:
            soup = self._fetch_page(search_url)
            if not soup:
                continue

            for result in soup.select("div.g"):
                snippet_el = result.select_one("div.VwiC3b, span.aCOpRe")
                link_el = result.select_one("a[href]")
                title_el = result.select_one("h3")

                if not snippet_el:
                    continue

                snippet_text = snippet_el.get_text(strip=True)
                if len(snippet_text) < 25:
                    continue

                source_url = ""
                if link_el:
                    href = link_el.get("href", "")
                    if href.startswith("/url?q="):
                        source_url = href.split("/url?q=")[1].split("&")[0]
                    elif href.startswith("http"):
                        source_url = href

                title_text = title_el.get_text(strip=True) if title_el else query

                record = self.create_record(
                    source_type="discussion",
                    search_query=query,
                    brand_or_platform=self._infer_brand(snippet_text),
                    title_or_context=title_text,
                    comment_text=snippet_text,
                    published_date=None,
                    source_url=source_url,
                    likes_or_upvotes=None,
                )
                records.append(record)
                self.records_collected += 1

        return records

    def _infer_brand(self, text: str) -> str:
        """Infer brand/platform from text."""
        text_lower = text.lower()
        if "myntra" in text_lower:
            return "Myntra"
        if "ajio" in text_lower:
            return "AJIO"
        if "flipkart" in text_lower:
            return "Flipkart"
        if "meesho" in text_lower:
            return "Meesho"
        return "General"

    def collect(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Collect from web sources for given queries."""
        all_records = []

        logger.info(f"Web: Starting collection for {len(queries)} queries")

        # Use a subset of queries to avoid excessive Google requests
        priority_queries = queries[:30]

        for i, query in enumerate(priority_queries):
            logger.info(f"Web: [{i+1}/{len(priority_queries)}] Searching: {query}")
            try:
                records = self._extract_discussions_from_search(query)
                all_records.extend(records)

                records = self._collect_from_public_forums(query)
                all_records.extend(records)

            except Exception as e:
                logger.warning(f"Web: Error for query '{query}': {e}")
                self.errors.append(f"'{query}': {e}")

        logger.info(f"Web: Collected {self.records_collected} records total")
        return all_records
