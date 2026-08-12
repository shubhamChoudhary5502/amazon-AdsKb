---
okf: "0.1"
id: sponsored-display
title: Sponsored Display
description: Amazon's self-service display product, whose ads can follow shoppers off Amazon to third-party destinations.
type: concept
status: active
created: 2026-08-10
updated: 2026-08-12
timestamp: 2026-08-12T00:00:00Z
confidence: high
tags: [ad-product, display, remarketing]
related: [advertising-eligibility, amazon-ads-api, amazon-marketing-stream, bidding-strategies, campaign-structure]
sources:
  - id: S1
    url: https://advertising.amazon.com/solutions/products/sponsored-display
    kind: official
    fetched: 2026-08-10
    snapshot: sources/samples/official/sponsored-display.html
  - id: S2
    url: https://advertising.amazon.com/solutions/products/sponsored-display
    kind: official
    fetched: 2026-08-12
    snapshot: state/cache/sd-official.txt
---

# Sponsored Display

## Overview

Sponsored Display is the self-service display product. Unlike Sponsored
Products and Sponsored Brands, its ads can follow shoppers off Amazon to
third-party destinations.

## Key facts

- Reaches audiences both on Amazon and on third-party destinations off Amazon. [S1]
- Contextual targeting targets products or categories. [S1]
- Audience targeting includes views remarketing, purchases remarketing, and Amazon audiences built from shopping signals. [S1]
- Supports cost-per-click bidding, and vCPM (cost per thousand viewable impressions) for reach-optimized campaigns. [S1]
- Requires Brand Registry for sellers. [S1]
- Sponsored Display is now part of Amazon's wider display ads offering within a centralized hub. [S2]
- Existing Sponsored Display campaigns continue to run uninterrupted through Campaign Manager. [S2]
- The platform connects display campaigns across Amazon properties including Twitch, Fire TV, and Echo Show, plus premium placements across the open internet. [S2]
- New display campaigns are created through "Campaigns" > "Create Campaign" > "Display" workflow. [S2]
- Display ads use flexible ad formats with Amazon-generated creative or custom creative assets. [S2]
- Sponsored Display is now known as display ads. [S2]
- Amazon introduced a single ad platform that connects display campaigns with customers across Amazon properties. [S2]
- Display campaigns can reach audiences on Twitch, Fire TV, and Echo Show. [S2]
- Display campaigns can reach audiences on premium placements across the open internet. [S2]
- Amazon created a centralized hub that unifies access to all Amazon Ads products. [S2]
- The new hub brings together sponsored ads and Amazon DSP workflows into a single workspace. [S2]
- Existing Sponsored Display campaigns are accessed through Campaign Manager in the Ads Console. [S2]
- New display campaigns are created by clicking Campaigns, Create Campaign, and Display. [S2]
- Display ads are flexible ad formats that help brands reach relevant audiences. [S2]
- Display ads can use Amazon-generated creative or custom creative assets. [S2]

## Relationships

- [Advertising eligibility](/concepts/advertising-eligibility.md): seller access depends on Brand Registry enrollment.
- [Bidding strategies](/concepts/bidding-strategies.md): supports CPC and vCPM pricing models.
- [Campaign structure](/concepts/campaign-structure.md): campaigns managed through Campaign Manager.
- [Amazon Ads API](/concepts/amazon-ads-api.md): programmatic campaign management available.
- [Amazon Marketing Stream](/concepts/amazon-marketing-stream.md): near real time metrics delivery for display campaigns.
