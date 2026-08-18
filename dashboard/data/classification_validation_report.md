# Classification Validation Report

## Summary Metrics

- **Total records classified**: 4927
- **High confidence (>= 0.75)**: 73.84%
- **Low confidence (< 0.60)**: 0.55%
- **With clear purchase barrier**: 65.21%
- **With clear wishlist intent**: 17.43%
- **With clear user need**: 74.08%
- **Logical contradictions found**: 1

## Known Limitations

- Validation is rule-based and may not catch all nuances.
- Sentiment analysis is rudimentary.
- Relies heavily on keyword matching, which can sometimes miss context (e.g. sarcasm).

## Flagged Records (Sample)

- **ID**: ``
  - **Text**: *Giving one start for their return/replacement service which is really pathetic. The product was pick...*
  - **Issues**: Mode is 'simple_bookmark' but impact is 'significantly_delays_purchase'