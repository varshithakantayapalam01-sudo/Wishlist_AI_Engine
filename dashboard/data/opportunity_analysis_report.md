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
| comparison_shortlist | returns | 15 |
| gift_or_future_need | delivery | 12 |


## Opportunity Comparison Matrix

| Opportunity | Freq | Impact | Intent | Conf | Overall Score | Strength |
|---|---|---|---|---|---|---|
| Delivery & Returns Confidence | 5.0 | 3.5 | 4.1 | 4.4 | **83.72** | strong |
| Stock Availability Visibility | 1.3 | 3.9 | 4.7 | 4.5 | **69.02** | strong |
| Platform & Brand Trust | 1.7 | 4.0 | 4.2 | 4.4 | **68.12** | strong |
| Fit & Sizing Confidence | 1.4 | 3.0 | 4.3 | 4.5 | **64.58** | strong |
| Review & Quality Trust | 1.8 | 2.7 | 3.7 | 4.4 | **62.53** | strong |
| Price & Value Clarity | 1.3 | 2.9 | 3.7 | 4.4 | **60.51** | strong |
| Decision & Comparison Support | 1.1 | 2.4 | 3.8 | 4.4 | **57.08** | directional |
| Social Validation Support | 1.2 | 2.1 | 3.7 | 4.3 | **52.3** | strong |
| Styling & Occasion Guidance | 1.0 | 2.0 | 3.8 | 2.1 | **41.35** | weak |


## Top Opportunity Areas

### Delivery & Returns Confidence
**User problem**: Users block purchases out of fear that delivery will be late or returns will be difficult/rejected.
- **Evidence**: Supported by 2489 conversations (50.52% of dataset)
- **Purchase impact**: Avg severity score 3.5/5.0
- **Evidence strength**: STRONG

**Representative evidence**:
> "Eventhough we raise issue with the team, they are also not sure about the delivery and gives automated messages like they will try to deliver it"
> "First of all they take platform fee and if the seller itself is always sending wrong product on exchange, and you decide to return the product in frustration they still cut the marketfee price from to"
> "I have ordered 3 dresses in different time intervals, everytime the order was confirmed then showed in transit and it's delivery date but as soon as delivery date arrives it shows the order is cancell"

---

### Stock Availability Visibility
**User problem**: Users face friction when items or specific sizes are out of stock, with no visibility on restocks.
- **Evidence**: Supported by 188 conversations (3.82% of dataset)
- **Purchase impact**: Avg severity score 3.9/5.0
- **Evidence strength**: STRONG

**Representative evidence**:
> "Another issue, the expected delivery takes a longer time to deliver"
> "I ordered one shirt and pant on that I got 400 welcome discount"
> "The products are really good but most of them are out of stock and there are multiple problems with this first of all it shows you a delivery date and then the product will be delivered after 5-6 days"

---

### Platform & Brand Trust
**User problem**: Users abandon purchases due to lack of trust in the platform, third-party seller, or unfamiliar brand.
- **Evidence**: Supported by 420 conversations (8.52% of dataset)
- **Purchase impact**: Avg severity score 4.0/5.0
- **Evidence strength**: STRONG

**Representative evidence**:
> "fraud app use traditional built and started with roots platform like amazon and Flipkart this is a faltu app and scam you with elevated price and add 1st time buyer coupon and resultant price would be"
> "2) I believe there is an issue in the app,I was thrilled to see the offer cost at the bottom of the product but when I opened the product it showed a different value on a higher side"
> "even if somehow u tried convincing customer care then whenever u start selecting reason for return then at the final step u see an interface saying "too many attempts from your side " please try later"

---

### Fit & Sizing Confidence
**User problem**: Users frequently postpone purchases because they lack confidence in whether the item will fit them or which size to choose.
- **Evidence**: Supported by 265 conversations (5.38% of dataset)
- **Purchase impact**: Avg severity score 3.0/5.0
- **Evidence strength**: STRONG

**Representative evidence**:
> "I also liked the variety of brands and styles available, making it easy to compare different options before buying"
> "and there was only size exchange option but dude i literally receive wrong product and that also late"
> "worst app for shopping , decided to return an item whose size did not fit but, ajio keeps on initiating no return on its own without my approval or initiation"

---

### Review & Quality Trust
**User problem**: Users hesitate because they cannot trust the product reviews or are uncertain about the actual quality.
- **Evidence**: Supported by 504 conversations (10.23% of dataset)
- **Purchase impact**: Avg severity score 2.7/5.0
- **Evidence strength**: STRONG

**Representative evidence**:
> "Even when I received a different product once, the issue was handled quickly nd I got my refund without any stress"
> "the quality of the product is very good and the delivery is so fast that I cannot expect and the delivery fee is also not more and it looks good no leg in the app the app is very nice there is option "
> "2) I believe there is an issue in the app,I was thrilled to see the offer cost at the bottom of the product but when I opened the product it showed a different value on a higher side"

---

## Limitations and Misleading Conclusions Check
- **Source Bias**: 100% of the dataset originates from Google Play Store reviews. While this captures mobile shopping friction effectively, it may underrepresent deep product exploration behaviors typically seen on desktop web or Reddit/YouTube.
- **AI Inference**: While explicit barriers (e.g. 'bad quality') are directly mapped, 'underlying user needs' are AI-inferred cross-signals and should be treated as directional hypotheses.