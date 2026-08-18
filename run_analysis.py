"""
Orchestrator for the Behavioral Analysis and Classification Phase.
"""

import sys
import os
import csv
import logging
from typing import List, Dict, Any

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analysis.behavioral_classifier import BehavioralClassifier
from analysis.theme_discovery import ThemeDiscoverer
from analysis.aggregate_analyzer import AggregateAnalyzer
from analysis.validation import Validator
from analysis.report_generator import ReportGenerator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-7s | %(name)-20s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("analysis_pipeline")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
INPUT_FILE = os.path.join(DATA_DIR, "clean_fashion_feedback.csv")
OUTPUT_CSV = os.path.join(DATA_DIR, "classified_fashion_feedback.csv")
SUMMARY_JSON = os.path.join(DATA_DIR, "behavioral_analysis_summary.json")
REPORT_MD = os.path.join(DATA_DIR, "behavioral_analysis_report.md")
THEMES_JSON = os.path.join(DATA_DIR, "emerging_themes.json")
VALIDATION_MD = os.path.join(DATA_DIR, "classification_validation_report.md")

def load_data() -> List[Dict[str, Any]]:
    """Load clean dataset."""
    logger.info(f"Loading data from {INPUT_FILE}")
    if not os.path.exists(INPUT_FILE):
        logger.error(f"Input file not found: {INPUT_FILE}")
        sys.exit(1)
        
    records = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    
    logger.info(f"Loaded {len(records)} records")
    return records

def save_csv(records: List[Dict[str, Any]], filepath: str):
    """Save classified records to CSV."""
    if not records:
        return
        
    fieldnames = [
        "record_id", "source", "source_url", "original_text", "translated_text",
        "wishlist_relevance", "explicit_signal", "ai_inferred_signal",
        "wishlist_intent", "purchase_intent_strength", "wishlist_mode",
        "primary_purchase_barrier", "secondary_purchase_barriers",
        "remaining_uncertainty", "uncertainty_summary",
        "external_research_behavior", "external_information_need",
        "comparison_behavior", "comparison_context",
        "purchase_delay_reason", "delay_strength",
        "underlying_user_need", "user_need_summary",
        "purchase_impact", "shopper_segment",
        "evidence_snippet", "classification_confidence"
    ]
    
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(records)
        
    logger.info(f"Exported {len(records)} classified records to {filepath}")

def main():
    logger.info("="*60)
    logger.info("STARTING BEHAVIORAL ANALYSIS PIPELINE")
    logger.info("="*60)

    # 1. Load data
    records = load_data()
    
    # 2. Classify
    logger.info("\n--- Phase 1: Classification ---")
    classifier = BehavioralClassifier()
    classified_records = classifier.classify_all(records)
    
    # Save raw classifications
    save_csv(classified_records, OUTPUT_CSV)
    
    # 3. Theme Discovery
    logger.info("\n--- Phase 2: Theme Discovery ---")
    try:
        discoverer = ThemeDiscoverer(num_clusters=12)
        themes = discoverer.discover_themes(classified_records)
        discoverer.save_themes(themes, THEMES_JSON)
    except Exception as e:
        logger.error(f"Theme discovery failed: {e}")
        
    # 4. Aggregate Analysis
    logger.info("\n--- Phase 3: Aggregate Analysis ---")
    analyzer = AggregateAnalyzer(classified_records)
    summary = analyzer.analyze()
    analyzer.save_summary(summary, SUMMARY_JSON)
    
    # 5. Report Generation
    logger.info("\n--- Phase 4: Report Generation ---")
    reporter = ReportGenerator(summary)
    reporter.generate(REPORT_MD)
    
    # 6. Validation
    logger.info("\n--- Phase 5: Validation ---")
    validator = Validator(classified_records)
    metrics = validator.validate()
    validator.save_report(metrics, VALIDATION_MD)
    
    logger.info("\n" + "="*60)
    logger.info("PIPELINE COMPLETE")
    logger.info("="*60)
    logger.info(f"Outputs:")
    logger.info(f"  Classified CSV: {OUTPUT_CSV}")
    logger.info(f"  JSON Summary:   {SUMMARY_JSON}")
    logger.info(f"  Analysis MD:    {REPORT_MD}")
    logger.info(f"  Themes JSON:    {THEMES_JSON}")
    logger.info(f"  Validation MD:  {VALIDATION_MD}")

if __name__ == "__main__":
    main()
