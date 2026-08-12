---
okf: "0.1"
id: bidding-strategies
title: Bidding strategies
description: Pricing models and bid optimization options that control how advertisers pay for ad placements.
type: concept
status: active
created: 2026-08-12
updated: 2026-08-12
timestamp: 2026-08-12T15:11:53Z
confidence: high
tags: [bidding, pricing, optimization]
related: [sponsored-products, sponsored-brands, sponsored-display, campaign-structure, acos-roas]
sources:
  - id: S1
    url: https://advertising.amazon.com/library/guides/targeting-with-sponsored-products
    kind: official
    fetched: 2026-08-12
    snapshot: state/cache/targeting-official.txt
  - id: S2
    url: https://advertising.amazon.com/solutions/products/sponsored-brands
    kind: official
    fetched: 2026-08-12
    snapshot: state/cache/sb-official.txt
  - id: S3
    url: https://advertising.amazon.com/solutions/products/sponsored-products
    kind: official
    fetched: 2026-08-12
    snapshot: state/cache/sp-official.txt
---

# Bidding strategies

## Overview

Bidding strategies determine how advertisers pay for ad placements and optimize campaign performance. Different ad products support various pricing models including cost-per-click (CPC), cost per thousand viewable impressions (vCPM), and fixed upfront pricing.

## Key facts

- Dynamic bidding up and down is recommended to help maximize automatic campaign performance. [S1]
- Dynamic down only bidding is recommended for optimizing based on return on ad spend. [S1]
- Sponsored Brands supports multiple pricing models: cost-per-click (CPC), cost per 1,000 viewable impressions (vCPM), and fixed upfront pricing with reserve share of voice. [S2]
- Sponsored Brands uses cost-per-click (CPC) pricing model for driving page visits. [S2]
- Sponsored Brands uses cost per 1,000 viewable impressions (vCPM) pricing model for growing brand impression share. [S2]
- Sponsored Brands uses fixed, upfront pricing with reserve share of voice to secure top-of-search placement for branded keywords. [S2]
- Sponsored Brands has no minimum spend for CPC or vCPM campaigns. [S2]
- Sponsored Brands reserve share of voice requires a minimum spend commitment. [S2]
- Sponsored Brands allows adjusting bids or pausing campaigns at any time. [S2]
- Sponsored Products bidding requires entering a maximum amount willing to pay when a customer clicks an ad. [S3]
- Sponsored Products uses daily budgets that are the amount willing to spend on a campaign over a calendar month. [S3]
- Sponsored Products daily budgets are not paced throughout the day and can be spent quickly if there is high demand. [S3]
- Sponsored Products daily budgets can be increased or decreased once ads are live. [S3]

## Relationships

- [Sponsored Products](/concepts/sponsored-products.md): uses CPC bidding with daily budgets.
- [Sponsored Brands](/concepts/sponsored-brands.md): supports CPC, vCPM, and fixed pricing models.
- [Sponsored Display](/concepts/sponsored-display.md): supports CPC and vCPM bidding.
- [Campaign structure](/concepts/campaign-structure.md): bidding strategies are configured at campaign level.
- [ACOS/ROAS](/concepts/acos-roas.md): advertisers move between bid strategies to hit ACOS targets.
