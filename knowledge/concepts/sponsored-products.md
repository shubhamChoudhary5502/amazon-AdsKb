---
okf: "0.1"
id: sponsored-products
title: Sponsored Products
description: Amazon's core self-service ad product, promoting individual product listings inside the shopping experience.
type: concept
status: active
created: 2026-08-10
updated: 2026-08-12
timestamp: 2026-08-12T16:42:54Z
confidence: high
tags: [ad-product, ppc, self-service]
related: [bidding-strategies, keyword-match-types, campaign-structure, advertising-eligibility, amazon-ads-api, amazon-marketing-stream, product-targeting, negative-targeting, targeting]
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
  - id: S3
    url: https://advertising.amazon.com/library/guides/targeting-with-sponsored-products
    kind: official
    fetched: 2026-08-12
    snapshot: state/cache/targeting-official.txt
---

# Sponsored Products

## Overview

Sponsored Products is Amazon's core self-service ad product. It promotes
individual product listings inside Amazon's shopping experience and is
usually the first ad type an advertiser runs.

## Key facts

- Sponsored Products use cost-per-click (CPC) pricing model. [S2]
- Sponsored Products promote individual product listings on Amazon. [S2]
- Advertisers only pay when shoppers click their Sponsored Products ad. [S2]
- Sponsored Products ads appear in shopping results and on product detail pages. [S2]
- Sponsored Products ads are created from existing product listings. [S2]
- Sponsored Products do not require custom ad copy or images. [S2]
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
- Sponsored Products offers three targeting options: automatic, manual, and negative targeting. [S3]
- Automatic targeting matches ads to keywords and products similar to the advertised product based on shopping queries and product information. [S3]
- Automatic targeting uses four default strategies: close match, loose match, substitutes, and complements. [S3]
- Close match automatic targeting shows ads to shoppers using search terms closely related to the advertised product. [S3]
- Loose match automatic targeting shows ads to shoppers using search terms loosely related to the advertised product. [S3]
- Substitutes automatic targeting shows ads to shoppers browsing detail pages of products similar to the advertised product. [S3]
- Complements automatic targeting shows ads to shoppers viewing detail pages of products that complement the advertised product. [S3]
- Manual targeting allows advertisers to manually select which keywords or products to target. [S3]
- Amazon recommends letting automatic campaigns run for about two weeks before creating manual campaigns. [S3]
- When customers click a Sponsored Products ad, they are directed to the advertised products detail page. [S2]
- Sponsored Products placements include the top of, alongside, or within shopping results and on product pages on Amazon. [S2]
- Sponsored Products ads appear beyond Amazon on Amazon-owned and operated sites and third-party destinations. [S2]
- Sponsored Products ads only appear when advertised items are in stock. [S2]
- New sellers can earn up to $1000 in ad credits when they launch and spend on Sponsored Products within 30 days. [S2]
- Sponsored Products campaigns have no monthly or upfront fees, advertisers pay only when a shopper clicks an ad. [S2]
- Sponsored Products provides tools and reports to help optimize campaign performance and measure success. [S2]
- Sponsored Products ads appear on desktop and mobile browsers as well as the Amazon mobile app. [S2]
- Sponsored Products with video saw an average 9% uplift in click-through rate compared to campaigns without video. [S2]

## Relationships

- [Bidding strategies](/concepts/bidding-strategies.md): dynamic bidding options apply to Sponsored Products campaigns.
- [Keyword match types](/concepts/keyword-match-types.md): manual keyword targeting uses these match types.
- [Product targeting](/concepts/product-targeting.md): manual targeting can focus on specific products or categories.
- [Negative targeting](/concepts/negative-targeting.md): excluding keywords or products to optimize performance.
- [Campaign structure](/concepts/campaign-structure.md): Sponsored Products campaigns follow the standard campaign and ad group hierarchy.
- [Targeting](/concepts/targeting.md): automatic and manual targeting options.
- [Advertising eligibility](/concepts/advertising-eligibility.md): who can run Sponsored Products and what enrollment it needs.
- [Amazon Ads API](/concepts/amazon-ads-api.md): campaign management is available programmatically, including a sandbox.
- [Amazon Marketing Stream](/concepts/amazon-marketing-stream.md): provides near real time metrics and campaign events for Sponsored Products.
