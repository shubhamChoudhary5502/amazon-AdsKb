# System and agent architecture

## The shape of the problem

The pipeline is five stages, but architecturally it is two kinds of work
glued together: exact bookkeeping (fetch, hash, diff, validate, write
logs) and semantic judgment (what is a concept, what does a page claim,
do two claims mean the same thing). The design principle of this repo is
that each kind of work goes to the tool that is reliable at it. Code does
bookkeeping. Claude does judgment. Neither crosses over.

## Data flow

    sources/sources.yaml
          |
          v
    [scripts/fetch.py]  normalize -> sha256 -> compare state/manifest.json
          |                                   (bookkeeping memory with locking)
          |  NEW / CHANGED only
          v
    state/cache/<id>.txt  (normalized text the agents read)
          |
          v
    (scout) -> generates run_id
          |
          v
    (extractor) -> persists to state/extracts/<run_id>/
          |
          v
    (validator) -> reads ONLY state/extracts/<run_id>/
                | -> persists to state/validated/<run_id>/
          |
          v
    (merger) -> reads ONLY state/validated/<run_id>/
                | -> cannot read state/extracts/ (bypass protection)
          |
          v  every Write/Edit
    [PreToolUse hook: scripts/hook_validate_pre.py]
          |  exit 2 blocks bad docs BEFORE write
          v
    knowledge/concepts/*.md   + build_index.py + log_run.py

## Artifact-based pipeline architecture

The current implementation uses artifact-based handoff between pipeline stages, NOT conversational context passing:

```
Scout
  |
  | generate run_id
  v
Extractor
  |
  | persist extraction artifact
  v
state/extracts/<run_id>/
  |
  | deterministic validation
  v
Validator
  |
  | persist validation artifact
  v
state/validated/<run_id>/
  |
  | validated facts only
  v
Merger
  |
  v
knowledge/
```

**Run isolation:** Each pipeline execution generates a unique `run_id` (format: `YYYYMMDD-HHMMSS-<random>`). All artifacts for that run are stored under run-specific directories:
- `state/extracts/<run_id>/` - extraction artifacts
- `state/validated/<run_id>/` - validation artifacts

This ensures:
- Run A artifacts are completely isolated from Run B artifacts
- Concurrent runs cannot cross-contaminate
- Historical runs can be inspected and audited
- Failed runs can be diagnosed without affecting other runs

**Stage boundaries enforced:**
- **Extractor → Validator:** Validator consumes ONLY extraction artifacts from `state/extracts/<run_id>/`
- **Validator → Merger:** Merger consumes ONLY validation artifacts from `state/validated/<run_id>/`
- **Merger bypass protection:** Merger is prohibited from reading `state/extracts/` directly, ensuring only validated facts reach knowledge documents

**Facts are NOT passed through conversational context.** Each stage persists artifacts to disk, and the next stage loads only those artifacts.

## Components

**Deterministic layer (scripts/, stdlib only)**

- `generate_run_id.py`: generates unique run IDs with timestamp and random suffix
- `persist_extraction.py`: persists extraction artifacts to `state/extracts/<run_id>/`
- `validate_extraction.py`: loads extraction artifacts, classifies facts as new/changed/duplicate/conflict/rejected, persists to `state/validated/<run_id>/`
- `load_validation_results.py`: loads validated facts for merger (ensures bypass protection)
- `fetch.py`: fetch or read snapshot, strip HTML chrome (nav, footer, script, style),
  collapse whitespace, hash. Uses file locking for safe concurrent manifest updates.
  Normalizing before hashing is what makes the hash mean "the content changed" rather
  than "any byte changed". Maintains the manifest.
- `okf.py` + `validate_okf.py`: a strict parser for this bundle's closed OKF profile
  and a validator that checks schema, citation integrity (every bullet cited, every
  citation resolvable), section order, and, in bundle mode, that related links exist
  and are symmetric.
- `hook_validate_pre.py`: PreToolUse hook that validates knowledge documents BEFORE
  they reach disk. Invalid Write/Edit operations are blocked before file creation.
- `build_index.py`, `log_run.py`: deterministic publishing. The index only rewrites
  on content difference.

**Judgment layer (.claude/agents/)**

Four subagents, one per fuzzy responsibility, each with the minimum tool access it needs:

- `scout` (Read, Bash): generates run_id, runs fetch.py, reports which sources changed.
  It is forbidden from deciding change by reading content; only the hash verdict counts.
  Read-only with respect to knowledge/.

- `extractor` (Read, Bash): loads normalized text from `state/cache/<id>.txt`, extracts atomic
  facts with supporting quotes and proposed concept slugs, persists extraction artifacts
  to `state/extracts/<run_id>/`. Must consult the concept registry before proposing new slugs.
  Does NOT return facts through conversation - must persist artifacts.

- `validator` (Read, Grep, Bash): consumes ONLY extraction artifacts from `state/extracts/<run_id>/`,
  classifies each fact as new, changed, duplicate, conflict, or rejected using deterministic
  rules, persists validation artifacts to `state/validated/<run_id>/`. Biased toward duplicate
  when unsure, because bundle bloat is the expensive failure. Does NOT receive facts through
  conversation.

- `merger` (Read, Write, Edit, Bash): the only agent allowed to write in knowledge/. Loads
  ONLY validation artifacts from `state/validated/<run_id>/` using `load_validation_results.py`.
  Cannot read `state/extracts/` directly (bypass protection). Applies facts per the dedup-merge
  policy, maintains symmetric related links, recomputes confidence.

Separating extraction from validation from merging keeps each prompt small and testable in
isolation, and means the only writer in the whole system sits behind the validation hook.

**Policy layer (.claude/skills/)**

Three skills hold the rules the agents share: `okf-format` (the document schema), `dedup-merge`
(concept identity and conflict resolution), `citations` (marker discipline and how confidence is
computed). Keeping policy in skills rather than inlined in each agent means one place to change
a rule.

**State**

- `state/manifest.json`: hash memory per source. This is the re-run contract. Uses file locking
  for safe concurrent updates.
- `state/concepts.json`: slug and alias registry, the single source of truth for concept identity.
  The answer to "what counts as the same topic" lives here plus rule 3 of the dedup-merge skill
  (the practitioner's one-page test).
- `state/cache/`: normalized text, so agents never parse raw HTML.
- `state/extracts/<run_id>/`: run-specific extraction artifacts
- `state/validated/<run_id>/`: run-specific validation artifacts

## Tech choices

- Python stdlib only for the deterministic layer: a reviewer can clone and run with zero installs,
  and nothing in the exact-work path depends on an environment.
- A strict closed-subset frontmatter parser instead of PyYAML: the format is ours, strictness keeps
  every doc machine-readable forever, and it removes the only dependency the project would have had.
- Claude Code native primitives (subagents, skills, hooks, slash command) instead of an orchestration
  framework: the assignment's pipeline maps one-to-one onto them, and the PreToolUse hook gives a
  guarantee frameworks usually only promise - validation BEFORE write, not after.
- Run-specific artifact directories provide isolation and auditability without requiring database
  infrastructure.
- File locking on manifest.json prevents race conditions during concurrent runs.

## Current implementation verification

**110 passing tests** covering:
- Run isolation between concurrent executions
- Artifact handoff between pipeline stages
- Merger bypass protection (cannot read extracts directly)
- PreToolUse hook validation before write
- Manifest locking for concurrent access
- Complete pipeline end-to-end with real data

**Live ingestion completed:** run ID `20260812-150401-c8da98f4`
- 4 real Amazon Ads sources fetched live
- 151 facts extracted and validated
- 146 new, 5 changed, 0 duplicate, 0 conflict, 0 rejected
- 16 concept documents in knowledge bundle
