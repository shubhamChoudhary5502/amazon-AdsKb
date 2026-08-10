---
description: Run the full pipeline for one source or all sources
argument-hint: [source-id | all]
---

Run the acquisition pipeline per CLAUDE.md for: $ARGUMENTS

Stages: scout (change detection) -> extractor -> validator -> merger ->
publish (validate_okf.py, log_run.py, build_index.py). If the scout reports
UNCHANGED for everything, stop and report "no changes, bundle untouched".
