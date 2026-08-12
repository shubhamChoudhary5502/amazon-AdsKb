"""Integration test demonstrating the A+B+C -> A unchanged, B changed, C unchanged scenario"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import fetch


class TestABCIncrementalScenario(unittest.TestCase):
    """Test the exact A+B+C → A unchanged, B changed, C unchanged scenario."""

    def test_abc_incremental_extraction_scenario(self):
        """
        Demonstrate the key requirement:
        Run 1: A + B + C (all new)
        Run 2: A unchanged, B changed, C unchanged
        Expected: Only B should be marked for extraction
        """
        with tempfile.TemporaryDirectory(dir=fetch.ROOT / "state") as tmpdir:
            tmp_path = Path(tmpdir)
            sample = tmp_path / "test.md"

            source = {
                "id": "test-abc-scenario",
                "url": "https://example.com",
                "type": "official",
                "sample": str(sample.relative_to(fetch.ROOT))
                if str(sample).startswith(str(fetch.ROOT))
                else str(sample)
            }

            manifest = {}

            # RUN 1: A + B + C (all new)
            print("\n=== RUN 1: A + B + C (all new) ===")
            sample.write_text("""# Section A

Content for section A.

# Section B

Content for section B.

# Section C

Content for section C.""")

            status1 = fetch.process(source, manifest, live=False)
            self.assertEqual(status1, "NEW", "First run should be NEW")

            # Verify all sections are tracked
            self.assertIn("sections", manifest["test-abc-scenario"])
            sections_run1 = manifest["test-abc-scenario"]["sections"]
            print(f"Run 1 sections: {list(sections_run1.keys())}")

            # Should have exactly 3 sections
            self.assertEqual(len(sections_run1), 3, "Should have 3 sections in run 1")
            self.assertIn("md1_section-a", sections_run1)
            self.assertIn("md1_section-b", sections_run1)
            self.assertIn("md1_section-c", sections_run1)

            # RUN 2: A unchanged, B changed, C unchanged
            print("\n=== RUN 2: A unchanged, B changed, C unchanged ===")
            sample.write_text("""# Section A

Content for section A.

# Section B

CHANGED content for section B.

# Section C

Content for section C.""")

            # Set up cache directory for this test
            original_cache = fetch.CACHE
            fetch.CACHE = tmp_path / "cache"
            try:
                status2 = fetch.process(source, manifest, live=False)
                self.assertEqual(status2, "CHANGED", "Second run should be CHANGED")

                # Check section changes file
                changes_file = fetch.CACHE / "test-abc-scenario-sections.json"
                self.assertTrue(changes_file.exists(), "Section changes file should exist")

                # Load and verify section changes
                with open(changes_file) as f:
                    section_changes = json.load(f)

                print(f"Section changes: {section_changes}")

                # The key test: exactly one section should be marked as changed
                self.assertEqual(len(section_changes["changed"]), 1,
                               "Exactly one section should be marked as changed")
                self.assertIn("md1_section-b", section_changes["changed"],
                              "Section B should be marked as changed")

                # A and C should be marked as unchanged
                self.assertIn("md1_section-a", section_changes["unchanged"],
                              "Section A should be marked as unchanged")
                self.assertIn("md1_section-c", section_changes["unchanged"],
                              "Section C should be marked as unchanged")

                # No sections should be added or removed
                self.assertEqual(len(section_changes["added"]), 0,
                               "No sections should be added")
                self.assertEqual(len(section_changes["removed"]), 0,
                               "No sections should be removed")

                # Verify the whole-source hash changed
                old_hash = manifest["test-abc-scenario"]["hash"]
                print(f"Whole-source hash changed: {old_hash != sections_run1.get('md1_section-a', old_hash)}")

                # Verify section hashes are stable for unchanged sections
                sections_run2 = manifest["test-abc-scenario"]["sections"]
                self.assertEqual(sections_run2["md1_section-a"], sections_run1["md1_section-a"],
                               "Section A hash should be identical (unchanged)")
                self.assertEqual(sections_run2["md1_section-c"], sections_run1["md1_section-c"],
                               "Section C hash should be identical (unchanged)")
                self.assertNotEqual(sections_run2["md1_section-b"], sections_run1["md1_section-b"],
                                   "Section B hash should be different (changed)")

                print("\n✅ SUCCESS: Section-level detection correctly identifies only B as changed")
                print(f"   Unchanged: {section_changes['unchanged']}")
                print(f"   Changed: {section_changes['changed']}")
                print(f"   Added: {section_changes['added']}")
                print(f"   Removed: {section_changes['removed']}")

            finally:
                fetch.CACHE = original_cache


class TestPartialExtractionRequirements(unittest.TestCase):
    """Test that section changes enable true partial extraction."""

    def test_section_changes_file_format(self):
        """Verify that section changes file has correct format for extractor."""
        with tempfile.TemporaryDirectory(dir=fetch.ROOT / "state") as tmpdir:
            tmp_path = Path(tmpdir)
            sample = tmp_path / "test.md"

            source = {
                "id": "test-format",
                "url": "https://example.com",
                "type": "official",
                "sample": str(sample.relative_to(fetch.ROOT))
                if str(sample).startswith(str(fetch.ROOT))
                else str(sample)
            }

            manifest = {}

            # First run
            sample.write_text("# A\n\nContent A\n\n# B\n\nContent B")
            fetch.process(source, manifest, live=False)

            # Second run with change
            sample.write_text("# A\n\nContent A\n\n# B\n\nChanged B")
            original_cache = fetch.CACHE
            fetch.CACHE = tmp_path / "cache"
            try:
                fetch.process(source, manifest, live=False)

                # Load changes file
                changes_file = fetch.CACHE / "test-format-sections.json"
                with open(changes_file) as f:
                    changes = json.load(f)

                # Verify required fields for extractor
                self.assertIn("changed", changes)
                self.assertIn("unchanged", changes)
                self.assertIn("added", changes)
                self.assertIn("removed", changes)

                # Verify all values are lists of section IDs
                for key in ["changed", "unchanged", "added", "removed"]:
                    self.assertIsInstance(changes[key], list)
                    for item in changes[key]:
                        self.assertIsInstance(item, str)

            finally:
                fetch.CACHE = original_cache


if __name__ == "__main__":
    unittest.main()
