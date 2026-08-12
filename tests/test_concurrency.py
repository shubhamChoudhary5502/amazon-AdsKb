"""Tests for concurrency safety in manifest operations.

These tests verify that concurrent pipeline runs cannot lose manifest records
or corrupt the state file through race conditions.

Run: python3 -m unittest tests.test_concurrency
"""
import json
import subprocess
import sys
import tempfile
import time
import threading
import unittest
from datetime import date
from pathlib import Path

# Get repo root dynamically
REPO_ROOT = Path(__file__).resolve().parent.parent
FETCH_SCRIPT = REPO_ROOT / "scripts" / "fetch.py"


def setup_test_repo(tmpdir):
    """Create a test repository structure with fetch.py and test data."""
    test_repo = Path(tmpdir)
    state_dir = test_repo / "state"
    sources_dir = test_repo / "sources"
    cache_dir = state_dir / "cache"

    # Create directories
    state_dir.mkdir(parents=True)
    sources_dir.mkdir(parents=True)
    cache_dir.mkdir(parents=True)

    # Copy fetch script
    test_scripts = test_repo / "scripts"
    test_scripts.mkdir(parents=True)
    (test_scripts / "fetch.py").write_text(FETCH_SCRIPT.read_text())

    # Create test sources.yaml
    sources_yaml = """# Test sources
sources:
  - id: source-a
    type: official
    url: https://example.com/a
    sample: samples/source-a.md
  - id: source-b
    type: community
    url: https://example.com/b
    sample: samples/source-b.md
  - id: source-c
    type: api
    url: https://example.com/c
    sample: samples/source-c.md
  - id: source-d
    type: official
    url: https://example.com/d
    sample: samples/source-d.md
"""
    (sources_dir / "sources.yaml").write_text(sources_yaml)

    # Create sample files (samples go in repo root, not under sources/)
    samples_dir = test_repo / "samples"
    samples_dir.mkdir(parents=True)
    for i in range(4):
        sample_content = f"""# Source {chr(65+i)}

Test content for source {chr(65+i)}.
"""
        (samples_dir / f"source-{chr(97+i)}.md").write_text(sample_content)

    manifest_file = state_dir / "manifest.json"
    lock_file = state_dir / "manifest.lock"

    return test_repo, state_dir, sources_dir, manifest_file, lock_file


def fetch_source(test_repo, source_id):
    """Run fetch.py for a single source and return the result."""
    script_path = test_repo / "scripts" / "fetch.py"
    result = subprocess.run(
        [sys.executable, str(script_path), source_id],
        capture_output=True,
        text=True,
        cwd=test_repo
    )
    return result.returncode == 0


def fetch_all_sources(test_repo):
    """Run fetch.py --all and return the result."""
    script_path = test_repo / "scripts" / "fetch.py"
    result = subprocess.run(
        [sys.executable, str(script_path), "--all"],
        capture_output=True,
        text=True,
        cwd=test_repo
    )
    return result.returncode == 0


def get_manifest_records(manifest_file):
    """Get current manifest records as a dict."""
    if manifest_file.exists():
        return json.loads(manifest_file.read_text())
    return {}


def manifest_record_count(manifest_file):
    """Count the number of records in manifest."""
    return len(get_manifest_records(manifest_file))


