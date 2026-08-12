---
description: Run the full artifact-based pipeline for one source or all sources
argument-hint: [source-id | all]
---

Run the acquisition pipeline per CLAUDE.md for: $ARGUMENTS

CRITICAL: This pipeline uses artifact-based handoff with run ID isolation.

Artifact-based workflow:
1. Scout generates run_id and detects changes
2. For each changed source:
   - Extractor reads cache, persists to state/extracts/<run_id>/<source-id>-<timestamp>.json
3. Validator consumes ALL extraction artifacts from state/extracts/<run_id>/, persists to state/validated/<run_id>/validation-<timestamp>.json
4. Merger loads ONLY from state/validated/<run_id>/, writes to knowledge/concepts/
5. Publish: validate_okf.py, log_run.py, build_index.py

Run ID isolation guarantees:
- Run A cannot consume Run B's extraction artifacts
- Tests don't interfere with live runs
- Concurrent runs don't cross-contaminate

Stages: scout -> extractor -> validator -> merger -> publish.

If the scout reports UNCHANGED for everything, stop and report "no changes, bundle untouched".

IMPORTANT: Each agent must use the run_id from the scout. Never pass facts through conversation.
