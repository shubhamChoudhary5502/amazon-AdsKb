---
name: okf-format
description: Structure and frontmatter schema for OKF v0.1 concept documents in this bundle. Use whenever creating or editing any file in knowledge/concepts/.
---

# OKF v0.1 document format (this bundle's profile)

Every file in `knowledge/concepts/` is one concept, named `<slug>.md`,
slug in kebab-case, and must follow this exact shape. The hook enforces it
with `scripts/validate_okf.py`, so deviations will be rejected on write.

## Frontmatter (YAML, all fields required unless marked optional)

    ---
    okf: "0.1"
    id: sponsored-products        # must equal the filename minus .md
    title: Sponsored Products
    type: concept
    status: active                # active | deprecated
    created: 2026-08-10           # ISO date, never changes after creation
    updated: 2026-08-10           # ISO date, bump on every content change
    confidence: high              # high | medium | low, per citations skill
    tags: [ad-product, ppc]       # at least one
    related: [keyword-match-types]  # slugs of other docs, may be empty []
    sources:                      # at least one
      - id: S1                    # cited in body as [S1]
        url: https://...
        kind: official            # official | community | api
        fetched: 2026-08-10
        snapshot: sources/samples/official/x.html   # optional, offline mode
    ---

## Body sections, in this order

1. `# <Title>` - one H1, matches frontmatter title.
2. `## Overview` - 2 to 4 sentences, what this concept is.
3. `## Key facts` - bullet list. Every bullet ends with one or more
   citation markers like [S1] or [S1][S3]. Only official and api sourced
   facts live here.
4. `## Community claims` - optional. Uncorroborated blog/community claims,
   each cited, each phrased as "Source X claims ...".
5. `## Conflicts and notes` - optional but never delete it once created.
   Records disagreements between sources and dated change notes.
6. `## Relationships` - one line per related slug explaining the link.

## Rules

- `related` must be symmetric: if A lists B, B must list A.
- No prose outside the sections above. No HTML. Plain markdown only.
- Keep docs under roughly 80 lines. If it grows past that, the concept
  probably needs splitting; stop and report rather than split silently.