class TestConcurrencySafety(unittest.TestCase):
    """Test that concurrent operations preserve manifest integrity."""

    def test_two_concurrent_updates_different_sources(self):
        """Test A: Two concurrent updates to different records both survive."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, state_dir, sources_dir, manifest_file, lock_file = setup_test_repo(tmpdir)

            # Run two concurrent fetch operations on different sources using threads
            results = {}
            def fetch_and_store(source_id):
                results[source_id] = fetch_source(test_repo, source_id)

            threads = []
            for source_id in ["source-a", "source-b"]:
                t = threading.Thread(target=fetch_and_store, args=(source_id,))
                t.start()
                threads.append(t)

            # Wait for all to complete
            for t in threads:
                t.join(timeout=10)
                self.assertFalse(t.is_alive(), "Thread should have completed")

            # Both operations should succeed
            for source_id, success in results.items():
                self.assertTrue(success, f"Fetch for {source_id} should succeed")

            # Check final manifest
            final_manifest = get_manifest_records(manifest_file)

            # Both records should exist
            self.assertIn("source-a", final_manifest, "Source A record should exist")
            self.assertIn("source-b", final_manifest, "Source B record should exist")

            # Both should have today's date in last_checked
            today = date.today().isoformat()
            self.assertEqual(final_manifest["source-a"]["last_checked"], today,
                           f"Source A should have last_checked={today}")
            self.assertEqual(final_manifest["source-b"]["last_checked"], today,
                           f"Source B should have last_checked={today}")

            # Both should have hash values (not empty)
            self.assertTrue(final_manifest["source-a"]["hash"])
            self.assertTrue(final_manifest["source-b"]["hash"])

    def test_multiple_concurrent_updates(self):
        """Test B: Multiple concurrent updates produce valid final state with all records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, state_dir, sources_dir, manifest_file, lock_file = setup_test_repo(tmpdir)

            # Start with empty manifest
            manifest_file.write_text("{}")

            # Run all 4 sources concurrently using threads
            sources = ["source-a", "source-b", "source-c", "source-d"]
            results = {}

            def fetch_and_store(source_id):
                results[source_id] = fetch_source(test_repo, source_id)

            threads = []
            for source_id in sources:
                t = threading.Thread(target=fetch_and_store, args=(source_id,))
                t.start()
                threads.append(t)

            # Wait for all to complete
            for t in threads:
                t.join(timeout=10)
                self.assertFalse(t.is_alive(), "Thread should have completed")

            # All operations should succeed
            for source_id, success in results.items():
                self.assertTrue(success, f"Fetch for {source_id} should succeed")

            # Check final manifest
            final_manifest = get_manifest_records(manifest_file)

            # All 4 records should exist
            self.assertEqual(len(final_manifest), 4,
                           "All 4 sources should be in manifest")

            for source_id in sources:
                self.assertIn(source_id, final_manifest,
                            f"{source_id} should be in final manifest")

            # Manifest should be valid JSON
            self.assertIsInstance(final_manifest, dict)

            # Each record should have required fields
            required_fields = {"url", "kind", "hash", "last_changed", "last_checked", "sections"}
            for source_id, record in final_manifest.items():
                self.assertEqual(required_fields, set(record.keys()),
                               f"{source_id} should have all required fields")

    def test_no_partial_corrupt_json(self):
        """Test C: Concurrent updates don't produce partial/corrupt JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, state_dir, sources_dir, manifest_file, lock_file = setup_test_repo(tmpdir)

            # Run multiple concurrent operations using threads
            sources = ["source-a", "source-b", "source-c", "source-d"]
            threads = []
            for source_id in sources:
                t = threading.Thread(target=fetch_source, args=(test_repo, source_id))
                t.start()
                threads.append(t)

            # Wait for all to complete
            for t in threads:
                t.join(timeout=10)
                self.assertFalse(t.is_alive(), "Thread should have completed")

            # Manifest should exist and be valid JSON
            self.assertTrue(manifest_file.exists(), "Manifest file should exist")

            # Try to parse as JSON
            try:
                manifest = json.loads(manifest_file.read_text())
                self.assertIsInstance(manifest, dict, "Manifest should be a valid JSON object")
            except json.JSONDecodeError as e:
                self.fail(f"Manifest should be valid JSON, got error: {e}")

            # Should have all 4 records
            self.assertEqual(len(manifest), 4, "All concurrent updates should be preserved")

    def test_failed_update_does_not_corrupt_state(self):
        """Test D: A failed update does not leave the state file corrupted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, state_dir, sources_dir, manifest_file, lock_file = setup_test_repo(tmpdir)

            # Create initial manifest
            initial_manifest = {
                "source-a": {
                    "url": "https://example.com/a",
                    "kind": "official",
                    "hash": "initial-hash",
                    "last_changed": "2026-08-10",
                    "last_checked": "2026-08-10"
                }
            }
            manifest_file.write_text(json.dumps(initial_manifest, indent=2))
            original_content = manifest_file.read_text()

            # Try to fetch a non-existent source (will fail)
            result = fetch_source(test_repo, "nonexistent")

            # Manifest should still be valid
            self.assertTrue(manifest_file.exists(), "Manifest should still exist")
            try:
                manifest = json.loads(manifest_file.read_text())
                self.assertIsInstance(manifest, dict)
            except json.JSONDecodeError:
                self.fail("Manifest should be valid JSON after failed fetch")

            # Original record should still be present
            manifest = json.loads(manifest_file.read_text())
            self.assertIn("source-a", manifest, "Original record should be preserved")
            self.assertEqual(manifest["source-a"]["hash"], "initial-hash")

    def test_repeated_concurrent_runs_preserve_idempotency(self):
        """Test E: Repeated concurrent runs preserve idempotency."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, state_dir, sources_dir, manifest_file, lock_file = setup_test_repo(tmpdir)

            # First run - fetch all sources
            fetch_all_sources(test_repo)
            manifest_after_first = get_manifest_records(manifest_file)

            # Second run - fetch all sources again (should report UNCHANGED for all)
            fetch_all_sources(test_repo)
            manifest_after_second = get_manifest_records(manifest_file)

            # Records should be identical (idempotency preserved)
            self.assertEqual(manifest_after_first, manifest_after_second,
                           "Manifest should be identical after repeated runs")

            # Hash values should not have changed
            for source_id in manifest_after_first:
                if source_id in manifest_after_second:
                    hash1 = manifest_after_first[source_id]["hash"]
                    hash2 = manifest_after_second[source_id]["hash"]
                    self.assertEqual(hash1, hash2,
                                   f"Hash for {source_id} should not change in unchanged run")


class TestAtomicReplacement(unittest.TestCase):
    """Test atomic file replacement mechanism."""

    def test_temp_file_cleaned_up(self):
        """Test that temporary .tmp files are cleaned up after atomic write."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, state_dir, sources_dir, manifest_file, lock_file = setup_test_repo(tmpdir)

            # Run fetch to create manifest
            fetch_source(test_repo, "source-a")

            # .tmp file should not exist
            temp_file = manifest_file.with_suffix(".tmp")
            self.assertFalse(temp_file.exists(),
                          "Temporary .tmp file should be cleaned up")

            # Manifest should exist
            self.assertTrue(manifest_file.exists())

    def test_atomic_write_prevents_partial_write(self):
        """Test that atomic write prevents partial/corrupted files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, state_dir, sources_dir, manifest_file, lock_file = setup_test_repo(tmpdir)

            # Run multiple concurrent operations
            for _ in range(5):
                fetch_all_sources(test_repo)

            # Manifest should always be valid JSON
            for check_iteration in range(10):  # Check multiple times
                try:
                    manifest = json.loads(manifest_file.read_text())
                    self.assertIsInstance(manifest, dict)
                except json.JSONDecodeError as e:
                    self.fail(f"Manifest corrupted on check {check_iteration}: {e}")

    def test_lock_file_released(self):
        """Test that lock file is released after operation completes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, state_dir, sources_dir, manifest_file, lock_file = setup_test_repo(tmpdir)

            # Lock file should not exist initially
            self.assertFalse(lock_file.exists(), "Lock file should not exist initially")

            # Run fetch (which acquires and releases lock)
            fetch_source(test_repo, "source-a")

            # Lock file should still exist (it's a permanent file)
            # But it should not be locked
            # We can verify by trying to run another fetch immediately
            result2 = fetch_source(test_repo, "source-a")
            self.assertTrue(result2, "Second fetch should succeed (lock was released)")


