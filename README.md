# amazon-ads-kb

An autonomous knowledge acquisition system for Amazon Ads, built as a
Claude Code project. It discovers registered sources, fetches source
content, extracts structured facts, validates those facts against the
existing knowledge base, detects new/changed/duplicate/conflicting facts,
merges only validated knowledge, and publishes an OKF v0.1 knowledge bundle.

The system separates deterministic Python code from Claude Code agent work.
Claude Code performs source discovery, extraction, validation decisions, and
knowledge merging, while deterministic scripts handle fetching, hashing,
artifact persistence, validation, indexing, logging, and state management.

The pipeline is safe to re-run. Each ingestion execution receives a unique
`run_id`, and extraction and validation artifacts are isolated by run so that
independent or concurrent executions cannot consume each other's intermediate
results.

## Quick start

Requirements: Python 3.9+ and Claude Code. No pip installs are required; the
deterministic layer uses only the Python standard library.

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

The repository currently contains 110 passing tests covering the
deterministic pipeline, validation, artifact-based agent handoff, run
isolation, concurrency, write protection, indexing, logging, and
idempotency.

System overview

The system is organized around a strict boundary between Claude Code agents
and deterministic Python code.

Claude Code is responsible for reasoning-heavy work:

discovering which registered sources should be processed
extracting facts from source content
classifying facts against existing knowledge
identifying conflicts and provenance
deciding which knowledge concepts need to be updated

The deterministic layer is responsible for operations that must be
repeatable and mechanically enforced:

fetching and normalizing source content
calculating content hashes
maintaining the source manifest
generating run IDs
persisting extraction artifacts
validating extraction artifacts
enforcing the validation boundary
loading validated facts
building the knowledge index
writing run logs
enforcing write-time schema checks

The boundary is deliberate: Claude Code does not directly control the
low-level state transitions that determine whether unvalidated information
can reach the published knowledge base.

Ingestion architecture

The ingestion pipeline uses four specialized Claude Code agents:

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

The agents do not pass extracted facts to one another through conversational
context. Instead, each stage produces a persisted artifact that becomes the
input contract for the next stage.

This makes the handoff inspectable, reproducible, and isolated between runs.

Scout

The Scout identifies the sources that should be processed for the current
ingestion and generates a unique run_id.

The same run ID is passed to all downstream stages.

Example:

20260812-150401-c8da98f4

The run ID becomes the namespace for all intermediate artifacts created
during that execution.

Extractor

The Extractor reads the fetched source content and produces structured facts.

Each extraction artifact contains information such as:

run_id
source ID
source URL
source type
extracted timestamp
content hash
extracted facts
concept
supporting quote/provenance

Artifacts are persisted under:

state/extracts/<run_id>/

The Extractor does not publish directly to the knowledge base.

Validator

The Validator consumes only the extraction artifacts belonging to the
current run.

It validates the structure and provenance of extracted facts and classifies
them against the existing knowledge base.

The classification paths include:

new
changed
duplicate
conflict
rejected

Validated results are persisted under:

state/validated/<run_id>/

The Validator is also responsible for ensuring that malformed, incomplete,
contaminated, or otherwise invalid facts do not reach the Merger.

Merger

The Merger consumes only the validated artifacts for the current run.

It does not read raw extraction artifacts directly.

The Merger:

loads validated facts for the current run
groups them by concept
applies the merge/deduplication rules
preserves source provenance
records conflicts and notes where appropriate
updates affected concept documents
rebuilds the knowledge index when required
records the resulting run information in the knowledge log

This creates an explicit validation gate:

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

An extraction artifact that has not passed validation cannot be used as
Merger input.

Run isolation

Every pipeline execution receives a unique run_id.

Extraction artifacts are stored under:

state/extracts/<run_id>/

Validation artifacts are stored under:

state/validated/<run_id>/

For example:

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

The Validator processes only:

state/extracts/<current-run-id>/

and the Merger loads only:

state/validated/<current-run-id>/

This prevents Run A from accidentally consuming artifacts produced by Run B.

The test suite includes explicit cross-run isolation and concurrent-run
coverage.

Two run modes
Offline

Offline mode uses deterministic source snapshots stored in the repository.

These fixtures allow the parser, validator, merger, and idempotency behavior
to be tested without relying on network availability or changing external
websites.

Offline fixtures are test data. They are not presented as evidence of live
Amazon ingestion.

The offline mode is useful for:

deterministic unit tests
regression testing
development
reproducible pipeline demonstrations
validating changes without network access
Live

Live mode fetches registered sources from their real URLs.

The deterministic fetch layer can be invoked with:

