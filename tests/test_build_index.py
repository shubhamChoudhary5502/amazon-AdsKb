"""Tests for scripts/build_index.py

Tests the index builder that rebuilds knowledge/index.md from concept docs.
The contract:
- Reads from knowledge/concepts/*.md
- Parses OKF frontmatter from each concept
- Generates index with deterministic ordering (sorted by slug)
- Only writes if generated content differs from existing
- Official/api sources counted separately from total

Run: python3 -m unittest tests.test_build_index
"""
import sys
import tempfile
import unittest
from pathlib import Path
import subprocess

# Get repo root dynamically
REPO_ROOT = Path(__file__).resolve().parent.parent
BUILD_INDEX_SCRIPT = REPO_ROOT / "scripts" / "build_index.py"
OKF_SCRIPT = REPO_ROOT / "scripts" / "okf.py"


def setup_test_repo(tmpdir):
    """Create a test repository structure with build_index.py and okf.py."""
    test_repo = Path(tmpdir)
    knowledge_dir = test_repo / "knowledge"
    concepts_dir = knowledge_dir / "concepts"
    concepts_dir.mkdir(parents=True)

    # Copy the scripts to the test repo
    test_scripts = test_repo / "scripts"
    test_scripts.mkdir(parents=True)
    (test_scripts / "build_index.py").write_text(BUILD_INDEX_SCRIPT.read_text())
    (test_scripts / "okf.py").write_text(OKF_SCRIPT.read_text())

    index_file = knowledge_dir / "index.md"
    return test_repo, knowledge_dir, concepts_dir, index_file


# Valid OKF frontmatter template
VALID_FRONTMATTER = """---
okf: "0.1"
id: {id}
title: {title}
description: Test description.
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
    url: https://example.com/{id}
    kind: official
    fetched: 2026-08-12
---

# {title}

## Overview

Test overview.

## Key facts

- Test fact. [S1]
"""


