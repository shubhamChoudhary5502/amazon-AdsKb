# amazon-ads-kb

An autonomous knowledge acquisition system for Amazon Ads, built as a Claude Code project.

The system discovers registered sources, fetches source content, extracts structured facts, validates those facts against the existing knowledge base, detects new/changed/duplicate/conflicting facts, merges only validated knowledge, and publishes an OKF v0.1 knowledge bundle.

The system separates deterministic Python code from Claude Code agent work:

- **Claude Code** performs source discovery, extraction, validation decisions, and knowledge merging.
- **Python** handles fetching, hashing, artifact persistence, validation, indexing, logging, and state management.

The pipeline is safe to re-run. Each ingestion execution receives a unique `run_id`, and extraction and validation artifacts are isolated by run so that independent or concurrent executions cannot consume each other's intermediate results.

---

## Quick Start

### Requirements

- Python 3.9+
- Claude Code
- No pip installs are required; the deterministic layer uses only the Python standard library.

### Run the project

```bash
git clone <this repo>
cd amazon-AdsKb

# Run the complete test suite
python3 -m unittest discover tests -v

# Validate the knowledge bundle
python3 scripts/validate_okf.py knowledge/concepts/

# Prove knowledge idempotency
sh scripts/demo_rerun.sh

# Start Claude Code
claude

# Then run the ingestion workflow
/ingest all
```

The repository currently contains **139 passing tests** covering the deterministic pipeline, validation, artifact-based agent handoff, run isolation, concurrency, write protection, indexing, logging, idempotency, and section-level incremental extraction.

---

## System Overview

The system is organized around a strict boundary between Claude Code agents and deterministic Python code.

### Claude Code Responsibilities

Claude Code performs the reasoning-heavy work:

- Discovering which registered sources should be processed
- Extracting facts from source content
- Classifying facts against existing knowledge
- Identifying conflicts and provenance
- Deciding which knowledge concepts need to be updated

### Deterministic Python Responsibilities

The deterministic layer handles operations that must be repeatable and mechanically enforced:

- Fetching and normalizing source content
- Calculating content hashes
- Maintaining the source manifest
- Generating run IDs
- Persisting extraction artifacts
- Validating extraction artifacts
- Enforcing the validation boundary
- Loading validated facts
- Building the knowledge index
- Writing run logs
- Enforcing write-time schema checks

The boundary is deliberate: Claude Code does not directly control the low-level state transitions that determine whether unvalidated information can reach the published knowledge base.

---

## Ingestion Architecture

The ingestion pipeline uses four specialized Claude Code agents:

```text
Scout
  |
  | generates unique run_id
  v
Extractor
  |
  | persists structured extraction artifacts
  v
state/extracts/<run_id>/
  |
  | deterministic validation
  v
Validator
  |
  | persists validated results
  v
state/validated/<run_id>/
  |
  | validated facts only
  v
Merger
  |
  | publishes accepted knowledge
  v
knowledge/concepts/
  |
  +--> knowledge/index.md
  |
  +--> knowledge/log.md
```

The agents do not pass extracted facts to one another through conversational context. Instead, each stage produces a persisted artifact that becomes the input contract for the next stage.

This makes the handoff inspectable, reproducible, and isolated between runs.

### 1. Scout

The Scout identifies the sources that should be processed for the current ingestion and generates a unique `run_id`.

The same run ID is passed to all downstream stages.

Example:

```text
20260812-150401-c8da98f4
```

The run ID becomes the namespace for all intermediate artifacts created during that execution.

### 2. Extractor

The Extractor reads the fetched source content and produces structured facts.

Each extraction artifact contains information such as:

- `run_id`
- Source ID
- Source URL
- Source type
- Extraction timestamp
- Content hash
- Extracted facts
- Concept
- Supporting quote/provenance

Artifacts are persisted under:

```text
state/extracts/<run_id>/
```

The Extractor does not publish directly to the knowledge base.

### 3. Validator

The Validator consumes only the extraction artifacts belonging to the current run.

It validates the structure and provenance of extracted facts and classifies them against the existing knowledge base.

Classification paths include:

- `NEW`
- `CHANGED`
- `DUPLICATE`
- `CONFLICT`
- `REJECTED`

Validated results are persisted under:

```text
state/validated/<run_id>/
```