python3 scripts/fetch.py --all --live

The complete live workflow can also be executed through Claude Code:

/ingest all

A live run records the real source URLs and fetch timestamps and persists
the resulting extraction and validation artifacts using the run-specific
artifact architecture.

For browser-dependent pages, Claude Code can use browser tooling when
available.

The repository contains a demonstrated live ingestion run using multiple
real Amazon Ads page types.

Live ingestion evidence

A completed live run used the following run ID:

20260812-150401-c8da98f4

The run produced extraction artifacts under:

state/extracts/20260812-150401-c8da98f4/

and validation results under:

state/validated/20260812-150401-c8da98f4/

The live run covered multiple Amazon Ads source/page types, including:

Sponsored Products
Sponsored Brands
Sponsored Display
Amazon Ads targeting documentation

The live run produced 151 extracted facts:

146 classified as new
5 classified as changed
0 duplicates
0 conflicts
0 rejected

The resulting facts retain their source URLs, source IDs, extracted
timestamps, quotes, and classification metadata.

The important distinction is that these artifacts were generated from a
real live ingestion run rather than from the repository's offline fixtures.

Two-stage artifact handoff

The pipeline deliberately uses two persistent artifact stages.

Extraction stage
state/extracts/<run_id>/

contains the facts produced by the Extractor.

These artifacts are not trusted as publishable knowledge.

Validation stage
state/validated/<run_id>/

contains the output of the deterministic validation process.

Only this stage is allowed to feed the Merger.

This gives the pipeline an explicit trust boundary:

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

The test suite verifies that:

Run A cannot consume Run B's extraction artifacts.
The Validator consumes only the extraction artifacts for its run.
The Merger cannot publish without the corresponding validation artifact.
The Merger cannot bypass validation by reading state/extracts/.
Rejected facts never reach the Merger.
Valid facts can reach the Merger through state/validated/.
Concurrent runs do not consume each other's artifacts.
Write protection

Writes to knowledge/ are protected by a PreToolUse Claude Code hook.

The hook runs before the proposed write reaches the knowledge directory and
validates the document against the repository's schema and constraints.

The relevant configuration is:

.claude/settings.json
scripts/hook_validate_pre.py

The hook is registered for knowledge-document write operations.

The purpose of the pre-write gate is to prevent invalid knowledge documents
from being accepted by the write path in the first place rather than
discovering the problem only after the file has already been written.

The hook is also covered by automated tests.

How re-run safety works

The pipeline uses source hashing and a manifest to avoid unnecessary
processing.

fetch.py fetches and normalizes source content.
Normalized content is hashed.
state/manifest.json stores the source state and last known hash.
Sources are classified as new, changed, unchanged, or error.
Unchanged sources can stop before unnecessary downstream processing.
Changed sources continue through extraction and validation.
Every pipeline execution receives a unique run_id.
Extraction and validation artifacts are isolated by run.
Only validated facts reach the Merger.
Only affected knowledge documents are updated.
The knowledge index is rebuilt when its content changes.
The run log records the resulting pipeline activity.

The repository also contains:

sh scripts/demo_rerun.sh

which verifies that an unchanged rerun does not modify the contents of the
knowledge/ bundle.

The manifest contains runtime information such as last_checked, so the
manifest itself is not expected to remain byte-identical between runs.

The idempotency guarantee applies to the published knowledge bundle when
the upstream knowledge has not changed.

Provenance model

Every published knowledge fact retains source provenance.

