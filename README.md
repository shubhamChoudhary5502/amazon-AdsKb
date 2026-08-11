# amazon-ads-kb

An autonomous knowledge acquisition system for Amazon Ads, built as a
Claude Code project. It discovers sources, extracts facts, validates them
against what it already knows, merges duplicates, and publishes an OKF
v0.1 knowledge bundle. Safe to re-run: no changes upstream means zero
bytes change in `knowledge/`.

## Quick start

Requirements: Python 3.9+ and Claude Code. No pip installs, the
deterministic layer is stdlib only.

    git clone <this repo> && cd amazon-ads-kb
    python3 -m unittest discover tests        # 14 tests, ~0.01s
    python3 scripts/validate_okf.py knowledge/concepts/   # bundle is valid
    sh scripts/demo_rerun.sh                  # idempotency proof
    claude                                    # then: /ingest all

## Two run modes

- **Offline (default).** Sources are read from snapshot fixtures in
  `sources/samples/`. Deterministic, works with no network, used by tests
  and the demo. This is the mode reviewers should use first.
- **Live.** `python3 scripts/fetch.py --all --live` fetches the real URLs.
  For JavaScript-heavy pages and discovery of new sources, add MCPs:
  `claude mcp add playwright npx @playwright/mcp@latest` plus a search MCP
  (Tavily or Brave).

## Repo map

    CLAUDE.md              agent behavior, scope, the code-vs-Claude line
    .claude/agents/        scout, extractor, validator, merger subagents
    .claude/skills/        okf-format, dedup-merge, citations
    .claude/settings.json  PostToolUse hook: every write to knowledge/
                           concepts/ is schema-validated, exit 2 blocks
    .claude/commands/      /ingest slash command
    scripts/               deterministic layer (fetch, hash, validate,
                           index, log), stdlib only
    sources/               source registry + offline snapshots (3 types:
                           official HTML, community blog, API notes)
    knowledge/             the OKF bundle: 12 concepts, index, log
    state/                 manifest (hashes), cache, concept registry
    tests/                 parser, validator, and idempotency tests

## How re-run safety works

1. `fetch.py` normalizes each source (HTML stripped, whitespace collapsed)
   and hashes it. Normalizing first means cosmetic upstream changes do not
   trigger work.
2. `state/manifest.json` remembers the last hash. Verdicts are NEW,
   CHANGED, UNCHANGED, or ERROR. UNCHANGED sources stop the pipeline for
   that source before any agent reads them.
3. Agents only touch concept docs that received classified facts. The
   index builder rewrites only on content difference.
4. `scripts/demo_rerun.sh` proves it: checksums all of `knowledge/`,
   re-runs, checksums again, asserts byte identity.

## Provenance model

Every bullet in every doc ends with [S#] markers resolving to the doc's
own frontmatter sources, each with url, kind (official, api, community),
and fetch date. Community claims are quarantined in their own section.
Conflicts between sources are resolved official-first and permanently
recorded in "Conflicts and notes". The bundle contains one real example
of each: see `knowledge/concepts/bidding-strategies.md` (conflict) and
`acos-roas.md` (community-only doc capped at confidence low).

## Known limitations

- Discovery is registry-driven. The scout checks known sources; finding
  brand new sources needs the search MCP in live mode and is not
  exercised offline.
- Change detection is document-level (whole-source hash). Section-level
  diffing would re-extract less; see docs/DESIGN.md.
- The offline fixtures are hand-made snapshots for deterministic testing.
  Facts in the bundle mirror them; live runs against real pages will
  update values with real fetch dates.
- Alias matching in the concept registry is exact/lowercase, not fuzzy.
  Semantic near-misses rely on the validator agent reading the registry.
- `last_checked` in the manifest moves on every run by design, so `state/`
  is not byte-stable, only `knowledge/` is. See DESIGN.md for why.