The Validator ensures that malformed, incomplete, contaminated, or otherwise invalid facts do not reach the Merger.

### 4. Merger

The Merger consumes only the validated artifacts for the current run. It does not read raw extraction artifacts directly.

The Merger:

- Loads validated facts for the current run
- Groups them by concept
- Applies merge/deduplication rules
- Preserves source provenance
- Records conflicts and notes where appropriate
- Updates affected concept documents
- Rebuilds the knowledge index when required
- Records the resulting run information in the knowledge log

This creates an explicit validation gate:

```text
Extraction
    |
    v
Validation
    |
    v
Validated artifact
    |
    v
Merger
```

An extraction artifact that has not passed validation cannot be used as Merger input.

---

## Run Isolation

Every pipeline execution receives a unique `run_id`.

Extraction artifacts are stored under:

```text
state/extracts/<run_id>/
```

Validation artifacts are stored under:

```text
state/validated/<run_id>/
```

Example:

```text
state/
├── extracts/
│   └── 20260812-150401-c8da98f4/
│       ├── sp-official-....json
│       ├── sb-official-....json
│       ├── sd-official-....json
│       └── targeting-official-....json
│
└── validated/
    └── 20260812-150401-c8da98f4/
        └── validation-....json
```

The Validator processes only:

```text
state/extracts/<current-run-id>/
```

and the Merger loads only:

```text
state/validated/<current-run-id>/
```

This prevents Run A from accidentally consuming artifacts produced by Run B.

The test suite includes explicit cross-run isolation and concurrent-run coverage.

---

## Two Run Modes

### Offline Mode

Offline mode uses deterministic source snapshots stored in the repository.

These fixtures allow the parser, validator, merger, and idempotency behavior to be tested without relying on network availability or changing external websites.

> **Note:** Offline fixtures are test data. They are not presented as evidence of live Amazon ingestion.

Offline mode is useful for:

- Deterministic unit tests
- Regression testing
- Development
- Reproducible pipeline demonstrations
- Validating changes without network access

### Live Mode

Live mode fetches registered sources from their real URLs.

The deterministic fetch layer can be invoked with:

```bash
python3 scripts/fetch.py --all --live
```

The complete live workflow can also be executed through Claude Code:

```text
/ingest all
```

A live run records the real source URLs and fetch timestamps and persists the resulting extraction and validation artifacts using the run-specific artifact architecture.

For browser-dependent pages, Claude Code can use browser tooling when available.

The repository contains a demonstrated live ingestion run using multiple real Amazon Ads page types.

---

## Live Ingestion Evidence

A completed live run used the following run ID:

```text
20260812-150401-c8da98f4
```

The run produced extraction artifacts under:

```text
state/extracts/20260812-150401-c8da98f4/
```

and validation results under:

```text
state/validated/20260812-150401-c8da98f4/
```

The live run covered multiple Amazon Ads source/page types, including:

- Sponsored Products
- Sponsored Brands
- Sponsored Display
- Amazon Ads targeting documentation

The live run produced **151 extracted facts**:

| Classification | Count |
|---|---:|
| New | 146 |
| Changed | 5 |
| Duplicate | 0 |
| Conflict | 0 |
| Rejected | 0 |

The resulting facts retain their source URLs, source IDs, extracted timestamps, quotes, and classification metadata.

> **Important:** These artifacts were generated from a real live ingestion run rather than from the repository's offline fixtures.

---

## Two-Stage Artifact Handoff

The pipeline deliberately uses two persistent artifact stages.

### Extraction Stage

```text
state/extracts/<run_id>/
```

Contains the facts produced by the Extractor.

These artifacts are **not trusted as publishable knowledge**.

### Validation Stage

```text
state/validated/<run_id>/
```

Contains the output of the deterministic validation process.

Only this stage is allowed to feed the Merger.

The trust boundary is therefore:

```text
Untrusted extraction
        |
        v
    Validation
        |
        v
  Validated facts
        |
        v
      Merger
        |
        v
 Published knowledge
```

The test suite verifies that:

- Run A cannot consume Run B's extraction artifacts.
- The Validator consumes only the extraction artifacts for its run.
- The Merger cannot publish without the corresponding validation artifact.
- The Merger cannot bypass validation by reading `state/extracts/`.
- Rejected facts never reach the Merger.
- Valid facts can reach the Merger through `state/validated/`.
- Concurrent runs do not consume each other's artifacts.

