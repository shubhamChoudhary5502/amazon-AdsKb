---
okf: "0.1"
id: acos-roas
title: ACOS, ROAS and TACOS
description: The three efficiency metrics advertisers steer by, currently resting on a single community source.
type: concept
status: active
created: 2026-08-10
updated: 2026-08-13
timestamp: 2026-08-13T04:02:43Z
confidence: low
tags: [metrics, measurement]
related: [bidding-strategies, sponsored-brands, new-to-brand-metrics, attributed-sales, clicks, impressions]
sources:
  - id: S1
    url: https://www.ppcpractitioner.example/amazon-acos-complete-guide
    kind: community
    fetched: 2026-08-10
    snapshot: sources/samples/blog/acos-complete-guide.md
  - id: S2
    url: https://ppcprotect.com/blog/amazon-ppc-ultimate-guide
    kind: community
    fetched: 2026-08-13
    snapshot: state/cache/ppc-community.txt
---

# ACOS, ROAS and TACOS

## Overview

The three efficiency metrics advertisers steer by. This doc currently
rests on a single community source, which is why its confidence is low;
it should be corroborated against official measurement docs on a future
run.

## Key facts

- ACOS (advertising cost of sales) is ad spend divided by ad-attributed sales, expressed as a percentage. [S1]
- ROAS is the inverse: ad-attributed sales divided by spend. [S1]
- TACOS (total advertising cost of sales) divides ad spend by total revenue including organic sales. [S1]

## Community claims

- ACOS example: spending 200 rupees to get 1000 rupees of attributed sales results in 20% ACOS. [S1]
- A good ACOS for most established products is under 30%. [S1]
- Launch campaigns often run higher ACOS on purpose compared to established products. [S1]
- Source S1 claims a "good" ACOS for established products sits under 30%, with launch campaigns deliberately running higher. [S1]
- TACOS is a better health metric for brands because it captures organic lift from advertising. [S1]
- Source S1 argues TACOS is the better brand health metric because it captures organic lift from ads. [S1]
- Products in the $21-$30 price range hit a sweet spot with greater RoAS than both more and less expensive products. [S2]
- If ACoS is less than profit margin, it is considered a good ACoS. [S2]
- Community practice aims for conversion rates of around 10% for products priced between $18-$25. [S2]

## Conflicts and notes

- 2026-08-10: formula definitions are widely agreed but only community-sourced in this bundle so far. Flagged for corroboration; confidence capped at low until an official or api source confirms.

## Relationships

- [Bidding strategies](/concepts/bidding-strategies.md): advertisers move between bid strategies to hit ACOS targets.
- [New-to-brand metrics](/concepts/new-to-brand-metrics.md): supplement ACOS/ROAS to measure brand growth impact.
