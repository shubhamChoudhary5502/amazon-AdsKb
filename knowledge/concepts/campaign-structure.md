---
okf: "0.1"
id: campaign-structure
title: Campaign structure
description: Hierarchical organization of campaigns and ad groups that determines how targeting, bidding, and budgeting are configured.
type: concept
status: active
created: 2026-08-12
updated: 2026-08-13
timestamp: 2026-08-13T04:02:43Z
confidence: high
tags: [organization, hierarchy, management]
related: [sponsored-products, sponsored-brands, sponsored-display, targeting, bidding-strategies, keyword-match-types, product-targeting, negative-targeting, display-ads, amazon-ads-api]
sources:
  - id: S1
    url: https://advertising.amazon.com/library/guides/targeting-with-sponsored-products
    kind: official
    fetched: 2026-08-13
    snapshot: state/cache/targeting-official.txt
  - id: S2
    url: https://advertising.amazon.com/solutions/products/sponsored-products
    kind: official
    fetched: 2026-08-13
    snapshot: state/cache/sp-official.txt
  - id: S3
    url: https://ppcprotect.com/blog/amazon-ppc-ultimate-guide
    kind: community
    fetched: 2026-08-13
    snapshot: state/cache/ppc-community.txt
---

# Campaign structure

## Overview

Campaign structure refers to how campaigns and ad groups are organized to manage targeting, bidding, and budgeting. Proper structure ensures that different targeting strategies are not mixed within the same campaign and ad group.

## Key facts

- Campaign targeting type cannot be changed once a campaign is live. [S1]
- Campaign strategies include expand, promote, protect, conquest, upsell, and cross-sell. [S1]
- Ad groups can contain a maximum of 1,000 products. [S1]
- Amazon recommends avoiding mixing different targeting strategies within the same campaign and ad group. [S1]
- Amazon recommends establishing benchmarks based on goals and historical campaign performance. [S1]
- Amazon recommends an always-on approach with evergreen campaigns. [S1]
- To create Sponsored Products you register for sponsored ads, sign in, click Create campaign and choose Sponsored Products. [S2]
- To create Sponsored Products you add products to advertise, define targeting and bidding strategies, and set campaign name, dates, and daily budget. [S2]
- Sponsored Products creation steps include registering, adding products, defining targeting and bidding, choosing settings, and launching. [S2]

## Community claims

- Let ad campaigns run for at least two weeks before running reports and making adjustments. [S3]
- Amazon allows leftover daily budget amounts to increase ads by 10% on a later date in the same month. [S3]
- When starting out, set daily budget to $50 or more since most costs per click are between $0.50 to $1.50. [S3]
- Ad costs are charged either when reaching $500 in total ads or at the first of the month. [S3]
- It usually takes 30 minutes to an hour for ads to premiere on Amazon after launch. [S3]
- High-performing keywords from automatic campaigns should be added to manual campaigns and removed from automatic targeting. [S3]
- Community best practice is to review ad reports once per week. [S3]
- Keep exact match keywords in separate campaigns so budget flows to proven converters. [S3]

## Relationships

- [Sponsored Products](/concepts/sponsored-products.md): campaign creation and management.
- [Sponsored Brands](/concepts/sponsored-brands.md): campaign organization and goals.
- [Sponsored Display](/concepts/sponsored-display.md): campaign workflow through Campaign Manager.
- [Targeting](/concepts/targeting.md): targeting strategies configured at campaign and ad group level.
- [Bidding strategies](/concepts/bidding-strategies.md): bidding configured at campaign level.
