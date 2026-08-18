"""
Fashion Shopping Data Collection Pipeline — Main Orchestrator
=============================================================
Runs all collectors, processes data through the cleaning pipeline,
applies relevance scoring, handles language detection/translation,
enforces source diversity, and exports all output files.
"""

import os
import sys
import json
import csv
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any

import pandas as pd
from tqdm import tqdm

# ── Setup logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(name)-20s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("pipeline")

# ── Ensure project root is on path ─────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# ── Imports ────────────────────────────────────────────────────────────────
from config.config import (
    YOUTUBE_API_KEY, REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT,
    DATA_DIR, RAW_CSV_PATH, CLEAN_CSV_PATH, SUMMARY_JSON_PATH, SOURCES_REPORT_PATH,
    RELEVANCE_THRESHOLD, SOURCE_DIVERSITY_CAP,
    ALL_QUERIES, MYNTRA_QUERIES, AJIO_QUERIES, GENERAL_FASHION_QUERIES,
    RELEVANCE_KEYWORDS, SPAM_PATTERNS, MIN_COMMENT_LENGTH,
    PLAYSTORE_APPS, REDDIT_SUBREDDITS,
    YOUTUBE_MAX_RESULTS_PER_QUERY, YOUTUBE_MAX_COMMENTS_PER_VIDEO,
    YOUTUBE_REGION_CODE, RATE_LIMITS, PRODUCT_CATEGORIES,
)
from collectors.youtube_collector import YouTubeCollector
from collectors.reddit_collector import RedditCollector
from collectors.playstore_collector import PlayStoreCollector
from collectors.web_collector import WebCollector
from processing.cleaner import DataCleaner
from processing.relevance_scorer import RelevanceScorer
from processing.language_handler import LanguageHandler


def infer_product_category(text: str) -> str:
    """Infer product category from text content."""
    text_lower = text.lower()
    for category, keywords in PRODUCT_CATEGORIES.items():
        for kw in keywords:
            if kw in text_lower:
                return category
    return "general"


def enforce_source_diversity(records: List[Dict[str, Any]],
                              cap: float = 0.60) -> List[Dict[str, Any]]:
    """
    Ensure no single source exceeds the cap percentage of total records.
    If a source is over-represented, randomly sample down to the cap.
    Preserves higher-relevance records when trimming.
    """
    import random
    random.seed(42)

    total = len(records)
    if total == 0:
        return records

    # Count by source
    source_counts = {}
    for r in records:
        src = r["source"]
        source_counts[src] = source_counts.get(src, 0) + 1

    # If only one source, diversity enforcement is not applicable
    if len(source_counts) <= 1:
        logger.info(
            f"Diversity: Only {len(source_counts)} source(s) available — "
            f"skipping diversity enforcement"
        )
        return records

    max_per_source = int(total * cap)
    over_represented = {
        src: count for src, count in source_counts.items()
        if count > max_per_source
    }

    if not over_represented:
        return records

    logger.info(f"Diversity: Over-represented sources: {over_represented}")

    # Group records by source
    by_source = {}
    for r in records:
        by_source.setdefault(r["source"], []).append(r)

    result = []
    for src, src_records in by_source.items():
        if src in over_represented:
            # Sort by relevance score (descending) and keep top N
            src_records.sort(key=lambda r: r["relevance_score"], reverse=True)
            trimmed = src_records[:max_per_source]
            removed = len(src_records) - len(trimmed)
            logger.info(
                f"Diversity: Trimmed {src} from {len(src_records)} to "
                f"{len(trimmed)} records (removed {removed})"
            )
            result.extend(trimmed)
        else:
            result.extend(src_records)

    return result


def export_csv(records: List[Dict[str, Any]], filepath: str):
    """Export records to CSV using pandas."""
    if not records:
        logger.warning(f"No records to export to {filepath}")
        return

    df = pd.DataFrame(records)

    # Ensure column order matches schema
    columns = [
        "record_id", "source", "source_type", "search_query",
        "brand_or_platform", "title_or_context", "comment_text",
        "original_text", "translated_text", "published_date",
        "source_url", "likes_or_upvotes", "product_category",
        "language", "relevance_score", "collection_timestamp",
    ]
    # Only include columns that exist
    columns = [c for c in columns if c in df.columns]
    df = df[columns]

    df.to_csv(filepath, index=False, encoding="utf-8-sig", quoting=csv.QUOTE_ALL)
    logger.info(f"Exported {len(df)} records to {filepath}")


