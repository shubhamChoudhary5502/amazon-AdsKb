#!/usr/bin/env python3
"""Validate one OKF doc or the whole bundle.

Usage:
  python3 scripts/validate_okf.py knowledge/concepts/            # bundle mode
  python3 scripts/validate_okf.py knowledge/concepts/foo.md      # single file

Bundle mode also checks that related links point to existing docs and are
symmetric. Exit code 0 = valid, 1 = errors printed to stderr.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import okf


def main():
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    target = Path(sys.argv[1])
    failed = False

    if target.is_dir():
        files = sorted(target.glob("*.md"))
        all_slugs = {f.stem for f in files}
        docs = {}
        for f in files:
            errors = okf.validate(f, all_slugs=all_slugs)
            if errors:
                failed = True
                for e in errors:
                    print(f"{f}: {e}", file=sys.stderr)
            else:
                fm, _ = okf.parse_doc(f)
                docs[f.stem] = set(fm["related"])
        for slug, related in docs.items():
            for other in related:
                if other in docs and slug not in docs[other]:
                    failed = True
                    print(f"{target/slug}.md: related link to {other!r} "
                          f"is not symmetric", file=sys.stderr)
    else:
        errors = okf.validate(target)
        if errors:
            failed = True
            for e in errors:
                print(f"{target}: {e}", file=sys.stderr)

    if failed:
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
