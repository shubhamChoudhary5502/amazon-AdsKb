"""Tests for section-level change detection in fetch.py"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import fetch


class TestSlugify(unittest.TestCase):
    """Test stable section ID generation."""

    def test_creates_stable_ids(self):
        """Slugify should produce stable IDs from same text."""
        text = "Targeting with Sponsored Products"
        id1 = fetch.slugify(text)
        id2 = fetch.slugify(text)
        self.assertEqual(id1, id2)

    def test_handles_special_characters(self):
        """Slugify should convert special characters to hyphens."""
        self.assertEqual(fetch.slugify("Hello World!"), "hello-world")
        self.assertEqual(fetch.slugify("Test & More"), "test-more")

    def test_limits_length(self):
        """Slugify should limit length to 50 chars."""
        long_text = "a" * 100
        result = fetch.slugify(long_text)
        self.assertLessEqual(len(result), 50)


class TestHashContent(unittest.TestCase):
    """Test content hashing."""

    def test_same_content_same_hash(self):
        """Same content should produce same hash."""
        content = "Test content here"
        hash1 = fetch.hash_content(content)
        hash2 = fetch.hash_content(content)
        self.assertEqual(hash1, hash2)

    def test_different_content_different_hash(self):
        """Different content should produce different hash."""
        hash1 = fetch.hash_content("Content A")
        hash2 = fetch.hash_content("Content B")
        self.assertNotEqual(hash1, hash2)

    def test_is_stable(self):
        """Hash should be stable across calls."""
        content = "Stable content"
        hashes = [fetch.hash_content(content) for _ in range(5)]
        self.assertTrue(all(h == hashes[0] for h in hashes))


class TestParseSections(unittest.TestCase):
    """Test Markdown section parsing."""

    def test_parses_markdown_sections(self):
        """Should parse Markdown into sections by headings."""
        markdown = """# Targeting

Keyword targeting options.

# Automatic Targeting

Automatic targeting uses Amazon's algorithm.

## Bidding

Bidding strategies for automatic targeting."""
        sections = fetch.parse_sections(markdown, is_html=False)
        self.assertIn("md1_targeting", sections)
        self.assertIn("md1_automatic-targeting", sections)
        self.assertIn("md2_bidding", sections)

    def test_section_content_captured(self):
        """Each section should capture its content."""
        markdown = """# Section A

Content of section A.

# Section B

