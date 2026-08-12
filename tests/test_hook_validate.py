"""Tests for the PreToolUse validation hook.

These tests verify the critical invariant:
INVALID KNOWLEDGE DOCUMENT → must NOT become → knowledge/*.md

IMPORTANT: The PreToolUse hook provides pre-write validation, not atomic
filesystem publication. The hook blocks invalid Write/Edit operations before
the Claude tool executes. Valid writes are then published by the Claude tool
using its normal (non-atomic) file writing mechanism.

Guarantees:
- Invalid Write operations are blocked before tool execution (file never created)
- Invalid Edit operations are blocked before tool execution (existing file unchanged)
- Valid Write/Edit operations are allowed to proceed

Run: python3 -m unittest tests.test_hook_validate
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Get repo root dynamically
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
import okf

HOOK = REPO_ROOT / "scripts" / "hook_validate_pre.py"

VALID_DOC = """---
okf: "0.1"
id: test-valid
title: Test Valid
description: A valid test document.
type: concept
status: active
created: 2026-08-12
updated: 2026-08-12
timestamp: 2026-08-12T00:00:00Z
confidence: high
tags: [test]
related: []
sources:
  - id: S1
    url: https://example.com/test
    kind: official
    fetched: 2026-08-12
---

# Test Valid

## Overview

Test overview section.

## Key facts

- A cited fact. [S1]
"""

INVALID_DOC_NO_SOURCES = """---
okf: "0.1"
id: test-invalid
title: Test Invalid
description: Missing sources key.
type: concept
status: active
created: 2026-08-12
updated: 2026-08-12
timestamp: 2026-08-12T00:00:00Z
confidence: high
tags: [test]
related: []
---

# Test Invalid

## Overview

Missing sources section.

## Key facts

- An uncited fact.
"""

INVALID_DOC_UNCITED = """---
okf: "0.1"
id: test-invalid-uncited
title: Test Invalid Uncited
description: Has sources but uncited fact.
type: concept
status: active
created: 2026-08-12
updated: 2026-08-12
timestamp: 2026-08-12T00:00:00Z
confidence: high
tags: [test]
related: []
sources:
  - id: S1
    url: https://example.com/test
    kind: official
    fetched: 2026-08-12
---

# Test Invalid Uncited

## Overview

Has uncited fact.

## Key facts

