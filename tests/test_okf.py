"""Unit tests for the OKF parser and validator. Run: python3 -m unittest discover tests"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import okf

VALID = """---
okf: "0.1"
id: test-doc
title: Test Doc
description: A minimal valid document used by the parser and validator tests.
type: concept
status: active
created: 2026-08-01
updated: 2026-08-10
timestamp: 2026-08-10T00:00:00Z
confidence: high
tags: [a, b]
related: []
sources:
  - id: S1
    url: https://example.com/x
    kind: official
    fetched: 2026-08-10
---

# Test Doc

## Overview

Two sentences here. That is all.

## Key facts

- A cited fact. [S1]
"""


def write_tmp(text, name="test-doc.md"):
    d = Path(tempfile.mkdtemp())
    p = d / name
    p.write_text(text)
    return p


class TestParser(unittest.TestCase):
    def test_parses_valid_doc(self):
        fm, body = okf.parse_doc(write_tmp(VALID))
        self.assertEqual(fm["id"], "test-doc")
        self.assertEqual(fm["tags"], ["a", "b"])
        self.assertEqual(fm["sources"][0]["kind"], "official")
        self.assertIn("# Test Doc", body)

    def test_rejects_missing_fence(self):
        with self.assertRaises(ValueError):
            okf.split_frontmatter("no frontmatter at all")


class TestValidator(unittest.TestCase):
    def test_valid_doc_passes(self):
        self.assertEqual(okf.validate(write_tmp(VALID)), [])

    def test_uncited_bullet_fails(self):
        broken = VALID.replace("A cited fact. [S1]", "An uncited fact.")
        errors = okf.validate(write_tmp(broken))
        self.assertTrue(any("uncited bullet" in e for e in errors))

    def test_unknown_citation_fails(self):
        broken = VALID.replace("[S1]", "[S9]")
        errors = okf.validate(write_tmp(broken))
        self.assertTrue(any("no matching source" in e for e in errors))

    def test_id_filename_mismatch_fails(self):
        errors = okf.validate(write_tmp(VALID, name="other-name.md"))
        self.assertTrue(any("does not match filename" in e for e in errors))

    def test_bad_confidence_fails(self):
        broken = VALID.replace("confidence: high", "confidence: certain")
        errors = okf.validate(write_tmp(broken))
        self.assertTrue(any("confidence" in e for e in errors))

    def test_missing_key_fails(self):
        broken = VALID.replace("status: active\n", "")
        errors = okf.validate(write_tmp(broken))
        self.assertTrue(any("missing frontmatter key: status" in e for e in errors))
    
    def test_missing_description_fails(self):
        broken = VALID.replace(
            "description: A minimal valid document used by the parser "
            "and validator tests.\n", "")
        errors = okf.validate(write_tmp(broken))
        self.assertTrue(any("missing frontmatter key: description" in e
                            for e in errors))

    def test_timestamp_must_be_datetime(self):
        broken = VALID.replace("timestamp: 2026-08-10T00:00:00Z",
                               "timestamp: 2026-08-10")
        errors = okf.validate(write_tmp(broken))
        self.assertTrue(any("ISO 8601 datetime" in e for e in errors))
    
    def test_description_colon_rejected(self):
        broken = VALID.replace("description: A minimal",
                               "description: Broken: A minimal")
        errors = okf.validate(write_tmp(broken))
        self.assertTrue(any("colon" in e for e in errors))


class TestBundle(unittest.TestCase):
    """The shipped bundle itself must always validate."""

    def test_shipped_bundle_is_valid(self):
        concepts = Path(__file__).resolve().parent.parent / "knowledge" / "concepts"
        files = sorted(concepts.glob("*.md"))
        self.assertGreaterEqual(len(files), 10)
        slugs = {f.stem for f in files}
        for f in files:
            self.assertEqual(okf.validate(f, all_slugs=slugs), [], f"{f} invalid")


if __name__ == "__main__":
    unittest.main()