---

## Write Protection

Writes to `knowledge/` are protected by a **PreToolUse Claude Code hook**.

The hook runs before the proposed write reaches the knowledge directory and validates the document against the repository's schema and constraints.

Relevant configuration:

```text
.claude/settings.json
scripts/hook_validate_pre.py
```

The hook is registered for knowledge-document write operations.

The purpose of the pre-write gate is to prevent invalid knowledge documents from being accepted by the write path in the first place rather than discovering the problem only after the file has already been written.

The hook is also covered by automated tests.

---

## How Re-run Safety Works

The pipeline uses whole-source hashing and section-level hashing to avoid unnecessary processing.

```text
fetch.py fetches and normalizes source content
        |
        v
Whole-source content is hashed
        +
Section-level content is hashed
        |
        v
state/manifest.json stores source state, whole-source hash, and section hashes
        |
        v
Source classified as:
new / changed / unchanged / error
        |
        v
For changed sources:
  - Sections classified as: changed / added / removed / unchanged
  - changed.txt created with only changed + added sections
  - Extractor reads changed.txt for semantic extraction
```

The pipeline then:

1. Stops unchanged sources before unnecessary downstream processing.
2. For changed sources, identifies which specific sections changed.
3. Sends only changed/added sections through extraction (not the full document).
4. Gives every pipeline execution a unique `run_id`.
5. Isolates extraction and validation artifacts by run.
6. Allows only validated facts to reach the Merger.
7. Updates only affected knowledge documents.
8. Rebuilds the knowledge index when its content changes.
9. Records pipeline activity in the run log.

The repository also contains:

```bash
sh scripts/demo_rerun.sh
```

This verifies that an unchanged rerun does not modify the contents of the `knowledge/` bundle.

> **Note:** `last_checked` in the manifest is runtime information, so the manifest itself is not expected to remain byte-identical between runs. The idempotency guarantee applies to the published knowledge bundle when upstream knowledge has not changed.

---

## Provenance Model

Every published knowledge fact retains source provenance.

Knowledge documents use `[S#]` markers that resolve to source entries in the document's frontmatter.

Source metadata includes:

- Source ID
- URL
- Source type
- Fetch date

The repository distinguishes source types including:

- `official`
- `api`
- `community`

Community claims are kept separate from official source claims.

The pipeline does not silently turn community information into official information.

When multiple sources disagree, the conflict is retained in the knowledge record and the source-priority rules are applied during merging.

This preserves the distinction between:

- What an official Amazon source states
- What an API/documentation source states
- What a community source claims
- Where sources disagree

---

## Knowledge Classification

Facts entering the Validator are classified against the existing knowledge base.

### `NEW`

The fact represents information that does not already exist in the relevant concept.

### `CHANGED`

The fact corresponds to an existing piece of knowledge but contains a meaningful updated value.

### `DUPLICATE`

The fact is substantively equivalent to an existing fact and does not need to create another copy.

### `CONFLICT`

The fact conflicts with an existing source-backed fact.

The conflict is retained rather than silently overwriting the previous information.

### `REJECTED`

The fact does not satisfy the required structural, provenance, or validation constraints and cannot proceed to the Merger.

These paths are covered by deterministic tests with explicit expected classifications.

---

## Knowledge Quality and OKF Bundle

The final output is an **OKF v0.1 knowledge bundle** stored under:

```text
knowledge/
```

The bundle contains:

```text
knowledge/
├── concepts/
├── index.md
└── log.md
```

Each concept document contains source-backed facts and provenance.

The index provides navigation across concepts, while the log records pipeline activity and relevant knowledge changes.

Validate the bundle with:

```bash
python3 scripts/validate_okf.py knowledge/concepts/
```

The index can be rebuilt using the deterministic index builder.

---

## Testing

Run the full suite with:

```bash
python3 -m unittest discover tests -v
```

The current repository has **139 passing tests**.

The tests cover the deterministic pipeline as well as the artifact-based Claude Code handoff.

### Test Coverage

