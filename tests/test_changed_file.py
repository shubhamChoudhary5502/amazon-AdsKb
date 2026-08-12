"""Test that changed.txt contains only changed/added sections"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import fetch


class TestChangedFileContent(unittest.TestCase):
    """Test that changed.txt contains ONLY changed/added sections."""

    def test_changed_file_contains_only_changed_section(self):
        """
        Test the exact A+B+C → A unchanged, B changed, C unchanged scenario
        and prove that <source-id>-changed.txt contains B and does NOT contain A or C.
        """
        with tempfile.TemporaryDirectory(dir=fetch.ROOT / "state") as tmpdir:
            tmp_path = Path(tmpdir)
            sample = tmp_path / "test.md"

            source = {
                "id": "test-changed-file",
                "url": "https://example.com",
                "type": "official",
                "sample": str(sample.relative_to(fetch.ROOT))
                if str(sample).startswith(str(fetch.ROOT))
                else str(sample)
            }

            manifest = {}

            # Set cache location before first run
            original_cache = fetch.CACHE
            fetch.CACHE = tmp_path / "cache"

            try:
                # RUN 1: Create A + B + C (all new)
                print("\n=== RUN 1: A + B + C (all new) ===")
                sample.write_text("""# Section A

Content for section A.

# Section B

Content for section B.

# Section C

Content for section C.""")

                status1 = fetch.process(source, manifest, live=False)
                self.assertEqual(status1, "NEW", "First run should be NEW")

                # Check that changed.txt exists for NEW source (contains all sections)
                changed_file_run1 = fetch.CACHE / "test-changed-file-changed.txt"
                self.assertTrue(changed_file_run1.exists(), "changed.txt should exist for NEW source")

                changed_content_run1 = changed_file_run1.read_text(encoding="utf-8")

                # For NEW source, changed.txt contains ALL sections (all are new)
                self.assertIn("Content for section A", changed_content_run1)
                self.assertIn("Content for section B", changed_content_run1)
                self.assertIn("Content for section C", changed_content_run1)

                print(f"Run 1 changed.txt contains all sections (NEW source)")
                print(f"  Length: {len(changed_content_run1)} chars")
                print(f"  Contains A: {'Content for section A' in changed_content_run1}")
                print(f"  Contains B: {'Content for section B' in changed_content_run1}")
                print(f"  Contains C: {'Content for section C' in changed_content_run1}")

                # RUN 2: A unchanged, B changed, C unchanged
                print("\n=== RUN 2: A unchanged, B changed, C unchanged ===")
                sample.write_text("""# Section A

Content for section A.

# Section B

CHANGED content for section B.

# Section C

Content for section C.""")

                status2 = fetch.process(source, manifest, live=False)
                self.assertEqual(status2, "CHANGED", "Second run should be CHANGED")

                # Check that changed.txt exists for CHANGED source
                changed_file_run2 = fetch.CACHE / "test-changed-file-changed.txt"
                self.assertTrue(changed_file_run2.exists(), "changed.txt should exist for CHANGED source")

                changed_content_run2 = changed_file_run2.read_text(encoding="utf-8")

                print(f"Run 2 changed.txt contains only changed sections:")
                print(f"  Length: {len(changed_content_run2)} chars")
                print(f"  Contains A: {'Content for section A' in changed_content_run2}")
                print(f"  Contains B: {'CHANGED content for section B' in changed_content_run2}")
                print(f"  Contains C: {'Content for section C' in changed_content_run2}")

                # THE KEY PROOF: changed.txt contains B but NOT A or C
                self.assertIn("CHANGED content for section B", changed_content_run2,
                              "changed.txt MUST contain the changed section B")
                self.assertNotIn("Content for section A", changed_content_run2,
                                 "changed.txt MUST NOT contain unchanged section A")
                self.assertNotIn("Content for section C", changed_content_run2,
                                 "changed.txt MUST NOT contain unchanged section C")

                # Verify full cache still has all content (for debugging)
                full_cache = (fetch.CACHE / "test-changed-file.txt").read_text(encoding="utf-8")
                self.assertIn("Content for section A", full_cache)
                self.assertIn("CHANGED content for section B", full_cache)
                self.assertIn("Content for section C", full_cache)

                print("\n✅ SUCCESS: changed.txt contains ONLY B, not A or C")
                print(f"   Full cache length: {len(full_cache)} chars (all sections)")
                print(f"   Changed cache length: {len(changed_content_run2)} chars (only B)")

                # Verify section changes metadata
                changes_file = fetch.CACHE / "test-changed-file-sections.json"
                self.assertTrue(changes_file.exists(), "Section changes file should exist")

                with open(changes_file) as f:
                    section_changes = json.load(f)

                self.assertIn("md1_section-b", section_changes["changed"])
                self.assertIn("md1_section-a", section_changes["unchanged"])
                self.assertIn("md1_section-c", section_changes["unchanged"])

            finally:
                fetch.CACHE = original_cache


class TestChangedFileNewSource(unittest.TestCase):
    """Test that NEW sources get changed.txt with all content."""

    def test_new_source_creates_changed_file_with_all_content(self):
        """For NEW sources, changed.txt should contain the complete source."""
        with tempfile.TemporaryDirectory(dir=fetch.ROOT / "state") as tmpdir:
            tmp_path = Path(tmpdir)
            sample = tmp_path / "test-new.md"

            source = {
                "id": "test-new-source",
                "url": "https://example.com",
                "type": "official",
                "sample": str(sample.relative_to(fetch.ROOT))
                if str(sample).startswith(str(fetch.ROOT))
                else str(sample)
            }

            manifest = {}
            content = """# Introduction

