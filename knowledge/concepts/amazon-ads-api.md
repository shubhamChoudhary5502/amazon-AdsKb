---
okf: "0.1"
id: amazon-ads-api
title: Amazon Ads API
type: concept
status: active
created: 2026-08-10
updated: 2026-08-10
confidence: medium
tags: [api, integration]
related: [amazon-marketing-stream, sponsored-products]
sources:
  - id: S1
    url: https://advertising.amazon.com/API/docs/en-us/release-notes/index
    kind: api
    fetched: 2026-08-10
    snapshot: sources/samples/api/ads-api-release-notes.md
---

# Amazon Ads API

## Overview

The programmatic interface to Amazon Ads. Version 3 is the current
generation and is the surface that tools, agencies, and this knowledge
base's own live mode would build against.

## Key facts

- Authorization uses OAuth 2.0 via Login with Amazon, and access requires an approved developer application. [S1]
- Requests are scoped to a profile, which represents an advertiser account in a specific marketplace. [S1]
- Version 3 reporting is asynchronous: request a report, poll status, download the file. [S1]
- A sandbox environment allows testing Sponsored Products campaign management without real spend. [S1]

## Relationships

- amazon-marketing-stream: the push-based alternative to pull-based report polling, delivered through this API.
- sponsored-products: the sandbox covers Sponsored Products campaign management operations.
