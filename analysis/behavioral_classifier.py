"""
Behavioral Classifier — 12-step classification engine.
Classifies each fashion shopping conversation into structured behavioral
signals using weighted keyword patterns, contextual inference, and
cross-signal reasoning.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Pattern Definitions
# ═══════════════════════════════════════════════════════════════════════════

# --- Step 1: Wishlist Intent Patterns ---
WISHLIST_INTENT_PATTERNS = {
    "purchase_later": [
        (r"\b(buy|purchase|order)\b.*\b(later|soon|tomorrow|next week|next month)\b", 3),
        (r"\bplanning to (buy|order|purchase)\b", 3),
        (r"\bwill (buy|order|get)\b", 2),
        (r"\bgoing to (buy|order)\b", 2),
        (r"\bwant(ed)? to (buy|order|purchase|get)\b", 2),
        (r"\bneed(ed)? to (buy|order)\b", 2),
        (r"\bintend(ing)? to (buy|purchase)\b", 3),
    ],
    "waiting_for_discount": [
        (r"\bwait(ing)? for (sale|discount|offer|price drop|deal)\b", 4),
        (r"\b(EORS|end of reason|big (bold|fashion) (sale|festival))\b", 3),
        (r"\bwhen.*(sale|discount|offer)\b", 2),
        (r"\bprice (drop|reduce|cut)\b", 3),
        (r"\btoo (expensive|costly|pricey)\b.*\bwait\b", 3),
        (r"\bcoupon|promo code|discount code\b", 2),
        (r"\bsale.*\bwait\b", 3),
    ],
    "comparison_shortlist": [
        (r"\b(compare|comparing|comparison)\b", 3),
        (r"\bvs\b|\bversus\b", 3),
        (r"\bwhich (one|is better|should i)\b", 3),
        (r"\b(better|best) (option|choice|between)\b", 2),
        (r"\bshortlist(ed)?\b", 3),
        (r"\bchoose|choosing|chose\b.*\bbetween\b", 3),
        (r"\bconfuse[d]? between\b", 3),
    ],
    "occasion_planning": [
        (r"\b(wedding|party|function|festival|diwali|eid|christmas|puja|holi)\b", 2),
        (r"\b(occasion|event|ceremony|reception|sangeet|mehendi)\b", 2),
        (r"\b(birthday|anniversary|date night|office party|farewell)\b", 2),
        (r"\b(bridal|bridesmaid|guest|ethnic wear for)\b", 3),
        (r"\blooking for.*(occasion|event|wedding|party)\b", 3),
    ],
    "inspiration_or_discovery": [
        (r"\bjust (browsing|looking|checking|exploring)\b", 3),
        (r"\b(inspiration|ideas|explore|discover)\b", 2),
        (r"\b(trendy|trending|fashion ideas|style ideas)\b", 2),
        (r"\bwhat's new\b|\bnew (arrivals|collection)\b", 2),
        (r"\bwindow shopping\b", 3),
    ],
    "bookmarking_only": [
        (r"\bjust (saved?|bookmarked?|liked)\b", 3),
        (r"\bsave for (later|reference)\b", 2),
        (r"\bkeep(ing)? track\b", 2),
        (r"\bno plan to buy\b", 3),
    ],
    "waiting_for_more_information": [
        (r"\bneed(s)? (more|better) (info|information|details|reviews|photos)\b", 3),
        (r"\bwant to (see|know|check|read|find out)\b.*\b(reviews?|details|info)\b", 2),
        (r"\b(unclear|not sure|unsure)\b.*\b(about|whether|if)\b", 2),
        (r"\b(no|few|lack of) reviews?\b", 3),
        (r"\bnot enough (info|information|details|photos|images)\b", 3),
    ],
    "waiting_for_stock": [
        (r"\bout of stock\b", 4),
        (r"\bsold out\b", 3),
        (r"\bnot available\b.*\bsize\b", 3),
        (r"\bback in stock\b", 3),
        (r"\bstock\b.*\b(unavailable|empty|not available)\b", 3),
        (r"\bmy size.*\bnot available\b", 4),
    ],
    "gift_or_future_need": [
        (r"\bgift\b", 2),
        (r"\bfor (someone|friend|mom|dad|sister|brother|wife|husband|partner)\b", 2),
        (r"\bfuture\b.*\b(need|use|reference)\b", 2),
        (r"\blater\b.*\b(need|want|might)\b", 1),
    ],
}

# --- Step 2: Purchase Barrier Patterns ---
BARRIER_PATTERNS = {
    "price": [
        (r"\b(expensive|costly|pricey|overpriced|high price)\b", 3),
        (r"\bnot (affordable|worth|value)\b", 2),
        (r"\btoo much (money|cost)\b", 2),
        (r"\bbudget\b", 1),
        (r"\bcheap(er)?\b", 1),
        (r"\bprice\b.*\b(high|too|issue|problem|concern)\b", 2),
    ],
    "waiting_for_discount": [
        (r"\bwait(ing)? for.*(sale|discount|offer|deal|price drop)\b", 4),
        (r"\bsale\b.*\bwait\b", 3),
        (r"\bdiscount\b.*\bwhen\b", 2),
    ],
    "fit": [
        (r"\b(doesn't|didn't|does not|did not|won't) fit\b", 4),
        (r"\bfit(ting)?\b.*\b(issue|problem|concern|bad|poor|wrong|tight|loose)\b", 3),
        (r"\bnot fit(ting)?\b", 3),
        (r"\btoo (tight|loose|big|small|short|long)\b", 3),
        (r"\bfit\b.*\b(unsure|worried|concern|not sure)\b", 3),
    ],
    "sizing": [
        (r"\bsize\b.*\b(issue|problem|wrong|incorrect|mismatch|confus)\b", 4),
        (r"\bsiz(e|ing)\b.*\b(chart|guide)\b.*\b(wrong|inaccurate|misleading|off)\b", 4),
        (r"\bordered\b.*\b(wrong|different) size\b", 3),
        (r"\bsize\b.*\b(exchange|return)\b", 3),
        (r"\b(which|what) size\b", 2),
        (r"\bsize (runs|ran) (small|large|big)\b", 3),
        (r"\btrue to size\b", 2),
    ],
    "product_quality": [
        (r"\b(poor|bad|low|cheap|worst|terrible|horrible) quality\b", 4),
        (r"\bquality\b.*\b(issue|problem|bad|poor|terrible|disappointing)\b", 3),
        (r"\b(fabric|material|stitching|color)\b.*\b(bad|poor|cheap|thin|different)\b", 3),
        (r"\bnot as (shown|described|pictured|expected|advertised)\b", 3),
        (r"\b(fake|duplicate|copy|counterfeit)\b", 3),
        (r"\bcolor\b.*\b(different|mismatch|faded|wrong)\b", 3),
    ],
    "review_uncertainty": [
        (r"\b(no|few|lack of|mixed|fake|unreliable) reviews?\b", 3),
        (r"\breviews?\b.*\b(fake|paid|unreliable|can't trust)\b", 3),
        (r"\bnot sure\b.*\breviews?\b", 2),
        (r"\bread(ing)?\b.*\breviews?\b.*\b(before|first)\b", 2),
    ],
    "trust": [
        (r"\b(don't|do not|can't|cannot) trust\b", 3),
        (r"\b(fraud|scam|cheat|fake|fraudulent)\b", 4),
        (r"\bnot (reliable|trustworthy|genuine|authentic)\b", 3),
        (r"\btrust\b.*\b(issue|problem|concern|worried)\b", 3),
    ],
    "insufficient_information": [
        (r"\bnot enough (info|information|details|photos|images|description)\b", 3),
        (r"\b(need|want) more (info|details|photos|images|description)\b", 3),
        (r"\b(unclear|vague|missing)\b.*\b(description|details|info)\b", 3),
    ],
    "product_comparison": [
        (r"\bcan't decide\b.*\bbetween\b", 3),
        (r"\btoo many (options|choices)\b", 3),
        (r"\bconfused\b.*\b(between|which|options)\b", 3),
    ],
    "too_many_choices": [
        (r"\btoo many (options|choices|products|similar)\b", 3),
        (r"\boverwhelm(ed|ing)?\b", 2),
        (r"\bconfused\b.*\b(too many|options|so many)\b", 3),
    ],
    "stock_availability": [
        (r"\bout of stock\b", 4),
        (r"\bsold out\b", 3),
        (r"\bnot available\b", 2),
        (r"\bstock\b.*\b(issue|unavailable|limited)\b", 3),
    ],
    "delivery": [
        (r"\bdeliver(y|ed)?\b.*\b(late|delay|slow|issue|problem|wrong|not|never|bad)\b", 3),
        (r"\b(late|delayed|slow|wrong) delivery\b", 3),
        (r"\bnot (delivered|received|shipped)\b", 3),
        (r"\bdelivery\b.*\b(time|date|days|weeks)\b.*\b(long|too|much)\b", 2),
        (r"\bshipping\b.*\b(slow|delayed|issue|expensive)\b", 2),
    ],
    "returns": [
        (r"\breturn\b.*\b(issue|problem|difficult|rejected|denied|fail|refus|refused)\b", 3),
        (r"\b(refund|replacement)\b.*\b(not|pending|delay|issue|problem|reject|denied)\b", 3),
        (r"\bno return\b", 3),
        (r"\breturn\b.*\b(policy|process|pickup)\b.*\b(bad|poor|worst|terrible|hard|difficult)\b", 3),
        (r"\b(exchange|refund)\b.*\b(not|pending|waiting|delay)\b", 3),
    ],
    "styling_uncertainty": [
        (r"\bhow to (style|wear|pair|match)\b", 3),
        (r"\bstyl(e|ing)\b.*\b(unsure|confused|help|advice)\b", 2),
        (r"\bwhat to wear with\b", 2),
        (r"\b(match|pair|go with)\b.*\b(what|which|how)\b", 2),
    ],
    "occasion_suitability": [
        (r"\b(suitable|right|appropriate|good) for\b.*\b(occasion|event|wedding|party|office)\b", 2),
        (r"\bwill (this|it) (work|look good|suit|be appropriate) for\b", 3),
    ],
    "social_validation": [
        (r"\bwhat do (you|others|people) think\b", 3),
        (r"\b(opinion|feedback|suggestion|recommend)\b", 2),
        (r"\bfriend(s)?\b.*\b(said|think|opinion|told)\b", 2),
        (r"\b(help me|help choosing|help decide)\b", 2),
    ],
    "brand_uncertainty": [
        (r"\b(never|not) (heard of|tried|used)\b.*\bbrand\b", 3),
        (r"\bbrand\b.*\b(unknown|new|unfamiliar|reliable|trustworthy)\b", 2),
        (r"\bis\b.*\bbrand\b.*\b(good|reliable|authentic)\b", 2),
    ],
    "seller_uncertainty": [
        (r"\bseller\b.*\b(fake|fraud|unreliable|unknown|genuine)\b", 3),
        (r"\bthird party (seller|vendor)\b", 2),
    ],
    "payment_or_checkout": [
        (r"\b(payment|checkout|pay)\b.*\b(issue|fail|error|problem|stuck)\b", 3),
        (r"\bCOD\b.*\bnot available\b", 2),
        (r"\b(UPI|card|payment method)\b.*\b(fail|error|issue|not working)\b", 3),
    ],
}

# --- Step 3: Uncertainty Patterns ---
UNCERTAINTY_PATTERNS = {
    "will_it_fit": [
        (r"\bwill (it|this) fit\b", 4),
        (r"\bfit\b.*\b(unsure|worried|not sure|don't know|concern)\b", 3),
        (r"\bhow (does|will) (it|this) fit\b", 3),
        (r"\bfitting\b.*\b(issue|concern|problem)\b", 2),
    ],
    "which_size_should_i_buy": [
        (r"\b(which|what) size (should|do|to)\b", 4),
        (r"\bsize\b.*\b(confus|unsure|which|not sure|don't know)\b", 3),
        (r"\bsize (guide|chart)\b.*\b(wrong|confusing|accurate|reliable)\b", 3),
    ],
    "will_it_suit_me": [
        (r"\bwill (it|this) (suit|look good on|look nice on) me\b", 4),
        (r"\b(suit|look)\b.*\b(my body|body type|skin tone|complexion)\b", 3),
    ],
    "is_quality_good": [
        (r"\b(is|how is) (the|its?) quality\b", 3),
        (r"\bquality\b.*\b(good|how|what|worth|decent|reliable)\b", 2),
        (r"\b(fabric|material)\b.*\b(good|soft|comfortable|worth)\b", 2),
        (r"\bworth (the|its?) (price|money|cost)\b", 2),
    ],
    "is_it_worth_the_price": [
        (r"\bworth (the|it|buying|ordering|the price|the money)\b", 3),
        (r"\bvalue for money\b", 3),
        (r"\boverpriced\b", 2),
        (r"\b(is it|is this) worth\b", 3),
    ],
    "will_price_drop": [
        (r"\bprice (drop|reduce|go down|decrease)\b", 3),
        (r"\bwill (price|it) (drop|reduce|go down|come down)\b", 3),
        (r"\bwait(ing)? for (price|it) to (drop|reduce|come down)\b", 4),
    ],
    "can_i_trust_reviews": [
        (r"\breviews?\b.*\b(fake|paid|trust|reliable|genuine|real)\b", 3),
        (r"\bcan (i|we|you) trust\b.*\breviews?\b", 4),
        (r"\b(honest|genuine|real) reviews?\b", 2),
    ],
    "which_product_is_better": [
        (r"\bwhich (one|is|product) (is )?(better|best)\b", 3),
        (r"\bbetter\b.*\b(option|choice|product|between)\b", 2),
        (r"\bcan't (decide|choose)\b", 2),
    ],
    "is_it_right_for_my_occasion": [
        (r"\b(right|suitable|appropriate|good) for\b.*\b(occasion|event|wedding|party)\b", 3),
        (r"\bwill (it|this) work for\b.*\b(wedding|party|office|event)\b", 3),
    ],
    "how_should_i_style_it": [
        (r"\bhow (to|should i|do i) (style|wear|pair|match)\b", 3),
        (r"\bstyle\b.*\b(tips|advice|suggestion|help|ideas)\b", 2),
    ],
    "will_it_arrive_on_time": [
        (r"\b(deliver|arrive|reach|ship)\b.*\b(on time|before|by|when)\b", 3),
        (r"\bdelivery\b.*\b(time|date|days|when|how long)\b", 2),
    ],
    "can_i_return_it": [
        (r"\bcan (i|we) return\b", 3),
        (r"\breturn\b.*\b(policy|possible|easy|if|can)\b", 2),
        (r"\b(refund|exchange)\b.*\b(possible|easy|if|policy)\b", 2),
    ],
    "will_it_be_available_later": [
        (r"\b(available|back in stock)\b.*\b(later|again|soon|when)\b", 3),
        (r"\bwill (it|this) be available\b", 3),
    ],
    "is_the_brand_reliable": [
        (r"\b(is|are)\b.*\bbrand\b.*\b(reliable|good|authentic|genuine|trustworthy)\b", 3),
        (r"\bbrand\b.*\b(reliable|trust|authentic|genuine|unknown)\b", 2),
    ],
}

# --- Step 4: External Research Patterns ---
EXTERNAL_RESEARCH_PATTERNS = {
    "youtube": [(r"\byoutube\b|\byou tube\b|\byt\b.*\b(video|review)\b", 3)],
    "reddit": [(r"\breddit\b|\bsubreddit\b", 3)],
    "instagram": [(r"\binsta(gram)?\b|\breels?\b|\binfluencer\b", 2)],
    "google_search": [(r"\bgoogle[d]?\b|\bsearch(ed)?\b.*\b(online|for|reviews?)\b", 2)],
    "influencer_content": [
        (r"\b(influencer|blogger|vlogger|creator|youtuber)\b", 3),
        (r"\b(haul|try.on|unboxing)\b.*\b(video|review)\b", 2),
    ],
    "friends_or_family": [
        (r"\b(friend|family|mom|dad|sister|brother|wife|husband|colleague)\b.*\b(said|told|suggest|recommend|ask)\b", 3),
        (r"\bask(ed)?\b.*\b(friend|family|opinion)\b", 2),
    ],
    "other_marketplace": [
        (r"\b(amazon|flipkart|meesho|myntra|ajio|tata cliq|nykaa)\b.*\b(also|check|compare|better|same)\b", 2),
        (r"\bcheaper (on|at|in)\b", 2),
    ],
    "brand_website": [(r"\b(brand|official) (website|site|store)\b", 2)],
    "offline_store": [(r"\b(store|shop|offline|showroom|try in store|try before)\b", 2)],
    "reviews_only": [(r"\b(read|check|saw|see)\b.*\breviews?\b", 2)],
}

EXTERNAL_INFO_NEED_PATTERNS = {
    "real-life product appearance": [(r"\b(real|actual|in person|irl)\b.*\b(look|photo|image|picture)\b", 3)],
    "fit validation": [(r"\bfit\b.*\b(review|check|see|validate|confirm)\b", 2)],
    "quality validation": [(r"\bquality\b.*\b(check|review|validate|see|verify)\b", 2)],
    "styling inspiration": [(r"\b(style|styling|outfit|pair)\b.*\b(ideas?|inspiration|tips?|how)\b", 2)],
    "price comparison": [(r"\b(price|cheaper|expensive)\b.*\b(compare|other|different|amazon|flipkart)\b", 2)],
    "social validation": [(r"\b(opinion|think|suggest|recommend|feedback)\b", 1)],
    "long-term product review": [(r"\b(long term|after|months?|weeks?|durabilit)\b.*\b(review|use|quality)\b", 3)],
    "brand trust": [(r"\bbrand\b.*\b(trust|reliable|genuine|authentic|real)\b", 2)],
    "size guidance": [(r"\bsize\b.*\b(guide|chart|help|which|what|correct|right)\b", 2)],
}

# --- Step 5: Comparison Patterns ---
COMPARISON_PATTERNS = {
    "comparing_multiple_products": [
        (r"\b(compare|comparing|which one|between these|shortlist)\b", 2),
        (r"\bvs\b|\bversus\b", 3),
    ],
    "comparing_brands": [
        (r"\b(myntra|ajio|flipkart|meesho|amazon|tata cliq|h&m|zara|bewakoof)\b.*\bvs\b", 3),
        (r"\b(myntra|ajio|flipkart)\b.*\b(better|worse|prefer|compared)\b", 2),
    ],
    "comparing_prices": [
        (r"\b(price|cheaper|expensive|cost)\b.*\b(compare|other|different|vs|than)\b", 3),
    ],
    "comparing_reviews": [
        (r"\breviews?\b.*\b(compare|better|mixed|different)\b", 2),
    ],
    "comparing_sizes": [
        (r"\bsize\b.*\b(different|varies?|brand|compare)\b", 2),
    ],
    "comparing_marketplaces": [
        (r"\b(myntra|ajio|flipkart|amazon|meesho|tata cliq)\b.*\b(vs|or|better|compare|compared)\b.*\b(myntra|ajio|flipkart|amazon|meesho|tata cliq)\b", 4),
        (r"\b(same|this) (product|item)\b.*\b(on|at|in)\b.*\b(myntra|ajio|flipkart|amazon)\b", 3),
    ],
}

# --- Step 6: Delay Patterns ---
DELAY_PATTERNS = {
    "waiting_for_sale": [
        (r"\bwait(ing)? for.*(sale|EORS|big bold|big fashion|end of reason)\b", 4),
    ],
    "waiting_for_price_drop": [
        (r"\bwait(ing)? for.*(price drop|price to drop|price reduce|price to come down)\b", 4),
    ],
    "waiting_for_payday": [
        (r"\b(payday|salary|next month|pay day)\b", 3),
        (r"\b(can't afford|no money|tight budget)\b.*\b(now|right now|currently)\b", 2),
    ],
    "waiting_for_occasion": [
        (r"\bwait(ing)? (for|until|till)\b.*\b(occasion|event|wedding|party|function)\b", 3),
    ],
    "waiting_for_reviews": [
        (r"\bwait(ing)? for\b.*\b(reviews?|feedback|ratings?)\b", 4),
        (r"\b(no|few|not enough) reviews?\b", 2),
    ],
    "waiting_for_stock": [
        (r"\bwait(ing)? for\b.*\b(stock|restock|available|back in stock)\b", 4),
    ],
    "waiting_for_size": [
        (r"\bwait(ing)? for\b.*\b(size|my size)\b", 4),
        (r"\bsize\b.*\bnot available\b", 3),
    ],
    "comparing_options": [
        (r"\b(still|busy|currently)\b.*\b(comparing|deciding|choosing|looking|exploring)\b", 3),
    ],
    "seeking_validation": [
        (r"\b(ask|asking|need|want)\b.*\b(opinion|advice|suggestion|validation|feedback)\b", 3),
    ],
    "unsure_about_fit": [
        (r"\b(unsure|not sure|worried|concern)\b.*\bfit\b", 3),
        (r"\bfit\b.*\b(unsure|not sure|worried|concern|risk)\b", 3),
    ],
    "unsure_about_quality": [
        (r"\b(unsure|not sure|worried|concern|doubt)\b.*\bquality\b", 3),
        (r"\bquality\b.*\b(unsure|not sure|worried|doubt|questionable)\b", 3),
    ],
    "unsure_about_value": [
        (r"\b(unsure|not sure|worth)\b.*\b(value|money|price|cost)\b", 2),
    ],
    "not_urgent": [
        (r"\bno (rush|hurry|urgency)\b", 3),
        (r"\bnot urgent\b", 3),
    ],
    "bookmarking_only": [
        (r"\bjust (saved?|bookmarked?|liked|browsing)\b", 3),
    ],
}

# --- Step 9: Wishlist Mode Patterns ---
WISHLIST_MODE_PATTERNS = {
    "genuine_purchase_intent": [
        (r"\b(buying|ordered|purchased|bought|going to buy|will buy|must buy|need to buy)\b", 3),
        (r"\b(placed|placing|making|made)\b.*\border\b", 3),
    ],
    "likely_purchase_intent": [
        (r"\b(want|planning|thinking|considering|might) (to )?(buy|order|purchase|get)\b", 2),
        (r"\b(interested|looking to buy|need)\b", 1),
    ],
    "comparison_tool": [
        (r"\b(comparing|shortlisting|deciding between|which one)\b", 3),
    ],
    "sale_tracking": [
        (r"\b(wait|track|alert)\b.*\b(sale|discount|price drop|deal|offer)\b", 3),
        (r"\b(notify|notification)\b.*\b(price|sale|discount)\b", 3),
    ],
    "inspiration_board": [
        (r"\b(inspiration|ideas|exploring|browsing|fashion ideas)\b", 2),
        (r"\bjust (browsing|exploring|looking around)\b", 3),
    ],
    "simple_bookmark": [
        (r"\bjust (saved?|bookmarked?|liked)\b", 3),
        (r"\bsave for (later|reference)\b", 2),
    ],
    "future_need": [
        (r"\b(later|future|someday|one day|eventually)\b", 1),
        (r"\b(for|during|in)\b.*\b(future|later|next|upcoming)\b", 2),
    ],
}


# ═══════════════════════════════════════════════════════════════════════════
# Classification Engine
# ═══════════════════════════════════════════════════════════════════════════

class BehavioralClassifier:
    """12-step behavioral classification engine."""

    def __init__(self):
        # Pre-compile all patterns
        self._compiled = {}
        pattern_groups = {
            "wishlist": WISHLIST_INTENT_PATTERNS,
            "barrier": BARRIER_PATTERNS,
            "uncertainty": UNCERTAINTY_PATTERNS,
            "external": EXTERNAL_RESEARCH_PATTERNS,
            "ext_need": EXTERNAL_INFO_NEED_PATTERNS,
            "comparison": COMPARISON_PATTERNS,
            "delay": DELAY_PATTERNS,
            "mode": WISHLIST_MODE_PATTERNS,
        }
        for group_name, group_patterns in pattern_groups.items():
            self._compiled[group_name] = {}
            for category, patterns in group_patterns.items():
                compiled_list = []
                for pattern_str, weight in patterns:
                    try:
                        compiled_list.append((re.compile(pattern_str, re.IGNORECASE), weight))
                    except re.error:
                        logger.warning(f"Failed to compile pattern: {pattern_str}")
                self._compiled[group_name][category] = compiled_list

    def _match_patterns(self, text: str, group: str) -> Dict[str, float]:
        """Match text against a pattern group. Returns {category: score}."""
        scores = {}
        for category, patterns in self._compiled[group].items():
            total = 0.0
            for regex, weight in patterns:
                if regex.search(text):
                    total += weight
            if total > 0:
                scores[category] = total
        return scores

    def _best_match(self, scores: Dict[str, float], default: str = "unclear") -> str:
        """Return the category with the highest score, or default."""
        if not scores:
            return default
        return max(scores, key=scores.get)

    def _top_matches(self, scores: Dict[str, float], threshold: float = 1.0) -> List[str]:
        """Return all categories above the threshold, sorted by score."""
        return [k for k, v in sorted(scores.items(), key=lambda x: x[1], reverse=True) if v >= threshold]

    def _extract_evidence(self, text: str, max_len: int = 200) -> str:
        """Extract the most informative sentence as evidence."""
        sentences = re.split(r'[.!?\n]+', text)
        if not sentences:
            return text[:max_len]

        # Score each sentence by keyword density
        keywords = [
            "size", "fit", "quality", "price", "return", "refund", "delivery",
            "order", "buy", "purchase", "review", "discount", "sale", "exchange",
            "wrong", "issue", "problem", "wait", "compare", "expensive",
        ]
        best_sentence = ""
        best_score = -1
        for sent in sentences:
            sent = sent.strip()
            if len(sent) < 10:
                continue
            score = sum(1 for kw in keywords if kw in sent.lower())
            score += len(sent) / 500  # Slight preference for longer sentences
            if score > best_score:
                best_score = score
                best_sentence = sent
        return best_sentence[:max_len] if best_sentence else text[:max_len]

    # ── Step 1: Wishlist Intent ────────────────────────────────────────────

    def classify_wishlist_intent(self, text: str) -> Tuple[str, str]:
        """Returns (wishlist_intent, purchase_intent_strength)."""
        scores = self._match_patterns(text, "wishlist")
        intent = self._best_match(scores, "unclear")

        # Determine purchase intent strength
        high_intent = {"purchase_later", "waiting_for_stock"}
        medium_intent = {"waiting_for_discount", "comparison_shortlist",
                         "occasion_planning", "waiting_for_more_information"}
        low_intent = {"inspiration_or_discovery", "gift_or_future_need"}
        no_intent = {"bookmarking_only"}

        if intent in high_intent:
            strength = "high"
        elif intent in medium_intent:
            strength = "medium"
        elif intent in low_intent:
            strength = "low"
        elif intent in no_intent:
            strength = "no_clear_purchase_intent"
        else:
            # Infer from text signals
            buy_signals = len(re.findall(
                r"\b(buy|order|purchase|need|want|get|must have)\b", text, re.IGNORECASE
            ))
            if buy_signals >= 3:
                strength = "high"
            elif buy_signals >= 1:
                strength = "medium"
            else:
                strength = "unclear"

        return intent, strength

    # ── Step 2: Purchase Barriers ──────────────────────────────────────────

    def classify_barriers(self, text: str) -> Tuple[str, List[str]]:
        """Returns (primary_barrier, [secondary_barriers])."""
        scores = self._match_patterns(text, "barrier")
        if not scores:
            return "no_clear_barrier", []

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        primary = ranked[0][0]
        secondary = [k for k, v in ranked[1:] if v >= 2.0]
        return primary, secondary

    # ── Step 3: Remaining Uncertainty ──────────────────────────────────────

    def classify_uncertainty(self, text: str) -> Tuple[List[str], str]:
        """Returns ([uncertainty_categories], uncertainty_summary)."""
        scores = self._match_patterns(text, "uncertainty")
        categories = self._top_matches(scores, threshold=2.0)

        if not categories:
            # Check for general uncertainty signals
            if re.search(r"\b(not sure|unsure|confused|don't know|worried|concern)\b",
                         text, re.IGNORECASE):
                categories = ["other"]
            else:
                categories = ["no_clear_uncertainty"]

        # Generate summary
        summary = self._generate_uncertainty_summary(text, categories)
        return categories, summary

    def _generate_uncertainty_summary(self, text: str, categories: List[str]) -> str:
        """Generate a natural language uncertainty summary."""
        if "no_clear_uncertainty" in categories:
            return "No clear uncertainty detected in this conversation."

        summaries = {
            "will_it_fit": "Unsure whether the product will fit correctly",
            "which_size_should_i_buy": "Confused about which size to select",
            "will_it_suit_me": "Uncertain whether the product will look good on them",
            "is_quality_good": "Questioning whether the product quality meets expectations",
            "is_it_worth_the_price": "Uncertain whether the product is worth the price",
            "will_price_drop": "Wondering if the price will drop soon",
            "can_i_trust_reviews": "Doubting the reliability of product reviews",
            "which_product_is_better": "Unable to decide between multiple products",
            "is_it_right_for_my_occasion": "Unsure if the product suits the intended occasion",
            "how_should_i_style_it": "Needs guidance on how to style the product",
            "will_it_arrive_on_time": "Concerned about delivery timing",
            "can_i_return_it": "Worried about the return/exchange process",
            "will_it_be_available_later": "Concerned about future stock availability",
            "is_the_brand_reliable": "Questioning the brand's reliability",
            "other": "General uncertainty about the purchase decision",
        }

        parts = [summaries.get(c, c.replace("_", " ")) for c in categories[:3]]
        return ". ".join(parts) + "."

    # ── Step 4: External Research ──────────────────────────────────────────

    def classify_external_research(self, text: str) -> Tuple[List[str], List[str]]:
        """Returns ([research_behaviors], [information_needs])."""
        r_scores = self._match_patterns(text, "external")
        behaviors = self._top_matches(r_scores, threshold=1.0)
        if not behaviors:
            behaviors = ["none_detected"]

        n_scores = self._match_patterns(text, "ext_need")
        needs = self._top_matches(n_scores, threshold=1.0)

        return behaviors, needs

    # ── Step 5: Comparison Behavior ────────────────────────────────────────

    def classify_comparison(self, text: str) -> Tuple[str, str]:
        """Returns (comparison_behavior, comparison_context)."""
        scores = self._match_patterns(text, "comparison")
        behavior = self._best_match(scores, "no_comparison_detected")

        context = ""
        if behavior != "no_comparison_detected":
            # Extract comparison context
            brands_found = re.findall(
                r"\b(myntra|ajio|flipkart|amazon|meesho|tata cliq|h&m|zara|bewakoof|nykaa)\b",
                text, re.IGNORECASE
            )
            products = re.findall(
                r"\b(dress|shirt|jeans|kurta|shoes|sneakers|top|saree|lehenga|jacket)\b",
                text, re.IGNORECASE
            )
            if brands_found:
                context = f"Comparing across: {', '.join(set(b.title() for b in brands_found))}"
            if products:
                context += f". Products: {', '.join(set(p.lower() for p in products[:3]))}"
            if not context:
                context = "Comparing options before purchase decision"

        return behavior, context.strip()

    # ── Step 6: Delay Behavior ─────────────────────────────────────────────

    def classify_delay(self, text: str) -> Tuple[str, str]:
        """Returns (delay_reason, delay_strength)."""
        scores = self._match_patterns(text, "delay")
        reason = self._best_match(scores, "no_delay_detected")

        # Determine delay strength
        if reason == "no_delay_detected":
            strength = "none"
        else:
            top_score = max(scores.values()) if scores else 0
            if top_score >= 4:
                strength = "strong"
            elif top_score >= 3:
                strength = "moderate"
            elif top_score >= 2:
                strength = "weak"
            else:
                strength = "unclear"

        return reason, strength

    # ── Step 7: Underlying User Need ───────────────────────────────────────

    def classify_user_need(self, text: str, barrier: str,
                            uncertainties: List[str]) -> Tuple[str, str]:
        """Infer user need from barrier + uncertainty cross-signals."""
        need_mapping = {
            "price": "price_confidence",
            "waiting_for_discount": "price_confidence",
            "fit": "fit_confidence",
            "sizing": "size_guidance",
            "product_quality": "quality_confidence",
            "review_uncertainty": "review_confidence",
            "trust": "trust",
            "insufficient_information": "decision_support",
            "product_comparison": "easier_comparison",
            "too_many_choices": "easier_comparison",
            "stock_availability": "stock_visibility",
            "delivery": "delivery_confidence",
            "returns": "return_confidence",
            "styling_uncertainty": "styling_guidance",
            "occasion_suitability": "occasion_guidance",
            "social_validation": "social_validation",
            "brand_uncertainty": "trust",
            "seller_uncertainty": "trust",
            "payment_or_checkout": "no_clear_need",
            "no_clear_barrier": "no_clear_need",
        }

        # Primary need from barrier
        need = need_mapping.get(barrier, "no_clear_need")

        # Refine with uncertainties
        unc_need_mapping = {
            "will_it_fit": "fit_confidence",
            "which_size_should_i_buy": "size_guidance",
            "is_quality_good": "quality_confidence",
            "is_it_worth_the_price": "price_confidence",
            "can_i_trust_reviews": "review_confidence",
            "which_product_is_better": "easier_comparison",
            "how_should_i_style_it": "styling_guidance",
            "is_it_right_for_my_occasion": "occasion_guidance",
            "is_the_brand_reliable": "trust",
            "will_it_arrive_on_time": "delivery_confidence",
            "can_i_return_it": "return_confidence",
        }

        for unc in uncertainties:
            if unc in unc_need_mapping:
                need = unc_need_mapping[unc]
                break

        # Generate need summary
        need_summaries = {
            "price_confidence": "User needs more confidence that the price is fair or will not drop further",
            "fit_confidence": "User needs more confidence that the selected size will fit before committing",
            "size_guidance": "User needs clearer size guidance to select the correct size",
            "quality_confidence": "User needs validation that the product quality matches expectations",
            "review_confidence": "User needs trustworthy reviews to feel confident about the purchase",
            "trust": "User needs to trust the platform, brand, or seller before purchasing",
            "easier_comparison": "User needs help comparing options to make a decision",
            "decision_support": "User needs more information to make a confident purchase decision",
            "styling_guidance": "User needs styling guidance for the product",
            "occasion_guidance": "User needs to know if the product is appropriate for their occasion",
            "social_validation": "User needs external opinions to validate their purchase decision",
            "stock_visibility": "User needs visibility into stock availability or restock timing",
            "delivery_confidence": "User needs confidence that the product will be delivered correctly and on time",
            "return_confidence": "User needs assurance that returns and exchanges will be hassle-free",
            "personalization": "User needs personalized product recommendations",
            "product_discovery": "User is discovering products and exploring options",
            "no_clear_need": "No specific unmet need clearly identified",
        }

        summary = need_summaries.get(need, "Underlying need not clearly identifiable")
        return need, summary

    # ── Step 8: Purchase Impact ────────────────────────────────────────────

    def classify_purchase_impact(self, barrier: str, delay_strength: str,
                                  uncertainties: List[str],
                                  intent_strength: str) -> str:
        """Estimate purchase impact from other signals."""
        blocking_barriers = {
            "trust", "stock_availability", "payment_or_checkout",
            "delivery", "returns",
        }
        strong_barriers = {
            "price", "fit", "sizing", "product_quality",
            "waiting_for_discount",
        }

        if barrier in blocking_barriers and delay_strength in ("strong", "moderate"):
            return "blocks_purchase"
        if barrier in blocking_barriers:
            return "significantly_delays_purchase"
        if barrier in strong_barriers and delay_strength == "strong":
            return "significantly_delays_purchase"
        if barrier in strong_barriers:
            return "moderately_delays_purchase"
        if barrier == "no_clear_barrier":
            if intent_strength in ("high", "medium"):
                return "no_clear_impact"
            return "unclear"
        if len([u for u in uncertainties if u != "no_clear_uncertainty"]) >= 2:
            return "moderately_delays_purchase"
        if delay_strength in ("weak", "none"):
            return "minor_friction"
        return "moderately_delays_purchase"

    # ── Step 9: Wishlist Mode ──────────────────────────────────────────────

    def classify_wishlist_mode(self, text: str, intent: str,
                                strength: str) -> str:
        """Classify wishlist usage mode."""
        scores = self._match_patterns(text, "mode")
        mode = self._best_match(scores, "unclear")

        # Cross-validate with intent
        if mode == "unclear":
            if strength == "high":
                mode = "genuine_purchase_intent"
            elif strength == "medium":
                mode = "likely_purchase_intent"
            elif intent == "waiting_for_discount":
                mode = "sale_tracking"
            elif intent == "comparison_shortlist":
                mode = "comparison_tool"
            elif intent == "inspiration_or_discovery":
                mode = "inspiration_board"
            elif intent == "bookmarking_only":
                mode = "simple_bookmark"
            elif intent == "gift_or_future_need":
                mode = "future_need"

        return mode

    # ── Step 10: Shopper Segment ───────────────────────────────────────────

    def classify_segment(self, intent: str, barrier: str,
                          uncertainties: List[str], mode: str,
                          research: List[str]) -> str:
        """Assign a preliminary shopper segment via multi-signal voting."""
        votes = {}

        # Intent-based voting
        intent_votes = {
            "waiting_for_discount": "deal_seeker",
            "purchase_later": "high_intent_decider",
            "comparison_shortlist": "comparison_shopper",
            "occasion_planning": "occasion_shopper",
            "inspiration_or_discovery": "inspiration_browser",
        }
        if intent in intent_votes:
            seg = intent_votes[intent]
            votes[seg] = votes.get(seg, 0) + 2

        # Barrier-based voting
        barrier_votes = {
            "price": "deal_seeker",
            "waiting_for_discount": "deal_seeker",
            "fit": "fit_sensitive_shopper",
            "sizing": "fit_sensitive_shopper",
            "product_quality": "review_dependent_shopper",
            "review_uncertainty": "review_dependent_shopper",
            "trust": "review_dependent_shopper",
            "social_validation": "social_validation_shopper",
            "styling_uncertainty": "occasion_shopper",
            "occasion_suitability": "occasion_shopper",
            "delivery": "convenience_focused_shopper",
            "returns": "convenience_focused_shopper",
            "product_comparison": "comparison_shopper",
            "too_many_choices": "comparison_shopper",
        }
        if barrier in barrier_votes:
            seg = barrier_votes[barrier]
            votes[seg] = votes.get(seg, 0) + 2

        # Uncertainty-based voting
        for unc in uncertainties:
            if unc in ("will_it_fit", "which_size_should_i_buy"):
                votes["fit_sensitive_shopper"] = votes.get("fit_sensitive_shopper", 0) + 1
            elif unc in ("is_quality_good", "can_i_trust_reviews"):
                votes["review_dependent_shopper"] = votes.get("review_dependent_shopper", 0) + 1
            elif unc in ("is_it_worth_the_price", "will_price_drop"):
                votes["deal_seeker"] = votes.get("deal_seeker", 0) + 1
            elif unc in ("is_it_right_for_my_occasion", "how_should_i_style_it"):
                votes["occasion_shopper"] = votes.get("occasion_shopper", 0) + 1
            elif unc == "which_product_is_better":
                votes["comparison_shopper"] = votes.get("comparison_shopper", 0) + 1

        # Research-based voting
        if any(r in research for r in ["youtube", "instagram", "influencer_content"]):
            votes["social_validation_shopper"] = votes.get("social_validation_shopper", 0) + 1

        # Mode-based voting
        if mode in ("inspiration_board", "simple_bookmark"):
            votes["inspiration_browser"] = votes.get("inspiration_browser", 0) + 1
        elif mode == "genuine_purchase_intent":
            votes["high_intent_decider"] = votes.get("high_intent_decider", 0) + 1

        if not votes:
            return "uncertain_or_mixed"

        # Return winner, or uncertain if no clear winner
        ranked = sorted(votes.items(), key=lambda x: x[1], reverse=True)
        if len(ranked) >= 2 and ranked[0][1] == ranked[1][1]:
            return "uncertain_or_mixed"

        return ranked[0][0]

    # ── New Step: Wishlist Relevance ───────────────────────────────────────

    def classify_wishlist_relevance(self, text: str, intent_strength: str, barrier: str) -> str:
        """Classify how relevant the record is to wishlist behavior."""
        explicit_patterns = [
            r"\bwishlist\b", r"\bsaved item", r"\bsaved for later", 
            r"\bshortlisted\b", r"\bfavorites\b", r"\bwaiting to buy\b", 
            r"\btracking a saved", r"\bsaved it\b", r"\bbookmarked\b"
        ]
        
        # Check for explicit wishlist statements
        for pat in explicit_patterns:
            if re.search(pat, text, re.IGNORECASE):
                return "explicit_wishlist"
                
        # If not explicit, check for strong purchase consideration (e.g. they want it but hit a barrier)
        if intent_strength in ("high", "medium") and barrier != "no_clear_barrier":
            return "strong_purchase_consideration"
            
        if intent_strength in ("high", "medium"):
            return "indirect_relevance"
            
        return "general_shopping_feedback"

    # ── New Step: Explicit vs AI Inferred ──────────────────────────────────

    def extract_signal_types(self, text: str, primary_barrier: str, intent: str) -> Tuple[str, str]:
        """Determine what was explicitly stated vs what AI inferred."""
        explicit = []
        inferred = []
        
        # Check explicit intent
        if re.search(r"\b(buy|purchase|order|saved|wishlist)\b", text, re.IGNORECASE):
            explicit.append(intent)
        else:
            if intent != "unclear":
                inferred.append(intent)
                
        # Check explicit barrier
        barrier_keywords = {
            "price": r"\b(price|expensive|cost)\b",
            "fit": r"\b(fit|tight|loose)\b",
            "sizing": r"\b(size|chart)\b",
            "product_quality": r"\b(quality|material|fabric)\b",
            "returns": r"\b(return|refund)\b",
            "delivery": r"\b(delivery|shipping)\b",
        }
        
        if primary_barrier != "no_clear_barrier":
            pat = barrier_keywords.get(primary_barrier, r"\b" + primary_barrier.replace("_", " ") + r"\b")
            if re.search(pat, text, re.IGNORECASE):
                explicit.append(primary_barrier)
            else:
                inferred.append(primary_barrier)
                
        explicit_str = ", ".join(explicit) if explicit else "none_explicit"
        inferred_str = ", ".join(inferred) if inferred else "none_inferred"
        
        return explicit_str, inferred_str

    # ── Step 12: Confidence Scoring ────────────────────────────────────────

    def calculate_confidence(self, text: str, barrier: str,
                              intent: str, uncertainties: List[str], relevance: str) -> float:
        """Calculate classification confidence strictly based on explicit signals."""
        confidence = 0.40  # Base for just having text
        
        # Strong explicit wishlist relevancy massively boosts confidence
        if relevance == "explicit_wishlist":
            confidence += 0.30
        elif relevance == "strong_purchase_consideration":
            confidence += 0.20

        # Clear barrier matched with high weight
        if barrier not in ("no_clear_barrier", "other", "unclear"):
            confidence += 0.15

        # Clear intent matched
        if intent != "unclear":
            confidence += 0.10

        # Multiple strict keywords matched
        keyword_count = len(re.findall(
            r"\b(size|fit|quality|price|return|refund|delivery|order|buy|review|"
            r"discount|exchange|expensive|cheap|wrong|issue|problem|trust|compare)\b",
            text, re.IGNORECASE
        ))
        confidence += min(keyword_count * 0.05, 0.25)
        
        # Penalize if it's general feedback and we're trying to extract wishlist insights
        if relevance == "general_shopping_feedback":
            confidence -= 0.20
            
        # Ensure it stays within bounds
        return round(max(0.0, min(confidence, 1.0)), 4)

    # ── Main Classification Entry Point ────────────────────────────────────

    def classify(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Run all 12 classification steps on a single record."""
        text = record.get("comment_text", "")
        if not text:
            return self._empty_classification(record)

        # Step 1: Wishlist intent
        intent, strength = self.classify_wishlist_intent(text)

        # Step 2: Purchase barriers
        primary_barrier, secondary_barriers = self.classify_barriers(text)

        # Step 3: Remaining uncertainty
        uncertainties, uncertainty_summary = self.classify_uncertainty(text)

        # Step 4: External research
        research, info_needs = self.classify_external_research(text)

        # Step 5: Comparison behavior
        comparison, comparison_context = self.classify_comparison(text)

        # Step 6: Delay behavior
        delay_reason, delay_strength = self.classify_delay(text)

        # Step 7: Underlying user need
        user_need, need_summary = self.classify_user_need(
            text, primary_barrier, uncertainties
        )

        # Step 8: Purchase impact
        impact = self.classify_purchase_impact(
            primary_barrier, delay_strength, uncertainties, strength
        )

        # Step 9: Wishlist mode
        mode = self.classify_wishlist_mode(text, intent, strength)

        # Step 10: Shopper segment
        segment = self.classify_segment(
            intent, primary_barrier, uncertainties, mode, research
        )

        # New Step: Wishlist Relevance
        relevance = self.classify_wishlist_relevance(text, strength, primary_barrier)
        
        # New Step: Explicit vs Inferred Signals
        explicit_sig, inferred_sig = self.extract_signal_types(text, primary_barrier, intent)

        # Step 11: Evidence
        evidence = self._extract_evidence(text)

        # Step 12: Confidence
        confidence = self.calculate_confidence(
            text, primary_barrier, intent, uncertainties, relevance
        )

        return {
            "record_id": record.get("record_id", ""),
            "source": record.get("source", ""),
            "source_url": record.get("source_url", ""),
            "original_text": record.get("comment_text", ""),
            "translated_text": record.get("translated_text", ""),
            "wishlist_relevance": relevance,
            "explicit_signal": explicit_sig,
            "ai_inferred_signal": inferred_sig,
            "wishlist_intent": intent,
            "purchase_intent_strength": strength,
            "wishlist_mode": mode,
            "primary_purchase_barrier": primary_barrier,
            "secondary_purchase_barriers": "|".join(secondary_barriers),
            "remaining_uncertainty": "|".join(uncertainties),
            "uncertainty_summary": uncertainty_summary,
            "external_research_behavior": "|".join(research),
            "external_information_need": "|".join(info_needs),
            "comparison_behavior": comparison,
            "comparison_context": comparison_context,
            "purchase_delay_reason": delay_reason,
            "delay_strength": delay_strength,
            "underlying_user_need": user_need,
            "user_need_summary": need_summary,
            "purchase_impact": impact,
            "shopper_segment": segment,
            "evidence_snippet": evidence,
            "classification_confidence": confidence,
        }

    def _empty_classification(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Return empty classification for records with no text."""
        return {
            "record_id": record.get("record_id", ""),
            "source": record.get("source", ""),
            "source_url": record.get("source_url", ""),
            "original_text": "",
            "translated_text": "",
            "wishlist_relevance": "irrelevant_to_wishlist",
            "explicit_signal": "none_explicit",
            "ai_inferred_signal": "none_inferred",
            "wishlist_intent": "unclear",
            "purchase_intent_strength": "unclear",
            "wishlist_mode": "unclear",
            "primary_purchase_barrier": "no_clear_barrier",
            "secondary_purchase_barriers": "",
            "remaining_uncertainty": "no_clear_uncertainty",
            "uncertainty_summary": "Insufficient text for analysis.",
            "external_research_behavior": "none_detected",
            "external_information_need": "",
            "comparison_behavior": "no_comparison_detected",
            "comparison_context": "",
            "purchase_delay_reason": "no_delay_detected",
            "delay_strength": "none",
            "underlying_user_need": "no_clear_need",
            "user_need_summary": "Insufficient text for analysis.",
            "purchase_impact": "unclear",
            "shopper_segment": "uncertain_or_mixed",
            "evidence_snippet": "",
            "classification_confidence": 0.0,
        }

    def classify_all(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Classify all records. Returns list of classified dicts."""
        logger.info(f"Classifier: Processing {len(records)} records")
        results = []
        for i, record in enumerate(records):
            if (i + 1) % 500 == 0:
                logger.info(f"Classifier: Processed {i+1}/{len(records)}")
            results.append(self.classify(record))
        logger.info(f"Classifier: Completed {len(results)} classifications")
        return results
