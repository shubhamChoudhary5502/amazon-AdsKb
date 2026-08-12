# Amazon Ads knowledge bundle update log

## 2026-08-12
* **Merge**: Semantic merge: Integrated sponsored-brands-video concept into sponsored-brands, reducing bundle from 16 to 15 concept documents. All unique video content preserved within sponsored-brands.md including Video Generator, creative production services, and video-specific placement details. Updated state/concepts.json to include video-related aliases under sponsored-brands.
* **Update**: Live ingestion: Added 151 facts from 4 official Amazon Ads sources (sp-official, sb-official, sd-official, targeting-official). Created 10 new concept documents: targeting, brand-stores, new-to-brand-metrics, sponsored-brands-video, product-targeting, negative-targeting, keyword-match-types, bidding-strategies, advertising-eligibility, campaign-structure. Updated 2 existing concepts: sponsored-display (2 changes), sponsored-products (3 changes).
* **Update**: Live Run 1: 27 validated facts from 6 sources processed via new persisted handoff architecture
* **Update**: Live ingestion update: Added 22 new facts from 4 live Amazon sources (sp-official, sb-official, sd-official, ads-api-notes). Updated 5 concept documents with enhanced content including Sponsored Display platform transition, Sponsored Brands pricing models, and API documentation updates. All sources validated as official Amazon content.
* **Update**: added dedicated test coverage for log_run.py and build_index.py (17 + 15 new tests)

## 2026-08-11
* **Creation**: initial acquisition run across 6 sources (4 official, 1 community, 1 api) produced 12 concept documents.
* **Update**: recorded a source conflict on the up-and-down top-of-search bid cap in [Bidding strategies](/concepts/bidding-strategies.md). Official 100% kept in Key facts, community-observed 50% preserved in Conflicts and notes.
* **Update**: capped [ACOS, ROAS and TACOS](/concepts/acos-roas.md) at low confidence, single community source pending official corroboration.
* **Update**: targeting-official changed upstream. 21 facts extracted, 20 dropped as duplicates, 1 new fact on portfolio-level budgets merged into [Campaign structure](/concepts/campaign-structure.md).
* **Update**: fix bug in validation: check sources first
* **Creation**: new concept added
* **Update**: existing concept updated
* **Deprecation**: old concept removed
* **Update**: New entry
* **Update**: 
* **Update**: Entry 1
* **Update**: Entry 2
* **Update**: No explicit kind
* **Update**: First entry
* **Update**: Test entry
* **Update**: Another entry

## 2026-08-11
* **Creation**: initial acquisition run across 6 sources (4 official, 1 community, 1 api) produced 12 concept documents.
* **Update**: recorded a source conflict on the up-and-down top-of-search bid cap in [Bidding strategies](/concepts/bidding-strategies.md). Official 100% kept in Key facts, community-observed 50% preserved in Conflicts and notes.
* **Update**: capped [ACOS, ROAS and TACOS](/concepts/acos-roas.md) at low confidence, single community source pending official corroboration.
* **Update**: targeting-official changed upstream. 21 facts extracted, 20 dropped as duplicates, 1 new fact on portfolio-level budgets merged into [Campaign structure](/concepts/campaign-structure.md).
