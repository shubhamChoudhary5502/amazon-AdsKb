---
okf: "0.1"
id: keyword-match-types
title: Keyword match types
description: Match type options (broad, phrase, exact) that control how closely keywords must match shopping queries.
type: concept
status: active
created: 2026-08-12
updated: 2026-08-12
timestamp: 2026-08-12T15:11:53Z
confidence: high
tags: [targeting, keywords, match-types]
related: [targeting, sponsored-products, negative-targeting, campaign-structure]
sources:
  - id: S1
    url: https://advertising.amazon.com/library/guides/targeting-with-sponsored-products
    kind: official
    fetched: 2026-08-12
    snapshot: state/cache/targeting-official.txt
  - id: S2
    url: https://advertising.amazon.com/solutions/products/sponsored-products
    kind: official
    fetched: 2026-08-12
    snapshot: state/cache/sp-official.txt
---

# Keyword match types

## Overview

Keyword match types determine how closely a keyword must match a customer's shopping query for an ad to be eligible to show. Amazon offers three match types: broad match, phrase match, and exact match.

## Key facts

- Keywords are word combinations bid on in manual campaigns to match customers shopping queries. [S1]
- Keyword targeting offers three match types: broad match, phrase match, and exact match. [S1]
- Broad match offers ad exposure to shopping queries containing keyword terms in any order including variations and related terms. [S1]
- Phrase match requires search terms to contain all components of the targeted keyword in the same order. [S1]
- Exact match requires search terms to match the targeted keyword word for word with the same words and order. [S1]
- Keywords are not case-sensitive and must not exceed 10 words or 80 characters. [S1]
- Branded keywords are directly associated with a brand including the brand name alone or combined with other words. [S1]
- Category keywords are non-branded generic keywords that relate to any product or category. [S1]
- Testing different keyword match types should continue for at least 1-2 weeks before pausing keywords. [S1]
- Sponsored Products allows manual keyword selection or automatic keyword targeting by Amazon systems. [S2]

## Relationships

- [Targeting](/concepts/targeting.md): keyword match types are a targeting method.
- [Sponsored Products](/concepts/sponsored-products.md): uses keyword match types for manual targeting.
- [Negative targeting](/concepts/negative-targeting.md): negative keywords also use phrase and exact match types.
- [Campaign structure](/concepts/campaign-structure.md): match types are configured at ad group level.
