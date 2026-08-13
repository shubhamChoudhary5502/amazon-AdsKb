---
okf: "0.1"
id: amazon-ads-api
title: Amazon Ads API
description: The programmatic interface to Amazon Ads, whose version 3 is the current generation tools and agencies build against.
type: concept
status: active
created: 2026-08-10
updated: 2026-08-13
timestamp: 2026-08-13T04:02:43Z
confidence: high
tags: [api, integration]
related: [amazon-marketing-stream, sponsored-products, sponsored-brands, sponsored-display, display-ads, campaign-structure]
sources:
  - id: S1
    url: https://advertising.amazon.com/API/docs/en-us/release-notes/index
    kind: api
    fetched: 2026-08-13
    snapshot: state/cache/ads-api-notes.txt
  - id: S2
    url: https://advertising.amazon.com/solutions/products/sponsored-display
    kind: official
    fetched: 2026-08-13
    snapshot: state/cache/sd-official.txt
---

# Amazon Ads API

## Overview

The programmatic interface to Amazon Ads. Version 3 is the current
generation and is the surface that tools, agencies, and this knowledge
base's own live mode would build against.

## Key facts

- The Amazon Ads API uses OAuth 2.0 via Login with Amazon for authorization. [S1]
- API access requires an approved developer application. [S1]
- Reporting in version 3 is asynchronous. [S1]
- The asynchronous reporting process involves requesting a report, polling its status, then downloading the generated file. [S1]
- The sandbox environment allows testing without spending real money. [S1]
- A sandbox environment is available for testing Sponsored Products campaign management operations. [S1]
- Authorization uses OAuth 2.0 via Login with Amazon, and access requires an approved developer application. [S1]
- Requests are scoped to a profile, which represents an advertiser account in a specific marketplace. [S1]
- Version 3 reporting is asynchronous: request a report, poll status, download the file. [S1]
- The new platform is a single ad platform that unifies access to all Amazon Ads products, bringing together sponsored ads and Amazon DSP workflows. [S2]

## Relationships

- [Amazon Marketing Stream](/concepts/amazon-marketing-stream.md): the push-based alternative to pull-based report polling, delivered through this API.
- [Sponsored Products](/concepts/sponsored-products.md): the sandbox covers Sponsored Products campaign management operations.
