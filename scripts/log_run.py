#!/usr/bin/env python3
"""Prepend entries to knowledge/log.md, the OKF v0.1 reserved update log.

Usage:
  python3 scripts/log_run.py "Update: what changed" ["Creation: what was added" ...]

Each argument is one entry. An optional leading kind, one of Creation, Update
or Deprecation, is separated by a colon and rendered in bold per OKF v0.1
section 7. Anything else defaults to Update.

Newest first: today's section is created at the top of the log, or reused if
it already exists. Only called when a run actually changed the bundle.
No-change runs leave knowledge/ byte-identical on purpose; their trace lives
in state/manifest.json last_checked.
"""
import sys
from datetime import date
from pathlib import Path

LOG = Path(__file__).resolve().parent.parent / "knowledge" / "log.md"
TITLE = "# Amazon Ads knowledge bundle update log"
KINDS = ("Creation", "Update", "Deprecation")


def render(arg):
    kind, sep, text = arg.partition(":")
    if sep and kind.strip() in KINDS:
        return f"* **{kind.strip()}**: {text.strip()}"
    return f"* **Update**: {arg.strip()}"


def main():
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2

    today = date.today().isoformat()
    bullets = [render(a) for a in sys.argv[1:]]

    if LOG.exists():
        lines = LOG.read_text(encoding="utf-8").rstrip("\n").split("\n")
    else:
        lines = [TITLE, ""]

    first = next((i for i, l in enumerate(lines) if l.startswith("## ")),
                 len(lines))

    if first < len(lines) and lines[first].strip() == f"## {today}":
        lines[first + 1:first + 1] = bullets
    else:
        lines[first:first] = [f"## {today}"] + bullets + [""]

    if len(lines) > 1 and lines[1].strip() != "":
        lines.insert(1, "")

    LOG.write_text("\n".join(lines).rstrip("\n") + "\n", encoding="utf-8")
    print(f"logged {len(bullets)} entry(s) under {today}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
