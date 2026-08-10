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
          |                                   (bookkeeping memory)
          |  NEW / CHANGED only
          v
    state/cache/<id>.txt  (normalized text the agents read)
          |
          v
    (scout) -> (extractor) -> (validator) -> (merger)
                                                 |
                                                 v  every Write/Edit
                                     [hook: scripts/hook_validate.py]
                                                 |  exit 2 blocks bad docs
                                                 v
    knowledge/concepts/*.md   + build_index.py + log_run.py

## Components

**Deterministic layer (scripts/, stdlib only)**

- `fetch.py`: fetch or read snapshot, strip HTML chrome (nav, footer,
  script, style), collapse whitespace, hash. Normalizing before hashing is
  what makes the hash mean "the content changed" rather than "any byte
  changed". Maintains the manifest.
- `okf.py` + `validate_okf.py`: a strict parser for this bundle's closed
  OKF profile and a validator that checks schema, citation integrity
  (every bullet cited, every citation resolvable), section order, and, in
  bundle mode, that related links exist and are symmetric.
- `hook_validate.py`: the same validator wired as a Claude Code
  PostToolUse hook. An invalid doc cannot be left on disk, because the
  hook exits 2 and forces the agent to fix it immediately.
- `build_index.py`, `log_run.py`: deterministic publishing. The index only
  rewrites on content difference.

**Judgment layer (.claude/agents/)**

Four subagents, one per fuzzy responsibility, each with the minimum tool
access it needs:

- `scout` (Read, Bash): runs fetch.py, reports which sources changed.
  It is forbidden from deciding change by reading content; only the hash
  verdict counts. Read-only with respect to knowledge/.
- `extractor` (Read): turns one changed source into atomic facts, each
  with a supporting quote and a proposed concept slug. Must consult the
  concept registry before proposing new slugs.
- `validator` (Read, Grep): classifies each fact against the existing
  bundle: new, changed, duplicate, conflict. Biased toward duplicate when
  unsure, because bundle bloat is the expensive failure.
- `merger` (Read, Write, Edit, Bash): the only agent allowed to write in
  knowledge/. Applies facts per the dedup-merge policy, maintains
  symmetric related links, recomputes confidence.

Separating extraction from validation from merging keeps each prompt
small and testable in isolation, and means the only writer in the whole
system sits behind the validation hook.

**Policy layer (.claude/skills/)**

Three skills hold the rules the agents share: `okf-format` (the document
schema), `dedup-merge` (concept identity and conflict resolution),
`citations` (marker discipline and how confidence is computed). Keeping
policy in skills rather than inlined in each agent means one place to
change a rule.

**State**

- `state/manifest.json`: hash memory per source. This is the re-run
  contract.
- `state/concepts.json`: slug and alias registry, the single source of
  truth for concept identity. The answer to "what counts as the same
  topic" lives here plus rule 3 of the dedup-merge skill (the
  practitioner's one-page test).
- `state/cache/`: normalized text, so agents never parse raw HTML.

## Tech choices

- Python stdlib only for the deterministic layer: a reviewer can clone
  and run with zero installs, and nothing in the exact-work path depends
  on an environment.
- A strict closed-subset frontmatter parser instead of PyYAML: the
  format is ours, strictness keeps every doc machine-readable forever,
  and it removes the only dependency the project would have had.
- Claude Code native primitives (subagents, skills, hooks, slash command)
  instead of an orchestration framework: the assignment's pipeline maps
  one-to-one onto them, and the hook gives a guarantee frameworks
  usually only promise.
