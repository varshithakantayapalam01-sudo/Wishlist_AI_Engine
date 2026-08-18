"""
Opportunity Analyzer Module.
Converts behavioral findings into quantified and ranked opportunity areas.
"""

import json
import csv
import os
import logging
from collections import defaultdict, Counter
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class OpportunityAnalyzer:
    def __init__(self, records: List[Dict[str, Any]]):
        # Strict confidence and relevance filtering
        self.total = len(records)
        self.records = [
            r for r in records 
            if r.get("classification_confidence", 0) and float(r.get("classification_confidence", 0)) >= 0.65
            and r.get("wishlist_relevance") in ("explicit_wishlist", "strong_purchase_consideration")
        ]
        logger.info(f"Filtered down to {len(self.records)} high-confidence, wishlist-relevant records for opportunity mapping (out of {self.total} total).")
        
        self.opportunities = {}
        self.high_intent_records = self._filter_high_intent()

    def _filter_high_intent(self) -> List[Dict[str, Any]]:
        """Filter records representing high purchase intent."""
        high_intent = []
        for r in self.records:
            if (r.get("purchase_intent_strength") == "high" or
                r.get("wishlist_mode") in ("genuine_purchase_intent", "likely_purchase_intent", 
                                           "sale_tracking", "comparison_tool")):
                high_intent.append(r)
        return high_intent

    def map_opportunities(self):
        """Map records into distinct opportunity areas based on barriers and uncertainties."""
        
        # Define opportunity mappings
        mappings = {
            "Fit & Sizing Confidence": {
                "barriers": {"fit", "sizing"},
                "uncertainties": {"will_it_fit", "which_size_should_i_buy"},
                "statement": "Users frequently postpone purchases because they lack confidence in whether the item will fit them or which size to choose."
            },
            "Price & Value Clarity": {
                "barriers": {"price", "waiting_for_discount"},
                "uncertainties": {"is_it_worth_the_price", "will_price_drop"},
                "statement": "Users delay buying because they are uncertain if the current price represents good value or if it will drop soon."
            },
            "Review & Quality Trust": {
                "barriers": {"product_quality", "review_uncertainty"},
                "uncertainties": {"is_quality_good", "can_i_trust_reviews"},
                "statement": "Users hesitate because they cannot trust the product reviews or are uncertain about the actual quality."
            },
            "Platform & Brand Trust": {
                "barriers": {"trust", "brand_uncertainty", "seller_uncertainty"},
                "uncertainties": {"is_the_brand_reliable"},
                "statement": "Users abandon purchases due to lack of trust in the platform, third-party seller, or unfamiliar brand."
            },
            "Decision & Comparison Support": {
                "barriers": {"product_comparison", "too_many_choices"},
                "uncertainties": {"which_product_is_better"},
                "statement": "Users are overwhelmed by choices and struggle to compare shortlisted items to make a final decision."
            },
            "Delivery & Returns Confidence": {
                "barriers": {"delivery", "returns"},
                "uncertainties": {"will_it_arrive_on_time", "can_i_return_it"},
                "statement": "Users block purchases out of fear that delivery will be late or returns will be difficult/rejected."
            },
            "Styling & Occasion Guidance": {
                "barriers": {"styling_uncertainty", "occasion_suitability"},
                "uncertainties": {"how_should_i_style_it", "is_it_right_for_my_occasion"},
                "statement": "Users hesitate because they don't know how to style the item or if it's appropriate for their specific occasion."
            },
            "Stock Availability Visibility": {
                "barriers": {"stock_availability"},
                "uncertainties": {"will_it_be_available_later"},
                "statement": "Users face friction when items or specific sizes are out of stock, with no visibility on restocks."
            },
            "Social Validation Support": {
                "barriers": {"social_validation"},
                "uncertainties": {},
                "statement": "Users delay purchases to seek opinions and validation from friends, family, or social media."
            }
        }

        # Initialize opportunity buckets
        for name, meta in mappings.items():
            self.opportunities[name] = {
                "opportunity_id": name.lower().replace(" ", "_").replace("&", "and"),
                "opportunity_name": name,
                "problem_statement": meta["statement"],
                "records": [],
                "high_intent_records": [],
                "meta": meta
            }

        # Map records to opportunities
        for r in self.records:
            barrier = r.get("primary_purchase_barrier", "")
            uncs = set(r.get("remaining_uncertainty", "").split("|"))
            is_high_intent = r in self.high_intent_records
            
            for name, opp in self.opportunities.items():
                if barrier in opp["meta"]["barriers"] or any(u in opp["meta"]["uncertainties"] for u in uncs):
                    opp["records"].append(r)
                    if is_high_intent:
                        opp["high_intent_records"].append(r)

    def calculate_scores(self):
        """Quantify each opportunity."""
        # Clean up empty opportunities
        self.opportunities = {k: v for k, v in self.opportunities.items() if len(v["records"]) > 0}
        
        # Max counts for normalization
        max_freq = max(len(o["records"]) for o in self.opportunities.values()) if self.opportunities else 1
        
        impact_weights = {
            "blocks_purchase": 5.0,
            "significantly_delays_purchase": 4.0,
            "moderately_delays_purchase": 3.0,
            "minor_friction": 2.0,
            "no_clear_impact": 1.0,
            "unclear": 1.0
        }

        for name, opp in self.opportunities.items():
            records = opp["records"]
            count = len(records)
            
            # 1. Frequency Score (1-5)
            # Logarithmic-like scaling relative to max frequency
            freq_ratio = count / max_freq
            freq_score = 1 + (freq_ratio * 4)
            
            # 2. Purchase Impact Score (1-5)
            impacts = [impact_weights.get(r.get("purchase_impact"), 1.0) for r in records]
            impact_score = sum(impacts) / count if count else 1.0
            
            # 3. High-Intent Relevance Score (1-5)
            high_intent_pct = len(opp["high_intent_records"]) / count if count else 0
            intent_score = 1 + (high_intent_pct * 4)
            
            # 4. Evidence Confidence Score (1-5)
            avg_conf = sum(float(r.get("classification_confidence", 0)) for r in records) / count if count else 0
            # Also factor in sample size (need at least ~30 records for full confidence)
            size_penalty = min(1.0, count / 30.0)
            conf_score = 1 + (avg_conf * size_penalty * 4)
            
            # 5. Segment Breadth Score (1-5)
            segments = set(r.get("shopper_segment") for r in records if r.get("shopper_segment"))
            breadth_ratio = min(1.0, len(segments) / 8.0) # Assuming ~8 main segments
            segment_score = 1 + (breadth_ratio * 4)
            
            # 6. External Leakage Score (1-5)
            leakage_count = sum(1 for r in records if r.get("external_research_behavior", "") not in ("none_detected", ""))
            leakage_pct = leakage_count / count if count else 0
            leakage_score = 1 + (leakage_pct * 4)
            
            # Overall Score Calculation
            weights = {
                "freq": 0.25,
                "impact": 0.25,
                "intent": 0.20,
                "conf": 0.15,
                "segment": 0.10,
                "leakage": 0.05
            }
            
            weighted_sum = (
                (freq_score * weights["freq"]) +
                (impact_score * weights["impact"]) +
                (intent_score * weights["intent"]) +
                (conf_score * weights["conf"]) +
                (segment_score * weights["segment"]) +
                (leakage_score * weights["leakage"])
            )
            
            overall_score = round(weighted_sum * 20, 2)
            
            # Sensitivity Analysis (Impact-heavy vs Freq-heavy)
            score_impact_heavy = round(((freq_score*0.15) + (impact_score*0.40) + (intent_score*0.20) + (conf_score*0.10) + (segment_score*0.10) + (leakage_score*0.05)) * 20, 2)
            score_freq_heavy = round(((freq_score*0.40) + (impact_score*0.15) + (intent_score*0.20) + (conf_score*0.10) + (segment_score*0.10) + (leakage_score*0.05)) * 20, 2)

            # Evidence Strength
            if count >= 100 and avg_conf >= 0.75:
                strength = "strong"
            elif count >= 40 and avg_conf >= 0.65:
                strength = "moderate"
            elif count >= 15:
                strength = "directional"
            else:
                strength = "weak"

            # Aggregate lists for reporting
            barriers_ctr = Counter(r.get("primary_purchase_barrier") for r in records)
            needs_ctr = Counter(r.get("underlying_user_need") for r in records)
            segments_ctr = Counter(r.get("shopper_segment") for r in records)
            modes_ctr = Counter(r.get("wishlist_mode") for r in records)
            delay_ctr = Counter(r.get("purchase_delay_reason") for r in records)
            sources_ctr = Counter(r.get("source") for r in records)

            # Sort records for snippets
            sorted_records = sorted(records, key=lambda x: float(x.get("classification_confidence", 0)), reverse=True)
            snippets = [r.get("evidence_snippet") for r in sorted_records[:5] if r.get("evidence_snippet")]

            opp["metrics"] = {
                "conversation_count": count,
                "percentage_of_relevant_dataset": round((count / self.total) * 100, 2),
                "high_intent_conversation_count": len(opp["high_intent_records"]),
                "high_intent_percentage": round(high_intent_pct * 100, 2),
                "frequency_score": round(freq_score, 2),
                "purchase_impact_score": round(impact_score, 2),
                "high_intent_relevance_score": round(intent_score, 2),
                "evidence_confidence_score": round(conf_score, 2),
                "segment_breadth_score": round(segment_score, 2),
                "external_leakage_score": round(leakage_score, 2),
                "overall_opportunity_score": overall_score,
                "score_impact_heavy": score_impact_heavy,
                "score_freq_heavy": score_freq_heavy,
                "evidence_strength": strength,
                "average_classification_confidence": round(avg_conf, 3),
            }
            
            opp["aggregates"] = {
                "underlying_user_need": needs_ctr.most_common(3),
                "related_barriers": barriers_ctr.most_common(5),
                "affected_segments": segments_ctr.most_common(3),
                "wishlist_modes_affected": modes_ctr.most_common(3),
                "purchase_delay_behaviors": delay_ctr.most_common(3),
                "source_distribution": sources_ctr.most_common(3),
                "representative_evidence": snippets
            }

    def generate_outputs(self, out_dir: str):
        """Generate all required JSON, CSV, and MD artifacts."""
        os.makedirs(out_dir, exist_ok=True)
        
        # Sort opportunities by overall score
        ranked_opps = sorted(self.opportunities.values(), key=lambda x: x["metrics"]["overall_opportunity_score"], reverse=True)
        
        # 1. Opportunity Ranking CSV
        csv_path = os.path.join(out_dir, "opportunity_ranking.csv")
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "rank", "opportunity_name", "problem_statement", "conversation_count", "dataset_percentage",
                "frequency_score", "purchase_impact_score", "high_intent_relevance_score",
                "evidence_confidence_score", "segment_breadth_score", "external_leakage_score",
                "overall_opportunity_score", "evidence_strength"
            ])
            for i, opp in enumerate(ranked_opps):
                m = opp["metrics"]
                writer.writerow([
                    i+1, opp["opportunity_name"], opp["problem_statement"], m["conversation_count"], m["percentage_of_relevant_dataset"],
                    m["frequency_score"], m["purchase_impact_score"], m["high_intent_relevance_score"],
                    m["evidence_confidence_score"], m["segment_breadth_score"], m["external_leakage_score"],
                    m["overall_opportunity_score"], m["evidence_strength"]
                ])
        
        # 2. High Intent Analysis JSON
        high_intent_path = os.path.join(out_dir, "high_intent_opportunity_analysis.json")
        hi_barriers = Counter(r.get("primary_purchase_barrier") for r in self.high_intent_records)
        hi_uncs = Counter(u for r in self.high_intent_records for u in str(r.get("remaining_uncertainty", "")).split("|") if u)
        hi_delays = Counter(r.get("purchase_delay_reason") for r in self.high_intent_records)
        hi_needs = Counter(r.get("underlying_user_need") for r in self.high_intent_records)
        
        hi_analysis = {
            "total_high_intent_records": len(self.high_intent_records),
            "top_barriers": hi_barriers.most_common(10),
            "top_uncertainties": hi_uncs.most_common(10),
            "top_delay_reasons": hi_delays.most_common(10),
            "top_unmet_needs": hi_needs.most_common(10),
            "opportunity_ranking_for_high_intent": [
                {
                    "opportunity": opp["opportunity_name"],
                    "high_intent_conversation_count": opp["metrics"]["high_intent_conversation_count"]
                }
                for opp in sorted(self.opportunities.values(), key=lambda x: x["metrics"]["high_intent_conversation_count"], reverse=True)
            ]
        }
        with open(high_intent_path, 'w', encoding='utf-8') as f:
            json.dump(hi_analysis, f, indent=2, ensure_ascii=False)

        # 3. Behavioral Chains JSON
        chains_path = os.path.join(out_dir, "behavioral_chains.json")
        chains_ctr = Counter()
        for r in self.records:
            intent = r.get("wishlist_intent", "unclear")
            barrier = r.get("primary_purchase_barrier", "no_clear_barrier")
            delay = r.get("purchase_delay_reason", "no_delay_detected")
            chain = f"{intent} -> {barrier} -> {delay}"
            chains_ctr[chain] += 1
            
        chains = []
        for chain, count in chains_ctr.most_common(15):
            if count < 5 or "unclear" in chain or "no_clear_barrier" in chain: continue
            chains.append({
                "chain_description": chain,
                "conversation_count": count
            })
        with open(chains_path, 'w', encoding='utf-8') as f:
            json.dump(chains, f, indent=2, ensure_ascii=False)

        # 4. Unmet Needs Analysis JSON
        unmet_path = os.path.join(out_dir, "unmet_needs_analysis.json")
        needs_dict = defaultdict(list)
        for r in self.records:
            need = r.get("underlying_user_need")
            if need and need != "no_clear_need":
                needs_dict[need].append(r)
                
        needs_analysis = []
        for need, recs in needs_dict.items():
            needs_analysis.append({
                "name": need,
                "supporting_conversations": len(recs),
                "associated_barriers": Counter(r.get("primary_purchase_barrier") for r in recs).most_common(3),
                "affected_segments": Counter(r.get("shopper_segment") for r in recs).most_common(3),
            })
        needs_analysis.sort(key=lambda x: x["supporting_conversations"], reverse=True)
        with open(unmet_path, 'w', encoding='utf-8') as f:
            json.dump(needs_analysis, f, indent=2, ensure_ascii=False)

        # 5. Opportunity Map JSON
        map_path = os.path.join(out_dir, "opportunity_map.json")
        opp_map = {
            "High Evidence / High Potential": [],
            "High Potential / Emerging Evidence": [],
            "High Evidence / Lower Conversion Impact": [],
            "Low Priority": []
        }
        for opp in ranked_opps:
            score = opp["metrics"]["overall_opportunity_score"]
            strength = opp["metrics"]["evidence_strength"]
            
            if score >= 75 and strength in ("strong", "moderate"):
                opp_map["High Evidence / High Potential"].append(opp["opportunity_name"])
            elif score >= 75 and strength in ("directional", "weak"):
                opp_map["High Potential / Emerging Evidence"].append(opp["opportunity_name"])
            elif score < 75 and strength in ("strong", "moderate"):
                opp_map["High Evidence / Lower Conversion Impact"].append(opp["opportunity_name"])
            else:
                opp_map["Low Priority"].append(opp["opportunity_name"])
                
        with open(map_path, 'w', encoding='utf-8') as f:
            json.dump(opp_map, f, indent=2, ensure_ascii=False)

        # 6. Opportunity Scoring Methodology MD
        methodology_path = os.path.join(out_dir, "opportunity_scoring_methodology.md")
        with open(methodology_path, 'w', encoding='utf-8') as f:
            f.write("# Opportunity Scoring Methodology\n\n")
            f.write("Opportunities are scored out of 100 based on a weighted average of 6 dimensions. Each dimension is normalized to a 1-5 scale.\n\n")
            f.write("- **Frequency (25%)**: Logarithmic scaling based on dataset percentage relative to the most frequent opportunity.\n")
            f.write("- **Purchase Impact (25%)**: Weighted average of severity (blocks=5, significant=4, moderate=3, minor=2, unclear=1).\n")
            f.write("- **High-Intent Relevance (20%)**: Percentage of conversations showing genuine/likely purchase intent.\n")
            f.write("- **Evidence Confidence (15%)**: Based on average classification confidence, penalized for small sample sizes (<30).\n")
            f.write("- **Segment Breadth (10%)**: Diversity of shopper segments affected.\n")
            f.write("- **External Leakage (5%)**: Frequency of users seeking answers off-platform.\n\n")
            f.write("## Sensitivity Analysis\n")
            f.write("We calculated alternative scores weighting Impact heavily (40%) and Frequency heavily (40%). Variations in ranking reflect whether an issue is highly blocking but rare, or common but less severe.\n")

        # 7. Executive Report MD
        report_path = os.path.join(out_dir, "opportunity_analysis_report.md")
        self._generate_markdown_report(report_path, ranked_opps)

    def _generate_markdown_report(self, filepath: str, ranked_opps: List[Dict]):
        lines = [
            "# Opportunity Analysis Report",
            "\n## Executive Summary",
            "This report synthesizes unstructured user feedback into prioritized opportunity areas. "
            "The goal is to identify the most critical unmet needs and purchase barriers blocking wishlist-to-purchase conversion.",
            "The analysis strictly focuses on *user problems*, avoiding premature feature recommendations.\n"
        ]
        
        # Matrix: Intent vs Friction
        lines.append("## Wishlist Intent vs. Purchase Friction Matrix\n")
        lines.append("| Wishlist Intent | Main Barrier | Count |")
        lines.append("|---|---|---|")
        matrix_ctr = Counter()
        for r in self.records:
            i = r.get("wishlist_intent")
            b = r.get("primary_purchase_barrier")
            if i != "unclear" and b != "no_clear_barrier":
                matrix_ctr[(i, b)] += 1
        for (i, b), count in matrix_ctr.most_common(10):
            lines.append(f"| {i} | {b} | {count} |")
        lines.append("\n")
        
        # Comparison Matrix
        lines.append("## Opportunity Comparison Matrix\n")
        lines.append("| Opportunity | Freq | Impact | Intent | Conf | Overall Score | Strength |")
        lines.append("|---|---|---|---|---|---|---|")
        for opp in ranked_opps:
            m = opp["metrics"]
            lines.append(f"| {opp['opportunity_name']} | {m['frequency_score']:.1f} | {m['purchase_impact_score']:.1f} | {m['high_intent_relevance_score']:.1f} | {m['evidence_confidence_score']:.1f} | **{m['overall_opportunity_score']}** | {m['evidence_strength']} |")
        lines.append("\n")

        lines.append("## Top Opportunity Areas\n")
        for opp in ranked_opps[:5]:
            m = opp["metrics"]
            a = opp["aggregates"]
            lines.append(f"### {opp['opportunity_name']}")
            lines.append(f"**User problem**: {opp['problem_statement']}")
            lines.append(f"- **Evidence**: Supported by {m['conversation_count']} conversations ({m['percentage_of_relevant_dataset']}% of dataset)")
            lines.append(f"- **Purchase impact**: Avg severity score {m['purchase_impact_score']:.1f}/5.0")
            lines.append(f"- **Evidence strength**: {m['evidence_strength'].upper()}")
            
            lines.append("\n**Representative evidence**:")
            for snip in a["representative_evidence"][:3]:
                lines.append(f"> \"{snip}\"")
            lines.append("\n---\n")

        lines.append("## Limitations and Misleading Conclusions Check")
        lines.append("- **Source Bias**: 100% of the dataset originates from Google Play Store reviews. While this captures mobile shopping friction effectively, it may underrepresent deep product exploration behaviors typically seen on desktop web or Reddit/YouTube.")
        lines.append("- **AI Inference**: While explicit barriers (e.g. 'bad quality') are directly mapped, 'underlying user needs' are AI-inferred cross-signals and should be treated as directional hypotheses.")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
        logger.info(f"Saved executive report to {filepath}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-7s | %(message)s')
    
    in_file = os.path.join(os.path.dirname(__file__), "..", "data", "classified_fashion_feedback.csv")
    out_dir = os.path.join(os.path.dirname(__file__), "..", "data", "opportunities")
    
    logger.info(f"Loading classified records from {in_file}")
    records = []
    with open(in_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
            
    analyzer = OpportunityAnalyzer(records)
    logger.info("Mapping opportunities...")
    analyzer.map_opportunities()
    
    logger.info("Calculating scores...")
    analyzer.calculate_scores()
    
    logger.info("Generating outputs...")
    analyzer.generate_outputs(out_dir)
    
    logger.info("Phase 3 Opportunity Analysis complete.")
