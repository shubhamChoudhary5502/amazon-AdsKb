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

CONCURRENCY: The manifest read-modify-write cycle is protected by file
locking to prevent concurrent runs from losing updates. The lock is held
during the entire read-modify-write sequence and released automatically
even if an exception occurs.
"""
import hashlib
import json
import os
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
LIVE_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AmazonAdsKb/1.0)"}


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
            sid = line.split(":", 1)[1].strip()
            if sid in entries:
                raise ValueError(f"duplicate source id in sources.yaml: {sid}")
            current = {"id": sid}
            entries[sid] = current
        elif current is not None and ":" in line and not line.startswith("#"):
            key, _, value = line.partition(":")
            current[key.strip()] = value.strip()
    return entries


def acquire_lock(lock_file):
    """Acquire an exclusive file lock using flock.

    Uses fcntl.flock() on Unix and msvcrt.locking() on Windows.
    Lock is released when the file is closed or on process exit.
    """
    lock_path = Path(lock_file)
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    # Open/create lock file
    if lock_path.exists():
        fd = os.open(lock_path, os.O_RDWR)
    else:
        fd = os.open(lock_path, os.O_RDWR | os.O_CREAT)

    try:
        if sys.platform == "win32":
            # Windows: use msvcrt.locking
            import msvcrt
            msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
        else:
            # Unix: use fcntl.flock with exclusive lock
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_EX)
        return fd
    except Exception:
        os.close(fd)
        raise


def release_lock(fd):
    """Release a file lock acquired by acquire_lock."""
    try:
        if sys.platform == "win32":
            import msvcrt
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


def load_manifest_locked(lock_fd):
    """Load manifest while holding the lock.

    The lock_fd is for the lock file, but we need to read the manifest.json file.
    The lock ensures exclusive access during the read.
    """
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text())
    return {}


def write_manifest_atomic(manifest):
    """Write manifest to a temporary file, then atomically replace the original."""
    # Write to temp file in same directory as manifest
    temp_manifest = MANIFEST.with_suffix(".tmp")
    temp_manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    # Atomic replacement - os.replace is atomic on POSIX systems
    temp_manifest.replace(MANIFEST)


def process(source, manifest, live):
    sid = source["id"]
    try:
        if live:
            req = urllib.request.Request(source["url"], headers=LIVE_HEADERS)
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
            is_html = source["url"].endswith((".html", "/")) or "<html" in raw[:2000].lower()
        else:
            sample = (ROOT / source["sample"]).resolve()
            if not str(sample).startswith(str(ROOT.resolve()) + os.sep):
                return "ERROR sample path escapes the repo root"
            raw = sample.read_text(encoding="utf-8", errors="replace")
            is_html = sample.suffix in (".html", ".htm")
    except Exception as exc:
        return f"ERROR {type(exc).__name__}: {exc}"

    text = normalize(raw, is_html)
    if not text.strip():
        return "ERROR normalized content is empty, refusing to treat as a change"
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

    try:
        sources = load_sources()
    except ValueError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2

    lock_file = ROOT / "state" / "manifest.lock"
    lock_fd = None

    try:
        # Acquire lock for concurrent run safety
        lock_fd = acquire_lock(lock_file)

        # Load manifest while holding lock
        manifest = load_manifest_locked(lock_fd)

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

        # Write manifest atomically while still holding lock
        MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        write_manifest_atomic(manifest)

        return exit_code

    finally:
        # Always release lock, even on exception
        if lock_fd is not None:
            release_lock(lock_fd)


if __name__ == "__main__":
    sys.exit(main())
