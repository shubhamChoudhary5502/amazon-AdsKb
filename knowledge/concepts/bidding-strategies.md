---
okf: "0.1"
id: bidding-strategies
title: Bidding strategies
description: Sponsored Products bidding strategies plus placement-level bid adjustments that decide how much of the stated bid enters each auction.
type: concept
status: active
created: 2026-08-10
updated: 2026-08-10
timestamp: 2026-08-10T00:00:00Z
confidence: medium
tags: [bidding, optimization]
related: [sponsored-products, acos-roas]
sources:
  - id: S1
    url: https://advertising.amazon.com/library/guides/campaign-targeting-bidding
    kind: official
    fetched: 2026-08-10
    snapshot: sources/samples/official/targeting-and-bidding.html
  - id: S2
    url: https://www.ppcpractitioner.example/amazon-acos-complete-guide
    kind: community
    fetched: 2026-08-10
    snapshot: sources/samples/blog/acos-complete-guide.md
---

# Bidding strategies

## Overview

Sponsored Products offers three campaign-level bidding strategies plus
placement-level bid adjustments. Together they decide how much of the
stated bid actually enters each auction.

## Key facts

- Dynamic bids, down only: Amazon lowers the bid in real time when a click is less likely to convert. [S1]
- Dynamic bids, up and down: Amazon can raise the bid by up to 100% for top of first page of shopping results, by up to 50% for all other placements, and lowers it when conversion is less likely. [S1]
- Fixed bids: the exact bid is used with no real-time adjustment. [S1]
- Placement adjustments can additionally increase bids by up to 900% for top of search and product pages placements. [S1]

## Community claims

- Source S2 recommends starting campaigns on down only, then moving proven performers to up and down. [S2]
- Source S2 recommends isolating exact match keywords in their own campaigns so budget concentrates on proven converters. [S2]

## Conflicts and notes

- 2026-08-10: S2 claims its dashboards only ever show up-and-down boosts up to 50%, including top of search, contradicting the official 100% top-of-search cap. Official value kept in Key facts per source policy; the community observation is recorded here and not treated as fact. [S1][S2]

## Relationships

- [Sponsored Products](/concepts/sponsored-products.md): these strategies apply to Sponsored Products campaigns.
- [ACOS, ROAS and TACOS](/concepts/acos-roas.md): bid strategy is the main lever advertisers use to steer ACOS.
