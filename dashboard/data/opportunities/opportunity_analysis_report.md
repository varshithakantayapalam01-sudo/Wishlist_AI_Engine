# Opportunity Analysis Report

## Executive Summary
This report synthesizes unstructured user feedback into prioritized opportunity areas. The goal is to identify the most critical unmet needs and purchase barriers blocking wishlist-to-purchase conversion.
The analysis strictly focuses on *user problems*, avoiding premature feature recommendations.

## Wishlist Intent vs. Purchase Friction Matrix

| Wishlist Intent | Main Barrier | Count |
|---|---|---|
| waiting_for_stock | stock_availability | 116 |
| purchase_later | delivery | 64 |
| purchase_later | returns | 45 |
| purchase_later | trust | 25 |
| waiting_for_discount | trust | 22 |
| occasion_planning | delivery | 19 |
| waiting_for_stock | trust | 17 |
| waiting_for_discount | delivery | 15 |
| purchase_later | product_quality | 11 |
| purchase_later | price | 11 |


## Opportunity Comparison Matrix

| Opportunity | Freq | Impact | Intent | Conf | Overall Score | Strength |
|---|---|---|---|---|---|---|
| Delivery & Returns Confidence | 5.0 | 3.9 | 5.0 | 4.8 | **90.2** | strong |
| Stock Availability Visibility | 1.5 | 4.0 | 5.0 | 4.8 | **72.29** | strong |
| Platform & Brand Trust | 1.9 | 4.0 | 5.0 | 4.7 | **71.98** | strong |
| Review & Quality Trust | 1.6 | 3.1 | 4.9 | 4.8 | **68.58** | strong |
| Price & Value Clarity | 1.3 | 3.1 | 4.9 | 4.8 | **66.86** | strong |
| Fit & Sizing Confidence | 1.4 | 3.1 | 4.9 | 4.9 | **66.64** | strong |
| Decision & Comparison Support | 1.0 | 3.3 | 5.0 | 2.6 | **60.41** | weak |
| Social Validation Support | 1.3 | 2.1 | 4.8 | 4.6 | **57.09** | moderate |
| Styling & Occasion Guidance | 1.0 | 2.0 | 4.2 | 1.6 | **42.25** | weak |


## Top Opportunity Areas

### Delivery & Returns Confidence
**User problem**: Users block purchases out of fear that delivery will be late or returns will be difficult/rejected.
- **Evidence**: Supported by 1393 conversations (28.27% of dataset)
- **Purchase impact**: Avg severity score 3.9/5.0
- **Evidence strength**: STRONG

**Representative evidence**:
> "there's nothing wrong with my account but I often get this issue, I don't even have any returns or anything and I'm one of the so-called "Insider" who has spent a lot on the app"
> "This app attracts customers with low-price offers, takes payment upfront, then delays the order with vague "logistics issues"
> "My order is highly delayed even after choosing express delivery"

---

### Stock Availability Visibility
**User problem**: Users face friction when items or specific sizes are out of stock, with no visibility on restocks.
- **Evidence**: Supported by 161 conversations (3.27% of dataset)
- **Purchase impact**: Avg severity score 4.0/5.0
- **Evidence strength**: STRONG

**Representative evidence**:
> "This app attracts customers with low-price offers, takes payment upfront, then delays the order with vague "logistics issues"
> "absolutely horrible delivery I placed and order twice from 2 different accounts and it was delayed both times, the customer service is also absolutely trash, I'm just not able to chat with anyone, it'"
> "To chk the exchange, the price is 3 times high and product is Out of Stock"

---

### Platform & Brand Trust
**User problem**: Users abandon purchases due to lack of trust in the platform, third-party seller, or unfamiliar brand.
- **Evidence**: Supported by 298 conversations (6.05% of dataset)
- **Purchase impact**: Avg severity score 4.0/5.0
- **Evidence strength**: STRONG

**Representative evidence**:
> "This app attracts customers with low-price offers, takes payment upfront, then delays the order with vague "logistics issues"
> "it's a worst app don't buy products from this, especially imported goods, no proper courier service money will get debited but you won't receive the product no enough employees available to resolve th"
> "If you choose to order, proceed entirely at your own risk regarding whether your package will ever arrive"

---

### Review & Quality Trust
**User problem**: Users hesitate because they cannot trust the product reviews or are uncertain about the actual quality.
- **Evidence**: Supported by 224 conversations (4.55% of dataset)
- **Purchase impact**: Avg severity score 3.1/5.0
- **Evidence strength**: STRONG

**Representative evidence**:
> "Poor product quality, unreliable delivery, and an extremely slow return process make this"
> "Overall, I'm very happy with Myntra and highly recommend it to anyone who loves shopping for quality products at great prices"
> "Even when I received a different product once, the issue was handled quickly nd I got my refund without any stress"

---

### Price & Value Clarity
**User problem**: Users delay buying because they are uncertain if the current price represents good value or if it will drop soon.
- **Evidence**: Supported by 118 conversations (2.39% of dataset)
- **Purchase impact**: Avg severity score 3.1/5.0
- **Evidence strength**: STRONG

**Representative evidence**:
> "They charge very high platform fees, and the worst part is that the platform fee is not refunded when an order is cancelled"
> "Even when I received a different product once, the issue was handled quickly nd I got my refund without any stress"
> "Myntra never seems to deliver good quality products, even after charging high price Every time I buy something I end up having to return it"

---

## Limitations and Misleading Conclusions Check
- **Source Bias**: 100% of the dataset originates from Google Play Store reviews. While this captures mobile shopping friction effectively, it may underrepresent deep product exploration behaviors typically seen on desktop web or Reddit/YouTube.
- **AI Inference**: While explicit barriers (e.g. 'bad quality') are directly mapped, 'underlying user needs' are AI-inferred cross-signals and should be treated as directional hypotheses.