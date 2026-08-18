"""
Aggregate Analyzer.
Calculates aggregate statistics and cross-tabulations from the 
classified records to generate behavioral insights.
"""

import json
import logging
from collections import Counter
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class AggregateAnalyzer:
    """Generates aggregate insights from classified records."""

    def __init__(self, records: List[Dict[str, Any]]):
        self.records = records
        self.total = len(records)

    def analyze(self) -> Dict[str, Any]:
        """Run all aggregate analyses."""
        logger.info(f"Analyzer: Processing {self.total} records...")
        if self.total == 0:
            return {}

        return {
            "wishlist_intent": self._analyze_intent(),
            "wishlist_mode": self._analyze_mode(),
            "top_purchase_barriers": self._analyze_barriers(),
            "remaining_uncertainties": self._analyze_uncertainty(),
            "purchase_delay_reasons": self._analyze_delay(),
            "comparison_behavior": self._analyze_comparison(),
            "external_research": self._analyze_research(),
            "shopper_segments": self._analyze_segments(),
            "cross_analysis": self._generate_cross_tables()
        }

    def _count_and_pct(self, field: str) -> List[Dict[str, Any]]:
        counts = Counter([r.get(field, "unknown") for r in self.records])
        results = []
        for k, v in counts.most_common():
            # Calculate confidence-weighted percentage
            conf_sum = sum(r.get("classification_confidence", 0) for r in self.records if r.get(field) == k)
            results.append({
                "category": k,
                "count": v,
                "percentage": round((v / self.total) * 100, 2),
                "confidence_weighted_percentage": round((conf_sum / self.total) * 100, 2)
            })
        return results

    def _analyze_intent(self):
        return self._count_and_pct("wishlist_intent")

    def _analyze_mode(self):
        return self._count_and_pct("wishlist_mode")

    def _analyze_barriers(self):
        counts = Counter([r.get("primary_purchase_barrier", "unknown") for r in self.records])
        results = []
        for k, v in counts.most_common():
            avg_conf = sum(r.get("classification_confidence", 0) for r in self.records if r.get("primary_purchase_barrier") == k) / v
            results.append({
                "barrier": k,
                "count": v,
                "percentage": round((v / self.total) * 100, 2),
                "average_confidence": round(avg_conf, 3)
            })
        return results

    def _analyze_uncertainty(self):
        # Remaining uncertainty is a pipe-separated string
        all_unc = []
        for r in self.records:
            uncs = r.get("remaining_uncertainty", "").split("|")
            all_unc.extend([u for u in uncs if u])
        
        counts = Counter(all_unc)
        return [{"uncertainty": k, "count": v, "percentage": round((v / self.total) * 100, 2)}
                for k, v in counts.most_common()]

    def _analyze_delay(self):
        return self._count_and_pct("purchase_delay_reason")

    def _analyze_comparison(self):
        counts = Counter([r.get("comparison_behavior", "no_comparison_detected") for r in self.records])
        return [{"behavior": k, "count": v, "percentage": round((v / self.total) * 100, 2)}
                for k, v in counts.most_common()]

    def _analyze_research(self):
        all_res = []
        all_needs = []
        for r in self.records:
            res = r.get("external_research_behavior", "").split("|")
            needs = r.get("external_information_need", "").split("|")
            all_res.extend([x for x in res if x])
            all_needs.extend([x for x in needs if x])
            
        res_counts = Counter(all_res)
        need_counts = Counter(all_needs)
        
        return {
            "platforms": [{"platform": k, "count": v, "percentage": round((v / self.total) * 100, 2)} for k, v in res_counts.most_common()],
            "information_needs": [{"need": k, "count": v, "percentage": round((v / self.total) * 100, 2)} for k, v in need_counts.most_common()]
        }

    def _analyze_segments(self):
        segments = {}
        for r in self.records:
            seg = r.get("shopper_segment", "uncertain_or_mixed")
            if seg not in segments:
                segments[seg] = []
            segments[seg].append(r)
            
        results = []
        for seg, records in segments.items():
            count = len(records)
            
            def top_field(field):
                c = Counter([r.get(field, "unknown") for r in records])
                return c.most_common(1)[0][0] if c else "unknown"
                
            results.append({
                "segment": seg,
                "sample_size": count,
                "percentage": round((count / self.total) * 100, 2),
                "top_wishlist_intent": top_field("wishlist_intent"),
                "top_purchase_barrier": top_field("primary_purchase_barrier"),
                "top_uncertainty": top_field("remaining_uncertainty").split("|")[0] if top_field("remaining_uncertainty") else "unknown",
                "top_user_need": top_field("underlying_user_need"),
                "typical_purchase_impact": top_field("purchase_impact")
            })
            
        # Sort by size
        results.sort(key=lambda x: x["sample_size"], reverse=True)
        return results

    def _generate_cross_tables(self) -> Dict[str, Any]:
        """Generate requested cross-analysis tables."""
        return {
            "barrier_by_segment": self._cross_tab("shopper_segment", "primary_purchase_barrier"),
            "intent_by_segment": self._cross_tab("shopper_segment", "wishlist_intent"),
            "barrier_by_source": self._cross_tab("source", "primary_purchase_barrier"),
            "impact_by_barrier": self._cross_tab("primary_purchase_barrier", "purchase_impact"),
            "mode_by_intent_strength": self._cross_tab("purchase_intent_strength", "wishlist_mode")
        }

    def _cross_tab(self, row_field: str, col_field: str) -> Dict[str, Dict[str, int]]:
        """Simple cross-tabulation of two fields."""
        table = {}
        for r in self.records:
            row = str(r.get(row_field, "unknown"))
            col = str(r.get(col_field, "unknown"))
            
            if row not in table:
                table[row] = {}
            table[row][col] = table[row].get(col, 0) + 1
            
        return table

    def save_summary(self, summary: Dict[str, Any], filepath: str):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved behavioral analysis summary to {filepath}")