Knowledge documents use [S#] markers that resolve to source entries in the
document's frontmatter.

Source metadata includes:

source ID
URL
source type
fetch date

The repository distinguishes source types including:

official
api
community

Community claims are kept separate from official source claims.

The pipeline does not silently turn community information into official
information.

When multiple sources disagree, the conflict is retained in the knowledge
record and the source-priority rules are applied during merging.

This preserves the distinction between:

what an official Amazon source states
what an API/documentation source states
what a community source claims
where sources disagree
Knowledge classification

Facts entering the Validator are classified against the existing knowledge
base.

NEW

The fact represents information that does not already exist in the relevant
concept.

CHANGED

The fact corresponds to an existing piece of knowledge but contains a
meaningful updated value.

DUPLICATE

The fact is substantively equivalent to an existing fact and does not need
to create another copy.

CONFLICT

The fact conflicts with an existing source-backed fact.

The conflict is retained rather than silently overwriting the previous
information.

REJECTED

The fact does not satisfy the required structural, provenance, or validation
constraints and cannot proceed to the Merger.

These paths are covered by deterministic tests with explicit expected
classifications.

Knowledge quality and OKF bundle

The final output is an OKF v0.1 knowledge bundle stored under:

knowledge/

The bundle contains:

knowledge/
├── concepts/
├── index.md
└── log.md

Each concept document contains source-backed facts and provenance.

The index provides navigation across concepts, while the log records
pipeline activity and relevant knowledge changes.

The bundle can be checked with:

python3 scripts/validate_okf.py knowledge/concepts/

The index can be rebuilt using the deterministic index builder.

Testing

Run the full suite with:

python3 -m unittest discover tests -v

The current repository has 110 passing tests.

The tests cover the deterministic pipeline as well as the artifact-based
Claude Code handoff.

Important test areas include:

source fetching
source normalization
content hashing
extraction persistence
extraction schema validation
validation result persistence
run-ID generation
run isolation
concurrent execution
artifact handoff
validation boundaries
rejected-fact filtering
NEW classification
CHANGED classification
DUPLICATE classification
CONFLICT classification
contamination protection
write-hook validation
index generation
run logging
pipeline handoff
idempotent reruns

The classification tests use deterministic fixtures and require the exact
expected classification rather than accepting multiple possible outcomes.

Repository map
CLAUDE.md
    Agent behavior, scope, constraints, and the code-vs-Claude boundary

.claude/agents/
    Scout, Extractor, Validator, and Merger subagents

.claude/skills/
    Knowledge-format, deduplication, merge, and citation guidance

.claude/settings.json
    Claude Code permissions and the PreToolUse validation hook

.claude/commands/
    /ingest and related Claude Code commands

scripts/
    Deterministic pipeline layer:
    fetch, hashing, validation, indexing, logging,
    run-ID generation, extraction persistence,
    validation-result loading, and related utilities

sources/
    Source registry and offline source snapshots

knowledge/
    Published OKF knowledge bundle:
    concept documents, index, and run log

state/
    Manifest, schemas, run-specific extraction artifacts,
    and run-specific validation artifacts

tests/
    Unit and integration tests covering fetching,
    validation, handoff, concurrency, hooks,
    indexing, logging, and idempotency

docs/
    Architecture, design tradeoffs, decisions,
    and Claude Code usage documentation
Design principles
Deterministic code vs. agent reasoning

The system intentionally separates operations that require reasoning from
operations that should be deterministic.

Claude Code handles semantic work such as extraction, classification, and
knowledge merging.

Python handles state transitions, schemas, hashing, persistence, indexing,
logging, and validation boundaries.

This makes the system easier to test and reason about.

Least privilege

The four agents have different responsibilities and corresponding tool
access.

The Merger is the only agent responsible for publishing knowledge.

Other agents persist or validate artifacts rather than directly modifying
the final knowledge base.

Artifact-based handoff

Facts are persisted between stages rather than passed through conversational
context.

This provides an inspectable contract between agents and makes run isolation
possible.

Provenance-first knowledge

Facts are stored with source metadata and supporting evidence so that the
resulting knowledge base can be traced back to the source material from
which it was derived.

Idempotent publication

If upstream source content has not changed, rerunning the pipeline should
not produce meaningless byte-level changes in the knowledge bundle.

Known limitations
Source discovery is currently registry-driven. Discovering completely new
sources requires adding them to the source registry or using an external
discovery mechanism in live mode.
Change detection is primarily source/document-level. Section-level
change detection could reduce re-extraction when only a small part of a
source changes.
Offline fixtures are synthetic snapshots used for deterministic testing.
They are intentionally separate from live-ingestion evidence.
Alias matching in the concept registry is exact/lowercase rather than
fuzzy. Semantic near-matches rely on validator and agent reasoning.
last_checked in the manifest is runtime state and can change between
runs even when the published knowledge bundle remains unchanged.
Live websites can change structure, content, or rendering behavior.
Browser-dependent pages may require browser tooling for reliable
acquisition.
The knowledge base currently processes the sources registered in
sources/sources.yaml. Broader coverage requires registering additional
sources.
Section-level incremental extraction is not yet implemented. A changed
source is currently considered at the source/document level rather than
tracking independent sections within the document.
Verification

The repository can be independently checked with:

# Run all automated tests
python3 -m unittest discover tests -v

# Validate the knowledge bundle
python3 scripts/validate_okf.py knowledge/concepts/

# Check the working tree for patch/whitespace errors
git diff --check

# Demonstrate idempotent knowledge publication
sh scripts/demo_rerun.sh

The combination of deterministic tests, run-isolated artifacts, validation
artifacts, provenance, and live-ingestion evidence is intended to make the
pipeline's behavior inspectable rather than relying solely on documentation
claims.