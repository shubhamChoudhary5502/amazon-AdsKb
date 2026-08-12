---
okf: "0.1"
id: amazon-marketing-stream
title: Amazon Marketing Stream
description: Marketing Stream replaces report polling with push delivery for near real time Amazon Ads data.
type: concept
status: active
created: 2026-08-10
updated: 2026-08-12
timestamp: 2026-08-12T00:00:00Z
confidence: high
tags: [api, data, reporting]
related: [amazon-ads-api, sponsored-products, sponsored-brands, sponsored-display]
sources:
  - id: S1
    url: https://advertising.amazon.com/API/docs/en-us/release-notes/index
    kind: api
    fetched: 2026-08-10
    snapshot: sources/samples/api/ads-api-release-notes.md
  - id: S2
    url: https://advertising.amazon.com/API/docs/en-us/release-notes/index
    kind: api
    fetched: 2026-08-12
    snapshot: state/cache/ads-api-notes.txt
---

# Amazon Marketing Stream

## Overview

Marketing Stream replaces report polling with push delivery. It matters to
anyone building near real time dashboards or automation on Amazon Ads
data.

## Key facts

- Delivers campaign metrics and console change events as push-based messages to the advertiser's AWS account. [S1]
- Uses Amazon SQS as the delivery destination. [S1]
- Provides near real time hourly metrics, in contrast to pull-based report polling. [S1]
- Is available through the Amazon Ads API. [S1]

## Relationships

- [Amazon Ads API](/concepts/amazon-ads-api.md): Stream is provisioned and accessed through the API.
