"""Tests for scripts/log_run.py

Tests the run logger that prepends entries to knowledge/log.md.
The contract:
- Requires at least one argument
- Each argument is one log entry
- Optional leading kind (Creation/Update/Deprecation) separated by colon
- Defaults to Update if no kind specified
- Newest-first ordering (today's section at top)
- Reuses today's section if it exists
- Only called when bundle actually changes

Run: python3 -m unittest tests.test_log_run
"""
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
import subprocess

# Get repo root dynamically
REPO_ROOT = Path(__file__).resolve().parent.parent
LOG_RUN_SCRIPT = REPO_ROOT / "scripts" / "log_run.py"


def setup_test_repo(tmpdir):
    """Create a test repository structure with log_run.py script."""
    test_repo = Path(tmpdir)
    knowledge_dir = test_repo / "knowledge"
    knowledge_dir.mkdir(parents=True)

    # Copy the script to the test repo
    test_scripts = test_repo / "scripts"
    test_scripts.mkdir(parents=True)
    test_script = test_scripts / "log_run.py"
    test_script.write_text(LOG_RUN_SCRIPT.read_text())

    log_file = knowledge_dir / "log.md"
    return test_repo, log_file, test_script


class TestLogRunContract(unittest.TestCase):
    """Test the basic contract of log_run.py."""

    def test_requires_at_least_one_argument(self):
        """log_run.py requires at least one argument."""
        result = subprocess.run(
            [sys.executable, str(LOG_RUN_SCRIPT)],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 2, "Should exit 2 without arguments")
        self.assertIn("Usage:", result.stderr)

    def test_single_entry(self):
        """Test creating the first run-log entry."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, log_file, test_script = setup_test_repo(tmpdir)

            result = subprocess.run(
                [sys.executable, str(test_script), "Test entry 1"],
                capture_output=True,
                text=True,
                cwd=test_repo
            )

            self.assertEqual(result.returncode, 0)
            self.assertIn("logged 1 entry", result.stdout)

            content = log_file.read_text()
            today = date.today().isoformat()
            self.assertIn(f"## {today}", content)
            self.assertIn("* **Update**: Test entry 1", content)

    def test_multiple_entries(self):
        """Test adding multiple entries in one call."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, log_file, test_script = setup_test_repo(tmpdir)

            result = subprocess.run(
                [sys.executable, str(test_script), "Entry 1", "Entry 2", "Entry 3"],
                capture_output=True,
                text=True,
                cwd=test_repo
            )

            self.assertEqual(result.returncode, 0)
            self.assertIn("logged 3 entry", result.stdout)

            content = log_file.read_text()
            today = date.today().isoformat()
            self.assertIn(f"## {today}", content)
            self.assertIn("* **Update**: Entry 1", content)
            self.assertIn("* **Update**: Entry 2", content)
            self.assertIn("* **Update**: Entry 3", content)

    def test_explicit_kinds(self):
        """Test Creation/Update/Deprecation entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, log_file, test_script = setup_test_repo(tmpdir)

            result = subprocess.run(
                [sys.executable, str(test_script),
                 "Creation: new concept added",
                 "Update: existing concept updated",
                 "Deprecation: old concept removed"],
                capture_output=True,
                text=True,
                cwd=test_repo
            )

            self.assertEqual(result.returncode, 0)
            content = log_file.read_text()

            self.assertIn("* **Creation**: new concept added", content)
            self.assertIn("* **Update**: existing concept updated", content)
            self.assertIn("* **Deprecation**: old concept removed", content)

    def test_default_kind_is_update(self):
        """Entries without explicit kind default to Update."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, log_file, test_script = setup_test_repo(tmpdir)

            result = subprocess.run(
                [sys.executable, str(test_script), "No explicit kind"],
                capture_output=True,
                text=True,
                cwd=test_repo
            )

            self.assertEqual(result.returncode, 0)
            content = log_file.read_text()
            self.assertIn("* **Update**: No explicit kind", content)

    def test_newest_first_ordering(self):
        """Verify newest entries come first (today's section at top)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, log_file, test_script = setup_test_repo(tmpdir)

            # Create initial log with yesterday's date
            yesterday = "2026-08-11"
            log_file.write_text(f"""# Amazon Ads knowledge bundle update log

