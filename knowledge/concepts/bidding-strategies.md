---
okf: "0.1"
id: bidding-strategies
title: Bidding strategies
description: Pricing models and bid optimization options that control how advertisers pay for ad placements.
type: concept
status: active
created: 2026-08-12
updated: 2026-08-13
timestamp: 2026-08-13T04:02:43Z
confidence: high
tags: [bidding, pricing, optimization]
related: [sponsored-products, sponsored-brands, sponsored-display, campaign-structure, acos-roas]
sources:
  - id: S1
    url: https://advertising.amazon.com/library/guides/targeting-with-sponsored-products
    kind: official
    fetched: 2026-08-13
    snapshot: state/cache/targeting-official.txt
  - id: S2
    url: https://advertising.amazon.com/solutions/products/sponsored-brands
    kind: official
    fetched: 2026-08-13
    snapshot: state/cache/sb-official.txt
  - id: S3
    url: https://advertising.amazon.com/solutions/products/sponsored-products
    kind: official
    fetched: 2026-08-13
    snapshot: state/cache/sp-official.txt
  - id: S4
    url: https://ppcprotect.com/blog/amazon-ppc-ultimate-guide
    kind: community
    fetched: 2026-08-13
    snapshot: state/cache/ppc-community.txt
---

# Bidding strategies

## Overview

Bidding strategies determine how advertisers pay for ad placements and optimize campaign performance. Different ad products support various pricing models including cost-per-click (CPC), cost per thousand viewable impressions (vCPM), and fixed upfront pricing.

## Key facts

- Sponsored Products campaigns use a daily budget. [S3]
- Sponsored Products advertisers control maximum cost-per-click bid. [S3]
- With Sponsored Products you bid the maximum amount willing to pay when a shopper clicks your ad. [S3]
- A bid in Sponsored Products is the maximum amount you are willing to pay when a customer clicks your ad. [S3]
- The Sponsored Products daily budget is a daily amount willing to spend on a campaign over a calendar month. [S3]
- You can increase or decrease your Sponsored Products daily budget once your ads are live. [S3]
- Sponsored Products daily budgets are not paced throughout the day and can be spent quickly if there is high demand. [S3]
- You control how much you want to spend on bids and budgets and can measure ad performance. [S3]
- With Sponsored Products you pay only for clicks and can refine campaigns using reporting insights. [S3]
- Sponsored Products campaigns have no monthly or upfront fees. [S3]
- More competitive Sponsored Products bids increase likelihood of ad display when matching customer shopping queries. [S3]
- For Sponsored Products you enter a bid for keywords you want to target. [S3]
- For Sponsored Products you set a daily budget for your campaign. [S3]
- The final Sponsored Products cost will never exceed the total amount set for the campaign duration. [S3]
- Dynamic bidding up and down is recommended to help maximize automatic campaign performance. [S1]
- Dynamic down only bidding is recommended for optimizing based on return on ad spend. [S1]
- Automatic targeting campaigns can set a single default bid or set bids by targeting group. [S1]
- Amazon recommends using dynamic bidding up and down for automatic targeting to maximize performance. [S1]
- Dynamic down only bidding strategy can optimize automatic targeting based on ROAS. [S1]
- Amazon recommends setting the highest bid on exact match, lower on phrase match, and lowest on broad match. [S1]
- Sponsored Brands supports multiple pricing models: cost-per-click (CPC), cost per 1,000 viewable impressions (vCPM), and fixed upfront pricing with reserve share of voice. [S2]
- Sponsored Brands uses cost-per-click (CPC) pricing model for driving page visits. [S2]
- Sponsored Brands uses cost per 1,000 viewable impressions (vCPM) pricing model for growing brand impression share. [S2]
- Sponsored Brands uses fixed, upfront pricing with reserve share of voice to secure top-of-search placement for branded keywords. [S2]
- Sponsored Brands has no minimum spend for CPC or vCPM campaigns. [S2]
- Sponsored Brands reserve share of voice requires a minimum spend commitment. [S2]
- Sponsored Brands allows adjusting bids or pausing campaigns at any time. [S2]

## Community claims

- Dynamic bids up and down can raise bids by up to 100% for top of search placement. [S4]
- Dynamic bids up and down can raise bids by up to 50% for other placements. [S4]
- Practitioners observe only up to 50% bid boosts even for top of search placement in testing. [S4]
- Recommended bidding strategy: start with dynamic down only while gathering data. [S4]
- Graduate winning campaigns to dynamic up and down bidding after data collection. [S4]
- When starting PPC campaigns, set daily budgets and default bids 50-100% higher than Amazon recommends. [S4]
- Dynamic bids down only lowers bids in real-time when less likely to make a sale. [S4]
- Dynamic bids up and down can increase bids by 10% when ads are more likely to convert. [S4]
- Fixed bids mean Amazon does not change the bid amount unless the seller adjusts it. [S4]
- Amazon suggests default bids of $0.75 regardless of the product. [S4]
- When starting out, bid as high as $1.50 to $2.00 to ensure early sales. [S4]
- PPC bid exact represents the average bid current sellers use for sponsored products ads using exact keywords. [S4]
- PPC bid broad represents the average bid current sellers use for sponsored products ads using closely related keywords. [S4]
- HSA bids represent the average bid current sellers use for sponsored brand ads at the top of Amazon searches. [S4]
- Amazon's suggested bids tend to be somewhat conservative for new campaigns. [S4]

## Relationships

- [Sponsored Products](/concepts/sponsored-products.md): uses CPC bidding with daily budgets.
- [Sponsored Brands](/concepts/sponsored-brands.md): supports CPC, vCPM, and fixed pricing models.
- [Sponsored Display](/concepts/sponsored-display.md): supports CPC and vCPM bidding.
- [Campaign structure](/concepts/campaign-structure.md): bidding strategies are configured at campaign level.
- [ACOS/ROAS](/concepts/acos-roas.md): advertisers move between bid strategies to hit ACOS targets.
