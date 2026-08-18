"""
Configuration module for the Fashion Shopping Data Collection Pipeline.
Loads API keys from environment variables / .env file and defines all
search queries, relevance keywords, and pipeline settings.
"""

import os
from dotenv import load_dotenv

# Load .env file if present
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

# ---------------------------------------------------------------------------
# API Keys (set via environment variables or .env file)
# ---------------------------------------------------------------------------
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.getenv(
    "REDDIT_USER_AGENT",
    "FashionDataCollector/1.0 (research; fashion shopping behavior)"
)

# ---------------------------------------------------------------------------
# Output paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

RAW_CSV_PATH = os.path.join(DATA_DIR, "raw_fashion_feedback.csv")
CLEAN_CSV_PATH = os.path.join(DATA_DIR, "clean_fashion_feedback.csv")
SUMMARY_JSON_PATH = os.path.join(DATA_DIR, "data_collection_summary.json")
SOURCES_REPORT_PATH = os.path.join(DATA_DIR, "data_sources_report.md")

# ---------------------------------------------------------------------------
# Relevance scoring threshold
# ---------------------------------------------------------------------------
RELEVANCE_THRESHOLD = 0.65
SOURCE_DIVERSITY_CAP = 0.60  # No single source > 60% of final dataset

# ---------------------------------------------------------------------------
# Search queries — organized by category
# ---------------------------------------------------------------------------

MYNTRA_QUERIES = [
    "Myntra wishlist",
    "Myntra wishlist purchase",
    "Myntra waiting for sale",
    "Myntra price drop",
    "Myntra discount",
    "Myntra sizing issue",
    "Myntra size chart",
    "Myntra fit review",
    "Myntra quality review",
    "Myntra return experience",
    "Myntra clothes review",
    "Myntra dress review",
    "Myntra jeans sizing",
    "Myntra haul",
    "Myntra vs AJIO",
    "should I buy from Myntra",
    "Myntra wedding clothes",
    "Myntra outfit review",
    # Semantic variations
    "Myntra size guide accuracy",
    "Myntra worth buying",
    "Myntra sale worth waiting",
    "Myntra product quality honest review",
    "Myntra kurta sizing",
    "Myntra top quality",
    "Myntra shoes fit",
    "Myntra delivery experience India",
    "Myntra exchange policy",
    "Myntra big fashion festival",
    "Myntra end of reason sale",
    "Myntra EORS haul",
]

AJIO_QUERIES = [
    "AJIO wishlist",
    "AJIO waiting for sale",
    "AJIO sizing issue",
    "AJIO size chart",
    "AJIO fit review",
    "AJIO quality",
    "AJIO reviews",
    "AJIO haul",
    "AJIO vs Myntra",
    "should I buy from AJIO",
    # Semantic variations
    "AJIO worth buying",
    "AJIO return experience",
    "AJIO big bold sale",
    "AJIO brand quality",
    "AJIO kurta review",
    "AJIO delivery time",
    "AJIO exchange process",
    "AJIO discount codes",
]

GENERAL_FASHION_QUERIES = [
    "online clothes sizing India",
    "online fashion fit problems",
    "online clothes quality issue",
    "waiting for fashion sale",
    "clothes wishlist sale",
    "fashion purchase decision",
    "clothes shopping regret",
    "fashion product comparison",
    "dress buying advice",
    "which dress should I buy",
    "outfit decision help",
    "online clothing reviews",
    "online shopping size confusion",
    "fashion purchase hesitation",
    "fashion discount waiting",
    "clothes price drop",
    "online fashion trust reviews",
    "fashion social validation",
    "shopping wishlist behavior",
    # Semantic variations
    "online shopping India size issue",
    "online dress quality India",
    "best online shopping app India clothes",
    "online shopping haul India",
    "clothing review honest India",
    "fashion shopping tips India",
    "online vs offline clothes shopping India",
    "hesitant to buy clothes online",
    "scared to buy clothes online India",
    "waiting for sale to buy clothes",
    "added to cart but not buying",
    "online shopping regret India",
    "online clothes too expensive",
    "should I buy this dress",
    "online shopping size chart wrong",
    "fashion app comparison India",
    "Meesho vs Myntra",
    "Flipkart fashion review",
    "Tata CLiQ fashion review",
]