Content of section B."""
        sections = fetch.parse_sections(markdown, is_html=False)
        self.assertIn("Content of section A", sections["md1_section-a"])
        self.assertIn("Content of section B", sections["md1_section-b"])

    def test_empty_markdown_returns_empty(self):
        """Empty Markdown should return empty sections."""
        sections = fetch.parse_sections("", is_html=False)
        self.assertEqual(sections, {})

    def test_html_returns_empty(self):
        """HTML should return empty sections (handled elsewhere)."""
        sections = fetch.parse_sections("<html>...</html>", is_html=True)
        self.assertEqual(sections, {})


class TestCompareSections(unittest.TestCase):
    """Test section comparison logic."""

    def test_identical_sections_no_changes(self):
        """Identical sections should show no changes."""
        old = {"md1_section-a": "hash1", "md1_section-b": "hash2"}
        new = {"md1_section-a": "hash1", "md1_section-b": "hash2"}
        result = fetch.compare_sections(old, new)
        self.assertEqual(result["changed"], [])
        self.assertEqual(result["added"], [])
        self.assertEqual(result["removed"], [])
        self.assertCountEqual(result["unchanged"], ["md1_section-a", "md1_section-b"])

    def test_one_changed_section(self):
        """Should detect exactly one changed section."""
        old = {"md1_section-a": "hash1", "md1_section-b": "hash2"}
        new = {"md1_section-a": "hash1", "md1_section-b": "hash3"}
        result = fetch.compare_sections(old, new)
        self.assertEqual(result["changed"], ["md1_section-b"])
        self.assertEqual(result["unchanged"], ["md1_section-a"])
        self.assertEqual(result["added"], [])
        self.assertEqual(result["removed"], [])

    def test_added_section(self):
        """Should detect added sections."""
        old = {"md1_section-a": "hash1"}
        new = {"md1_section-a": "hash1", "md1_section-b": "hash2"}
        result = fetch.compare_sections(old, new)
        self.assertEqual(result["added"], ["md1_section-b"])
        self.assertEqual(result["unchanged"], ["md1_section-a"])
        self.assertEqual(result["changed"], [])
        self.assertEqual(result["removed"], [])

    def test_removed_section(self):
        """Should detect removed sections."""
        old = {"md1_section-a": "hash1", "md1_section-b": "hash2"}
        new = {"md1_section-a": "hash1"}
        result = fetch.compare_sections(old, new)
        self.assertEqual(result["removed"], ["md1_section-b"])
        self.assertEqual(result["unchanged"], ["md1_section-a"])
        self.assertEqual(result["changed"], [])
        self.assertEqual(result["added"], [])

    def test_multiple_changes(self):
        """Should detect multiple simultaneous changes."""
        old = {"md1_a": "h1", "md1_b": "h2", "md1_c": "h3"}
        new = {"md1_a": "h1", "md1_b": "h4", "md1_d": "h5"}
        result = fetch.compare_sections(old, new)
        self.assertCountEqual(result["changed"], ["md1_b"])
        self.assertCountEqual(result["added"], ["md1_d"])
        self.assertCountEqual(result["removed"], ["md1_c"])
        self.assertCountEqual(result["unchanged"], ["md1_a"])

    def test_unrelated_sections_remain_unchanged(self):
        """Unchanged sections should be classified correctly."""
        old = {"md1_a": "h1", "md1_b": "h2", "md1_c": "h3"}
        new = {"md1_a": "h1", "md1_b": "h4", "md1_c": "h3"}
        result = fetch.compare_sections(old, new)
        self.assertEqual(result["unchanged"], ["md1_a", "md1_c"])
        self.assertEqual(result["changed"], ["md1_b"])


class TestSectionIntegration(unittest.TestCase):
    """Integration tests for section tracking with full pipeline."""

    def test_manifest_includes_section_hashes(self):
        """Manifest entries should include section hashes."""
        with tempfile.TemporaryDirectory(dir=fetch.ROOT / "state") as tmpdir:
            tmp_path = Path(tmpdir)
            sample = tmp_path / "test.md"
            sample.write_text("# Section A\n\nContent A\n\n# Section B\n\nContent B")

            source = {
                "id": "test-sections",
                "url": "https://example.com",
                "type": "official",
                "sample": str(sample.relative_to(fetch.ROOT))
                if str(sample).startswith(str(fetch.ROOT))
                else str(sample)
            }

            manifest = {}
            status = fetch.process(source, manifest, live=False)

            self.assertEqual(status, "NEW")
            self.assertIn("sections", manifest["test-sections"])
            self.assertIsInstance(manifest["test-sections"]["sections"], dict)

    def test_unchanged_source_no_section_changes(self):
        """When source unchanged, no section changes should be recorded."""
        with tempfile.TemporaryDirectory(dir=fetch.ROOT / "state") as tmpdir:
            tmp_path = Path(tmpdir)
            sample = tmp_path / "test.md"
            original_content = "# Section A\n\nContent A"
            sample.write_text(original_content)

            source = {
                "id": "test-unchanged",
                "url": "https://example.com",
                "type": "official",
                "sample": str(sample.relative_to(fetch.ROOT))
                if str(sample).startswith(str(fetch.ROOT))
                else str(sample)
            }

            manifest = {}
            # First run - NEW
            status1 = fetch.process(source, manifest, live=False)
            self.assertEqual(status1, "NEW")

            # Second run - UNCHANGED
            status2 = fetch.process(source, manifest, live=False)
            self.assertEqual(status2, "UNCHANGED")

    def test_changed_source_creates_section_changes_file(self):
        """Changed source should create section changes file."""
        with tempfile.TemporaryDirectory(dir=fetch.ROOT / "state") as tmpdir:
            tmp_path = Path(tmpdir)
            sample = tmp_path / "test.md"

            # First run
            sample.write_text("# Section A\n\nContent A\n\n# Section B\n\nContent B")
            source = {
                "id": "test-changes",
                "url": "https://example.com",
                "type": "official",
                "sample": str(sample.relative_to(fetch.ROOT))
                if str(sample).startswith(str(fetch.ROOT))
                else str(sample)
            }

            manifest = {}
            status1 = fetch.process(source, manifest, live=False)
            self.assertEqual(status1, "NEW")

            # Second run - change Section B
            sample.write_text("# Section A\n\nContent A\n\n# Section B\n\nChanged Content B")
            original_cache = fetch.CACHE
            fetch.CACHE = tmp_path / "cache"
            try:
                status2 = fetch.process(source, manifest, live=False)
                self.assertEqual(status2, "CHANGED")

                # Check for section changes file
                changes_file = fetch.CACHE / "test-changes-sections.json"
                self.assertTrue(changes_file.exists(), "Section changes file should be created")

                # Verify section changes content
                with open(changes_file) as f:
                    changes = json.load(f)
                self.assertIn("changed", changes)
                self.assertIn("unchanged", changes)
            finally:
                fetch.CACHE = original_cache

    def test_whole_source_hash_still_works(self):
        """Whole-source hash change detection should still work."""
        with tempfile.TemporaryDirectory(dir=fetch.ROOT / "state") as tmpdir:
            tmp_path = Path(tmpdir)
            sample = tmp_path / "test.md"

            source = {
                "id": "test-whole-hash",
                "url": "https://example.com",
                "type": "official",
                "sample": str(sample.relative_to(fetch.ROOT))
                if str(sample).startswith(str(fetch.ROOT))
                else str(sample)
            }

            manifest = {}
            # First run
            sample.write_text("# Section A\n\nContent A")
            status1 = fetch.process(source, manifest, live=False)
            self.assertEqual(status1, "NEW")
            first_hash = manifest["test-whole-hash"]["hash"]

            # Second run with different content
            sample.write_text("# Section A\n\nChanged Content A")
            status2 = fetch.process(source, manifest, live=False)
            self.assertEqual(status2, "CHANGED")
            second_hash = manifest["test-whole-hash"]["hash"]

            self.assertNotEqual(first_hash, second_hash)


class TestStableSectionIds(unittest.TestCase):
    """Test that section IDs remain stable across runs."""

    def test_heading_creates_same_id_each_time(self):
        """Same heading should create same section ID."""
        markdown1 = "# Targeting Options\n\nContent here"
        markdown2 = "# Targeting Options\n\nDifferent content"

        sections1 = fetch.parse_sections(markdown1, is_html=False)
        sections2 = fetch.parse_sections(markdown2, is_html=False)

        self.assertIn("md1_targeting-options", sections1)
        self.assertIn("md1_targeting-options", sections2)

    def test_different_headings_different_ids(self):
        """Different headings should create different IDs."""
        markdown = "# Section A\n\nContent A\n\n# Section B\n\nContent B\n\n# Section C\n\nContent C"
        sections = fetch.parse_sections(markdown, is_html=False)

        # Check that all three sections exist
        self.assertIn("md1_section-a", sections)
        self.assertIn("md1_section-b", sections)
        self.assertIn("md1_section-c", sections)

        # Check that they have different content
        self.assertNotEqual(sections.get("md1_section-a"), sections.get("md1_section-b"))
        self.assertNotEqual(sections.get("md1_section-b"), sections.get("md1_section-c"))

    def test_heading_levels_included_in_id(self):
        """Section ID should include heading level."""
        markdown = """# Level 1

Content 1

## Level 2

Content 2

### Level 3

Content 3"""
        sections = fetch.parse_sections(markdown, is_html=False)

        self.assertIn("md1_level-1", sections)
        self.assertIn("md2_level-2", sections)
        self.assertIn("md3_level-3", sections)


if __name__ == "__main__":
    unittest.main()
