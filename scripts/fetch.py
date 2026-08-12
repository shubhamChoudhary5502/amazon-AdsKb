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
        self._skip_depth = 0  # Keep original skip_depth for backward compatibility
        self.sections = []  # Track sections for incremental extraction
        self.current_section = None
        self.section_level = None
        self.in_heading = False

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._skip_depth += 1
        elif tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            # Save previous section if any
            if self.current_section is not None:
                self.sections.append(self.current_section)
            # Start new section
            self.section_level = tag
            self.current_section = {"level": tag, "heading": "", "content": ""}
            self.in_heading = True

    def handle_endtag(self, tag):
        if tag in self.SKIP and self._skip_depth:
            self._skip_depth -= 1
        elif tag in ["h1", "h2", "h3", "h4", "h5", "h6"] and self.in_heading:
            self.in_heading = False

    def handle_data(self, data):
        if not self._skip_depth:
            self.parts.append(data)
        # Capture heading text when inside heading tags
        if self.in_heading:
            self.current_section["heading"] += data.strip()
        elif self.current_section is not None:
            self.current_section["content"] += data


def normalize(raw, is_html):
    if is_html:
        parser = _TextExtractor()
        parser.feed(raw)
        text = " ".join(parser.parts)
    else:
        text = raw
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return "\n".join(line.strip() for line in text.split("\n")).strip()


def parse_sections(text, is_html=False):
    """Parse text into sections based on headings.

    Returns dict with section IDs as keys and content as values.
    For HTML, sections are extracted during normalization via _TextExtractor.
    For Markdown, sections are parsed from headings.
    """
    import re
    sections = {}

    if is_html:
        # HTML sections should be extracted during normalization
        # This function is for post-processing normalized Markdown
        return {}

    # Markdown section parsing
    lines = text.split("\n")
    current_section = None
    current_section_id = None
    section_level = 0

    for line in lines:
        # Match Markdown headings
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if heading_match:
            level = len(heading_match.group(1))
            heading_text = heading_match.group(2).strip()

            # Save previous section if any
            if current_section is not None and current_section.strip():
                sections[current_section_id] = current_section.strip()

            # Create stable section ID
            section_id = f"md{level}_{slugify(heading_text)}"
            current_section_id = section_id
            current_section = ""
            section_level = level
        else:
            if current_section_id is not None:
                current_section += "\n" + line

    # Save final section
    if current_section is not None and current_section.strip():
        sections[current_section_id] = current_section.strip()

    return sections


def slugify(text):
    """Convert text to a stable slug for section IDs."""
    # Convert to lowercase, replace special chars with hyphens, remove consecutive hyphens
    slug = text.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)  # Replace non-alphanum with single hyphen
    slug = slug.strip('-')  # Remove leading/trailing hyphens
    return slug[:50]  # Limit length for stability


def extract_changed_sections(text, sections, section_ids_to_include):
    """Extract only the specified sections from the original text.

    Args:
        text: Full normalized text
        sections: Dict of section_id -> content from parse_sections
        section_ids_to_include: List of section IDs to include in output

    Returns:
        Text containing only the specified sections, with original headings
    """
    if not section_ids_to_include:
        return ""

    # Parse the original text to find section boundaries
    lines = text.split("\n")
    result_lines = []
    current_section_id = None
    in_target_section = False

    for line in lines:
        # Check if this line is a heading
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if heading_match:
            level = len(heading_match.group(1))
            heading_text = heading_match.group(2).strip()
            potential_section_id = f"md{level}_{slugify(heading_text)}"

            # Check if we're entering a target section
            if potential_section_id in section_ids_to_include:
                current_section_id = potential_section_id
                in_target_section = True
                result_lines.append(line)  # Include the heading
            else:
                # Check if we were in a target section and now leaving it
                if in_target_section:
                    in_target_section = False
                    current_section_id = None
        elif in_target_section:
            # Include content lines for target sections
            result_lines.append(line)

    return "\n".join(result_lines).strip()


def hash_content(content):
    """Hash a string content using SHA-256."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def compare_sections(old_sections, new_sections):
    """Compare old and new section hashes to detect changes.

    Args:
        old_sections: dict of section_id -> content_hash (or content)
        new_sections: dict of section_id -> content_hash (or content)

    Returns dict with 'unchanged', 'changed', 'added', 'removed' lists.
    """
    all_section_ids = set(list(old_sections.keys()) + list(new_sections.keys()))

    unchanged = []
    changed = []
    added = []
    removed = []

    # Check for unchanged sections (comparing hashes or content)
    for section_id in old_sections:
        if section_id in new_sections:
            if old_sections[section_id] == new_sections[section_id]:
                unchanged.append(section_id)
            else:
                changed.append(section_id)
        else:
            removed.append(section_id)

    # Check for added sections
    for section_id in new_sections:
        if section_id not in old_sections:
            added.append(section_id)

    return {
        "unchanged": unchanged,
        "changed": changed,
        "added": added,
        "removed": removed
    }


def get_section_changes(old_manifest, new_manifest, source_id):
    """Get section-level changes for a source.

    Returns dict with section changes or None if manifest format doesn't support sections.
    """
    if source_id not in old_manifest or source_id not in new_manifest:
        return None

    old_entry = old_manifest[source_id]
    new_entry = new_manifest[source_id]

    old_sections = old_entry.get("sections", {})
    new_sections = new_entry.get("sections", {})

    if not old_sections and not new_sections:
        return None  # No section tracking for this source

    return compare_sections(old_sections, new_sections)


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

    # Parse sections for incremental change tracking
    sections = parse_sections(text, is_html=is_html)
    section_hashes = {sid: hash_content(content) for sid, content in sections.items()}

    if entry is None:
        status = "NEW"
    elif entry["hash"] != digest:
        status = "CHANGED"
    else:
        status = "UNCHANGED"

    if status != "UNCHANGED":
        CACHE.mkdir(parents=True, exist_ok=True)

        # Keep full normalized source cache for debugging/backward compatibility
        (CACHE / f"{sid}.txt").write_text(text, encoding="utf-8")

        # Calculate section changes for CHANGED sources
        section_changes = None
        sections_to_include = []

        if status == "CHANGED" and entry:
            old_sections = entry.get("sections", {})
            section_changes = compare_sections(old_sections, section_hashes)

            # Include only changed and added sections for extraction
            sections_to_include = section_changes.get("changed", []) + section_changes.get("added", [])
        elif status == "NEW":
            # For NEW sources, all sections are effectively new
            sections_to_include = list(sections.keys())

        # Create changed.txt containing only changed/added sections
        if sections_to_include and sections:
            changed_content = extract_changed_sections(text, sections, sections_to_include)
            if changed_content.strip():
                (CACHE / f"{sid}-changed.txt").write_text(changed_content, encoding="utf-8")
        else:
            # Remove old changed.txt if no sections changed/added (e.g., only removed sections)
            changed_file = CACHE / f"{sid}-changed.txt"
            if changed_file.exists():
                changed_file.unlink()

        manifest[sid] = {
            "url": source["url"],
            "kind": source.get("type", "community"),
            "hash": digest,
            "last_changed": today,
            "last_checked": today,
            "sections": section_hashes,
        }

        # Persist section changes metadata for debugging/validation
        if section_changes and any(section_changes.values()):
            changes_file = CACHE / f"{sid}-sections.json"
            changes_file.write_text(json.dumps(section_changes, indent=2), encoding="utf-8")
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