ALL_QUERIES = MYNTRA_QUERIES + AJIO_QUERIES + GENERAL_FASHION_QUERIES

# ---------------------------------------------------------------------------
# Relevance keywords and their weights for scoring
# ---------------------------------------------------------------------------
RELEVANCE_KEYWORDS = {
    # Purchase intent & wishlisting
    "wishlist": 0.15, "wish list": 0.15, "saved": 0.10, "save for later": 0.12,
    "add to cart": 0.10, "added to cart": 0.10, "bookmarked": 0.10,
    "want to buy": 0.12, "planning to buy": 0.12, "thinking of buying": 0.12,

    # Postponing / hesitation
    "waiting": 0.10, "wait for": 0.10, "postpone": 0.12, "later": 0.05,
    "not sure": 0.10, "confused": 0.10, "hesitant": 0.12, "hesitation": 0.12,
    "can't decide": 0.12, "undecided": 0.10, "thinking": 0.05,
    "should I buy": 0.15, "worth buying": 0.12, "worth it": 0.10,

    # Price sensitivity
    "price drop": 0.15, "price": 0.05, "expensive": 0.10, "costly": 0.10,
    "affordable": 0.08, "budget": 0.08, "overpriced": 0.12,
    "discount": 0.10, "sale": 0.08, "offer": 0.06, "coupon": 0.08,
    "deal": 0.06, "EORS": 0.10, "big fashion festival": 0.10,

    # Fit & sizing
    "size": 0.08, "sizing": 0.12, "fit": 0.08, "fitting": 0.10,
    "size chart": 0.15, "size guide": 0.15, "true to size": 0.15,
    "runs small": 0.12, "runs large": 0.12, "loose": 0.06, "tight": 0.06,
    "measurements": 0.10, "body type": 0.08,

    # Quality
    "quality": 0.08, "fabric": 0.10, "material": 0.08, "stitching": 0.10,
    "color difference": 0.12, "looks different": 0.10, "not as shown": 0.12,
    "cheap quality": 0.12, "good quality": 0.08, "poor quality": 0.12,

    # Reviews & trust
    "review": 0.06, "rating": 0.06, "stars": 0.05, "honest review": 0.10,
    "trust": 0.08, "trustworthy": 0.08, "reliable": 0.06, "fake review": 0.12,
    "real review": 0.10, "genuine": 0.06,

    # Returns & delivery
    "return": 0.08, "exchange": 0.08, "refund": 0.10, "replacement": 0.08,
    "delivery": 0.06, "shipping": 0.06, "damaged": 0.08, "wrong product": 0.10,

    # Stock & availability
    "out of stock": 0.12, "sold out": 0.10, "back in stock": 0.10,
    "unavailable": 0.08, "limited stock": 0.08,

    # Styling & occasion
    "styling": 0.08, "style": 0.05, "occasion": 0.08, "wedding": 0.08,
    "party": 0.05, "office wear": 0.08, "casual": 0.04, "formal": 0.06,
    "festive": 0.08, "ethnic": 0.06, "western": 0.05,

    # Comparison & research
    "compare": 0.10, "comparison": 0.10, "vs": 0.08, "versus": 0.08,
    "better": 0.05, "alternative": 0.08, "similar": 0.06, "which one": 0.10,

    # Social validation
    "opinion": 0.08, "suggest": 0.06, "recommendation": 0.08, "advice": 0.08,
    "help me choose": 0.12, "what do you think": 0.10, "friends": 0.05,

    # Brand mentions (context signals)
    "myntra": 0.06, "ajio": 0.06, "flipkart": 0.04, "meesho": 0.04,
    "tata cliq": 0.04, "nykaa fashion": 0.04, "amazon fashion": 0.04,

    # Abandonment
    "abandoned": 0.12, "didn't buy": 0.12, "didn't purchase": 0.12,
    "removed from cart": 0.12, "changed my mind": 0.10, "regret": 0.08,
    "impulse": 0.08,
}

