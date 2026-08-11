---
okf: "0.1"
id: keyword-match-types
title: Keyword match types
description: How tightly a shopper's query must match a manually targeted keyword before an ad is eligible to show.
type: concept
status: active
created: 2026-08-10
updated: 2026-08-10
timestamp: 2026-08-10T00:00:00Z
confidence: medium
tags: [targeting, keywords]
related: [sponsored-products, negative-targeting]
sources:
  - id: S1
    url: https://advertising.amazon.com/library/guides/campaign-targeting-bidding
    kind: official
    fetched: 2026-08-10
    snapshot: sources/samples/official/targeting-and-bidding.html
---

# Keyword match types

## Overview

Match types control how tightly a shopper's query must match a manually
targeted keyword before an ad is eligible to show. Amazon supports three.

## Key facts

- Broad match reaches queries containing all keyword terms in any order, including close variations. [S1]
- Phrase match requires the query to contain the exact phrase or close variations, in order. [S1]
- Exact match requires the query to match the keyword or its close variations exactly. [S1]

## Relationships

- [Sponsored Products](/concepts/sponsored-products.md): manual keyword campaigns choose one of these per keyword.
- [Negative targeting](/concepts/negative-targeting.md): negative keywords use exact and phrase forms of the same idea in reverse.
