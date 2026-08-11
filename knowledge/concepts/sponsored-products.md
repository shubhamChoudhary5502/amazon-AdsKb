---
okf: "0.1"
id: sponsored-products
title: Sponsored Products
description: Amazon's core self-service ad product, promoting individual product listings inside the shopping experience.
type: concept
status: active
created: 2026-08-10
updated: 2026-08-10
timestamp: 2026-08-10T00:00:00Z
confidence: medium
tags: [ad-product, ppc, self-service]
related: [bidding-strategies, keyword-match-types, campaign-structure, advertising-eligibility, amazon-ads-api]
sources:
  - id: S1
    url: https://advertising.amazon.com/solutions/products/sponsored-products
    kind: official
    fetched: 2026-08-10
    snapshot: sources/samples/official/sponsored-products.html
---

# Sponsored Products

## Overview

Sponsored Products is Amazon's core self-service ad product. It promotes
individual product listings inside Amazon's shopping experience and is
usually the first ad type an advertiser runs.

## Key facts

- Pricing is cost-per-click: the advertiser pays only when a shopper clicks the ad. [S1]
- Ads appear in shopping results and on product detail pages. [S1]
- Ads are generated from the existing product listing, so no custom copy or images are required. [S1]
- Targeting is either automatic, where Amazon matches ads to queries and products, or manual, where the advertiser picks keywords or products. [S1]
- Campaigns set a daily budget, and the advertiser controls the maximum cost-per-click bid. [S1]

## Relationships

- [Bidding strategies](/concepts/bidding-strategies.md): dynamic bidding options apply to Sponsored Products campaigns.
- [Keyword match types](/concepts/keyword-match-types.md): manual keyword targeting uses these match types.
- [Campaign structure](/concepts/campaign-structure.md): Sponsored Products campaigns follow the standard campaign and ad group hierarchy.
- [Advertising eligibility](/concepts/advertising-eligibility.md): who can run Sponsored Products and what enrollment it needs.
- [Amazon Ads API](/concepts/amazon-ads-api.md): campaign management is available programmatically, including a sandbox.
