#!/usr/bin/env python3
"""Claude Code PostToolUse hook: validate any OKF doc the agent just wrote.

Reads the hook event JSON from stdin. If the touched file is inside
knowledge/concepts/, validates it. Exit 2 blocks and feeds the errors back
to the agent so it must fix the doc before moving on.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import okf


def main():
    try:
        event = json.load(sys.stdin)
    except Exception:
        return 0  # not our event shape, stay out of the way
    file_path = (event.get("tool_input") or {}).get("file_path", "")
    if not file_path:
        return 0
    path = Path(file_path)
    if "knowledge/concepts" not in str(path) or path.suffix != ".md":
        return 0
    if not path.exists():
        return 0
    errors = okf.validate(path)
    if errors:
        print("OKF validation failed, fix before continuing:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