def generate_summary_json(
    raw_records: List[Dict[str, Any]],
    clean_records: List[Dict[str, Any]],
    cleaner_stats: Dict,
    language_stats: Dict,
    collector_statuses: List[Dict],
    pipeline_start: datetime,
    pipeline_end: datetime,
) -> Dict[str, Any]:
    """Generate the data_collection_summary.json content."""

    # Source distribution
    raw_source_dist = {}
    for r in raw_records:
        raw_source_dist[r["source"]] = raw_source_dist.get(r["source"], 0) + 1

    clean_source_dist = {}
    for r in clean_records:
        clean_source_dist[r["source"]] = clean_source_dist.get(r["source"], 0) + 1

    # Date range
    dates = [r.get("published_date") for r in clean_records if r.get("published_date")]
    dates = [d for d in dates if d and isinstance(d, str) and len(d) >= 10]
    earliest = min(dates) if dates else None
    latest = max(dates) if dates else None

    # Valid source URLs
    total_urls = len(clean_records)
    valid_urls = sum(1 for r in clean_records
                     if r.get("source_url") and r["source_url"].startswith("http"))

    # Relevance scores
    scores = [r["relevance_score"] for r in clean_records]
    avg_score = sum(scores) / len(scores) if scores else 0

    summary = {
        "pipeline_metadata": {
            "pipeline_version": "1.0.0",
            "start_time": pipeline_start.isoformat(),
            "end_time": pipeline_end.isoformat(),
            "duration_seconds": (pipeline_end - pipeline_start).total_seconds(),
        },
        "record_counts": {
            "total_raw_records": len(raw_records),
            "total_clean_records": len(clean_records),
            "duplicate_removal_rate": round(
                cleaner_stats.get("removed_exact_duplicates", 0) +
                cleaner_stats.get("removed_near_duplicates", 0), 0
            ),
            "percentage_relevant": round(
                len(clean_records) / max(len(raw_records), 1) * 100, 2
            ),
        },
        "source_distribution": {
            "raw": raw_source_dist,
            "clean": clean_source_dist,
        },
        "quality_metrics": {
            "average_relevance_score": round(avg_score, 4),
            "min_relevance_score": round(min(scores), 4) if scores else 0,
            "max_relevance_score": round(max(scores), 4) if scores else 0,
            "relevance_threshold": RELEVANCE_THRESHOLD,
            "percentage_with_valid_urls": round(valid_urls / max(total_urls, 1) * 100, 2),
        },
        "date_range": {
            "earliest": earliest,
            "latest": latest,
        },
        "language_stats": language_stats,
        "cleaning_stats": cleaner_stats,
        "collector_statuses": collector_statuses,
    }

    return summary


