"""
Validation Module.
Validates the classification results against expected logical constraints.
"""

import random
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class Validator:
    """Validates classification results and generates validation metrics."""

    def __init__(self, records: List[Dict[str, Any]]):
        self.records = records
        self.total = len(records)

    def validate(self) -> Dict[str, Any]:
        """Run validation checks on the classified records."""
        logger.info(f"Validator: Validating {self.total} records...")
        
        if self.total == 0:
            return {}

        metrics = {
            "total_classified": self.total,
            "high_confidence_records": 0,
            "low_confidence_records": 0,
            "with_clear_barrier": 0,
            "with_clear_intent": 0,
            "with_clear_need": 0,
            "logical_contradictions_found": 0,
            "flagged_records": []
        }

        # Select a random sample for potential manual review
        sample_indices = random.sample(range(self.total), min(50, self.total))
        metrics["validation_sample"] = [self.records[i]["record_id"] for i in sample_indices]

        for record in self.records:
            # Confidence checks
            conf = record.get("classification_confidence", 0)
            if conf >= 0.75:
                metrics["high_confidence_records"] += 1
            elif conf < 0.60:
                metrics["low_confidence_records"] += 1

            # Clarity checks
            if record.get("primary_purchase_barrier") not in ("no_clear_barrier", "unknown"):
                metrics["with_clear_barrier"] += 1
            if record.get("wishlist_intent") not in ("unclear", "unknown"):
                metrics["with_clear_intent"] += 1
            if record.get("underlying_user_need") not in ("no_clear_need", "unknown"):
                metrics["with_clear_need"] += 1

            # Logical contradiction checks
            contradictions = self._check_contradictions(record)
            if contradictions:
                metrics["logical_contradictions_found"] += 1
                # Only keep a sample of flagged records to avoid huge reports
                if len(metrics["flagged_records"]) < 100:
                    metrics["flagged_records"].append({
                        "record_id": record.get("record_id"),
                        "text": str(record.get("original_text", ""))[:100] + "...",
                        "contradictions": contradictions
                    })

        # Calculate percentages
        for key in ["high_confidence_records", "low_confidence_records", 
                    "with_clear_barrier", "with_clear_intent", "with_clear_need"]:
            metrics[f"{key}_pct"] = round((metrics[key] / self.total) * 100, 2)

        return metrics

    def _check_contradictions(self, record: Dict[str, Any]) -> List[str]:
        """Check for logical contradictions in a single record."""
        contradictions = []
        
        intent_strength = record.get("purchase_intent_strength")
        mode = record.get("wishlist_mode")
        impact = record.get("purchase_impact")
        barrier = record.get("primary_purchase_barrier")
        
        # High intent but simple bookmark mode
        if intent_strength == "high" and mode == "simple_bookmark":
            contradictions.append(f"High intent strength but mode is '{mode}'")
            
        # Blocking impact but no clear barrier
        if impact == "blocks_purchase" and barrier == "no_clear_barrier":
            contradictions.append("Purchase impact is 'blocks_purchase' but no barrier identified")
            
        # Bookmark mode but blocks purchase
        if mode == "simple_bookmark" and impact in ("blocks_purchase", "significantly_delays_purchase"):
            contradictions.append(f"Mode is '{mode}' but impact is '{impact}'")
            
        return contradictions

    def save_report(self, metrics: Dict[str, Any], filepath: str):
        """Save validation report as Markdown."""
        report = [
            "# Classification Validation Report\n",
            "## Summary Metrics\n",
            f"- **Total records classified**: {metrics.get('total_classified', 0)}",
            f"- **High confidence (>= 0.75)**: {metrics.get('high_confidence_records_pct', 0)}%",
            f"- **Low confidence (< 0.60)**: {metrics.get('low_confidence_records_pct', 0)}%",
            f"- **With clear purchase barrier**: {metrics.get('with_clear_barrier_pct', 0)}%",
            f"- **With clear wishlist intent**: {metrics.get('with_clear_intent_pct', 0)}%",
            f"- **With clear user need**: {metrics.get('with_clear_need_pct', 0)}%",
            f"- **Logical contradictions found**: {metrics.get('logical_contradictions_found', 0)}\n",
            "## Known Limitations\n",
            "- Validation is rule-based and may not catch all nuances.",
            "- Sentiment analysis is rudimentary.",
            "- Relies heavily on keyword matching, which can sometimes miss context (e.g. sarcasm).\n",
        ]
        
        if metrics.get("flagged_records"):
            report.append("## Flagged Records (Sample)\n")
            for f in metrics["flagged_records"][:10]:
                report.append(f"- **ID**: `{f['record_id']}`")
                report.append(f"  - **Text**: *{f['text']}*")
                report.append(f"  - **Issues**: {', '.join(f['contradictions'])}")
                
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("\n".join(report))
        logger.info(f"Saved validation report to {filepath}")
