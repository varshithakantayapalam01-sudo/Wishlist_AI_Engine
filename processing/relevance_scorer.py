"""
Relevance scoring module.
Assigns a 0.0–1.0 relevance score to each record based on weighted keyword
presence, comment structure, and contextual signals.
"""

import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class RelevanceScorer:
    """Score records for relevance to fashion shopping behavior analysis."""

    def __init__(self, keywords: Dict[str, float], threshold: float = 0.65):
        """
        Args:
            keywords: dict mapping keyword -> weight (0.0 to 1.0)
            threshold: minimum score to be considered relevant
        """
        self.keywords = keywords
        self.threshold = threshold

        # Pre-compile keyword patterns (word boundary matching)
        self._keyword_patterns = {}
        for kw, weight in keywords.items():
            # Use word boundaries for short keywords to avoid false matches
            if len(kw) <= 3:
                pattern = re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE)
            else:
                pattern = re.compile(re.escape(kw), re.IGNORECASE)
            self._keyword_patterns[pattern] = weight

    def _score_keywords(self, text: str) -> float:
        """Calculate keyword-based relevance score."""
        if not text:
            return 0.0

        total_weight = 0.0
        matched_keywords = set()

        for pattern, weight in self._keyword_patterns.items():
            if pattern.search(text):
                # Track unique keyword matches
                matched_keywords.add(pattern.pattern)
                total_weight += weight

        # Normalize: cap raw keyword score and scale
        # More keyword matches = higher score, but diminishing returns
        keyword_score = min(total_weight, 1.0)

        return keyword_score

    def _score_structure(self, text: str) -> float:
        """Score based on structural signals in the text."""
        score = 0.0

        # Longer comments tend to be more informative
        length = len(text)
        if length > 300:
            score += 0.15
        elif length > 200:
            score += 0.12
        elif length > 100:
            score += 0.08
        elif length > 50:
            score += 0.04

        # Questions indicate decision-making or seeking advice
        question_marks = text.count("?")
        if question_marks >= 2:
            score += 0.10
        elif question_marks >= 1:
            score += 0.06

        # Comparative language
        comparative_patterns = [
            r'\bvs\b', r'\bversus\b', r'\bcompare\b', r'\bbetter\b',
            r'\bworse\b', r'\bor\b.*\b(buy|get|choose)\b',
            r'\bwhich\s+(one|is)\b', r'\bshould\s+i\b',
        ]
        for pattern in comparative_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                score += 0.06
                break

        # Personal experience indicators
        experience_patterns = [
            r'\bi\s+(bought|ordered|received|returned|exchanged)\b',
            r'\bmy\s+(order|purchase|experience|review)\b',
            r'\bi\s+(tried|wore|used|checked)\b',
            r'\bwhen\s+i\b',
            r'\bafter\s+(buying|ordering|receiving)\b',
        ]
        experience_count = 0
        for pattern in experience_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                experience_count += 1
        score += min(experience_count * 0.05, 0.10)

        # Shopping-specific experience patterns
        shopping_patterns = [
            r'\b(wishlist|wish\s*list|saved|cart|add\s*to\s*cart)\b',
            r'\b(ordered|delivered|shipped|dispatched|tracking)\b',
            r'\b(refund|replacement|pickup|cancelled)\b',
            r'\b(COD|cash on delivery|prepaid|payment)\b',
            r'\b(app|website|online|platform|shopping)\b',
        ]
        shop_count = 0
        for pattern in shopping_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                shop_count += 1
        score += min(shop_count * 0.04, 0.12)

        # Numerical details (sizes, prices, ratings)
        if re.search(r'\b(size\s+)?\d+\b', text, re.IGNORECASE):
            score += 0.03
        if re.search(r'₹|rs\.?|inr|\brupee', text, re.IGNORECASE):
            score += 0.04

        return min(score, 0.45)  # Cap structural bonus

    def score_record(self, record: Dict[str, Any]) -> float:
        """
        Calculate the relevance score for a single record.
        Returns a float between 0.0 and 1.0.
        """
        text = record.get("comment_text", "")
        title = record.get("title_or_context", "")

        # Combine text and title for scoring
        combined = f"{title} {text}"

        # Component scores
        keyword_score = self._score_keywords(combined)
        structure_score = self._score_structure(text)

        # Source type bonus
        source_bonus = 0.0
        source_type = record.get("source_type", "")
        if source_type == "post":
            source_bonus = 0.08  # Reddit posts tend to be more substantive
        elif source_type == "review":
            source_bonus = 0.05  # Reviews are inherently relevant

        # Fashion app context bonus — reviews from fashion-specific apps
        # are inherently about fashion shopping, so they deserve a base boost
        context_bonus = 0.0
        brand = record.get("brand_or_platform", "")
        fashion_brands = {
            "Myntra", "AJIO", "Nykaa Fashion", "Meesho", "Tata CLiQ",
            "Flipkart", "Bewakoof", "Limeroad", "H&M", "Max Fashion",
        }
        if brand in fashion_brands and source_type == "review":
            context_bonus = 0.15  # Fashion app review baseline
            # Extra bonus if the review discusses shopping-specific topics
            shopping_signals = [
                r'\b(order|buy|purchase|bought|shop)\b',
                r'\b(deliver|return|exchange|refund|replace)\b',
                r'\b(product|item|cloth|dress|shirt|jeans|shoe)\b',
                r'\b(price|cost|expensive|cheap|afford|discount|sale|offer)\b',
            ]
            signals_matched = sum(
                1 for p in shopping_signals if re.search(p, text, re.IGNORECASE)
            )
            context_bonus += min(signals_matched * 0.04, 0.12)

        # Engagement bonus (highly upvoted content tends to be quality)
        engagement_bonus = 0.0
        likes = record.get("likes_or_upvotes")
        if likes is not None:
            if likes >= 50:
                engagement_bonus = 0.06
            elif likes >= 10:
                engagement_bonus = 0.04
            elif likes >= 5:
                engagement_bonus = 0.02
            elif likes >= 1:
                engagement_bonus = 0.01

        # Final score
        final_score = (
            keyword_score + structure_score + source_bonus +
            context_bonus + engagement_bonus
        )

        # Clamp to [0.0, 1.0]
        return round(min(max(final_score, 0.0), 1.0), 4)

    def score_all(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score all records and update their relevance_score field."""
        logger.info(f"Scorer: Scoring {len(records)} records")

        for record in records:
            record["relevance_score"] = self.score_record(record)

        # Log distribution
        scores = [r["relevance_score"] for r in records]
        if scores:
            above_threshold = sum(1 for s in scores if s >= self.threshold)
            avg_score = sum(scores) / len(scores)
            logger.info(
                f"Scorer: Avg score={avg_score:.3f}, "
                f"Above {self.threshold}={above_threshold}/{len(records)} "
                f"({above_threshold/len(records)*100:.1f}%)"
            )

        return records

    def filter_relevant(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return only records meeting the relevance threshold."""
        relevant = [r for r in records if r["relevance_score"] >= self.threshold]
        removed = len(records) - len(relevant)
        logger.info(
            f"Scorer: Kept {len(relevant)} records (removed {removed} below threshold)"
        )
        return relevant
