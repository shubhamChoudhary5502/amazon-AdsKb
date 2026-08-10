---
okf: "0.1"
id: sponsored-products
title: Sponsored Products
type: concept
status: active
created: 2026-08-10
updated: 2026-08-10
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

- bidding-strategies: dynamic bidding options apply to Sponsored Products campaigns.
- keyword-match-types: manual keyword targeting uses these match types.
- campaign-structure: Sponsored Products campaigns follow the standard campaign and ad group hierarchy.
- advertising-eligibility: who can run Sponsored Products and what enrollment it needs.
- amazon-ads-api: campaign management is available programmatically, including a sandbox.