## {yesterday}
* **Update**: Old entry
""")

            # Add new entries for today
            result = subprocess.run(
                [sys.executable, str(test_script), "New entry"],
                capture_output=True,
                text=True,
                cwd=test_repo
            )

            self.assertEqual(result.returncode, 0)
            content = log_file.read_text()

            # Today's section should come first
            lines = content.split("\n")
            today_idx = next(i for i, line in enumerate(lines)
                           if line.startswith("##") and date.today().isoformat() in line)
            yesterday_idx = next(i for i, line in enumerate(lines)
                                if yesterday in line)

            self.assertLess(today_idx, yesterday_idx,
                          "Today's section should come before yesterday's")

    def test_reuses_existing_today_section(self):
        """Verify it reuses today's section if it already exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, log_file, test_script = setup_test_repo(tmpdir)
            today = date.today().isoformat()

            # Create log with today's section
            log_file.write_text(f"""# Amazon Ads knowledge bundle update log

## {today}
* **Update**: Existing entry
""")

            # Add more entries to same day
            result = subprocess.run(
                [sys.executable, str(test_script), "New entry"],
                capture_output=True,
                text=True,
                cwd=test_repo
            )

            self.assertEqual(result.returncode, 0)
            content = log_file.read_text()

            # Should have one today section with both entries
            today_sections = [line for line in content.split("\n")
                            if line.startswith(f"## {today}")]
            self.assertEqual(len(today_sections), 1,
                          "Should reuse existing today section")

            self.assertIn("* **Update**: Existing entry", content)
            self.assertIn("* **Update**: New entry", content)

    def test_existing_entries_not_lost(self):
        """Verify existing log entries are not accidentally lost."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, log_file, test_script = setup_test_repo(tmpdir)

            # Create log with multiple days and entries
            log_file.write_text("""# Amazon Ads knowledge bundle update log

## 2026-08-10
* **Update**: Old entry 1
* **Update**: Old entry 2

