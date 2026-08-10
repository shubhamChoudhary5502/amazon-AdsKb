#!/usr/bin/env python3
"""Rebuild knowledge/index.md from the concept docs.

Deterministic: sorted by slug, and the file is only rewritten when the
generated content differs, so re-runs leave it byte-identical.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import okf

ROOT = Path(__file__).resolve().parent.parent
CONCEPTS = ROOT / "knowledge" / "concepts"
INDEX = ROOT / "knowledge" / "index.md"


def main():
    rows = []
    for f in sorted(CONCEPTS.glob("*.md")):
        fm, _ = okf.parse_doc(f)
        official = sum(1 for s in fm["sources"] if s.get("kind") in ("official", "api"))
        rows.append((fm["id"], fm["title"], fm["confidence"], fm["updated"],
                     f"{official}/{len(fm['sources'])}", ", ".join(fm["tags"])))

    lines = [
        "# Amazon Ads knowledge bundle - index",
        "",
        f"{len(rows)} concepts. Sources column is official-or-api / total.",
        "",
        "| Concept | Confidence | Updated | Sources | Tags |",
        "|---|---|---|---|---|",
    ]
    for slug, title, conf, updated, srcs, tags in rows:
        lines.append(f"| [{title}](concepts/{slug}.md) | {conf} | {updated} "
                     f"| {srcs} | {tags} |")
    content = "\n".join(lines) + "\n"

    if INDEX.exists() and INDEX.read_text() == content:
        print("index unchanged")
        return 0
    INDEX.write_text(content)
    print(f"index rebuilt: {len(rows)} concepts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
