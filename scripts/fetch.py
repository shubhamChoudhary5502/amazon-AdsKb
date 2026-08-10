#!/usr/bin/env python3
"""Fetch one registered source, normalize, hash, and report change status.

Usage:
  python3 scripts/fetch.py <source-id> [--live]
  python3 scripts/fetch.py --all [--live]

Offline mode (default) reads the local snapshot listed in sources.yaml so
runs are deterministic and testable. --live fetches the url instead.

Prints one line per source:  <STATUS> <source-id>
STATUS is NEW | CHANGED | UNCHANGED | ERROR <reason>

Manifest state/manifest.json is the change-detection memory. The content
hash only moves when the normalized text moves; last_checked moves every
run (bookkeeping, deliberately outside the idempotency contract, see
docs/DESIGN.md).
"""
import hashlib
import json
import re
import sys
import urllib.request
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "state" / "manifest.json"
CACHE = ROOT / "state" / "cache"
SOURCES = ROOT / "sources" / "sources.yaml"


class _TextExtractor(HTMLParser):
    SKIP = {"script", "style", "nav", "footer"}

    def __init__(self):
        super().__init__()
        self.parts = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag in self.SKIP and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data):
        if not self._skip_depth:
            self.parts.append(data)


def normalize(raw, is_html):
    if is_html:
        parser = _TextExtractor()
        parser.feed(raw)
        raw = " ".join(parser.parts)
    text = re.sub(r"[ \t]+", " ", raw)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return "\n".join(line.strip() for line in text.split("\n")).strip()


def load_sources():
    """Parse sources.yaml (same closed subset as OKF frontmatter)."""
    entries = {}
    current = None
    for raw in SOURCES.read_text().split("\n"):
        line = raw.strip()
        if line.startswith("- id:"):
            current = {"id": line.split(":", 1)[1].strip()}
            entries[current["id"]] = current
        elif current is not None and ":" in line and not line.startswith("#"):
            key, _, value = line.partition(":")
            current[key.strip()] = value.strip()
    return entries


def load_manifest():
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text())
    return {}


def process(source, manifest, live):
    sid = source["id"]
    try:
        if live:
            with urllib.request.urlopen(source["url"], timeout=30) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
            is_html = source["url"].endswith((".html", "/")) or "<html" in raw[:2000].lower()
        else:
            sample = ROOT / source["sample"]
            raw = sample.read_text(encoding="utf-8")
            is_html = sample.suffix in (".html", ".htm")
    except Exception as exc:
        return f"ERROR {type(exc).__name__}: {exc}"

    text = normalize(raw, is_html)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    today = date.today().isoformat()
    entry = manifest.get(sid)

    if entry is None:
        status = "NEW"
    elif entry["hash"] != digest:
        status = "CHANGED"
    else:
        status = "UNCHANGED"

    if status != "UNCHANGED":
        CACHE.mkdir(parents=True, exist_ok=True)
        (CACHE / f"{sid}.txt").write_text(text, encoding="utf-8")
        manifest[sid] = {
            "url": source["url"],
            "kind": source.get("type", "community"),
            "hash": digest,
            "last_changed": today,
            "last_checked": today,
        }
    else:
        entry["last_checked"] = today
    return status


def main():
    args = sys.argv[1:]
    live = "--live" in args
    args = [a for a in args if a != "--live"]
    if not args:
        print(__doc__, file=sys.stderr)
        return 2

    sources = load_sources()
    manifest = load_manifest()
    targets = list(sources.values()) if args[0] == "--all" else []
    if not targets:
        if args[0] not in sources:
            print(f"ERROR unknown source id {args[0]}", file=sys.stderr)
            return 2
        targets = [sources[args[0]]]

    exit_code = 0
    for source in targets:
        status = process(source, manifest, live)
        print(f"{status} {source['id']}")
        if status.startswith("ERROR"):
            exit_code = 1

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
