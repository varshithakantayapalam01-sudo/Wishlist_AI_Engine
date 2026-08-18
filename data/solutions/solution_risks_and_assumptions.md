# Solution Risks and Assumptions

## Why This Might Not Work (Challenge Section)

1. **Assumption**: Wishlist users actually want to buy.
   **Risk**: Users may have fundamentally low purchase intent (using wishlist as an inspiration board). If true, no decision support tool will drive conversion.
   **Validation**: Monitor conversion rate specifically for cohorts explicitly segmented as 'genuine_purchase_intent'.
2. **Assumption**: Information gap causes the delay.
   **Risk**: Price sensitivity may outweigh information improvements. If they just can't afford it, fit guidance won't help.
   **Validation**: Cross-reference conversion lifts against items that are actively discounted.
3. **Assumption**: Users trust our interventions.
   **Risk**: Users may not trust AI recommendations or platform badges, preferring external validation (YouTube, friends).
   **Validation**: Measure click-through rates on interventions vs external outbound leakage.
4. **Assumption**: Resolving friction leads to *kept* purchases.
   **Risk**: The solution could increase initial conversion but drastically increase return rates if the guidance is inaccurate.
   **Validation**: Strict monitoring of 30-day return rate guardrail metric.
5. **Assumption**: Discovery data represents all customers.
   **Risk**: Behavior seen in public App Store conversations may overrepresent vocal, extreme negative experiences and not the silent majority.
   **Validation**: Run the MVP experiment on a broad random sample to establish a true baseline.