def generate_sources_report(
    summary: Dict[str, Any],
    collector_statuses: List[Dict],
    top_queries: List[str],
) -> str:
    """Generate the data_sources_report.md content."""

    lines = [
        "# Data Sources Report",
        "",
        f"**Generated**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "",
        "---",
        "",
        "## Pipeline Overview",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total raw records | {summary['record_counts']['total_raw_records']} |",
        f"| Total clean records | {summary['record_counts']['total_clean_records']} |",
        f"| Percentage relevant | {summary['record_counts']['percentage_relevant']}% |",
        f"| Duplicate removal count | {summary['record_counts']['duplicate_removal_rate']} |",
        f"| Average relevance score | {summary['quality_metrics']['average_relevance_score']} |",
        f"| Records with valid URLs | {summary['quality_metrics']['percentage_with_valid_urls']}% |",
        f"| Pipeline duration | {summary['pipeline_metadata']['duration_seconds']:.1f}s |",
        "",
        "---",
        "",
        "## Sources Attempted",
        "",
        "| Source | Available | Records Collected | Errors |",
        "|--------|-----------|-------------------|--------|",
    ]

    for status in collector_statuses:
        avail = "✅" if status["available"] else "❌"
        lines.append(
            f"| {status['source']} | {avail} | "
            f"{status['records_collected']} | {status['errors']} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## Source Distribution (Clean Dataset)",
        "",
        "| Source | Records | Percentage |",
        "|--------|---------|------------|",
    ])

    clean_dist = summary["source_distribution"]["clean"]
    total_clean = summary["record_counts"]["total_clean_records"]
    for src, count in sorted(clean_dist.items(), key=lambda x: x[1], reverse=True):
        pct = round(count / max(total_clean, 1) * 100, 1)
        lines.append(f"| {src} | {count} | {pct}% |")

    lines.extend([
        "",
        "---",
        "",
        "## Date Range",
        "",
        f"- **Earliest record**: {summary['date_range']['earliest'] or 'N/A'}",
        f"- **Latest record**: {summary['date_range']['latest'] or 'N/A'}",
        "",
        "---",
        "",
        "## Language Distribution",
        "",
        "| Language | Count |",
        "|----------|-------|",
    ])

    lang_dist = summary.get("language_stats", {}).get("language_distribution", {})
    for lang, count in sorted(lang_dist.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"| {lang} | {count} |")

    lines.extend([
        "",
        f"- **Translated records**: {summary['language_stats'].get('total_translated', 0)}",
        f"- **Percentage translated**: {summary['language_stats'].get('percentage_translated', 0)}%",
        "",
        "---",
        "",
        "## Cleaning Statistics",
        "",
        "| Step | Records Removed |",
        "|------|----------------|",
    ])

    cs = summary.get("cleaning_stats", {})
    lines.append(f"| Too short (< {MIN_COMMENT_LENGTH} chars) | {cs.get('removed_too_short', 0)} |")
    lines.append(f"| Spam | {cs.get('removed_spam', 0)} |")
    lines.append(f"| Generic / low-value | {cs.get('removed_generic', 0)} |")
    lines.append(f"| Exact duplicates | {cs.get('removed_exact_duplicates', 0)} |")
    lines.append(f"| Near-duplicates | {cs.get('removed_near_duplicates', 0)} |")
    lines.append(f"| **Total removed** | **{cs.get('total_removed', 0)}** |")

    lines.extend([
        "",
        "---",
        "",
        "## Top Search Queries (by yield)",
        "",
    ])

    for i, q in enumerate(top_queries[:20], 1):
        lines.append(f"{i}. {q}")

    lines.extend([
        "",
        "---",
        "",
        "## API & Access Limitations",
        "",
    ])

    for status in collector_statuses:
        if not status["available"]:
            lines.append(f"- **{status['source']}**: Not available (API credentials not configured)")
        elif status["errors"] > 0:
            lines.append(f"- **{status['source']}**: {status['errors']} errors during collection")

    if all(s["available"] for s in collector_statuses):
        lines.append("- No significant limitations encountered.")

    lines.extend(["", "---", ""])

    return "\n".join(lines)


def validate_dataset(records: List[Dict[str, Any]], dataset_name: str):
    """Run validation checks on a dataset and log results."""
    logger.info(f"")
    logger.info(f"{'=' * 60}")
    logger.info(f"VALIDATION: {dataset_name}")
    logger.info(f"{'=' * 60}")
    logger.info(f"  Total records: {len(records)}")

    if not records:
        logger.warning(f"  ⚠ Dataset is empty!")
        return

    # Check required fields
    required = ["record_id", "source", "comment_text", "relevance_score"]
    for field in required:
        missing = sum(1 for r in records if not r.get(field) and r.get(field) != 0)
        if missing:
            logger.warning(f"  ⚠ {missing} records missing '{field}'")
        else:
            logger.info(f"  ✓ All records have '{field}'")

    # Source distribution
    sources = {}
    for r in records:
        sources[r["source"]] = sources.get(r["source"], 0) + 1
    logger.info(f"  Source distribution: {sources}")

    # Relevance scores
    scores = [r["relevance_score"] for r in records]
    below_threshold = sum(1 for s in scores if s < RELEVANCE_THRESHOLD)
    if below_threshold:
        logger.warning(f"  ⚠ {below_threshold} records below relevance threshold")
    else:
        logger.info(f"  ✓ All records meet relevance threshold ({RELEVANCE_THRESHOLD})")

    # Source diversity
    for src, count in sources.items():
        pct = count / len(records)
        if pct > SOURCE_DIVERSITY_CAP:
            logger.warning(f"  ⚠ {src} represents {pct*100:.1f}% (cap: {SOURCE_DIVERSITY_CAP*100}%)")
        else:
            logger.info(f"  ✓ {src}: {pct*100:.1f}% (within diversity cap)")

    # Valid URLs
    valid_urls = sum(1 for r in records
                     if r.get("source_url") and str(r["source_url"]).startswith("http"))
    logger.info(f"  Valid source URLs: {valid_urls}/{len(records)} ({valid_urls/len(records)*100:.1f}%)")

    logger.info(f"{'=' * 60}")