# ---------------------------------------------------------------------------
# Spam / irrelevant patterns to filter out
# ---------------------------------------------------------------------------
SPAM_PATTERNS = [
    r"^(nice|good|great|awesome|amazing|love it|loved it|love this|wow|cool|best)\s*[.!]*$",
    r"^[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\s]+$",
    r"^(first|first comment|first!|hi|hello|hey)\s*[.!]*$",
    r"subscribe.*channel",
    r"check.*(my|out).*channel",
    r"follow me",
    r"earn money",
    r"make money online",
    r"click.*(link|here|bio)",
    r"use.*code.*discount",
    r"dm for",
    r"whatsapp",
    r"https?://bit\.ly",
    r"https?://t\.co",
    r"giveaway",
]

# Minimum comment length to keep (characters)
MIN_COMMENT_LENGTH = 20

# ---------------------------------------------------------------------------
# Google Play Store app IDs for review collection
# ---------------------------------------------------------------------------
PLAYSTORE_APPS = {
    "Myntra": "com.myntra.android",
    "AJIO": "com.ril.ajio",
    "Flipkart": "com.flipkart.android",
    "Meesho": "com.meesho.supply",
    "Tata CLiQ": "com.tul.tatacliq",
    "Nykaa Fashion": "com.fsn.nykaa",
    "Bewakoof": "com.bewakoof.bewakoof",
    "Limeroad": "com.shopping.limeroad",
    "H&M": "com.hm.goe",
    "Max Fashion": "com.landmark.maxfashion",
}

# ---------------------------------------------------------------------------
# Reddit subreddits to search
# ---------------------------------------------------------------------------
REDDIT_SUBREDDITS = [
    "IndianFashionAddicts",
    "india",
    "indianfashion",
    "IndianSkincareAddicts",
    "TwoXIndia",
    "InstaCelebsGossip",
    "delhi",
    "mumbai",
    "bangalore",
    "femalefashionadvice",
    "frugalmalefashion",
]

# ---------------------------------------------------------------------------
# YouTube search settings
# ---------------------------------------------------------------------------
YOUTUBE_MAX_RESULTS_PER_QUERY = 5  # Videos per search query
YOUTUBE_MAX_COMMENTS_PER_VIDEO = 100  # Comments per video
YOUTUBE_REGION_CODE = "IN"  # India
YOUTUBE_RELEVANCE_LANGUAGE = "en"

# ---------------------------------------------------------------------------
# Rate limiting (seconds between requests)
# ---------------------------------------------------------------------------
RATE_LIMITS = {
    "youtube": 0.5,
    "reddit": 1.0,
    "playstore": 2.0,
    "web": 3.0,
}

# ---------------------------------------------------------------------------
# Product categories for inference
# ---------------------------------------------------------------------------
PRODUCT_CATEGORIES = {
    "clothing": ["dress", "top", "shirt", "tshirt", "t-shirt", "kurta", "kurti",
                  "jeans", "trousers", "pants", "leggings", "saree", "sari",
                  "blouse", "jacket", "hoodie", "sweater", "skirt", "shorts",
                  "ethnic wear", "western wear", "co-ord", "jumpsuit", "palazzo",
                  "salwar", "suit", "sherwani", "lehenga", "anarkali", "tunic"],
    "footwear": ["shoes", "sneakers", "heels", "sandals", "boots", "flats",
                  "slippers", "loafers", "sports shoes", "running shoes",
                  "flip flops", "wedges", "stilettos", "mojaris", "juttis"],
    "accessories": ["bag", "handbag", "watch", "belt", "wallet", "sunglasses",
                     "jewelry", "earrings", "necklace", "bracelet", "ring",
                     "clutch", "backpack", "cap", "hat", "scarf", "dupatta"],
    "innerwear": ["bra", "lingerie", "innerwear", "underwear", "boxers",
                   "briefs", "camisole", "slip"],
    "sportswear": ["activewear", "gym wear", "sports", "tracksuit",
                    "track pants", "yoga", "running"],
    "beauty": ["makeup", "lipstick", "foundation", "concealer", "mascara",
                "skincare", "moisturizer", "serum", "sunscreen"],
}
