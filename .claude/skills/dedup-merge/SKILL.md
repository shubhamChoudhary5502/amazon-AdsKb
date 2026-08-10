---
name: dedup-merge
description: Identity rules for what counts as the same concept and the merge policy when sources overlap or disagree. Use during validate and merge stages.
---

# Deduplication and merge policy

## Concept identity

The registry `state/concepts.json` is the single source of truth for
identity. Shape:

    { "sponsored-products": { "aliases": ["sp", "sponsored products ads"] } }

Resolution order for a proposed concept name:
1. Exact slug match in registry -> use it.
2. Alias match (case-insensitive) -> use the canonical slug.
3. Semantic check: read the closest existing docs. If the proposed concept
   is the same thing under a new name, add it as an alias, do NOT create a
   doc. "SP bids", "Sponsored Products bidding" -> bidding-strategies.
4. Only if genuinely distinct: create doc, register slug and aliases.

The test for "same concept": would a practitioner expect to find these
facts on one page? If yes, one doc.

## Merge policy when sources overlap

- Same claim, same value, multiple sources: one bullet, stack citations
  [S1][S2]. More corroboration raises confidence, never duplicates lines.
- Same claim, different values:
  - official vs anything: official value stays in Key facts, the other
    goes to Conflicts and notes with its citation.
  - community vs community: neither is authoritative. Both go to
    Community claims, disagreement noted in Conflicts and notes.
  - old official vs new official: newer fetch wins, change is dated in
    Conflicts and notes ("Until 2026-08-01 the limit was X [S1]").
- Never merge by averaging or hedging ("around 50-100%"). Pick per policy.

## What is NOT a duplicate

Two facts about the same feature at different specificity are distinct:
"placement adjustments exist" and "placement adjustments cap at 900%" can
coexist, but prefer replacing the vague line with the specific one when
the specific one is official.
