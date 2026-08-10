---
name: citations
description: How every fact is cited and how document confidence is computed. Use whenever writing facts into any concept doc.
---

# Citations and confidence

## Citation markers

- Every bullet in Key facts and Community claims ends with [S#] markers.
- [S#] maps to the `sources` list in that same document's frontmatter.
  Ids are local to the document (S1, S2, ...), assigned in order of first
  citation, never reused after a source is removed.
- Multiple sources for one fact: stack markers [S1][S2], strongest first
  (official > api > community).
- A quote fragment used during extraction is evidence for you; it does not
  go into the doc. Docs carry the fact, frontmatter carries the pointer.

## Source kinds

- official: amazon.com, advertising.amazon.com, Amazon Ads console docs.
- api: Amazon Ads API reference, official release notes, official SDKs.
- community: blogs, forums, third-party repos, practitioner guides.

## Document confidence (set in frontmatter)

- high: every Key fact is backed by at least one official or api source.
- medium: Key facts are official/api, but material parts of the doc rest
  on a single source with no corroboration.
- low: the doc exists mainly on community sourcing, or an unresolved
  conflict touches a central fact.

Recompute confidence on every merge. Downgrading is fine and honest;
silently keeping "high" after adding a shaky claim is not.

## The anti-hallucination rule

If you cannot name the source id for a sentence you are about to write,
the sentence does not get written. There is no "general knowledge" tier
in this bundle.
