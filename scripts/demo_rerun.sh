#!/bin/sh
# End-to-end idempotency proof. Run from repo root.
# Shows: (1) re-run with no source changes touches nothing in knowledge/,
#        (2) an edited source is detected as CHANGED.
set -e
echo "== knowledge/ checksum before =="
BEFORE=$(find knowledge -type f | sort | xargs cat | sha256sum)
echo "$BEFORE"
echo
echo "== fetch all (nothing edited since last run) =="
python3 scripts/fetch.py --all
python3 scripts/build_index.py
echo
echo "== knowledge/ checksum after =="
AFTER=$(find knowledge -type f | sort | xargs cat | sha256sum)
echo "$AFTER"
[ "$BEFORE" = "$AFTER" ] && echo "PASS: bundle byte-identical after re-run" \
  || { echo "FAIL: bundle changed on a no-op re-run"; exit 1; }
echo
echo "== simulate an upstream edit =="
printf "\nEdited line for demo.\n" >> sources/samples/blog/acos-complete-guide.md
python3 scripts/fetch.py acos-blog
git checkout -- sources/samples/blog/acos-complete-guide.md 2>/dev/null || \
  sed -i '/Edited line for demo./d' sources/samples/blog/acos-complete-guide.md
python3 scripts/fetch.py acos-blog
echo "(second fetch shows CHANGED again because the revert is itself a change;"
echo " the agent pipeline would now re-extract only this source)"