Welcome to the guide.

# Main Content

This is the main content.

# Conclusion

Thanks for reading."""

            sample.write_text(content)

            original_cache = fetch.CACHE
            fetch.CACHE = tmp_path / "cache"

            try:
                status = fetch.process(source, manifest, live=False)
                self.assertEqual(status, "NEW")

                # Check that changed.txt exists and contains all content
                changed_file = fetch.CACHE / "test-new-source-changed.txt"
                self.assertTrue(changed_file.exists(), "changed.txt should exist for NEW source")

                changed_content = changed_file.read_text(encoding="utf-8")

                # For NEW source, all sections should be in changed.txt
                self.assertIn("Welcome to the guide", changed_content)
                self.assertIn("This is the main content", changed_content)
                self.assertIn("Thanks for reading", changed_content)

                # Verify it contains the headings
                self.assertIn("# Introduction", changed_content)
                self.assertIn("# Main Content", changed_content)
                self.assertIn("# Conclusion", changed_content)

            finally:
                fetch.CACHE = original_cache


class TestChangedFileWithAddedSections(unittest.TestCase):
    """Test that added sections are included in changed.txt."""

    def test_added_sections_included_in_changed_file(self):
        """When new sections are added, they should appear in changed.txt."""
        with tempfile.TemporaryDirectory(dir=fetch.ROOT / "state") as tmpdir:
            tmp_path = Path(tmpdir)
            sample = tmp_path / "test-added.md"

            source = {
                "id": "test-added-sections",
                "url": "https://example.com",
                "type": "official",
                "sample": str(sample.relative_to(fetch.ROOT))
                if str(sample).startswith(str(fetch.ROOT))
                else str(sample)
            }

            manifest = {}

            # RUN 1: Just A and B
            sample.write_text("""# Section A

Content A.

# Section B

Content B.""")

            original_cache = fetch.CACHE
            fetch.CACHE = tmp_path / "cache"

            try:
                status1 = fetch.process(source, manifest, live=False)
                self.assertEqual(status1, "NEW")

                # RUN 2: A unchanged, B unchanged, C added
                sample.write_text("""# Section A

Content A.

# Section B

Content B.

# Section C

New section C.""")

                status2 = fetch.process(source, manifest, live=False)
                self.assertEqual(status2, "CHANGED")

                # Check that changed.txt contains the added section C
                changed_file = fetch.CACHE / "test-added-sections-changed.txt"
                changed_content = changed_file.read_text(encoding="utf-8")

                self.assertIn("New section C", changed_content,
                              "changed.txt MUST contain added section C")
                self.assertNotIn("Content A", changed_content,
                                 "changed.txt MUST NOT contain unchanged section A")
                self.assertNotIn("Content B", changed_content,
                                 "changed.txt MUST NOT contain unchanged section B")

                # Verify section changes metadata
                changes_file = fetch.CACHE / "test-added-sections-sections.json"
                with open(changes_file) as f:
                    section_changes = json.load(f)

                self.assertIn("md1_section-c", section_changes["added"])
                self.assertIn("md1_section-a", section_changes["unchanged"])
                self.assertIn("md1_section-b", section_changes["unchanged"])

            finally:
                fetch.CACHE = original_cache


class TestChangedFileWithRemovedSections(unittest.TestCase):
    """Test that removed sections are NOT included in changed.txt."""

    def test_removed_sections_not_in_changed_file(self):
        """When sections are removed, they should NOT appear in changed.txt."""
        with tempfile.TemporaryDirectory(dir=fetch.ROOT / "state") as tmpdir:
            tmp_path = Path(tmpdir)
            sample = tmp_path / "test-removed.md"

            source = {
                "id": "test-removed-sections",
                "url": "https://example.com",
                "type": "official",
                "sample": str(sample.relative_to(fetch.ROOT))
                if str(sample).startswith(str(fetch.ROOT))
                else str(sample)
            }

            manifest = {}

            # RUN 1: A + B + C
            sample.write_text("""# Section A

Content A.

# Section B

Content B.

# Section C

Content C.""")

            original_cache = fetch.CACHE
            fetch.CACHE = tmp_path / "cache"

            try:
                status1 = fetch.process(source, manifest, live=False)
                self.assertEqual(status1, "NEW")

                # RUN 2: A unchanged, B unchanged, C removed
                sample.write_text("""# Section A

Content A.

# Section B

Content B.""")

                status2 = fetch.process(source, manifest, live=False)
                self.assertEqual(status2, "CHANGED")

                # When sections are only removed (no changed/added), changed.txt should not exist
                changed_file = fetch.CACHE / "test-removed-sections-changed.txt"
                self.assertFalse(changed_file.exists(),
                               "changed.txt should NOT exist when only sections are removed (no changed/added)")

                # Verify section changes metadata marks C as removed
                changes_file = fetch.CACHE / "test-removed-sections-sections.json"
                self.assertTrue(changes_file.exists(), "Section changes file should exist")

                with open(changes_file) as f:
                    section_changes = json.load(f)

                self.assertIn("md1_section-c", section_changes["removed"])
                self.assertIn("md1_section-a", section_changes["unchanged"])
                self.assertIn("md1_section-b", section_changes["unchanged"])

            finally:
                fetch.CACHE = original_cache


if __name__ == "__main__":
    unittest.main()
