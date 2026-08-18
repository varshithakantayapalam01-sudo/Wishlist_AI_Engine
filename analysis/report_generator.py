"""
Report Generator Module.
Formats the aggregate analysis into a comprehensive Markdown report.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generates the final Markdown behavioral analysis report."""

    def __init__(self, summary: Dict[str, Any]):
        self.summary = summary

    def generate(self, filepath: str):
        """Generate and save the report."""
        report = ["# Behavioral Analysis Report\n"]
        
        # 1. Why users wishlist
        report.append("## 1. Why Users Wishlist (Intent)")
        report.append("| Intent | Count | % | Confidence-Weighted % |")
        report.append("|---|---|---|---|")
        for item in self.summary.get("wishlist_intent", []):
            report.append(f"| {item['category']} | {item['count']} | {item['percentage']}% | {item['confidence_weighted_percentage']}% |")
        report.append("\n")

        # 2. Wishlist mode
        report.append("## 2. Wishlist as Intent vs Bookmarking")
        report.append("| Mode | Count | % |")
        report.append("|---|---|---|")
        for item in self.summary.get("wishlist_mode", []):
            report.append(f"| {item['category']} | {item['count']} | {item['percentage']}% |")
        report.append("\n")

        # 3. Top purchase barriers
        report.append("## 3. Top Purchase Barriers")
        report.append("| Barrier | Count | % | Avg Confidence |")
        report.append("|---|---|---|---|")
        for item in self.summary.get("top_purchase_barriers", []):
            report.append(f"| {item['barrier']} | {item['count']} | {item['percentage']}% | {item['average_confidence']} |")
        report.append("\n")

        # 4. Remaining uncertainties
        report.append("## 4. Most Common Remaining Uncertainties")
        report.append("| Uncertainty | Count | % |")
        report.append("|---|---|---|")
        for item in self.summary.get("remaining_uncertainties", []):
            report.append(f"| {item['uncertainty']} | {item['count']} | {item['percentage']}% |")
        report.append("\n")

        # 5. Purchase delay reasons
        report.append("## 5. Purchase Delay Reasons")
        report.append("| Reason | Count | % |")
        report.append("|---|---|---|")
        for item in self.summary.get("purchase_delay_reasons", []):
            report.append(f"| {item['category']} | {item['count']} | {item['percentage']}% |")
        report.append("\n")

        # 6. Comparison behavior
        report.append("## 6. Comparison Behavior")
        report.append("| Behavior | Count | % |")
        report.append("|---|---|---|")
        for item in self.summary.get("comparison_behavior", []):
            report.append(f"| {item['behavior']} | {item['count']} | {item['percentage']}% |")
        report.append("\n")

        # 7. External research
        report.append("## 7. External Research Behavior")
        ext = self.summary.get("external_research", {})
        report.append("### Platforms")
        for item in ext.get("platforms", []):
            report.append(f"- **{item['platform']}**: {item['percentage']}% ({item['count']})")
        report.append("\n### Information Needs")
        for item in ext.get("information_needs", []):
            report.append(f"- **{item['need']}**: {item['percentage']}% ({item['count']})")
        report.append("\n")

        # 8. Shopper segments
        report.append("## 8. Shopper Segments")
        for seg in self.summary.get("shopper_segments", []):
            report.append(f"### {seg['segment']} ({seg['percentage']}%, n={seg['sample_size']})")
            report.append(f"- **Top Intent**: {seg['top_wishlist_intent']}")
            report.append(f"- **Top Barrier**: {seg['top_purchase_barrier']}")
            report.append(f"- **Top Uncertainty**: {seg['top_uncertainty']}")
            report.append(f"- **Top User Need**: {seg['top_user_need']}")
            report.append(f"- **Typical Impact**: {seg['typical_purchase_impact']}\n")

        # 9. Cross-analysis Highlights
        report.append("## 9. Cross-Analysis (Highlights)")
        report.append("Detailed cross-tabulations are available in the JSON summary file. They include:")
        report.append("- Purchase barrier by shopper segment")
        report.append("- Wishlist intent by shopper segment")
        report.append("- Purchase barrier by source")
        report.append("- Purchase impact by barrier")
        report.append("- Wishlist mode by purchase intent strength\n")

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("\n".join(report))
        logger.info(f"Saved markdown report to {filepath}")
