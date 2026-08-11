# Design document: tradeoffs, gaps, and how Claude Code was used

## The one real choice: where code ends and Claude begins

The brief asks for the line to be picked and explained. The line here is:
anything with a right answer is code, anything needing meaning is Claude.

Concretely, code owns fetch, normalize, hash, change detection, schema
validation, citation integrity, link symmetry, index and log. Claude
owns concept identity, fact extraction, duplicate judgment, and conflict
handling. The enforcement is structural, not aspirational: the merger is
the only agent with write access to knowledge/, and a PostToolUse hook
runs the schema validator on every one of its writes, blocking on failure.
Claude physically cannot publish an uncited or malformed fact.

Why this line and not further toward code? Section-similarity scoring or
embedding-based dedup could move duplicate detection into code. It was
considered and rejected for this scope: it adds a dependency and a tuning
problem, while "would a practitioner expect these facts on one page" is
exactly the judgment LLMs are good at, and the failure mode (an extra
merge review) is cheap. Why not further toward Claude? Letting the agent
eyeball "has this page changed" invites drift and burns tokens on
unchanged sources. Hashes are free and exact.

## What counts as the same topic

Concept identity is the hardest sub-problem, and hashing does not touch
it. The design is a registry (state/concepts.json) of canonical slugs and
aliases, consulted by the extractor before proposing slugs and by the
validator before classifying. New aliases accumulate over runs, so the
registry gets better at catching rename-style duplicates the longer the
system lives. The residual risk, semantic near-misses that no alias
covers, is handled by an explicit rule biasing the validator toward
"duplicate" when unsure, because a missed nuance costs one fact while a
duplicate doc poisons every future merge.

## What counts as changed

Three levels were considered:

1. Skip-if-unchanged (whole-source hash). Implemented, tested, proven by
   scripts/demo_rerun.sh.
2. Real change detection (which claims moved). Implemented at the agent
   level: the validator classifies facts as changed when a source updates
   a value it previously stated, and the merger replaces the line and
   dates the change in Conflicts and notes.
3. Section-level hashing so an edit re-extracts one section, not the
   whole source. Not built. It is the first thing to add with more time,
   since it cuts extraction cost on large official docs by an order of
   magnitude.

Normalization before hashing matters more than it looks: stripping nav,
footers, scripts, and whitespace means a CMS re-render or a tracking
parameter does not masquerade as a content change. There is a test
asserting whitespace edits do not move the hash.

## Provenance and the hallucination problem

The rule is blunt: no source id, no sentence. It is enforced twice, once
as agent policy and once mechanically, since the validator rejects any
Key facts or Community claims bullet without a resolvable [S#] marker.
Community claims are quarantined in their own section and can never
silently upgrade to fact. The bundle ships a live demonstration of the
conflict policy: a community source contradicts the official top-of-search
boost cap, the official value stays in Key facts, and the disagreement is
permanently recorded in bidding-strategies.md. It also ships an honest
weakness on purpose: acos-roas.md rests on one community source, so its
confidence is capped at low and flagged for corroboration, rather than
being quietly promoted because "everyone knows the formula".

## Idempotency contract, precisely stated

Re-running with no upstream changes leaves knowledge/ byte-identical.
state/ is deliberately outside the contract: last_checked moves every run
because "when did we last look" is audit information worth keeping. The
alternative, freezing state too, would have made the system look purer in
a demo while destroying the audit trail. Contract on the output, honesty
in the bookkeeping.

## What I would improve with more time

- Section-level change detection (above).
- A discovery scout that proposes new sources from search results with a
  human approval step, instead of the registry being hand-edited.
- Fuzzy alias matching (normalized edit distance) as a pre-filter before
  the validator's semantic check.
- Relation-aware classification: a new fact adjacent to an existing one
  (portfolio budgets next to campaign budgets) is currently classified
  new and appended, when it should be recognised as extending the
  existing line.
- Contradiction sweep: a periodic agent pass that re-reads all docs and
  looks for cross-document conflicts, not just within-merge ones.
- Live-mode hardening: retries, rate limiting, robots.txt respect, and
  content-type detection beyond the current heuristic.
- OKF conformance against the published spec test suite, if one exists.
  The validator enforces this repo's documented profile of v0.1.

## How Claude Code was used to build this

I used Claude Code as the primary builder and treated my own role as
direction, review, and verification. Most of the initial scaffolding came
from it: the folder structure, first drafts of the scripts, the four agent
prompts, and the three skills. But I didn't just accept everything blindly.
I read through CLAUDE.md and all the agent files before running anything,
because during the call I need to be able to explain and defend every rule
in them, rather than point at them and say Claude wrote it.

The architecture is not decoration. Pipeline stages are subagents, shared
policy lives in skills, the quality gate is a hook, and there is no
orchestration framework anywhere. The merger is the only agent with write
access to knowledge/, so every write passes through the validator.

The environment was my own mess to deal with. I set up WSL fresh on Windows
and hit an issue where my old Windows npm install of Claude Code was
shadowing the Linux one after an auto-update broke the nvm path. I fixed it
with hash -r and cleaning up PATH, and learned the hard way not to launch
Claude from a /mnt/c path. That lesson came back a second time and cost me
more: I ended up with two copies of this repo, one holding the git history
and the remote, the other holding a session's worth of uncommitted work.
Reconciling them ate an hour. Untracked work in a second directory is work
you do not have.

Three things broke in ways that reading the code would not have caught.

The validation hook was silently doing nothing. settings.json invoked it as
python3 scripts/hook_validate.py, a path resolved against the session working
directory rather than the project root. The moment an agent cd'd into
knowledge/concepts, the hook failed to start and the write went through
unvalidated. I only saw it because the error surfaced in a transcript. Fixed
by anchoring the command to $CLAUDE_PROJECT_DIR. A quality gate that fails
open is worse than no gate, because you stop looking.

The authoring skill drifted from the validator. I added description and
timestamp to REQUIRED_KEYS but did not update okf-format/SKILL.md, so anyone
authoring a doc from the skill alone would have written an invalid one. The
agent flagged the mismatch on the next run rather than working around it.

Early on, Claude called log_run.py with no arguments. The script rejected it
with exit code 2 and Claude corrected itself and retried properly. I liked
seeing that, because it is the deterministic layer catching the agent instead
of the agent being trusted.

Testing also surfaced a real gap in the validator's judgment. When a source
added a fact about portfolio-level budgets, it was classified new rather than
recognised as related to the existing campaign-level budget line. Worth
separating from a case it does handle well: a later run where the same source
gained two reworded restatements produced 22 extracted facts, all 22
classified duplicate, and zero merges. Restatement is handled. Relating a
genuinely new fact to an adjacent existing one is not.

Every one of these was caught because a script or a transcript disagreed with
what the agent reported, not because I read the code carefully. That is the
whole argument for the deterministic layer. The tests, demo_rerun.sh, and
docs/run-transcripts.md exist so that nobody, including me, has to take the
agent's word for how this system behaves. If a claim in this repo matters,
there should be something a reviewer can run that proves it.