- Source fetching
- Source normalization
- Content hashing
- Extraction persistence
- Extraction schema validation
- Validation result persistence
- Run-ID generation
- Run isolation
- Concurrent execution
- Artifact handoff
- Validation boundaries
- Rejected-fact filtering
- `NEW` classification
- `CHANGED` classification
- `DUPLICATE` classification
- `CONFLICT` classification
- Contamination protection
- Write-hook validation
- Index generation
- Run logging
- Pipeline handoff
- Idempotent reruns

The classification tests use deterministic fixtures and require the exact expected classification rather than accepting multiple possible outcomes.

---

## Repository Map

```text
.
├── CLAUDE.md
│   └── Agent behavior, scope, constraints, and the code-vs-Claude boundary
│
├── .claude/
│   ├── agents/
│   │   └── Scout, Extractor, Validator, and Merger subagents
│   ├── skills/
│   │   └── Knowledge-format, deduplication, merge, and citation guidance
│   ├── settings.json
│   │   └── Claude Code permissions and the PreToolUse validation hook
│   └── commands/
│       └── /ingest and related Claude Code commands
│
├── scripts/
│   └── Deterministic pipeline layer:
│       fetch, hashing, validation, indexing, logging,
│       run-ID generation, extraction persistence,
│       validation-result loading, and related utilities
│
├── sources/
│   └── Source registry and offline source snapshots
│
├── knowledge/
│   └── Published OKF knowledge bundle:
│       concept documents, index, and run log
│
├── state/
│   └── Manifest, schemas, run-specific extraction artifacts,
│       and run-specific validation artifacts
│
├── tests/
│   └── Unit and integration tests covering fetching,
│       validation, handoff, concurrency, hooks,
│       indexing, logging, and idempotency
│
└── docs/
    └── Architecture, design tradeoffs, decisions,
        and Claude Code usage documentation
```

---

## Design Principles

### Deterministic Code vs. Agent Reasoning

The system intentionally separates operations that require reasoning from operations that should be deterministic.

**Claude Code** handles semantic work such as extraction, classification, and knowledge merging.

**Python** handles state transitions, schemas, hashing, persistence, indexing, logging, and validation boundaries.

This makes the system easier to test and reason about.

### Least Privilege

The four agents have different responsibilities and corresponding tool access.

The **Merger** is the only agent responsible for publishing knowledge.

Other agents persist or validate artifacts rather than directly modifying the final knowledge base.

### Artifact-Based Handoff

Facts are persisted between stages rather than passed through conversational context.

This provides an inspectable contract between agents and makes run isolation possible.

### Provenance-First Knowledge

Facts are stored with source metadata and supporting evidence so that the resulting knowledge base can be traced back to the source material from which it was derived.

### Idempotent Publication

If upstream source content has not changed, rerunning the pipeline should not produce meaningless byte-level changes in the knowledge bundle.

---

## Known Limitations

- Source discovery is currently registry-driven. Discovering completely new sources requires adding them to the source registry or using an external discovery mechanism in live mode.
- Section-level change detection is implemented for Markdown sources only. HTML sources use whole-source hashing (section tracking not yet implemented for HTML).
- Offline fixtures are synthetic snapshots used for deterministic testing. They are intentionally separate from live-ingestion evidence.
- Alias matching in the concept registry is exact/lowercase rather than fuzzy. Semantic near-matches rely on Validator and agent reasoning.
- `last_checked` in the manifest is runtime state and can change between runs even when the published knowledge bundle remains unchanged.
- Live websites can change structure, content, or rendering behavior.
- Browser-dependent pages may require browser tooling for reliable acquisition.
- The knowledge base currently processes the sources registered in `sources/sources.yaml`. Broader coverage requires registering additional sources.
- Section-level hashing operates on Markdown heading boundaries, not paragraph-level semantic diffing. Section IDs depend on heading text stability (renaming headings creates new sections).

---

## Verification

The repository can be independently checked with:

```bash
# Run all automated tests
python3 -m unittest discover tests -v

# Validate the knowledge bundle
python3 scripts/validate_okf.py knowledge/concepts/

# Check the working tree for patch/whitespace errors
git diff --check

# Demonstrate idempotent knowledge publication
sh scripts/demo_rerun.sh
```

The combination of deterministic tests, run-isolated artifacts, validation artifacts, provenance, and live-ingestion evidence is intended to make the pipeline's behavior inspectable rather than relying solely on documentation claims.
