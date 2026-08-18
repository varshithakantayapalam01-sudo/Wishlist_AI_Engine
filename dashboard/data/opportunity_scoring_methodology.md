# Opportunity Scoring Methodology

Opportunities are scored out of 100 based on a weighted average of 6 dimensions. Each dimension is normalized to a 1-5 scale.

- **Frequency (25%)**: Logarithmic scaling based on dataset percentage relative to the most frequent opportunity.
- **Purchase Impact (25%)**: Weighted average of severity (blocks=5, significant=4, moderate=3, minor=2, unclear=1).
- **High-Intent Relevance (20%)**: Percentage of conversations showing genuine/likely purchase intent.
- **Evidence Confidence (15%)**: Based on average classification confidence, penalized for small sample sizes (<30).
- **Segment Breadth (10%)**: Diversity of shopper segments affected.
- **External Leakage (5%)**: Frequency of users seeking answers off-platform.

## Sensitivity Analysis
We calculated alternative scores weighting Impact heavily (40%) and Frequency heavily (40%). Variations in ranking reflect whether an issue is highly blocking but rare, or common but less severe.
