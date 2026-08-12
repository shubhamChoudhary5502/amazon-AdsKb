# Design Decisions

## 1. Strict closed-subset parser instead of PyYAML

I initially considered using a YAML library, but decided against it. Since I control the format of these documents, I only need to support scalars, inline lists, and one level of list-of-dicts.

Keeping the parser limited to this makes the output predictable and machine-readable. The downside is that it isn't a full YAML parser, so there are some edge cases that real YAML would handle differently. For example, I don't allow colons in descriptions, and the validator checks for that.

## 2. Document-level hashing instead of section-level hashing

Section-level hashing would be more efficient for larger documents because we could re-process only the part that changed. But with only six sources right now, I felt that was unnecessary complexity.

Hashing the whole source is simple, exact, and easy to test. If this had to scale to a much larger set of documents, section-level hashing would probably be one of the first things I'd add.

## 3. Four subagents instead of one large prompt

I wanted each agent to have a clear responsibility and only the tools it actually needs.

The scout can use bash but can't write files, the extractor is read-only, the validator can read and grep, and the merger is the only agent that can actually write.

This also gives some security by design, instead of just relying on instructions telling the agents not to do something.

## 4. Hook-based validation instead of agent self-validation

I used a hook for validation instead of asking the agent to validate its own work. My thinking was that an instruction inside a prompt can potentially be missed, especially when the context gets large, while a hook will run regardless.

One issue I found during testing was that if the hook uses a relative path for its working directory, it can fail silently and end up validating nothing. That's actually worse than not having the hook, so that's something I had to account for.

## 5. Registry-based discovery instead of open web crawling

I considered having the scout search for new sources automatically, but that brings in a few extra problems: search MCP requirements, deciding which domains to trust, and potentially needing human approval for unknown sources.

So for this version, I made the source registry explicit. The tradeoff is that the system currently maintains the knowledge it is given, but it doesn't discover new sources on its own yet.

## 6. Frontmatter sources and `[S#]` markers instead of OKF section 8 citations

The OKF specification puts citations into a numbered section at the bottom of the document. I didn't find that sufficient for this use case because I wanted provenance at the individual fact level, including things like the source type and fetch date.

That information is also useful later for conflict resolution and confidence scoring. So this is a deliberate deviation from the spec, and I've documented it rather than treating it as an accidental difference.

## 7. Strict producer, permissive consumer

There is a slight difference between what section 9 of the spec says and what my validator does. The spec says consumers shouldn't reject a bundle just because it contains unknown keys, while my validator is stricter and rejects them.

I don't see that as a contradiction because my validator is acting as a producer-side quality gate. I'd rather stop a document from drifting when my system is creating it, while still allowing another consumer to read documents with additional metadata.

## 8. Offline fixtures instead of live scraping for tests

I ran into the practical issue that Amazon blocks a basic `urllib` request with a 403, and some of the pages also depend on JavaScript. Proper live fetching would therefore need something like the Playwright MCP.

For testing, I chose snapshots instead because they make the runs deterministic and mean someone can clone the repo and test it without needing network access.

The tradeoff is that the six fixtures are still hand-made snapshots, so I wouldn't claim they represent six completely independent live sources.

## 9. PostToolUse hook instead of PreToolUse (SUPERSEDED)

**DECISION SUPERSEDED - See Decision #9A for current implementation**

A pre-write hook inspects the content the agent proposes to write. A post-write hook reads the file that actually landed on disk. I went with post because it validates the real result, which matters most for partial edits where the proposed change looks fine on its own but the merged file does not.

The cost showed up in testing. PostToolUse blocks the agent from continuing, but it cannot undo the write, so a rejected document stays on disk and fails bundle validation until someone removes it. The per-file gate does its job, but the bundle is briefly inconsistent. With more time I'd have the hook restore the previous version of the file when it rejects a write, which is what would actually guarantee that an invalid document never lands. This is demonstrated in RUN 3c of docs/run-transcripts.md.

**Why this was superseded:** The implementation was subsequently changed to PreToolUse because:
- PreToolUse validates BEFORE the write executes, preventing invalid files from ever being created
- No cleanup or rollback mechanism required
- True atomic behavior at the tool level
- Invalid writes are blocked before file creation

The current implementation uses `scripts/hook_validate_pre.py` as registered in `.claude/settings.json`.

## 9A. Use PreToolUse for knowledge write validation (CURRENT)

**CURRENT IMPLEMENTATION - Supersedes Decision #9**

The implementation now uses PreToolUse validation instead of PostToolUse. The PreToolUse hook (`scripts/hook_validate_pre.py`) validates documents BEFORE they reach disk.

**Why PreToolUse is now preferred:**
- Validates the proposed content before the write executes
- Invalid Write operations are blocked (target file is never created)
- Invalid Edit operations are blocked (existing file remains unchanged)
- No cleanup required for rejected writes
- Atomic behavior: invalid documents never reach disk
- Clear error messages before write attempts

**Current hook configuration:** `.claude/settings.json` registers:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/scripts/hook_validate_pre.py\""
          }
        ]
      }
    ]
  }
}
```

**Test coverage:** `tests/test_hook_validate.py` verifies current PreToolUse behavior including:
- Invalid writes are blocked before file creation
- Original files remain unchanged on invalid edit attempts
- Valid writes and edits proceed normally
- Hook fails gracefully with malformed input
- Hook ignores non-knowledge files

The old PostToolUse script (`scripts/hook_validate.py`) may still exist for historical reference but is not the active hook.

## 10. Artifact-based handoff vs conversational context passing (CURRENT)

**CURRENT IMPLEMENTATION**

The pipeline uses artifact-based handoff between stages instead of conversational context passing. Each stage persists artifacts to run-specific directories:

- Scout generates unique `run_id`
- Extractor persists to `state/extracts/<run_id>/`
- Validator consumes ONLY from `state/extracts/<run_id>/`, persists to `state/validated/<run_id>/`
- Merger consumes ONLY from `state/validated/<run_id>/` (bypass protection enforced)

**Why artifact-based handoff is preferred:**
- Complete provenance tracking for every fact
- Run isolation prevents cross-contamination
- Historical runs can be audited and debugged
- Clear stage boundaries enforced by scripts
- Bypass protection prevents merger from reading extracts directly
- Reproducible pipeline execution

**Stage boundaries:**
- `persist_extraction.py` ensures proper artifact storage with run_id, source metadata, timestamps
- `validate_extraction.py` ensures only current run's artifacts are processed
- `load_validation_results.py` ensures merger can only access validated facts
- Merger prohibited from reading `state/extracts/` directly

**Verification:** 110 passing tests include explicit tests for run isolation, bypass protection, and artifact handoff. Live run `20260812-150401-c8da98f4` demonstrates the system with 151 real facts.

## 11. Turned down a normalisation change the agent proposed mid-run

During RUN 2b, after correctly classifying all 22 restated facts as duplicates, Claude suggested stripping everything after `</html>` during normalisation so the same content wouldn't be re-extracted on every run.

I declined. The churn only existed because I had edited the fixture with `printf >>`, which appends past the closing tag. A real page wouldn't change that way, so the fix would have been tuned to my test method rather than to the actual problem. That's how you end up with a system that only works on your own tests.