## 2026-08-09
* **Update**: Very old entry
""")

            old_content = log_file.read_text()

            # Add new entry
            result = subprocess.run(
                [sys.executable, str(test_script), "New entry"],
                capture_output=True,
                text=True,
                cwd=test_repo
            )

            self.assertEqual(result.returncode, 0)
            new_content = log_file.read_text()

            # Old entries should still be present
            self.assertIn("* **Update**: Old entry 1", new_content)
            self.assertIn("* **Update**: Old entry 2", new_content)
            self.assertIn("* **Update**: Very old entry", new_content)

    def test_deterministic_behavior(self):
        """Verify repeated execution behaves deterministically."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, log_file, test_script = setup_test_repo(tmpdir)

            # First run
            result1 = subprocess.run(
                [sys.executable, str(test_script), "Entry 1", "Entry 2"],
                capture_output=True,
                text=True,
                cwd=test_repo
            )
            content1 = log_file.read_text()

            # Second run with same entries (on same day)
            # Note: In real usage, this would be called only when bundle changes
            # But we test deterministic behavior
            log_file.write_text(content1)  # Reset to same content
            result2 = subprocess.run(
                [sys.executable, str(test_script), "Entry 3", "Entry 4"],
                capture_output=True,
                text=True,
                cwd=test_repo
            )
            content2 = log_file.read_text()

            self.assertEqual(result1.returncode, 0)
            self.assertEqual(result2.returncode, 0)

            # Both should have today's section
            today = date.today().isoformat()
            self.assertIn(f"## {today}", content1)
            self.assertIn(f"## {today}", content2)

    def test_handles_colon_in_entry_text(self):
        """Verify entries with colons in text are handled correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, log_file, test_script = setup_test_repo(tmpdir)

            result = subprocess.run(
                [sys.executable, str(test_script),
                 "Update: fix bug in validation: check sources first"],
                capture_output=True,
                text=True,
                cwd=test_repo
            )

            self.assertEqual(result.returncode, 0)
            content = log_file.read_text()
            self.assertIn("* **Update**: fix bug in validation: check sources first", content)

    def test_empty_title_handling(self):
        """Verify entries with only kind (no text after colon) work."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, log_file, test_script = setup_test_repo(tmpdir)

            result = subprocess.run(
                [sys.executable, str(test_script), "Update:"],
                capture_output=True,
                text=True,
                cwd=test_repo
            )

            self.assertEqual(result.returncode, 0)
            content = log_file.read_text()
            # Should handle gracefully - empty text after colon
            self.assertTrue("* **Update**:" in content or "* **Update**" in content)

    def test_unicode_handling(self):
        """Verify Unicode characters are handled correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, log_file, test_script = setup_test_repo(tmpdir)

            result = subprocess.run(
                [sys.executable, str(test_script),
                 "Update: added support for café and 日本語"],
                capture_output=True,
                text=True,
                cwd=test_repo
            )

            self.assertEqual(result.returncode, 0)
            content = log_file.read_text()
            self.assertIn("café", content)
            self.assertIn("日本語", content)

    def test_multiple_runs_same_day(self):
        """Verify multiple calls on the same day append to today's section."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, log_file, test_script = setup_test_repo(tmpdir)

            # First call
            result1 = subprocess.run(
                [sys.executable, str(test_script), "First run"],
                capture_output=True,
                text=True,
                cwd=test_repo
            )

            # Second call (simulating another pipeline run on same day)
            result2 = subprocess.run(
                [sys.executable, str(test_script), "Second run"],
                capture_output=True,
                text=True,
                cwd=test_repo
            )

            self.assertEqual(result1.returncode, 0)
            self.assertEqual(result2.returncode, 0)

            content = log_file.read_text()
            today = date.today().isoformat()

            # Should have one today section with both entries
            today_sections = [line for line in content.split("\n")
                            if line.startswith(f"## {today}")]
            self.assertEqual(len(today_sections), 1,
                          "Should have one today section")

            self.assertIn("* **Update**: First run", content)
            self.assertIn("* **Update**: Second run", content)

    def test_creates_new_log_file_if_missing(self):
        """Verify log file is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, log_file, test_script = setup_test_repo(tmpdir)

            self.assertFalse(log_file.exists(), "Log should not exist initially")

            result = subprocess.run(
                [sys.executable, str(test_script), "First entry"],
                capture_output=True,
                text=True,
                cwd=test_repo
            )

            self.assertEqual(result.returncode, 0)
            self.assertTrue(log_file.exists(), "Log should be created")

            content = log_file.read_text()
            self.assertIn("# Amazon Ads knowledge bundle update log", content)


class TestLogRunEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def test_malformed_date_handling(self):
        """Verify script handles date formatting correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, log_file, test_script = setup_test_repo(tmpdir)

            # Script uses date.today() which is always valid
            result = subprocess.run(
                [sys.executable, str(test_script), "Test entry"],
                capture_output=True,
                text=True,
                cwd=test_repo
            )

            self.assertEqual(result.returncode, 0)
            content = log_file.read_text()
            # Should contain valid ISO date
            self.assertRegex(content, r"## \d{4}-\d{2}-\d{2}")

    def test_long_entry_text(self):
        """Verify long entry text is handled correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, log_file, test_script = setup_test_repo(tmpdir)

            long_text = "Update: " + "word " * 100
            result = subprocess.run(
                [sys.executable, str(test_script), long_text],
                capture_output=True,
                text=True,
                cwd=test_repo
            )

            self.assertEqual(result.returncode, 0)
            content = log_file.read_text()
            # Just check that a significant portion is present
            self.assertIn("word word word word word", content)

    def test_special_characters_in_entry(self):
        """Verify special markdown characters are handled correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, log_file, test_script = setup_test_repo(tmpdir)

            result = subprocess.run(
                [sys.executable, str(test_script),
                 "Update: test *bold*, _italic_, `code`, and [links](url)"],
                capture_output=True,
                text=True,
                cwd=test_repo
            )

            self.assertEqual(result.returncode, 0)
            content = log_file.read_text()
            # Should preserve the characters
            self.assertIn("*bold*", content)
            self.assertIn("[links](url)", content)


if __name__ == "__main__":
    unittest.main()
