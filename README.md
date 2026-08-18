# AI-Powered Fashion Wishlist Discovery Engine

## Project Objective
The objective of this project is to understand why users add fashion products to wishlists but do not purchase them within 30 days. The goal is to identify the most significant underlying user problems, quantify them, and propose testable product solutions (experiments) to increase the **30-Day Wishlist-to-Purchase User Conversion Rate**.

## Architecture & Methodology
The project was executed in a 5-phase pipeline, transitioning from raw unstructured data to a prioritized product strategy:

1. **Data Collection**: Scraped ~5,000 public fashion shopping conversations/reviews (focusing on Myntra/AJIO behavior) using `google-play-scraper`.
2. **Behavioral Analysis**: Used a custom rule-based NLP classification engine to structure the text across 12 dimensions (e.g., Wishlist Intent, Purchase Barrier, Remaining Uncertainty). *Note: Due to lack of API keys, a deterministic NLP approach was used over an LLM, achieving high speed and zero cost.*
3. **Opportunity Prioritization**: Grouped behaviors into 9 strategic Opportunity Areas and scored them out of 100 based on Frequency, Purchase Impact, Intent Relevance, Confidence, Segment Breadth, and External Leakage.
4. **Solution Ideation**: Generated testable product hypotheses (UX, Personalization, AI) mapped strictly to the prioritized opportunities, along with A/B experiment designs and guardrail metrics.
5. **Interactive Dashboard**: A custom Single Page Application (SPA) built with Vanilla JavaScript, HTML, CSS, and Chart.js to visualize the complete evidence-to-experiment narrative.

## Data Sources
- **Primary Source**: Google Play Store reviews for top Indian fashion apps (Myntra, AJIO, Nykaa Fashion, etc.).
- **Volume**: 4,927 cleaned and relevance-filtered conversations.

## How to Run the Application
1. Ensure you have Python 3 installed.
2. Open a terminal and navigate to the dashboard directory:
   `cd d:\AI_ENGINE\dashboard`
3. Start the local server:
   `py -3 server.py`
4. Open your browser and navigate to: `http://localhost:8000`

## Key Outputs
- **`classified_fashion_feedback.csv`**: The master dataset of 4,927 structurally classified records.
- **`opportunity_ranking.csv`**: The prioritized list of unmet user needs blocking conversion.
- **`solution_concepts.json`**: Ideated solutions mapped to opportunities, explicitly classifying where AI is actually useful vs unnecessary.
- **`experiment_plans.json`**: Detailed A/B test designs including primary metrics and critical guardrails (e.g., return rates).

## Limitations & Risks
- **Data Proxy Bias**: The discovery relies on public conversations (App Store reviews) which may overrepresent vocal, extreme experiences. It is external qualitative evidence, not a replacement for internal behavioral analytics.
- **Causality vs Correlation**: External research cannot definitively prove causal impact on the 30-day conversion rate. All proposed solutions must be treated as **hypotheses requiring A/B testing** on internal traffic.
