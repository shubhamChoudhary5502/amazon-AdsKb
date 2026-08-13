---
okf: "0.1"
id: keyword-match-types
title: Keyword match types
description: Match type options (broad, phrase, exact) that control how closely keywords must match shopping queries.
type: concept
status: active
created: 2026-08-12
updated: 2026-08-13
timestamp: 2026-08-13T04:02:43Z
confidence: high
tags: [targeting, keywords, match-types]
related: [targeting, sponsored-products, negative-targeting, campaign-structure]
sources:
  - id: S1
    url: https://advertising.amazon.com/library/guides/targeting-with-sponsored-products
    kind: official
    fetched: 2026-08-13
    snapshot: state/cache/targeting-official.txt
  - id: S2
    url: https://advertising.amazon.com/solutions/products/sponsored-products
    kind: official
    fetched: 2026-08-13
    snapshot: state/cache/sp-official.txt
  - id: S3
    url: https://ppcprotect.com/blog/amazon-ppc-ultimate-guide
    kind: community
    fetched: 2026-08-13
    snapshot: state/cache/ppc-community.txt
---

# Keyword match types

## Overview

Keyword match types determine how closely a keyword must match a customer's shopping query for an ad to be eligible to show. Amazon offers three match types: broad match, phrase match, and exact match.

## Key facts

- Keywords are word combinations bid on in manual campaigns to match customers shopping queries. [S1]
- Keyword targeting offers three match types: broad match, phrase match, and exact match. [S1]
- Keyword targeting allows choosing specific keywords to help products appear in shopping results and on product detail pages. [S1]
- Keyword match types control which search terms ads will be eligible to show against. [S1]
- Amazon provides keyword recommendations and suggested bids to help with keyword selection. [S1]
- Keyword recommendations are based on past keyword performance and search terms that translate into sales. [S1]
- Broad match offers ad exposure to shopping queries containing keyword terms in any order including variations and related terms. [S1]
- Broad match offers ads broad exposure to customer shopping queries including synonyms and related terms. [S1]
- Broad match can include singulars, plurals, variations, synonyms, and related terms based on keyword meaning. [S1]
- Phrase match requires search terms to contain all components of the targeted keyword in the same order. [S1]
- Phrase match is more restrictive than broad match and requires all keyword components in the same order. [S1]
- Phrase match includes the plural form of the keyword. [S1]
- Exact match requires search terms to match the targeted keyword word for word with the same words and order. [S1]
- Exact match is the most restrictive match type and matches search terms word for word in the same order. [S1]
- Exact match tends to result in the highest conversion rates. [S1]
- Keywords are not case-sensitive and must not exceed 10 words or 80 characters. [S1]
- Keywords are not case-sensitive and will match uppercase or lowercase letters. [S1]
- Keywords have a maximum limit of 10 words per keyword and 80 characters. [S1]
- Keywords can contain letters, numbers, or spaces but not special characters like question marks or slashes. [S1]
- Amazon recommends testing all three keyword match types with different bids to maximize performance. [S1]
- Branded keywords are directly associated with a brand including the brand name alone or combined with other words. [S1]
- Category keywords are non-branded generic keywords that relate to any product or category. [S1]
- Testing different keyword match types should continue for at least 1-2 weeks before pausing keywords. [S1]
- Sponsored Products allows manual keyword selection or automatic keyword targeting by Amazon systems. [S2]

## Community claims

- Before adjusting or removing a keyword from a manual campaign, ensure the keyword gets at least 10 clicks. [S3]
- Close match ads appear when shoppers use search terms closely related to the advertised product. [S3]
- Loose match ads appear when shoppers search keywords loosely related to the product. [S3]
- Poor-performing keywords are defined as those with more than 10 clicks and high ACoS or low 7-day conversion rate. [S3]
- High-performing keywords are defined as having at least 10 clicks and being at or below ACoS or conversion rate thresholds. [S3]
- 30-Day search volume exact is the number of times Amazon shoppers entered the exact term while performing searches. [S3]
- 30-Day trend is the increase in searches for a term over the last 30 days compared to the previous 30-day period. [S3]
- 30-Day search volume broad counts searches for terms closely related to the given search term. [S3]

## Relationships

- [Targeting](/concepts/targeting.md): keyword match types are a targeting method.
- [Sponsored Products](/concepts/sponsored-products.md): uses keyword match types for manual targeting.
- [Negative targeting](/concepts/negative-targeting.md): negative keywords also use phrase and exact match types.
- [Campaign structure](/concepts/campaign-structure.md): match types are configured at ad group level.
