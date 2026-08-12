---
okf: "0.1"
id: sponsored-brands
title: Sponsored Brands
description: A cost-per-click ad product that showcases a brand and a selection of its products rather than a single listing.
type: concept
status: active
created: 2026-08-10
updated: 2026-08-12
timestamp: 2026-08-12T00:00:00Z
confidence: high
tags: [ad-product, ppc, branding]
related: [advertising-eligibility, amazon-ads-api, acos-roas, amazon-marketing-stream]
sources:
  - id: S1
    url: https://advertising.amazon.com/solutions/products/sponsored-brands
    kind: official
    fetched: 2026-08-10
    snapshot: sources/samples/official/sponsored-brands.html
  - id: S2
    url: https://advertising.amazon.com/solutions/products/sponsored-brands
    kind: official
    fetched: 2026-08-12
    snapshot: state/cache/sb-official.txt
---

# Sponsored Brands

## Overview

Sponsored Brands is a cost-per-click ad product that showcases a brand and
a selection of its products rather than a single listing. It is the main
upper-funnel option inside the self-service console.

## Key facts

- Pricing is cost-per-click. [S1][S2]
- Requires enrollment in Amazon Brand Registry for sellers. [S1][S2]
- Multiple formats available: product collection (multiple products), store spotlight (drives to Store pages), and video (single product with autoplay video in shopping results). [S1][S2]
- Ads can link to the brand's Amazon Store or a custom product landing page. [S1][S2]
- Placements include top of shopping results, within results, and product pages, on both desktop and mobile devices. [S1][S2]
- Supports multiple pricing models: CPC for driving page visits, vCPM for growing brand impression share, and fixed upfront pricing with reserve share of voice. [S2]
- No minimum spend for CPC or vCPM campaigns; reserve share of voice requires minimum spend commitment. [S2]
- Available for vendors, book vendors, Kindle Direct Publishing (KDP) authors, agencies, and professional sellers enrolled in Brand Registry. [S2]
- New-to-brand metrics measure orders and sales from first-time customers with 12-month look-back window. [S2]
- Video ads can feature up to three products and link to Brand Stores. [S2]
- AI-powered image generation available at no cost for branded creatives. [S2]
- Reserve share of voice secures top-of-search placement for branded keywords at fixed pricing. [S2]
- Case studies show significant performance improvements: 80% sales from new customers, 224% YoY impressions growth, 142% YoY clicks increase. [S2]
- Adult products, used products, refurbished products, and products in closed categories are not eligible. [S2]

## Relationships

- [Advertising eligibility](/concepts/advertising-eligibility.md): Brand Registry enrollment is the gate for this product.
- [Amazon Ads API](/concepts/amazon-ads-api.md): programmatic campaign management and reporting available.
- [Amazon Marketing Stream](/concepts/amazon-marketing-stream.md): near real time metrics delivery for Sponsored Brands campaigns.
- [ACOS/ROAS](/concepts/acos-roas.md): efficiency metrics used to measure Sponsored Brands performance.
