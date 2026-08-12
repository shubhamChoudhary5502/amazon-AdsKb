---
okf: "0.1"
id: sponsored-products
title: Sponsored Products
description: Amazon's core self-service ad product, promoting individual product listings inside the shopping experience.
type: concept
status: active
created: 2026-08-10
updated: 2026-08-12
timestamp: 2026-08-12T00:00:00Z
confidence: high
tags: [ad-product, ppc, self-service]
related: [bidding-strategies, keyword-match-types, campaign-structure, advertising-eligibility, amazon-ads-api, amazon-marketing-stream]
sources:
  - id: S1
    url: https://advertising.amazon.com/solutions/products/sponsored-products
    kind: official
    fetched: 2026-08-10
    snapshot: sources/samples/official/sponsored-products.html
  - id: S2
    url: https://advertising.amazon.com/solutions/products/sponsored-products
    kind: official
    fetched: 2026-08-12
    snapshot: state/cache/sp-official.txt
---

# Sponsored Products

## Overview

Sponsored Products is Amazon's core self-service ad product. It promotes
individual product listings inside Amazon's shopping experience and is
usually the first ad type an advertiser runs.

## Key facts

- Pricing is cost-per-click: the advertiser pays only when a shopper clicks the ad. [S1][S2]
- Ads appear in shopping results and on product detail pages, as well as on Amazon-owned sites and third-party destinations. [S1][S2]
- Ads are generated from the existing product listing, so no custom copy or images are required. [S1]
- Targeting is either automatic, where Amazon matches ads to queries and products, or manual, where the advertiser picks keywords or products. [S1]
- Campaigns set a daily budget, and the advertiser controls the maximum cost-per-click bid. [S1][S2]
- Ads appear as images or video creatives in shopping results and on product detail pages. [S2]
- Available for professional sellers, vendors, book vendors, Kindle Direct Publishing (KDP) authors, and agencies. [S2]
- Products must be in eligible categories and eligible for the Featured Offer to advertise. [S2]
- No monthly or upfront fees; advertisers bid maximum CPC and set daily budgets. [S2]
- Campaigns with video saw average +9% uplift in click-through rate (CTR) compared to campaigns without video. [S2]
- Daily budgets are not paced throughout the day and represent a monthly calendar commitment. [S2]
- Ads serve on desktop and mobile browsers as well as Amazon mobile app across devices. [S2]
- Adult products, used products, refurbished products, and products in closed categories are not eligible. [S2]

## Relationships

- [Bidding strategies](/concepts/bidding-strategies.md): dynamic bidding options apply to Sponsored Products campaigns.
- [Keyword match types](/concepts/keyword-match-types.md): manual keyword targeting uses these match types.
- [Campaign structure](/concepts/campaign-structure.md): Sponsored Products campaigns follow the standard campaign and ad group hierarchy.
- [Advertising eligibility](/concepts/advertising-eligibility.md): who can run Sponsored Products and what enrollment it needs.
- [Amazon Ads API](/concepts/amazon-ads-api.md): campaign management is available programmatically, including a sandbox.
- [Amazon Marketing Stream](/concepts/amazon-marketing-stream.md): provides near real time metrics and campaign events for Sponsored Products.
