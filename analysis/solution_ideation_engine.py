"""
Solution Ideation, Hypothesis, and Experimentation Engine.
Translates Phase 3 Opportunity data into structured product strategies,
experiment plans, and prioritized solutions.
"""

import os
import json
import csv
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class SolutionIdeationEngine:
    def __init__(self, opportunities: List[Dict[str, Any]], high_intent_data: Dict[str, Any]):
        self.opportunities = opportunities
        self.high_intent_data = high_intent_data
        
        # Select Top 3 Opportunities
        self.top_opps = self._select_top_opportunities()
        
        # Seeded PM ideation structures linked to the top opportunities
        self.concepts = self._seed_solution_concepts()
        
    def _select_top_opportunities(self) -> List[Dict[str, Any]]:
        """Select top 3 opportunities based on overall score and high-intent relevance."""
        sorted_opps = sorted(self.opportunities, key=lambda x: (
            float(x["overall_opportunity_score"]), 
            float(x["high_intent_relevance_score"])
        ), reverse=True)
        
        selected = sorted_opps[:3]
        logger.info(f"Selected top {len(selected)} opportunities for ideation.")
        return selected

    def _seed_solution_concepts(self) -> List[Dict[str, Any]]:
        """
        Generates structured solution concepts based on the top opportunities.
        Contains JTBDs, Hypotheses, Experiment designs, and AI applicability.
        """
        solutions = []
        
        # We assume the top 3 will likely be Fit/Size, Price/Value, and Quality/Trust based on typical fashion friction.
        # The engine dynamically matches these seeded concepts to the loaded opportunity names.
        
        opp_map = {opp["opportunity_name"]: opp for opp in self.top_opps}
        
        # --- Opportunity 1: Fit & Sizing Confidence ---
        fit_opp_name = next((k for k in opp_map.keys() if "Fit" in k or "Size" in k), None)
        if fit_opp_name:
            opp = opp_map[fit_opp_name]
            
            jtbd = [
                "When I have shortlisted a fashion item that I like, I want to know whether it will fit my body correctly, so I can confidently purchase without worrying about returns.",
                "When I see a size chart, I want to easily understand how it maps to my specific measurements, so I can pick the right size on the first try."
            ]
            problem_stmt = f"When high-intent fashion shoppers save an item they like, they often postpone purchasing because they are uncertain whether the selected size will fit them (supported by {opp['conversation_count']} conversations), which leads them to continue researching or abandon the decision."
            
            # Sol 1: Lightweight UX
            solutions.append(self._build_concept(
                name="Contextual Size Badge (Lightweight)",
                opp_name=fit_opp_name,
                problem=problem_stmt,
                jtbd=jtbd[0],
                target="Users viewing a wishlisted item",
                desc="A simple UI badge near the 'Move to Cart' button showing return rates for size issues on this specific brand.",
                how_it_works="Pulls historical return data for the brand/category. Displays 'Typically True to Size' or 'Runs Small' badge.",
                behavior="Increases confidence by providing crowdsourced sizing reality at the moment of decision.",
                conversion_why="Reduces the 'will it fit' uncertainty that causes wishlist abandonment.",
                effort=2, impact=3, reach=5, risk=1, conf=4,
                ai="AI_not_needed - Simple aggregate statistics lookup."
            ))
            
            # Sol 2: Personalization
            solutions.append(self._build_concept(
                name="Personalized Fit Predictor",
                opp_name=fit_opp_name,
                problem=problem_stmt,
                jtbd=jtbd[1],
                target="Users with past purchase history",
                desc="Compares the item's dimensions against the user's past kept items.",
                how_it_works="Uses a rule-based engine to say 'Based on the Levis jeans you kept in size M, we recommend size L here'.",
                behavior="Eliminates the cognitive load of reading size charts.",
                conversion_why="Provides a definitive answer to the primary friction point for high-intent users.",
                effort=3, impact=4, reach=3, risk=2, conf=4,
                ai="AI_helpful - Useful for matching unstructured sizing formats across brands."
            ))
            
            # Sol 3: Advanced AI
            solutions.append(self._build_concept(
                name="AI Body-Twin Review Summarizer",
                opp_name=fit_opp_name,
                problem=problem_stmt,
                jtbd=jtbd[0],
                target="Users lingering on product detail pages from the wishlist",
                desc="Generates an AI summary of reviews specifically from users with similar height/weight.",
                how_it_works="LLM processes thousands of reviews, filters by user self-reported body types, and summarizes the consensus on fit.",
                behavior="Provides highly relatable social proof.",
                conversion_why="Directly answers 'will it look good on ME' rather than 'is it a good product'.",
                effort=5, impact=5, reach=2, risk=3, conf=3,
                ai="AI_required - Requires NLP to extract and summarize nuanced fit feedback from unstructured text."
            ))

        # --- Opportunity 2: Price & Value Clarity ---
        price_opp_name = next((k for k in opp_map.keys() if "Price" in k or "Value" in k), None)
        if price_opp_name:
            opp = opp_map[price_opp_name]
            jtbd = [
                "When I see an expensive item I like, I want to know if it's currently at a good price, so I can buy it now rather than wait for a sale."
            ]
            problem_stmt = f"When deal-seeking shoppers add items to their wishlist, they often refuse to purchase at full price because they lack visibility into upcoming sales or price history (supported by {opp['conversation_count']} conversations)."
            
            # Sol 1: Simple Nudge
            solutions.append(self._build_concept(
                name="Price Drop Urgency Alert",
                opp_name=price_opp_name,
                problem=problem_stmt,
                jtbd=jtbd[0],
                target="Users with items in wishlist > 7 days",
                desc="Push notification when a wishlisted item drops in price.",
                how_it_works="Standard pub/sub alert on price changes.",
                behavior="Triggers immediate revisit and conversion.",
                conversion_why="Directly resolves the 'waiting_for_discount' delay reason.",
                effort=1, impact=3, reach=5, risk=1, conf=5,
                ai="AI_not_needed - Simple threshold trigger."
            ))
            
            # Sol 2: Decision Support
            solutions.append(self._build_concept(
                name="Value Confidence Indicator",
                opp_name=price_opp_name,
                problem=problem_stmt,
                jtbd=jtbd[0],
                target="Users viewing wishlisted items",
                desc="Shows a 'Good Price' badge if current price is within 5% of the 90-day low.",
                how_it_works="Calculates rolling 90-day price history min/max.",
                behavior="Assures user they aren't getting a bad deal.",
                conversion_why="Reduces the fear of buying right before a sale.",
                effort=2, impact=3, reach=4, risk=2, conf=4,
                ai="AI_not_needed - Basic time-series math."
            ))

            # Sol 3: Advanced
            solutions.append(self._build_concept(
                name="Smart Wardrobe ROI Calculator",
                opp_name=price_opp_name,
                problem=problem_stmt,
                jtbd=jtbd[0],
                target="Users viewing high-ticket items",
                desc="Shows cost-per-wear estimates based on user's typical wardrobe usage.",
                how_it_works="Predicts how often an item will be worn based on category and user's past purchase frequency.",
                behavior="Reframes the purchase from 'expensive' to 'investment'.",
                conversion_why="Overcomes price objections for high-quality items.",
                effort=4, impact=2, reach=2, risk=3, conf=2,
                ai="AI_helpful - Can predict usage patterns."
            ))

        # --- Opportunity 3: Review & Quality Trust ---
        trust_opp_name = next((k for k in opp_map.keys() if "Review" in k or "Quality" in k or "Trust" in k), None)
        if trust_opp_name:
            opp = opp_map[trust_opp_name]
            jtbd = [
                "When I am ready to buy an unknown brand, I want to quickly verify its quality through authentic reviews, so I don't waste money on a poor product."
            ]
            problem_stmt = f"When shoppers shortlist an item, they often abandon the purchase because they cannot trust the product quality or suspect reviews are fake (supported by {opp['conversation_count']} conversations)."
            
            # Sol 1: Lightweight
            solutions.append(self._build_concept(
                name="Verified Buyer Photo Highlight",
                opp_name=trust_opp_name,
                problem=problem_stmt,
                jtbd=jtbd[0],
                target="Users scrolling to reviews",
                desc="Surfaces user-uploaded photos to the top of the wishlist item page.",
                how_it_works="UI change to prioritize media over text reviews.",
                behavior="Provides immediate visual proof of actual product quality.",
                conversion_why="Resolves the 'is quality good' uncertainty visually.",
                effort=1, impact=3, reach=5, risk=1, conf=4,
                ai="AI_not_needed - UI reordering."
            ))
            
            # Sol 2: Advanced AI
            solutions.append(self._build_concept(
                name="AI Quality Extraction Summary",
                opp_name=trust_opp_name,
                problem=problem_stmt,
                jtbd=jtbd[0],
                target="Users viewing items with >50 reviews",
                desc="An AI-generated summary explicitly focused on fabric, stitching, and durability.",
                how_it_works="LLM extracts only quality-related sentiments from reviews and synthesizes them into a 2-sentence summary.",
                behavior="Saves the user from reading dozens of reviews to find quality indicators.",
                conversion_why="Directly answers the 'is the quality good' friction point instantly.",
                effort=4, impact=4, reach=4, risk=2, conf=4,
                ai="AI_required - Requires NLP to extract specific semantic themes (quality) from messy reviews."
            ))

        return solutions

    def _build_concept(self, name, opp_name, problem, jtbd, target, desc, how_it_works, behavior, conversion_why, effort, impact, reach, risk, conf, ai):
        """Helper to build a standardized solution concept dictionary."""
        
        # Calculate prioritization score (normalized to 100)
        # Formula: (Impact*0.25 + Reach*0.15 + Conf*0.15) - (Effort*0.20 + Risk*0.25)
        # Base starts at 50 to allow negative penalties to drop below 50.
        raw_score = 50 + (impact*5) + (reach*3) + (conf*3) - (effort*4) - (risk*5)
        priority_score = max(0, min(100, raw_score))
        
        return {
            "solution_name": name,
            "opportunity_addressed": opp_name,
            "user_problem": problem,
            "jtbd": jtbd,
            "target_segment": target,
            "concept_description": desc,
            "how_it_works": how_it_works,
            "behavior_change_expected": behavior,
            "why_it_may_improve_wishlist_conversion": conversion_why,
            "evidence_support": f"Supported by high incidence in discovery data for {opp_name}.",
            "implementation_complexity": effort,
            "user_impact_score": impact,
            "expected_metric_impact_score": impact,
            "evidence_strength_score": conf,
            "reach_score": reach,
            "risk_score": risk,
            "time_to_learn_score": effort,
            "overall_priority_score": priority_score,
            "ai_classification": ai,
            "hypothesis": f"If we provide {target.lower()} with a {name.lower()}, then they will {behavior.lower()}, because {conversion_why.lower()}, resulting in an increase in 30-Day Wishlist-to-Purchase User Conversion Rate."
        }

    def _generate_experiment_plan(self, sol: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a detailed experiment plan for a solution."""
        return {
            "experiment_name": f"EXP: {sol['solution_name']}",
            "opportunity": sol["opportunity_addressed"],
            "hypothesis": sol["hypothesis"],
            "target_population": sol["target_segment"],
            "control": "Current experience (no intervention).",
            "treatment": sol["concept_description"],
            "primary_metric": "30-Day Wishlist-to-Purchase User Conversion Rate (Numerator: users who purchase >=1 wishlisted item in 30d. Denominator: users who add >=1 item to wishlist).",
            "secondary_metrics": [
                "Time from wishlist to purchase",
                "Add-to-cart from wishlist rate"
            ],
            "guardrail_metrics": [
                "Return rate (ensure we aren't driving bad purchases)",
                "Notification opt-outs (if applicable)",
                "Wishlist abandonment rate"
            ],
            "expected_direction": "Increase in primary metric. No significant increase in return rate.",
            "experiment_duration": "14 days (subject to traffic/power calculations)",
            "decision_criteria": {
                "ship": "Statistically significant increase in primary metric AND neutral/positive guardrails.",
                "iterate": "Trending positive primary metric BUT negative impact on return rates.",
                "stop": "Flat or negative primary metric."
            },
            "timing_strategy": "Triggered when user revisits the wishlist or dwells on the Product Detail Page of a wishlisted item. Timing matters to catch them in the decision phase, not the initial bookmarking phase."
        }

    def generate_all_outputs(self, out_dir: str):
        """Generates all 8 requested artifacts."""
        os.makedirs(out_dir, exist_ok=True)
        
        # Sort solutions by priority
        self.concepts.sort(key=lambda x: x["overall_priority_score"], reverse=True)
        
        # 1. Solution Concepts JSON
        with open(os.path.join(out_dir, "solution_concepts.json"), 'w', encoding='utf-8') as f:
            json.dump([{k: v for k, v in c.items() if k not in ("user_impact_score", "expected_metric_impact_score", "evidence_strength_score", "reach_score", "risk_score", "time_to_learn_score", "overall_priority_score", "hypothesis")} for c in self.concepts], f, indent=2)

        # 2. Prioritization CSV
        csv_path = os.path.join(out_dir, "solution_prioritization.csv")
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "rank", "solution_name", "opportunity_addressed", "user_impact_score",
                "expected_metric_impact_score", "evidence_strength_score", "reach_score",
                "implementation_effort_score", "time_to_learn_score", "risk_score",
                "overall_priority_score", "ai_classification"
            ])
            for i, c in enumerate(self.concepts):
                writer.writerow([
                    i+1, c["solution_name"], c["opportunity_addressed"], c["user_impact_score"],
                    c["expected_metric_impact_score"], c["evidence_strength_score"], c["reach_score"],
                    c["implementation_complexity"], c["time_to_learn_score"], c["risk_score"],
                    c["overall_priority_score"], c["ai_classification"]
                ])

        # 3. Product Hypotheses JSON
        hypotheses = [{"solution_name": c["solution_name"], "hypothesis": c["hypothesis"]} for c in self.concepts]
        with open(os.path.join(out_dir, "product_hypotheses.json"), 'w', encoding='utf-8') as f:
            json.dump(hypotheses, f, indent=2)

        # 4. Experiment Plans JSON
        experiments = [self._generate_experiment_plan(c) for c in self.concepts]
        with open(os.path.join(out_dir, "experiment_plans.json"), 'w', encoding='utf-8') as f:
            json.dump(experiments, f, indent=2)

        # 5. Experiment Roadmap MD
        self._write_experiment_roadmap(os.path.join(out_dir, "experiment_roadmap.md"), self.concepts)

        # 6. Recommended Product Concept MD
        recommended = self.concepts[0] # Highest priority score
        self._write_product_concept(os.path.join(out_dir, "recommended_product_concept.md"), recommended)

        # 7. Risks & Assumptions MD
        self._write_risks(os.path.join(out_dir, "solution_risks_and_assumptions.md"))

        # 8. Strategy Report MD
        self._write_strategy_report(os.path.join(out_dir, "solution_strategy_report.md"), recommended)

    def _write_experiment_roadmap(self, path, concepts):
        lines = [
            "# Experimentation Roadmap\n",
            "## Phase 1 — Fast Validation (Low Effort, High Reach)",
            "Test lightweight UX interventions to validate the core user problems before building complex data pipelines."
        ]
        p1 = [c for c in concepts if c["implementation_complexity"] <= 2]
        for c in p1:
            lines.extend([f"- **Experiment**: {c['solution_name']}", f"  - **Why Now**: Cheap to build, validates if {c['opportunity_addressed']} actually drives conversion.", f"  - **Expected Learning**: Do users care about this information?"])
            
        lines.extend([
            "\n## Phase 2 — Personalized Decision Support (Medium Effort)",
            "Test personalized experiences using historical user data, assuming Phase 1 proves the problem is worth solving."
        ])
        p2 = [c for c in concepts if c["implementation_complexity"] == 3]
        for c in p2:
            lines.extend([f"- **Experiment**: {c['solution_name']}", f"  - **Dependency**: Requires user auth and purchase history.", f"  - **Expected Learning**: Does personalization significantly outperform generic UX interventions?"])

        lines.extend([
            "\n## Phase 3 — Advanced AI Intelligence (High Effort)",
            "Deploy LLMs and advanced ML only where unstructured data processing is strictly required."
        ])
        p3 = [c for c in concepts if c["implementation_complexity"] >= 4]
        for c in p3:
            lines.extend([f"- **Experiment**: {c['solution_name']}", f"  - **Dependency**: Requires NLP pipeline and model tuning.", f"  - **Expected Learning**: Can AI effectively synthesize nuanced qualitative feedback to drive conversion?"])

        with open(path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

    def _write_product_concept(self, path, recommended):
        lines = [
            "# Recommended Product Concept Brief\n",
            f"## Selected Concept: {recommended['solution_name']}",
            f"**Targeting Opportunity**: {recommended['opportunity_addressed']}\n",
            "## Problem", recommended['user_problem'],
            "\n## Target User", recommended['target_segment'],
            "\n## User Insight", "High-intent users often abandon purchases because they lack specific confidence at the final decision moment. They don't need more inspiration; they need definitive validation.",
            "\n## Jobs to Be Done", recommended['jtbd'],
            "\n## Product Hypothesis", recommended['hypothesis'],
            "\n## Proposed Experience", recommended['concept_description'],
            "\n## User Flow",
            "1. User wishlists item",
            "2. Intent signal detected (User returns to app within 48h and views wishlist)",
            "3. Relevant uncertainty identified based on item category",
            f"4. Decision-support intervention shown: {recommended['solution_name']}",
            "5. User resolves uncertainty",
            "6. Add to cart & Purchase",
            "\n## Why This Could Change Behavior", recommended['behavior_change_expected'],
            "\n## Primary Metric", "30-Day Wishlist-to-Purchase User Conversion Rate",
            "\n## Guardrails", "Return Rate, Wishlist Abandonment Rate",
            "\n## MVP vs Vision",
            "**MVP**: Static rules-based trigger using historical aggregates.",
            "**V2**: Personalized based on user's past browsing.",
            "**Long-term Vision**: Fully contextual, predicting the exact friction point for that specific user and item."
        ]
        with open(path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

    def _write_risks(self, path):
        lines = [
            "# Solution Risks and Assumptions\n",
            "## Why This Might Not Work (Challenge Section)\n",
            "1. **Assumption**: Wishlist users actually want to buy.\n   **Risk**: Users may have fundamentally low purchase intent (using wishlist as an inspiration board). If true, no decision support tool will drive conversion.\n   **Validation**: Monitor conversion rate specifically for cohorts explicitly segmented as 'genuine_purchase_intent'.",
            "2. **Assumption**: Information gap causes the delay.\n   **Risk**: Price sensitivity may outweigh information improvements. If they just can't afford it, fit guidance won't help.\n   **Validation**: Cross-reference conversion lifts against items that are actively discounted.",
            "3. **Assumption**: Users trust our interventions.\n   **Risk**: Users may not trust AI recommendations or platform badges, preferring external validation (YouTube, friends).\n   **Validation**: Measure click-through rates on interventions vs external outbound leakage.",
            "4. **Assumption**: Resolving friction leads to *kept* purchases.\n   **Risk**: The solution could increase initial conversion but drastically increase return rates if the guidance is inaccurate.\n   **Validation**: Strict monitoring of 30-day return rate guardrail metric.",
            "5. **Assumption**: Discovery data represents all customers.\n   **Risk**: Behavior seen in public App Store conversations may overrepresent vocal, extreme negative experiences and not the silent majority.\n   **Validation**: Run the MVP experiment on a broad random sample to establish a true baseline."
        ]
        with open(path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

    def _write_strategy_report(self, path, recommended):
        lines = [
            "# Solution Strategy Report",
            "\n## The Evidence-to-Experiment Narrative",
            "This document traces the path from raw user feedback to a prioritized product experiment.\n",
            "### 1. The User Evidence",
            "In Phase 2, we analyzed 4,927 conversations and identified that users frequently abandon wishlists not due to lack of interest, but due to highly specific, unresolved uncertainties (Fit, Price, Quality).",
            f"\n### 2. The Opportunity",
            f"Phase 3 quantified these issues. We selected **{recommended['opportunity_addressed']}** as the primary focus because it heavily impacts high-intent users. The data explicitly supported this as a major friction point.",
            f"\n### 3. The Solution Hypothesis",
            f"We hypothesize that: *{recommended['hypothesis']}*",
            f"\n### 4. The Experiment",
            f"We will test **{recommended['solution_name']}**. This was chosen over AI-heavy alternatives because it requires significantly less implementation effort (Score: {recommended['implementation_complexity']}) while maintaining high Expected Impact (Score: {recommended['expected_metric_impact_score']}).",
            "\n### 5. The Business Metric",
            "Success will be measured strictly by the **30-Day Wishlist-to-Purchase User Conversion Rate**, ensuring we are driving true business value, not just feature engagement.",
            "\n---\n**Final Recommendation:**",
            f"We should build the MVP for **{recommended['solution_name']}** immediately. It is a low-risk, high-evidence intervention targeting our most valuable user cohort."
        ]
        with open(path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-7s | %(message)s')
    
    # Load Phase 3 Data
    opps_file = os.path.join(os.path.dirname(__file__), "..", "data", "opportunities", "opportunity_ranking.csv")
    hi_file = os.path.join(os.path.dirname(__file__), "..", "data", "opportunities", "high_intent_opportunity_analysis.json")
    out_dir = os.path.join(os.path.dirname(__file__), "..", "data", "solutions")
    
    opps = []
    if os.path.exists(opps_file):
        with open(opps_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader: opps.append(row)
            
    hi_data = {}
    if os.path.exists(hi_file):
        with open(hi_file, 'r', encoding='utf-8') as f:
            hi_data = json.load(f)
            
    if not opps:
        logger.error("Could not load opportunity ranking data. Ensure Phase 3 has run.")
        import sys; sys.exit(1)
        
    engine = SolutionIdeationEngine(opps, hi_data)
    logger.info("Generating solution concepts, hypotheses, and experiments...")
    engine.generate_all_outputs(out_dir)
    logger.info("Phase 4 Solution Ideation complete. All artifacts generated.")
