# RUN

Every command below was run against this commit. Output is pasted verbatim.
Agent-level runs are in `docs/run-transcripts.md`.

## Setup

    git clone https://github.com/shubhamChoudhary5502/amazon-AdsKb.git
    cd amazon-AdsKb

Python 3.9+ only. No pip installs, the deterministic layer is stdlib.

## Tests

    $ python3 -m unittest discover tests
    ...................
    ----------------------------------------------------------------------
    Ran 19 tests in 0.009s
    
    OK

## Bundle validation

    $ python3 scripts/validate_okf.py knowledge/concepts/
    OK

## Index is generator output, not hand-written

    $ python3 scripts/build_index.py
    index unchanged

## Idempotency proof

    $ sh scripts/demo_rerun.sh
    == knowledge/ checksum before ==
    f37b1b4b32021809ae3e42550790fc165e479b33c79aa15a2c74eb1a544dd4c2  -
    
    == fetch all (nothing edited since last run) ==
    UNCHANGED sp-official
    UNCHANGED sb-official
    UNCHANGED sd-official
    UNCHANGED targeting-official
    UNCHANGED acos-blog
    UNCHANGED ads-api-notes
    index unchanged
    
    == knowledge/ checksum after ==
    f37b1b4b32021809ae3e42550790fc165e479b33c79aa15a2c74eb1a544dd4c2  -
    PASS: bundle byte-identical after re-run
    
    == simulate an upstream edit ==
    CHANGED acos-blog
    CHANGED acos-blog
    (second fetch shows CHANGED again because the revert is itself a change;
     the agent pipeline would now re-extract only this source)

## Guard: a duplicate source id cannot shadow a real source

Appending a second `- id: sp-official` to sources.yaml, pointing at the
community blog fixture:

    $ python3 scripts/fetch.py --all
    ERROR duplicate source id in sources.yaml: sp-official
    exit=2

Before this guard the run reported `CHANGED sp-official` and would have
re-extracted the official Sponsored Products concept from a blog fixture.