def run_pipeline():
    """Execute the full data collection and processing pipeline."""

    pipeline_start = datetime.now(timezone.utc)
    logger.info("=" * 70)
    logger.info("  FASHION SHOPPING DATA COLLECTION PIPELINE")
    logger.info("=" * 70)
    logger.info(f"  Start time: {pipeline_start.isoformat()}")
    logger.info(f"  Total search queries: {len(ALL_QUERIES)}")
    logger.info(f"  Relevance threshold: {RELEVANCE_THRESHOLD}")
    logger.info(f"  Source diversity cap: {SOURCE_DIVERSITY_CAP * 100}%")
    logger.info("")

    # ── Phase 1: Initialize Collectors ─────────────────────────────────────
    logger.info("─── Phase 1: Initializing Collectors ───")

    collectors = [
        PlayStoreCollector(
            app_ids=PLAYSTORE_APPS,
            rate_limit=RATE_LIMITS["playstore"],
            reviews_per_app=1500,
        ),
        YouTubeCollector(
            api_key=YOUTUBE_API_KEY,
            rate_limit=RATE_LIMITS["youtube"],
            max_videos_per_query=YOUTUBE_MAX_RESULTS_PER_QUERY,
            max_comments_per_video=YOUTUBE_MAX_COMMENTS_PER_VIDEO,
            region_code=YOUTUBE_REGION_CODE,
        ),
        RedditCollector(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT,
            subreddits=REDDIT_SUBREDDITS,
            rate_limit=RATE_LIMITS["reddit"],
        ),
        WebCollector(
            rate_limit=RATE_LIMITS["web"],
        ),
    ]

    for c in collectors:
        avail = c.is_available()
        status = "✅ Available" if avail else "❌ Not available"
        logger.info(f"  {c.SOURCE_NAME}: {status}")

    # ── Phase 2: Collect Data ──────────────────────────────────────────────
    logger.info("")
    logger.info("─── Phase 2: Collecting Data ───")

    all_raw_records = []
    query_yield = {}  # Track which queries produce results

    for collector in collectors:
        if not collector.is_available():
            logger.info(f"  Skipping {collector.SOURCE_NAME} (not available)")
            continue

        logger.info(f"")
        logger.info(f"  ▸ Running {collector.SOURCE_NAME} collector...")

        try:
            records = collector.collect(ALL_QUERIES)
            all_raw_records.extend(records)

            # Track query yields
            for r in records:
                q = r.get("search_query", "unknown")
                query_yield[q] = query_yield.get(q, 0) + 1

            logger.info(
                f"  ✓ {collector.SOURCE_NAME}: {len(records)} records collected"
            )
        except Exception as e:
            logger.error(f"  ✗ {collector.SOURCE_NAME} failed: {e}")
            collector.errors.append(str(e))

    logger.info(f"")
    logger.info(f"  Total raw records: {len(all_raw_records)}")

    # ── Phase 3: Infer Product Categories ──────────────────────────────────
    logger.info("")
    logger.info("─── Phase 3: Inferring Product Categories ───")

    for record in all_raw_records:
        text = record.get("comment_text", "") + " " + record.get("title_or_context", "")
        record["product_category"] = infer_product_category(text)

    category_dist = {}
    for r in all_raw_records:
        cat = r["product_category"]
        category_dist[cat] = category_dist.get(cat, 0) + 1
    logger.info(f"  Category distribution: {category_dist}")

    # ── Phase 4: Export Raw CSV ────────────────────────────────────────────
    logger.info("")
    logger.info("─── Phase 4: Exporting Raw Dataset ───")
    export_csv(all_raw_records, RAW_CSV_PATH)

    # ── Phase 5: Clean Data ────────────────────────────────────────────────
    logger.info("")
    logger.info("─── Phase 5: Cleaning Data ───")

    cleaner = DataCleaner(
        spam_patterns=SPAM_PATTERNS,
        min_length=MIN_COMMENT_LENGTH,
        near_dupe_threshold=85.0,
    )
    cleaned_records = cleaner.clean(all_raw_records)
    cleaner_stats = cleaner.get_stats()

    # ── Phase 6: Language Detection & Translation ──────────────────────────
    logger.info("")
    logger.info("─── Phase 6: Language Detection & Translation ───")

    lang_handler = LanguageHandler()
    cleaned_records = lang_handler.process(cleaned_records)
    language_stats = lang_handler.get_stats()

    # ── Phase 7: Relevance Scoring ─────────────────────────────────────────
    logger.info("")
    logger.info("─── Phase 7: Relevance Scoring ───")

    scorer = RelevanceScorer(
        keywords=RELEVANCE_KEYWORDS,
        threshold=RELEVANCE_THRESHOLD,
    )
    cleaned_records = scorer.score_all(cleaned_records)

    # Filter by relevance
    relevant_records = scorer.filter_relevant(cleaned_records)

    # ── Phase 8: Source Diversity ───────────────────────────────────────────
    logger.info("")
    logger.info("─── Phase 8: Enforcing Source Diversity ───")

    final_records = enforce_source_diversity(relevant_records, cap=SOURCE_DIVERSITY_CAP)
    logger.info(f"  Final dataset size: {len(final_records)}")

    # ── Phase 9: Export Clean CSV ──────────────────────────────────────────
    logger.info("")
    logger.info("─── Phase 9: Exporting Clean Dataset ───")
    export_csv(final_records, CLEAN_CSV_PATH)

    # ── Phase 10: Generate Reports ─────────────────────────────────────────
    logger.info("")
    logger.info("─── Phase 10: Generating Reports ───")

    pipeline_end = datetime.now(timezone.utc)

    # Collector statuses
    collector_statuses = [c.get_status() for c in collectors]

    # Top queries by yield
    top_queries = sorted(query_yield.keys(), key=lambda q: query_yield[q], reverse=True)

    # Summary JSON
    summary = generate_summary_json(
        raw_records=all_raw_records,
        clean_records=final_records,
        cleaner_stats=cleaner_stats,
        language_stats=language_stats,
        collector_statuses=collector_statuses,
        pipeline_start=pipeline_start,
        pipeline_end=pipeline_end,
    )

    with open(SUMMARY_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
    logger.info(f"  Summary JSON: {SUMMARY_JSON_PATH}")

    # Sources report
    report_md = generate_sources_report(
        summary=summary,
        collector_statuses=collector_statuses,
        top_queries=top_queries,
    )

    with open(SOURCES_REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_md)
    logger.info(f"  Sources report: {SOURCES_REPORT_PATH}")

    # ── Phase 11: Validate ─────────────────────────────────────────────────
    logger.info("")
    logger.info("─── Phase 11: Validation ───")

    validate_dataset(all_raw_records, "RAW DATASET")
    validate_dataset(final_records, "CLEAN DATASET")

    # ── Final Summary ──────────────────────────────────────────────────────
    logger.info("")
    logger.info("=" * 70)
    logger.info("  PIPELINE COMPLETE")
    logger.info("=" * 70)
    logger.info(f"  Duration: {(pipeline_end - pipeline_start).total_seconds():.1f}s")
    logger.info(f"  Raw records: {len(all_raw_records)}")
    logger.info(f"  Clean records: {len(final_records)}")
    logger.info(f"  Relevance threshold: {RELEVANCE_THRESHOLD}")
    logger.info(f"")
    logger.info(f"  Output files:")
    logger.info(f"    {RAW_CSV_PATH}")
    logger.info(f"    {CLEAN_CSV_PATH}")
    logger.info(f"    {SUMMARY_JSON_PATH}")
    logger.info(f"    {SOURCES_REPORT_PATH}")
    logger.info("=" * 70)

    return summary


if __name__ == "__main__":
    run_pipeline()
