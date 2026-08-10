#!/usr/bin/env python3
"""Append a dated entry to knowledge/CHANGELOG.md.

Usage: python3 scripts/log_run.py "summary line" ["detail" ...]

Only called when a run actually changed the bundle. No-change runs leave
knowledge/ byte-identical on purpose; their trace lives in
state/manifest.json last_checked.
"""
import sys
from datetime import date
from pathlib import Path

LOG = Path(__file__).resolve().parent.parent / "knowledge" / "CHANGELOG.md"


def main():
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    summary, details = sys.argv[1], sys.argv[2:]
    entry = [f"\n## {date.today().isoformat()} - {summary}\n"]
    entry += [f"- {d}\n" for d in details]
    if not LOG.exists():
        LOG.write_text("# Changelog\n\nEvery entry is one pipeline run that "
                       "changed the bundle.\n")
    with LOG.open("a", encoding="utf-8") as f:
        f.writelines(entry)
    print(f"logged: {summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
