"""Minimal, strict parser for this bundle's OKF v0.1 profile.

Deliberately not a full YAML parser. The profile in
.claude/skills/okf-format/SKILL.md is a closed subset, and a strict parser
that rejects anything outside it is a feature: it keeps every doc machine
readable forever. Zero dependencies by design.
"""

import re
from pathlib import Path

REQUIRED_KEYS = [
    "okf", "id", "title", "type", "status", "created", "updated",
    "confidence", "tags", "related", "sources",
]
CONFIDENCE = {"high", "medium", "low"}
STATUS = {"active", "deprecated"}
KINDS = {"official", "community", "api"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SOURCE_ID_RE = re.compile(r"^S\d+$")
CITE_RE = re.compile(r"\[S\d+\]")


def _clean(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return value


def _parse_inline_list(value):
    inner = value.strip()[1:-1].strip()
    if not inner:
        return []
    return [_clean(x) for x in inner.split(",")]


def split_frontmatter(text):
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing opening --- frontmatter fence")
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i], "\n".join(lines[i + 1:])
    raise ValueError("missing closing --- frontmatter fence")


def parse_frontmatter(fm_lines):
    """Parse the closed subset: scalars, inline lists, one level of
    list-of-dicts (used by `sources`)."""
    data = {}
    current_list_key = None
    current_item = None
    for raw in fm_lines:
        if not raw.strip():
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        if indent == 0:
            current_list_key, current_item = None, None
            if ":" not in line:
                raise ValueError(f"bad frontmatter line: {raw!r}")
            key, _, value = line.partition(":")
            key, value = key.strip(), value.strip()
            if value == "":
                data[key] = []
                current_list_key = key
            elif value.startswith("["):
                data[key] = _parse_inline_list(value)
            else:
                data[key] = _clean(value)
        else:
            if current_list_key is None:
                raise ValueError(f"unexpected indented line: {raw!r}")
            if line.startswith("- "):
                current_item = {}
                data[current_list_key].append(current_item)
                line = line[2:].strip()
                if line:
                    key, _, value = line.partition(":")
                    current_item[key.strip()] = _clean(value)
            else:
                if current_item is None:
                    raise ValueError(f"list item continuation before item: {raw!r}")
                key, _, value = line.partition(":")
                current_item[key.strip()] = _clean(value)
    return data


def parse_doc(path):
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    fm_lines, body = split_frontmatter(text)
    fm = parse_frontmatter(fm_lines)
    return fm, body


def body_sections(body):
    """Return ordered list of (heading, list-of-lines)."""
    sections = []
    current = None
    for line in body.split("\n"):
        if line.startswith("## "):
            current = (line[3:].strip(), [])
            sections.append(current)
        elif current is not None:
            current[1].append(line)
    return sections


def validate(path, all_slugs=None):
    """Return a list of error strings. Empty list means valid.

    all_slugs: optional set of every slug in the bundle, enables the
    related-links existence and symmetry checks in directory mode.
    """
    errors = []
    path = Path(path)
    try:
        fm, body = parse_doc(path)
    except ValueError as exc:
        return [str(exc)]

    for key in REQUIRED_KEYS:
        if key not in fm:
            errors.append(f"missing frontmatter key: {key}")
    if errors:
        return errors

    if fm["okf"] != "0.1":
        errors.append(f"okf version must be \"0.1\", got {fm['okf']!r}")
    if fm["type"] != "concept":
        errors.append("type must be concept")
    if fm["status"] not in STATUS:
        errors.append(f"status must be one of {sorted(STATUS)}")
    if fm["confidence"] not in CONFIDENCE:
        errors.append(f"confidence must be one of {sorted(CONFIDENCE)}")
    if not SLUG_RE.match(fm["id"]):
        errors.append(f"id is not kebab-case: {fm['id']!r}")
    if fm["id"] != path.stem:
        errors.append(f"id {fm['id']!r} does not match filename {path.stem!r}")
    for key in ("created", "updated"):
        if not DATE_RE.match(str(fm[key])):
            errors.append(f"{key} is not an ISO date: {fm[key]!r}")
    if DATE_RE.match(str(fm["created"])) and DATE_RE.match(str(fm["updated"])):
        if fm["updated"] < fm["created"]:
            errors.append("updated is earlier than created")
    if not fm["tags"]:
        errors.append("tags must not be empty")
    if not isinstance(fm["sources"], list) or not fm["sources"]:
        errors.append("sources must be a non-empty list")

    source_ids = set()
    for i, src in enumerate(fm.get("sources") or []):
        if not isinstance(src, dict):
            errors.append(f"source #{i + 1} is not a mapping")
            continue
        sid = src.get("id", "")
        if not SOURCE_ID_RE.match(sid):
            errors.append(f"source #{i + 1} id must look like S1, got {sid!r}")
        if sid in source_ids:
            errors.append(f"duplicate source id {sid}")
        source_ids.add(sid)
        if not src.get("url", "").startswith(("http://", "https://")):
            errors.append(f"source {sid} url missing or not absolute")
        if src.get("kind") not in KINDS:
            errors.append(f"source {sid} kind must be one of {sorted(KINDS)}")
        if not DATE_RE.match(src.get("fetched", "")):
            errors.append(f"source {sid} fetched is not an ISO date")

    # Body checks
    h1 = [l for l in body.split("\n") if l.startswith("# ")]
    if len(h1) != 1:
        errors.append("body must contain exactly one H1")
    elif h1[0][2:].strip() != fm["title"]:
        errors.append("H1 does not match frontmatter title")

    sections = body_sections(body)
    names = [name for name, _ in sections]
    for required in ("Overview", "Key facts"):
        if required not in names:
            errors.append(f"missing required section: {required}")
    allowed = ["Overview", "Key facts", "Community claims",
               "Conflicts and notes", "Relationships"]
    for name in names:
        if name not in allowed:
            errors.append(f"unknown section: {name}")
    order = [allowed.index(n) for n in names if n in allowed]
    if order != sorted(order):
        errors.append("sections out of canonical order")

    for name, lines in sections:
        if name not in ("Key facts", "Community claims"):
            continue
        for line in lines:
            if not line.strip().startswith("- "):
                continue
            cites = CITE_RE.findall(line)
            if not cites:
                errors.append(f"uncited bullet in {name}: {line.strip()[:60]!r}")
            for cite in cites:
                if cite[1:-1] not in source_ids:
                    errors.append(f"citation {cite} has no matching source entry")

    if all_slugs is not None:
        for slug in fm["related"]:
            if slug not in all_slugs:
                errors.append(f"related slug does not exist: {slug}")

    return errors