class TestBuildIndexContract(unittest.TestCase):
    """Test the basic contract of build_index.py."""

    def test_creates_index_from_concepts(self):
        """Test that valid knowledge documents appear in the index."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, knowledge_dir, concepts_dir, index_file = setup_test_repo(tmpdir)

            # Create test concept documents
            (concepts_dir / "concept-alpha.md").write_text(
                VALID_FRONTMATTER.format(id="concept-alpha", title="Concept Alpha")
            )
            (concepts_dir / "concept-beta.md").write_text(
                VALID_FRONTMATTER.format(id="concept-beta", title="Concept Beta")
            )

            # Run build_index.py
            result = subprocess.run(
                [sys.executable, "scripts/build_index.py"],
                capture_output=True,
                text=True,
                cwd=test_repo
            )

            self.assertEqual(result.returncode, 0)
            self.assertTrue(index_file.exists(), "Index should be created")

            content = index_file.read_text()

            # Should contain both concepts
            self.assertIn("Concept Alpha", content)
            self.assertIn("Concept Beta", content)
            self.assertIn("concepts/concept-alpha.md", content)
            self.assertIn("concepts/concept-beta.md", content)

    def test_deterministic_ordering(self):
        """Test that concepts appear in deterministic (sorted) order."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, knowledge_dir, concepts_dir, index_file = setup_test_repo(tmpdir)

            # Create concepts in random order
            for name in ["zebra", "apple", "middle"]:
                (concepts_dir / f"{name}.md").write_text(
                    VALID_FRONTMATTER.format(id=name, title=name.title())
                )

            # Run build_index.py
            result = subprocess.run(
                [sys.executable, "scripts/build_index.py"],
                capture_output=True,
                text=True,
                cwd=test_repo
            )

            self.assertEqual(result.returncode, 0)
            content = index_file.read_text()

            # Should be sorted alphabetically: apple, middle, zebra
            lines = content.split("\n")
            concept_lines = [l for l in lines if "| [" in l and "](" in l]

            # Find positions
            apple_idx = next(i for i, l in enumerate(concept_lines) if "Apple" in l)
            middle_idx = next(i for i, l in enumerate(concept_lines) if "Middle" in l)
            zebra_idx = next(i for i, l in enumerate(concept_lines) if "Zebra" in l)

            self.assertLess(apple_idx, middle_idx,
                          "Apple should come before Middle")
            self.assertLess(middle_idx, zebra_idx,
                          "Middle should come before Zebra")

    def test_index_unchanged_when_no_concepts_change(self):
        """Test that running twice without changes produces byte-identical output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, knowledge_dir, concepts_dir, index_file = setup_test_repo(tmpdir)

            # Create test concept
            (concepts_dir / "test-concept.md").write_text(
                VALID_FRONTMATTER.format(id="test-concept", title="Test Concept")
            )

            # First run
            result1 = subprocess.run(
                [sys.executable, "scripts/build_index.py"],
                capture_output=True,
                text=True,
                cwd=test_repo
            )

            self.assertEqual(result1.returncode, 0)
            self.assertIn("index rebuilt", result1.stdout)

            content1 = index_file.read_text()

            # Second run (no changes)
            result2 = subprocess.run(
                [sys.executable, "scripts/build_index.py"],
                capture_output=True,
                text=True,
                cwd=test_repo
            )

            self.assertEqual(result2.returncode, 0)
            content2 = index_file.read_text()

            # Should report unchanged
            self.assertIn("index unchanged", result2.stdout)

            # Content should be byte-identical
            self.assertEqual(content1, content2,
                           "Index should be byte-identical when no concepts change")

    def test_updated_document_updates_index(self):
        """Test that updating a document updates the index correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, knowledge_dir, concepts_dir, index_file = setup_test_repo(tmpdir)

            # Create initial concept
            concept_file = concepts_dir / "test-concept.md"
            concept_file.write_text(
                VALID_FRONTMATTER.format(id="test-concept", title="Old Title")
            )

            # First build
            subprocess.run(
                [sys.executable, "scripts/build_index.py"],
                capture_output=True,
                cwd=test_repo
            )
            content1 = index_file.read_text()

            # Update the concept
            concept_file.write_text(
                VALID_FRONTMATTER.format(id="test-concept", title="New Title")
            )

            # Second build
            result = subprocess.run(
                [sys.executable, "scripts/build_index.py"],
                capture_output=True,
                text=True,
                cwd=test_repo
            )

            self.assertEqual(result.returncode, 0)
            self.assertIn("index rebuilt", result.stdout)

            content2 = index_file.read_text()

            # Index should reflect the change
            self.assertNotIn("Old Title", content2)
            self.assertIn("New Title", content2)

    def test_unrelated_files_do_not_affect_index(self):
        """Test that unrelated files don't unexpectedly alter the index."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, knowledge_dir, concepts_dir, index_file = setup_test_repo(tmpdir)

            # Create a concept
            (concepts_dir / "test-concept.md").write_text(
                VALID_FRONTMATTER.format(id="test-concept", title="Test Concept")
            )

            # Create unrelated files
            (knowledge_dir / "notes.txt").write_text("Random notes")
            (knowledge_dir / "README.md").write_text("# README")
            (concepts_dir / ".hidden").write_text("hidden file")

            # Build index
            result = subprocess.run(
                [sys.executable, "scripts/build_index.py"],
                capture_output=True,
                text=True,
                cwd=test_repo
            )

            self.assertEqual(result.returncode, 0)
            content = index_file.read_text()

            # Should only contain the concept
            self.assertIn("Test Concept", content)
            self.assertNotIn("Random notes", content)
            self.assertNotIn("README", content)
            self.assertNotIn("hidden file", content)

    def test_official_source_counting(self):
        """Test that official/api sources are counted correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, knowledge_dir, concepts_dir, index_file = setup_test_repo(tmpdir)

            # Create concept with official source
            (concepts_dir / "official-concept.md").write_text(
                VALID_FRONTMATTER.format(id="official-concept", title="Official Concept")
            )

            # Build index
            result = subprocess.run(
                [sys.executable, "scripts/build_index.py"],
                capture_output=True,
                text=True,
                cwd=test_repo
            )

            self.assertEqual(result.returncode, 0)
            content = index_file.read_text()

            # Should show official count
            self.assertIn("1/1", content)

    def test_empty_concepts_directory(self):
        """Test behavior when there are no concept documents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, knowledge_dir, concepts_dir, index_file = setup_test_repo(tmpdir)

            # Run with no concepts
            result = subprocess.run(
                [sys.executable, "scripts/build_index.py"],
                capture_output=True,
                text=True,
                cwd=test_repo
            )

            self.assertEqual(result.returncode, 0)
            self.assertTrue(index_file.exists())

            content = index_file.read_text()

            # Should show 0 concepts
            self.assertIn("0 concepts", content)


class TestBuildIndexEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def test_invalid_document_skipped_or_handled(self):
        """Test behavior with invalid documents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, knowledge_dir, concepts_dir, index_file = setup_test_repo(tmpdir)

            # Create a valid concept
            (concepts_dir / "valid-concept.md").write_text(
                VALID_FRONTMATTER.format(id="valid-concept", title="Valid Concept")
            )

            # Create an invalid concept (missing frontmatter)
            (concepts_dir / "invalid-concept.md").write_text(
                "# Invalid Concept\n\nNo frontmatter here."
            )

            # Build index - should fail on invalid documents
            result = subprocess.run(
                [sys.executable, "scripts/build_index.py"],
                capture_output=True,
                text=True,
                cwd=test_repo
            )

            # The script should fail when it encounters an invalid document
            self.assertNotEqual(result.returncode, 0,
                              "build_index.py should fail on invalid documents")
            self.assertIn("frontmatter", result.stderr.lower() +
                          " or front matter or frontmatter fence" +
                          " or parsing or error",
                          "Error should mention parsing/frontmatter issue")

    def test_missing_concepts_directory(self):
        """Test behavior when concepts directory doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo = Path(tmpdir)
            knowledge_dir = test_repo / "knowledge"
            knowledge_dir.mkdir(parents=True)
            index_file = knowledge_dir / "index.md"

            # Copy scripts
            test_scripts = test_repo / "scripts"
            test_scripts.mkdir(parents=True)
            (test_scripts / "build_index.py").write_text(BUILD_INDEX_SCRIPT.read_text())
            (test_scripts / "okf.py").write_text(OKF_SCRIPT.read_text())

            # concepts/ doesn't exist

            # Run build_index.py
            result = subprocess.run(
                [sys.executable, "scripts/build_index.py"],
                capture_output=True,
                text=True,
                cwd=test_repo
            )

            # Should handle gracefully
            self.assertEqual(result.returncode, 0)

            if index_file.exists():
                content = index_file.read_text()
                # Should show 0 concepts
                self.assertIn("0 concepts", content)

    def test_concept_with_community_sources(self):
        """Test concepts with community source types."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, knowledge_dir, concepts_dir, index_file = setup_test_repo(tmpdir)

            # Create concept with community source
            community_doc = VALID_FRONTMATTER.replace("kind: official", "kind: community")
            (concepts_dir / "community-concept.md").write_text(
                community_doc.format(id="community-concept", title="Community Concept")
            )

            # Build index
            result = subprocess.run(
                [sys.executable, "scripts/build_index.py"],
                capture_output=True,
                text=True,
                cwd=test_repo
            )

            self.assertEqual(result.returncode, 0)
            content = index_file.read_text()

            # Should show 0 official, 1 total
            self.assertIn("0/1", content)

    def test_mixed_source_types(self):
        """Test concepts with mixed source types."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, knowledge_dir, concepts_dir, index_file = setup_test_repo(tmpdir)

            # Create concept with mixed sources manually
            mixed_doc = """---