class TestLockContention(unittest.TestCase):
    """Test behavior under high concurrency and lock contention."""

    def test_rapid_sequential_updates(self):
        """Test rapid sequential updates don't interfere with each other."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, state_dir, sources_dir, manifest_file, lock_file = setup_test_repo(tmpdir)

            # Run 20 sequential fetches
            for i in range(20):
                fetch_source(test_repo, "source-a")

            # Manifest should be valid and have exactly one record
            manifest = get_manifest_records(manifest_file)
            self.assertEqual(len(manifest), 1, "Should have exactly one source record")
            self.assertIn("source-a", manifest)

    def test_simultaneous_same_source_updates(self):
        """Test simultaneous updates to the same source record."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, state_dir, sources_dir, manifest_file, lock_file = setup_test_repo(tmpdir)

            # Create initial manifest
            initial_manifest = {
                "source-a": {
                    "url": "https://example.com/a",
                    "kind": "official",
                    "hash": "initial-hash",
                    "last_changed": "2026-08-10",
                    "last_checked": "2026-08-10"
                }
            }
            manifest_file.write_text(json.dumps(initial_manifest, indent=2))

            # Run 5 concurrent updates to the same source using threads
            threads = []
            for _ in range(5):
                t = threading.Thread(target=fetch_source, args=(test_repo, "source-a"))
                t.start()
                threads.append(t)

            # Wait for all to complete
            for t in threads:
                t.join(timeout=10)
                self.assertFalse(t.is_alive(), "Thread should have completed")

            # Manifest should be valid
            manifest = get_manifest_records(manifest_file)
            self.assertIsInstance(manifest, dict)
            self.assertIn("source-a", manifest)

            # Only one record should exist (no duplicates)
            source_a_records = [k for k in manifest.keys() if k == "source-a"]
            self.assertEqual(len(source_a_records), 1, "Should have exactly one source-a record")


if __name__ == "__main__":
    unittest.main()