- An uncited fact.
"""


def run_hook(event):
    """Run the hook with a mock event and return exit code."""
    hook_input = json.dumps(event)
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=hook_input,
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent
    )
    return result.returncode, result.stdout, result.stderr


class TestPreToolUseValidation(unittest.TestCase):
    """Test that PreToolUse hook validates BEFORE write."""

    def test_non_knowledge_file_passes(self):
        """Files outside knowledge/concepts/ are ignored."""
        event = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": "/tmp/some-file.md",
                "content": VALID_DOC
            }
        }
        exit_code, stdout, stderr = run_hook(event)
        self.assertEqual(exit_code, 0, "Non-knowledge files should be allowed")
        self.assertEqual(stderr, "")

    def test_valid_write_accepted(self):
        """A valid OKF document is accepted."""
        event = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(REPO_ROOT / "knowledge/concepts/test-valid.md"),
                "content": VALID_DOC
            }
        }
        exit_code, stdout, stderr = run_hook(event)
        self.assertEqual(exit_code, 0, "Valid document should be accepted")
        self.assertEqual(stderr, "", f"Expected no stderr, got: {stderr}")

    def test_invalid_write_blocked_no_sources(self):
        """A document with no sources key is blocked."""
        event = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(REPO_ROOT / "knowledge/concepts/test-invalid.md"),
                "content": INVALID_DOC_NO_SOURCES
            }
        }
        exit_code, stdout, stderr = run_hook(event)
        self.assertEqual(exit_code, 2, "Invalid document should be blocked")
        self.assertIn("OKF validation failed", stderr)
        self.assertIn("missing frontmatter key: sources", stderr)

    def test_invalid_write_blocked_uncited(self):
        """A document with uncited facts is blocked."""
        event = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(REPO_ROOT / "knowledge/concepts/test-invalid-uncited.md"),
                "content": INVALID_DOC_UNCITED
            }
        }
        exit_code, stdout, stderr = run_hook(event)
        self.assertEqual(exit_code, 2, "Document with uncited fact should be blocked")
        self.assertIn("OKF validation failed", stderr)
        self.assertIn("uncited bullet", stderr)

    def test_valid_edit_accepted(self):
        """A valid edit to a document is accepted."""
        # Use a knowledge/concepts path so the hook will validate it
        test_file = REPO_ROOT / "knowledge/concepts/test-valid-edit-accepted.md"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text(VALID_DOC)

        try:
            event = {
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": str(test_file),
                    "old_string": "- A cited fact. [S1]",
                    "new_string": "- An updated cited fact. [S1]"
                }
            }
            exit_code, stdout, stderr = run_hook(event)
            self.assertEqual(exit_code, 0, "Valid edit should be accepted")
            self.assertEqual(stderr, "")
        finally:
            test_file.unlink(missing_ok=True)

    def test_invalid_edit_blocked(self):
        """An invalid edit (introducing uncited fact) is blocked."""
        # Use a knowledge/concepts path so the hook will validate it
        test_file = REPO_ROOT / "knowledge/concepts/test-invalid-edit.md"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text(VALID_DOC)

        try:
            event = {
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": str(test_file),
                    "old_string": "- A cited fact. [S1]",
                    "new_string": "- An uncited fact without citation."
                }
            }
            exit_code, stdout, stderr = run_hook(event)
            self.assertEqual(exit_code, 2, f"Invalid edit should be blocked, got exit {exit_code}, stderr: {stderr}")
            self.assertIn("OKF validation failed", stderr)
            self.assertIn("uncited bullet", stderr)
        finally:
            test_file.unlink(missing_ok=True)

    def test_unknown_citation_blocked(self):
        """A document with unknown citation marker is blocked."""
        invalid_doc = VALID_DOC.replace("[S1]", "[S99]")
        event = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(REPO_ROOT / "knowledge/concepts/test-unknown-cite.md"),
                "content": invalid_doc
            }
        }
        exit_code, stdout, stderr = run_hook(event)
        self.assertEqual(exit_code, 2, "Unknown citation should be blocked")
        self.assertIn("no matching source", stderr.lower())

    def test_bash_command_ignored(self):
        """Non-Write/Edit commands are ignored."""
        event = {
            "tool_name": "Bash",
            "tool_input": {
                "command": "echo test"
            }
        }
        exit_code, stdout, stderr = run_hook(event)
        self.assertEqual(exit_code, 0, "Bash commands should be ignored")


class TestFilesystemInvariants(unittest.TestCase):
    """Test that invalid documents cannot remain in knowledge/."""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.knowledge_dir = self.test_dir / "knowledge" / "concepts"
        self.knowledge_dir.mkdir(parents=True)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_invalid_new_document_does_not_exist_after_block(self):
        """When write is blocked, the target file must not exist."""
        test_file = self.knowledge_dir / "test-blocked.md"

        # Simulate a blocked write attempt
        event = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(test_file),
                "content": INVALID_DOC_NO_SOURCES
            }
        }

        exit_code, stdout, stderr = run_hook(event)

        # The file should NOT exist
        self.assertFalse(test_file.exists(),
                        "Invalid document must not exist after blocked write")
        self.assertEqual(exit_code, 2)

    def test_valid_document_exists_and_passes_validation(self):
        """A valid write succeeds and produces a valid file."""
        # Create a valid doc with ID matching the filename
        valid_doc = VALID_DOC.replace("test-valid", "test-valid-created")
        test_file = self.knowledge_dir / "test-valid-created.md"

        event = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(test_file),
                "content": valid_doc
            }
        }

        exit_code, stdout, stderr = run_hook(event)

        # Hook should accept
        self.assertEqual(exit_code, 0, f"Hook should accept valid doc, stderr: {stderr}")

        # Manually write the file (simulating agent proceeding after hook passes)
        test_file.write_text(valid_doc)

        # File must exist and pass validation
        self.assertTrue(test_file.exists())
        errors = okf.validate(test_file)
        self.assertEqual(errors, [],
                         f"Created file should be valid, got errors: {errors}")

    def test_original_file_unchanged_after_invalid_edit_block(self):
        """When an edit is blocked, original file must remain byte-identical."""
        test_file = self.knowledge_dir / "test-unchanged.md"
        original_content = VALID_DOC
        test_file.write_text(original_content)
        original_hash = hash(original_content)

        event = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": str(test_file),
                "old_string": "- A cited fact. [S1]",
                "new_string": "- An uncited fact."
            }
        }

        exit_code, stdout, stderr = run_hook(event)

        # The edit should be blocked
        self.assertEqual(exit_code, 2)

        # File must remain unchanged
        current_content = test_file.read_text()
        current_hash = hash(current_content)
        self.assertEqual(current_hash, original_hash,
                        "Original file must be byte-identical after blocked edit")

    def test_valid_edit_succeeds_and_produces_valid_file(self):
        """A valid edit succeeds and produces a valid file."""
        # Create a valid doc with ID matching the filename
        valid_doc = VALID_DOC.replace("test-valid", "test-edit-valid")
        test_file = self.knowledge_dir / "test-edit-valid.md"
        original_content = valid_doc
        test_file.write_text(original_content)

        event = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": str(test_file),
                "old_string": "- A cited fact. [S1]",
                "new_string": "- An edited cited fact. [S1]"
            }
        }

        exit_code, stdout, stderr = run_hook(event)

        # Hook should accept
        self.assertEqual(exit_code, 0, f"Valid edit should be accepted, stderr: {stderr}")

        # Apply the edit (simulating agent proceeding)
        new_content = original_content.replace("- A cited fact. [S1]",
                                               "- An edited cited fact. [S1]")
        test_file.write_text(new_content)

        # File must pass validation
        errors = okf.validate(test_file)
        self.assertEqual(errors, [],
                         f"Edited file should be valid, got errors: {errors}")


class TestHookRobustness(unittest.TestCase):
    """Test hook behavior with edge cases and malformed input.

    The hook should fail gracefully rather than crash when given unexpected
    input, and should ignore operations it's not designed to handle.
    """

    def test_hook_fails_gracefully_with_malformed_event(self):
        """Hook should not crash on malformed input."""
        # Missing required fields
        event = {"tool_name": "Write"}  # No tool_input

        exit_code, stdout, stderr = run_hook(event)
        # Should return 0 (ignore) rather than crash
        self.assertEqual(exit_code, 0)

    def test_hook_ignores_non_markdown_files(self):
        """Hook ignores non-.md files even in knowledge/concepts/."""
        event = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(REPO_ROOT / "knowledge/concepts/test.txt"),
                "content": "not markdown"
            }
        }
        exit_code, stdout, stderr = run_hook(event)
        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