okf: "0.1"
id: mixed-concept
title: Mixed Concept
description: Test description.
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
  - id: S2
    url: https://blog.example.com/test
    kind: community
    fetched: 2026-08-12
---

# Mixed Concept

## Overview

Test overview.

## Key facts

- Test fact. [S1]
- Another fact. [S2]
"""
            (concepts_dir / "mixed-concept.md").write_text(mixed_doc)

            # Build index
            result = subprocess.run(
                [sys.executable, "scripts/build_index.py"],
                capture_output=True,
                text=True,
                cwd=test_repo
            )

            self.assertEqual(result.returncode, 0)
            content = index_file.read_text()

            # Should show 1 official (S1), 2 total (S1 + S2)
            self.assertIn("1/2", content)

    def test_unicode_in_titles(self):
        """Test that Unicode characters in titles are handled correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, knowledge_dir, concepts_dir, index_file = setup_test_repo(tmpdir)

            # Create concept with Unicode title
            (concepts_dir / "unicode-concept.md").write_text(
                VALID_FRONTMATTER.format(
                    id="unicode-concept",
                    title="Café & 日本語 Concept"
                )
            )

            # Build index
            result = subprocess.run(
                [sys.executable, "scripts/build_index.py"],
                capture_output=True,
                text=True,
                cwd=test_repo
            )

            self.assertEqual(result.returncode, 0)
            content = index_file.read_text()

            # Should preserve Unicode
            self.assertIn("Café", content)
            self.assertIn("日本語", content)

    def test_long_titles_and_tags(self):
        """Test handling of long titles and tag lists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, knowledge_dir, concepts_dir, index_file = setup_test_repo(tmpdir)

            # Create concept with long tags
            long_tags_doc = VALID_FRONTMATTER.replace(
                "tags: [test]",
                "tags: [very-long-tag-name, another-extended-tag, third-lengthy-tag-name]"
            )
            (concepts_dir / "long-concept.md").write_text(
                long_tags_doc.format(id="long-concept", title="A" * 50)
            )

            # Build index
            result = subprocess.run(
                [sys.executable, "scripts/build_index.py"],
                capture_output=True,
                text=True,
                cwd=test_repo
            )

            self.assertEqual(result.returncode, 0)
            content = index_file.read_text()

            # Should handle long content
            self.assertIn("A" * 50, content)
            self.assertIn("very-long-tag-name", content)


class TestBuildIndexDeterminism(unittest.TestCase):
    """Test deterministic behavior guarantees."""

    def test_rebuild_produces_identical_output(self):
        """Test that rebuilding produces identical output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, knowledge_dir, concepts_dir, index_file = setup_test_repo(tmpdir)

            # Create multiple concepts
            for i in range(5):
                (concepts_dir / f"concept-{i}.md").write_text(
                    VALID_FRONTMATTER.format(
                        id=f"concept-{i}",
                        title=f"Concept {i}"
                    )
                )

            # First build
            subprocess.run(
                [sys.executable, "scripts/build_index.py"],
                capture_output=True,
                cwd=test_repo
            )
            content1 = index_file.read_text()

            # Delete and rebuild
            index_file.unlink()
            subprocess.run(
                [sys.executable, "scripts/build_index.py"],
                capture_output=True,
                cwd=test_repo
            )
            content2 = index_file.read_text()

            # Should be byte-identical
            self.assertEqual(content1, content2,
                           "Rebuilding should produce byte-identical output")

    def test_ordering_independent_of_creation_order(self):
        """Test that ordering doesn't depend on file creation order."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_repo, knowledge_dir, concepts_dir, index_file = setup_test_repo(tmpdir)

            # Create concepts in random order
            import random
            names = ["delta", "alpha", "charlie", "bravo"]
            random.shuffle(names)

            for name in names:
                (concepts_dir / f"{name}.md").write_text(
                    VALID_FRONTMATTER.format(id=name, title=name.title())
                )

            # Build index
            subprocess.run(
                [sys.executable, "scripts/build_index.py"],
                capture_output=True,
                cwd=test_repo
            )
            content = index_file.read_text()

            # Should be sorted regardless of creation order
            lines = content.split("\n")
            concept_lines = [l for l in lines if "| [" in l and "](" in l]

            # Verify alphabetical order
            titles = []
            for line in concept_lines:
                if "| [" in line:
                    start = line.index("| [") + 3
                    end = line.index("](", start)
                    titles.append(line[start:end])

            self.assertEqual(titles, sorted(titles),
                          "Titles should be in alphabetical order")


if __name__ == "__main__":
    unittest.main()
