#!/usr/bin/env python3
"""
Comprehensive tests for validate_extraction.py covering the bug fix and conflict path.

Tests verify:
1. The undefined variable bug is fixed (fact_lower → normalized_fact)
2. Conflict classification works correctly
3. All validation edge cases are handled
4. Output schema is correct for all classifications
5. Run isolation is maintained
"""

import unittest
import json
import tempfile
import shutil
from pathlib import Path
import sys

# Add scripts directory to path for imports
sys.path.insert(0, 'scripts')

import validate_extraction


class TestConflictClassification(unittest.TestCase):
    """Test the conflict classification path that was previously broken."""

    def setUp(self):
        """Set up test environment with conflict scenario."""
        self.test_dir = tempfile.mkdtemp()
        self.extracts_dir = Path(self.test_dir) / "extracts"
        self.concepts_dir = Path(self.test_dir) / "concepts"
        self.validated_dir = Path(self.test_dir) / "validated"
        self.cache_dir = Path(self.test_dir) / "cache"

        for dir_path in [self.extracts_dir, self.concepts_dir, self.validated_dir, self.cache_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Create cache file
        self.cache_file = self.cache_dir / "test-source.txt"
        self.cache_file.write_text("Test content")

        self.run_id = "20260812-conflict-test"

    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir)

    def create_extraction_artifact(self, run_id, facts, source_id="sp-official"):
        """Create a test extraction artifact."""
        # Get realistic source URL for genuine sources
        genuine_urls = {
            "sp-official": "https://advertising.amazon.com/solutions/products/sponsored-products",
            "sb-official": "https://advertising.amazon.com/solutions/products/sponsored-brands",
            "sd-official": "https://advertising.amazon.com/solutions/products/sponsored-display",
            "targeting-official": "https://advertising.amazon.com/library/guides/targeting-with-sponsored-products",
            "ppc-community": "https://www.junglescout.com/resources/articles/amazon-ppc/",
            "ads-api-notes": "https://advertising.amazon.com/API/docs/en-us/release-notes/index"
        }
        source_url = genuine_urls.get(source_id, f"https://example.com/{source_id}")

        artifact = {
            "version": "1.0",
            "run_id": run_id,
            "extracted_at": "2026-08-12T10:00:00Z",
            "source_id": source_id,
            "source_type": "official",
            "source_url": source_url,
            "cache_file": str(self.cache_file),
            "content_hash": "abc123",
            "facts": facts,
            "extraction_metadata": {}
        }

        run_dir = self.extracts_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        artifact_file = run_dir / f"{source_id}-20260812100000.json"
        with open(artifact_file, 'w') as f:
            json.dump(artifact, f)

        return str(artifact_file)

    def test_conflict_classification_bug_is_fixed(self):
        """Test that the undefined variable bug (fact_lower) is fixed."""
        # Create a concept document with conflicting information
        concept_file = self.concepts_dir / "bidding-strategies.md"
        concept_content = """---
id: bidding-strategies
title: Bidding Strategies
---

# Bidding Strategies

- The up-and-down bid adjustment for top-of-search placement is capped at 100%, but some sources report 50%.
- This is an official Amazon source.
"""
        concept_file.write_text(concept_content)

        # Create extraction artifact that would trigger the conflict path
        facts = [
            {
                "fact": "The up-and-down bid adjustment for top-of-search placement is 50%",
                "concept": "bidding-strategies",
                "quote": "up-and-down bid adjustment for top-of-search placement is 50%",
                "extracted_at": "2026-08-12T10:00:00Z"
            }
        ]

        self.create_extraction_artifact(self.run_id, facts)

        # Run validation - this should NOT raise NameError anymore
        try:
            results, summary, artifact_path = validate_extraction.validate_extraction_artifacts(
                self.run_id,
                extracts_dir=str(self.extracts_dir),
                concepts_dir=str(self.concepts_dir),
                output_dir=str(self.validated_dir)
            )

            # Should succeed without NameError
            self.assertIsNotNone(results)
            self.assertIsNotNone(summary)
            self.assertIsNotNone(artifact_path)

        except NameError as e:
            self.fail(f"NameError should be fixed but got: {e}")

    def test_genuine_conflict_classification(self):
        """Test detection of genuine conflicting facts with deterministic classification."""
        # Create concept with documented conflict - unambiguous fixture
        concept_file = self.concepts_dir / "test-concept.md"
        concept_content = """---
id: test-concept
title: Test Concept
---

# Test Concept

- Official documentation states the bid adjustment is capped at 100%, however community reports suggest 50% in some cases.
"""
        concept_file.write_text(concept_content)

        # Create extraction artifact with conflicting fact - designed to trigger conflict
        facts = [
            {
                "fact": "Community reports suggest the bid adjustment is 50% in some cases",
                "concept": "test-concept",
                "quote": "bid adjustment is 50%",
                "extracted_at": "2026-08-12T10:00:00Z"
            }
        ]

        self.create_extraction_artifact(self.run_id, facts)

        # Run validation
        results, summary, artifact_path = validate_extraction.validate_extraction_artifacts(
            self.run_id,
            extracts_dir=str(self.extracts_dir),
            concepts_dir=str(self.concepts_dir),
            output_dir=str(self.validated_dir)
        )

        # MUST be classified as conflict (not duplicate, not changed, not new)
        self.assertEqual(summary["conflict_count"], 1, "Must be classified as conflict")
        self.assertEqual(summary["duplicate_count"], 0, "Must not be classified as duplicate")
        self.assertEqual(summary["changed_count"], 0, "Must not be classified as changed")
        self.assertEqual(summary["new_count"], 0, "Must not be classified as new")

        # Verify conflict record structure
        conflict_record = results["conflict"][0]
        self.assertEqual(conflict_record["classification"], "conflict")
        self.assertIn("conflicting_line", conflict_record)
        self.assertIn("fact", conflict_record)
        self.assertIn("concept", conflict_record)
        self.assertIn("source_id", conflict_record)
        self.assertIn("source_url", conflict_record)
        self.assertIn("source_type", conflict_record)
        self.assertIn("quote", conflict_record)
        self.assertIn("extracted_at", conflict_record)

    def test_conflict_preserves_source_information(self):
        """Test that both sides of conflict preserve source information with exact classification."""
        # Create concept with documented conflict and source information - designed for unambiguous conflict
        concept_file = self.concepts_dir / "pricing.md"
        concept_content = """---
id: pricing
title: Pricing
sources:
  - id: S1
    url: https://official.example.com/pricing
    kind: official
    fetched: 2026-08-10
  - id: S2
    url: https://blog.example.com/pricing
    kind: community
    fetched: 2026-08-10
---

# Pricing

- Official source states minimum bid is $0.02, but community blog reports minimum bid can be $0.01 in some cases. [S1][S2]
"""
        concept_file.write_text(concept_content)

        # Create extraction artifact from community source - designed to trigger conflict
        facts = [
            {
                "fact": "The minimum bid can be as low as $0.01 in some cases",
                "concept": "pricing",
                "quote": "minimum bid can be $0.01",
                "extracted_at": "2026-08-12T10:00:00Z"
            }
        ]

        self.create_extraction_artifact(self.run_id, facts)

        # Run validation
        results, summary, artifact_path = validate_extraction.validate_extraction_artifacts(
            self.run_id,
            extracts_dir=str(self.extracts_dir),
            concepts_dir=str(self.concepts_dir),
            output_dir=str(self.validated_dir)
        )

        # MUST be classified as conflict (overlap with conflicting line)
        self.assertEqual(summary["conflict_count"], 1, "Must be classified as conflict")
        self.assertEqual(summary["duplicate_count"], 0, "Must not be classified as duplicate")
        self.assertEqual(summary["new_count"], 0, "Must not be classified as new")
        self.assertEqual(summary["changed_count"], 0, "Must not be classified as changed")

        # Verify conflict record preserves all source information
        conflict_record = results["conflict"][0]
        self.assertIn("source_id", conflict_record)
        self.assertIn("source_url", conflict_record)
        self.assertIn("source_type", conflict_record)
        self.assertIn("quote", conflict_record)
        self.assertIn("fact", conflict_record)
        self.assertEqual(conflict_record["classification"], "conflict")


class TestValidationEdgeCases(unittest.TestCase):
    """Test edge cases in validation."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.extracts_dir = Path(self.test_dir) / "extracts"
        self.concepts_dir = Path(self.test_dir) / "concepts"
        self.validated_dir = Path(self.test_dir) / "validated"
        self.cache_dir = Path(self.test_dir) / "cache"

        for dir_path in [self.extracts_dir, self.concepts_dir, self.validated_dir, self.cache_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Create cache file
        self.cache_file = self.cache_dir / "test-source.txt"
        self.cache_file.write_text("Test content")

        self.run_id = "20260812-edge-case-test"

    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir)

    def create_extraction_artifact(self, run_id, facts, source_id="sp-official"):
        """Create a test extraction artifact."""
        # Get realistic source URL for genuine sources
        genuine_urls = {
            "sp-official": "https://advertising.amazon.com/solutions/products/sponsored-products",
            "sb-official": "https://advertising.amazon.com/solutions/products/sponsored-brands",
            "sd-official": "https://advertising.amazon.com/solutions/products/sponsored-display",
            "targeting-official": "https://advertising.amazon.com/library/guides/targeting-with-sponsored-products",
            "ppc-community": "https://www.junglescout.com/resources/articles/amazon-ppc/",
            "ads-api-notes": "https://advertising.amazon.com/API/docs/en-us/release-notes/index"
        }
        source_url = genuine_urls.get(source_id, f"https://example.com/{source_id}")

        artifact = {
            "version": "1.0",
            "run_id": run_id,
            "extracted_at": "2026-08-12T10:00:00Z",
            "source_id": source_id,
            "source_type": "official",
            "source_url": source_url,
            "cache_file": str(self.cache_file),
            "content_hash": "abc123",
            "facts": facts,
            "extraction_metadata": {}
        }

        run_dir = self.extracts_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        artifact_file = run_dir / f"{source_id}-20260812100000.json"
        with open(artifact_file, 'w') as f:
            json.dump(artifact, f)

        return str(artifact_file)

    def test_empty_fact_rejected(self):
        """Test that empty facts are rejected with exact classification."""
        facts = [
            {
                "fact": "",
                "concept": "test-concept",
                "quote": "some quote",
                "extracted_at": "2026-08-12T10:00:00Z"
            }
        ]

        self.create_extraction_artifact(self.run_id, facts)

        results, summary, artifact_path = validate_extraction.validate_extraction_artifacts(
            self.run_id,
            extracts_dir=str(self.extracts_dir),
            concepts_dir=str(self.concepts_dir),
            output_dir=str(self.validated_dir)
        )

        # MUST be classified as rejected
        self.assertEqual(summary["rejected_count"], 1, "Must be classified as rejected")
        self.assertEqual(summary["new_count"], 0, "Must not be classified as new")
        self.assertEqual(summary["duplicate_count"], 0, "Must not be classified as duplicate")
        self.assertEqual(summary["changed_count"], 0, "Must not be classified as changed")
        self.assertEqual(summary["conflict_count"], 0, "Must not be classified as conflict")

        # Verify rejected fact schema
        rejected_fact = results["rejected"][0]
        self.assertEqual(rejected_fact["classification"], "rejected")
        self.assertEqual(rejected_fact["rejection_reason"], "fact_is_empty")

    def test_short_fact_rejected(self):
        """Test that short facts are rejected with exact classification."""
        facts = [
            {
                "fact": "Short",
                "concept": "test-concept",
                "quote": "short",
                "extracted_at": "2026-08-12T10:00:00Z"
            }
        ]

        self.create_extraction_artifact(self.run_id, facts)

        results, summary, artifact_path = validate_extraction.validate_extraction_artifacts(
            self.run_id,
            extracts_dir=str(self.extracts_dir),
            concepts_dir=str(self.concepts_dir),
            output_dir=str(self.validated_dir)
        )

        # MUST be classified as rejected
        self.assertEqual(summary["rejected_count"], 1, "Must be classified as rejected")
        self.assertEqual(summary["new_count"], 0, "Must not be classified as new")
        self.assertEqual(summary["duplicate_count"], 0, "Must not be classified as duplicate")
        self.assertEqual(summary["changed_count"], 0, "Must not be classified as changed")
        self.assertEqual(summary["conflict_count"], 0, "Must not be classified as conflict")

        # Verify rejected fact schema
        rejected_fact = results["rejected"][0]
        self.assertEqual(rejected_fact["classification"], "rejected")
        self.assertEqual(rejected_fact["rejection_reason"], "fact_too_short")

    def test_empty_concept_rejected(self):
        """Test that facts with empty concepts are rejected with exact classification."""
        facts = [
            {
                "fact": "This is a valid fact with sufficient length",
                "concept": "",
                "quote": "valid quote",
                "extracted_at": "2026-08-12T10:00:00Z"
            }
        ]

        self.create_extraction_artifact(self.run_id, facts)

        results, summary, artifact_path = validate_extraction.validate_extraction_artifacts(
            self.run_id,
            extracts_dir=str(self.extracts_dir),
            concepts_dir=str(self.concepts_dir),
            output_dir=str(self.validated_dir)
        )

        # MUST be classified as rejected
        self.assertEqual(summary["rejected_count"], 1, "Must be classified as rejected")
        self.assertEqual(summary["new_count"], 0, "Must not be classified as new")
        self.assertEqual(summary["duplicate_count"], 0, "Must not be classified as duplicate")
        self.assertEqual(summary["changed_count"], 0, "Must not be classified as changed")
        self.assertEqual(summary["conflict_count"], 0, "Must not be classified as conflict")

        # Verify rejected fact schema
        rejected_fact = results["rejected"][0]
        self.assertEqual(rejected_fact["classification"], "rejected")
        self.assertEqual(rejected_fact["rejection_reason"], "concept_is_empty")

    def test_empty_quote_rejected(self):
        """Test that facts with empty quotes are rejected with exact classification."""
        facts = [
            {
                "fact": "This is a valid fact with sufficient length",
                "concept": "test-concept",
                "quote": "",
                "extracted_at": "2026-08-12T10:00:00Z"
            }
        ]

        self.create_extraction_artifact(self.run_id, facts)

        results, summary, artifact_path = validate_extraction.validate_extraction_artifacts(
            self.run_id,
            extracts_dir=str(self.extracts_dir),
            concepts_dir=str(self.concepts_dir),
            output_dir=str(self.validated_dir)
        )

        # MUST be classified as rejected
        self.assertEqual(summary["rejected_count"], 1, "Must be classified as rejected")
        self.assertEqual(summary["new_count"], 0, "Must not be classified as new")
        self.assertEqual(summary["duplicate_count"], 0, "Must not be classified as duplicate")
        self.assertEqual(summary["changed_count"], 0, "Must not be classified as changed")
        self.assertEqual(summary["conflict_count"], 0, "Must not be classified as conflict")

        # Verify rejected fact schema
        rejected_fact = results["rejected"][0]
        self.assertEqual(rejected_fact["classification"], "rejected")
        self.assertEqual(rejected_fact["rejection_reason"], "quote_is_empty")

    def test_duplicate_fact_identified(self):
        """Test that duplicate facts are identified with exact classification."""
        # Create concept with existing fact - designed for exact match duplicate
        concept_file = self.concepts_dir / "test-concept.md"
        concept_content = """---
id: test-concept
title: Test Concept
---

# Test Concept

- Sponsored Products uses cost-per-click pricing model.
"""
        concept_file.write_text(concept_content)

        # Create extraction artifact with exact duplicate fact
        facts = [
            {
                "fact": "Sponsored Products uses cost-per-click pricing model",
                "concept": "test-concept",
                "quote": "cost-per-click pricing",
                "extracted_at": "2026-08-12T10:00:00Z"
            }
        ]

        self.create_extraction_artifact(self.run_id, facts)

        results, summary, artifact_path = validate_extraction.validate_extraction_artifacts(
            self.run_id,
            extracts_dir=str(self.extracts_dir),
            concepts_dir=str(self.concepts_dir),
            output_dir=str(self.validated_dir)
        )

        # MUST be classified as duplicate (exact match)
        self.assertEqual(summary["duplicate_count"], 1, "Must be classified as duplicate")
        self.assertEqual(summary["new_count"], 0, "Must not be classified as new")
        self.assertEqual(summary["changed_count"], 0, "Must not be classified as changed")
        self.assertEqual(summary["conflict_count"], 0, "Must not be classified as conflict")

        # Verify duplicate record structure
        duplicate_record = results["duplicate"][0]
        self.assertEqual(duplicate_record["classification"], "duplicate")
        self.assertIn("existing_line", duplicate_record)
        self.assertIn("fact", duplicate_record)
        self.assertIn("concept", duplicate_record)
        self.assertIn("source_id", duplicate_record)
        self.assertIn("match_type", duplicate_record)

    def test_new_fact_identified(self):
        """Test that genuinely new facts are identified with exact classification."""
        # Create concept without the fact - designed for unambiguous new classification
        concept_file = self.concepts_dir / "new-concept.md"
        concept_content = """---
id: new-concept
title: New Concept
---

# New Concept

- Existing fact about Amazon Ads targeting options.
"""
        concept_file.write_text(concept_content)

        # Create extraction artifact with clearly new fact (no overlap)
        facts = [
            {
                "fact": "Display advertising supports retargeting based on shopper behavior",
                "concept": "new-concept",
                "quote": "retargeting based on shopper behavior",
                "extracted_at": "2026-08-12T10:00:00Z"
            }
        ]

        self.create_extraction_artifact(self.run_id, facts)

        results, summary, artifact_path = validate_extraction.validate_extraction_artifacts(
            self.run_id,
            extracts_dir=str(self.extracts_dir),
            concepts_dir=str(self.concepts_dir),
            output_dir=str(self.validated_dir)
        )

        # MUST be classified as new (no overlap with existing content)
        self.assertEqual(summary["new_count"], 1, "Must be classified as new")
        self.assertEqual(summary["duplicate_count"], 0, "Must not be classified as duplicate")
        self.assertEqual(summary["changed_count"], 0, "Must not be classified as changed")
        self.assertEqual(summary["conflict_count"], 0, "Must not be classified as conflict")

        # Verify new fact record structure
        new_record = results["new"][0]
        self.assertEqual(new_record["classification"], "new")
        self.assertIn("fact", new_record)
        self.assertIn("concept", new_record)
        self.assertIn("source_id", new_record)
        self.assertIn("source_url", new_record)
        self.assertIn("source_type", new_record)
        self.assertIn("quote", new_record)
        self.assertIn("extracted_at", new_record)

    def test_multiple_sources_multiple_facts(self):
        """Test validation with multiple sources and multiple facts with exact classification."""
        # Create concept
        concept_file = self.concepts_dir / "multi-source-concept.md"
        concept_content = """---
id: multi-source-concept
title: Multi Source Concept
---

# Multi Source Concept

- Existing fact from source A about campaign optimization.
"""
        concept_file.write_text(concept_content)

        # Create extraction artifacts from multiple sources - designed for deterministic classification
        facts_source1 = [
            {
                "fact": "New fact from source 1 about dynamic bidding strategies",
                "concept": "multi-source-concept",
                "quote": "dynamic bidding strategies",
                "extracted_at": "2026-08-12T10:00:00Z"
            },
            {
                "fact": "Existing fact from source A about campaign optimization",
                "concept": "multi-source-concept",
                "quote": "campaign optimization",
                "extracted_at": "2026-08-12T10:00:00Z"
            }
        ]

        facts_source2 = [
            {
                "fact": "New fact from source 2 regarding portfolio optimization techniques",
                "concept": "multi-source-concept",
                "quote": "portfolio optimization",
                "extracted_at": "2026-08-12T10:01:00Z"
            }
        ]

        self.create_extraction_artifact(self.run_id, facts_source1, "sp-official")
        self.create_extraction_artifact(self.run_id, facts_source2, "sb-official")

        results, summary, artifact_path = validate_extraction.validate_extraction_artifacts(
            self.run_id,
            extracts_dir=str(self.extracts_dir),
            concepts_dir=str(self.concepts_dir),
            output_dir=str(self.validated_dir)
        )

        # MUST have exact counts (2 new facts from both sources, 1 duplicate)
        self.assertEqual(summary["total_facts"], 3, "Must process exactly 3 facts")
        self.assertEqual(summary["new_count"], 2, "Must classify exactly 2 facts as new")
        self.assertEqual(summary["duplicate_count"], 1, "Must classify exactly 1 fact as duplicate")
        self.assertEqual(summary["changed_count"], 0, "Must have no changed facts")
        self.assertEqual(summary["conflict_count"], 0, "Must have no conflicts")

        # Verify facts from both sources are in results
        source_ids = set()
        for category in ["new", "changed", "duplicate", "conflict"]:
            for fact_record in results[category]:
                if "source_id" in fact_record:
                    source_ids.add(fact_record["source_id"])

        # Should have both sources represented
        self.assertIn("sp-official", source_ids)
        self.assertIn("sb-official", source_ids)


class TestRunIsolationInValidation(unittest.TestCase):
    """Test that validation only processes artifacts from the specified run."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.extracts_dir = Path(self.test_dir) / "extracts"
        self.concepts_dir = Path(self.test_dir) / "concepts"
        self.validated_dir = Path(self.test_dir) / "validated"
        self.cache_dir = Path(self.test_dir) / "cache"

        for dir_path in [self.extracts_dir, self.concepts_dir, self.validated_dir, self.cache_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Create cache file
        self.cache_file = self.cache_dir / "test-source.txt"
        self.cache_file.write_text("Test content")

    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir)

    def create_extraction_artifact(self, run_id, facts, source_id="sp-official"):
        """Create a test extraction artifact."""
        # Get realistic source URL for genuine sources
        genuine_urls = {
            "sp-official": "https://advertising.amazon.com/solutions/products/sponsored-products",
            "sb-official": "https://advertising.amazon.com/solutions/products/sponsored-brands",
            "sd-official": "https://advertising.amazon.com/solutions/products/sponsored-display",
            "targeting-official": "https://advertising.amazon.com/library/guides/targeting-with-sponsored-products",
            "ppc-community": "https://www.junglescout.com/resources/articles/amazon-ppc/",
            "ads-api-notes": "https://advertising.amazon.com/API/docs/en-us/release-notes/index"
        }
        source_url = genuine_urls.get(source_id, f"https://example.com/{source_id}")

        artifact = {
            "version": "1.0",
            "run_id": run_id,
            "extracted_at": "2026-08-12T10:00:00Z",
            "source_id": source_id,
            "source_type": "official",
            "source_url": source_url,
            "cache_file": str(self.cache_file),
            "content_hash": "abc123",
            "facts": facts,
            "extraction_metadata": {}
        }

        run_dir = self.extracts_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        artifact_file = run_dir / f"{source_id}-20260812100000.json"
        with open(artifact_file, 'w') as f:
            json.dump(artifact, f)

        return str(artifact_file)

    def test_validation_only_processes_current_run_artifacts(self):
        """Test that validation only processes artifacts from the specified run."""
        run_a_id = "20260812-100000-run-a"
        run_b_id = "20260812-100001-run-b"

        # Create artifacts for both runs
        facts_a = [{"fact": "Fact from run A", "concept": "concept-a", "quote": "Quote A", "extracted_at": "2026-08-12T10:00:00Z"}]
        facts_b = [{"fact": "Fact from run B", "concept": "concept-b", "quote": "Quote B", "extracted_at": "2026-08-12T10:00:00Z"}]

        self.create_extraction_artifact(run_a_id, facts_a)
        self.create_extraction_artifact(run_b_id, facts_b)

        # Validate only Run A
        results_a, summary_a, artifact_path_a = validate_extraction.validate_extraction_artifacts(
            run_a_id,
            extracts_dir=str(self.extracts_dir),
            concepts_dir=str(self.concepts_dir),
            output_dir=str(self.validated_dir)
        )

        # Should only process Run A facts
        self.assertEqual(summary_a["total_facts"], 1)
        self.assertEqual(results_a["new"][0]["fact"], "Fact from run A")

        # Verify validation artifact is in Run A directory
        self.assertIn(run_a_id, artifact_path_a)


class TestOutputSchema(unittest.TestCase):
    """Test that validation output has correct schema for all classifications."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.extracts_dir = Path(self.test_dir) / "extracts"
        self.concepts_dir = Path(self.test_dir) / "concepts"
        self.validated_dir = Path(self.test_dir) / "validated"
        self.cache_dir = Path(self.test_dir) / "cache"

        for dir_path in [self.extracts_dir, self.concepts_dir, self.validated_dir, self.cache_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Create cache file
        self.cache_file = self.cache_dir / "test-source.txt"
        self.cache_file.write_text("Test content")

        self.run_id = "20260812-schema-test"

    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir)

    def create_extraction_artifact(self, run_id, facts, source_id="sp-official"):
        """Create a test extraction artifact."""
        # Get realistic source URL for genuine sources
        genuine_urls = {
            "sp-official": "https://advertising.amazon.com/solutions/products/sponsored-products",
            "sb-official": "https://advertising.amazon.com/solutions/products/sponsored-brands",
            "sd-official": "https://advertising.amazon.com/solutions/products/sponsored-display",
            "targeting-official": "https://advertising.amazon.com/library/guides/targeting-with-sponsored-products",
            "ppc-community": "https://www.junglescout.com/resources/articles/amazon-ppc/",
            "ads-api-notes": "https://advertising.amazon.com/API/docs/en-us/release-notes/index"
        }
        source_url = genuine_urls.get(source_id, f"https://example.com/{source_id}")

        artifact = {
            "version": "1.0",
            "run_id": run_id,
            "extracted_at": "2026-08-12T10:00:00Z",
            "source_id": source_id,
            "source_type": "official",
            "source_url": source_url,
            "cache_file": str(self.cache_file),
            "content_hash": "abc123",
            "facts": facts,
            "extraction_metadata": {}
        }

        run_dir = self.extracts_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        artifact_file = run_dir / f"{source_id}-20260812100000.json"
        with open(artifact_file, 'w') as f:
            json.dump(artifact, f)

        return str(artifact_file)

    def test_new_fact_schema(self):
        """Test that new facts have correct output schema."""
        facts = [
            {
                "fact": "A completely new fact for testing schema",
                "concept": "schema-test-concept",
                "quote": "new fact quote",
                "extracted_at": "2026-08-12T10:00:00Z"
            }
        ]

        self.create_extraction_artifact(self.run_id, facts)

        results, summary, artifact_path = validate_extraction.validate_extraction_artifacts(
            self.run_id,
            extracts_dir=str(self.extracts_dir),
            concepts_dir=str(self.concepts_dir),
            output_dir=str(self.validated_dir)
        )

        # Verify new fact schema
        new_fact = results["new"][0]
        self.assertIn("fact", new_fact)
        self.assertIn("concept", new_fact)
        self.assertIn("source_id", new_fact)
        self.assertIn("source_url", new_fact)
        self.assertIn("source_type", new_fact)
        self.assertIn("quote", new_fact)
        self.assertIn("extracted_at", new_fact)
        self.assertIn("classification", new_fact)
        self.assertEqual(new_fact["classification"], "new")

    def test_duplicate_fact_schema(self):
        """Test that duplicate facts have correct output schema with exact classification."""
        # Create concept with existing fact
        concept_file = self.concepts_dir / "duplicate-test.md"
        concept_content = """---
id: duplicate-test
title: Duplicate Test
---

# Duplicate Test

- Existing fact for duplicate testing.
"""
        concept_file.write_text(concept_content)

        facts = [
            {
                "fact": "Existing fact for duplicate testing",
                "concept": "duplicate-test",
                "quote": "existing",
                "extracted_at": "2026-08-12T10:00:00Z"
            }
        ]

        self.create_extraction_artifact(self.run_id, facts)

        results, summary, artifact_path = validate_extraction.validate_extraction_artifacts(
            self.run_id,
            extracts_dir=str(self.extracts_dir),
            concepts_dir=str(self.concepts_dir),
            output_dir=str(self.validated_dir)
        )

        # MUST be classified as duplicate (exact match)
        self.assertEqual(summary["duplicate_count"], 1, "Must be classified as duplicate")
        self.assertEqual(summary["new_count"], 0, "Must not be classified as new")
        self.assertEqual(summary["changed_count"], 0, "Must not be classified as changed")
        self.assertEqual(summary["conflict_count"], 0, "Must not be classified as conflict")

        # Verify duplicate fact schema
        duplicate_fact = results["duplicate"][0]
        self.assertIn("fact", duplicate_fact)
        self.assertIn("concept", duplicate_fact)
        self.assertIn("source_id", duplicate_fact)
        self.assertIn("classification", duplicate_fact)
        self.assertEqual(duplicate_fact["classification"], "duplicate")
        self.assertIn("existing_line", duplicate_fact)
        self.assertIn("match_type", duplicate_fact)

    def test_changed_fact_schema(self):
        """Test that changed facts have correct output schema with exact classification."""
        # Create concept with existing fact - designed for unambiguous changed classification
        concept_file = self.concepts_dir / "changed-test.md"
        concept_content = """---
id: changed-test
title: Changed Test
---

# Changed Test

- Amazon charges a minimum bid of $0.02 for Sponsored Products clicks.
"""
        concept_file.write_text(concept_content)

        # Create extraction artifact with changed value (same structure, different value)
        facts = [
            {
                "fact": "Amazon now charges a minimum bid of $0.05 for clicks",
                "concept": "changed-test",
                "quote": "minimum bid of $0.05",
                "extracted_at": "2026-08-12T10:00:00Z"
            }
        ]

        self.create_extraction_artifact(self.run_id, facts)

        results, summary, artifact_path = validate_extraction.validate_extraction_artifacts(
            self.run_id,
            extracts_dir=str(self.extracts_dir),
            concepts_dir=str(self.concepts_dir),
            output_dir=str(self.validated_dir)
        )

        # MUST be classified as changed (similar but different values)
        self.assertEqual(summary["changed_count"], 1, "Must be classified as changed")
        self.assertEqual(summary["new_count"], 0, "Must not be classified as new")
        self.assertEqual(summary["duplicate_count"], 0, "Must not be classified as duplicate")
        self.assertEqual(summary["conflict_count"], 0, "Must not be classified as conflict")

        # Verify changed fact schema
        changed_fact = results["changed"][0]
        self.assertIn("fact", changed_fact)
        self.assertIn("concept", changed_fact)
        self.assertIn("source_id", changed_fact)
        self.assertIn("classification", changed_fact)
        self.assertEqual(changed_fact["classification"], "changed")
        self.assertIn("existing_line", changed_fact)
        self.assertIn("overlap_ratio", changed_fact)

    def test_conflict_fact_schema(self):
        """Test that conflict facts have correct output schema with exact classification."""
        # Create concept with conflict - designed for unambiguous conflict detection
        concept_file = self.concepts_dir / "conflict-schema-test.md"
        concept_content = """---
id: conflict-schema-test
title: Conflict Schema Test
---

# Conflict Schema Test

- Official documentation states the bid adjustment is capped at 100%, however community reports suggest 50% in some cases.
"""
        concept_file.write_text(concept_content)

        facts = [
            {
                "fact": "Community reports suggest the bid adjustment is 50% in some cases",
                "concept": "conflict-schema-test",
                "quote": "bid adjustment is 50%",
                "extracted_at": "2026-08-12T10:00:00Z"
            }
        ]

        self.create_extraction_artifact(self.run_id, facts)

        results, summary, artifact_path = validate_extraction.validate_extraction_artifacts(
            self.run_id,
            extracts_dir=str(self.extracts_dir),
            concepts_dir=str(self.concepts_dir),
            output_dir=str(self.validated_dir)
        )

        # MUST be classified as conflict (overlap with conflicting line)
        self.assertEqual(summary["conflict_count"], 1, "Must be classified as conflict")
        self.assertEqual(summary["new_count"], 0, "Must not be classified as new")
        self.assertEqual(summary["duplicate_count"], 0, "Must not be classified as duplicate")
        self.assertEqual(summary["changed_count"], 0, "Must not be classified as changed")

        # Verify conflict fact schema
        conflict_fact = results["conflict"][0]
        self.assertIn("fact", conflict_fact)
        self.assertIn("concept", conflict_fact)
        self.assertIn("source_id", conflict_fact)
        self.assertIn("source_url", conflict_fact)
        self.assertIn("source_type", conflict_fact)
        self.assertIn("quote", conflict_fact)
        self.assertIn("classification", conflict_fact)
        self.assertEqual(conflict_fact["classification"], "conflict")
        self.assertIn("conflicting_line", conflict_fact)
        self.assertIn("overlap_ratio", conflict_fact)

    def test_rejected_fact_schema(self):
        """Test that rejected facts have correct output schema with exact classification."""
        facts = [
            {
                "fact": "Short",
                "concept": "rejected-test",
                "quote": "short",
                "extracted_at": "2026-08-12T10:00:00Z"
            }
        ]

        self.create_extraction_artifact(self.run_id, facts)

        results, summary, artifact_path = validate_extraction.validate_extraction_artifacts(
            self.run_id,
            extracts_dir=str(self.extracts_dir),
            concepts_dir=str(self.concepts_dir),
            output_dir=str(self.validated_dir)
        )

        # MUST be classified as rejected
        self.assertEqual(summary["rejected_count"], 1, "Must be classified as rejected")
        self.assertEqual(summary["new_count"], 0, "Must not be classified as new")
        self.assertEqual(summary["duplicate_count"], 0, "Must not be classified as duplicate")
        self.assertEqual(summary["changed_count"], 0, "Must not be classified as changed")
        self.assertEqual(summary["conflict_count"], 0, "Must not be classified as conflict")

        # Verify rejected fact schema
        rejected_fact = results["rejected"][0]
        self.assertIn("fact", rejected_fact)
        self.assertIn("concept", rejected_fact)
        self.assertIn("source_id", rejected_fact)
        self.assertIn("classification", rejected_fact)
        self.assertEqual(rejected_fact["classification"], "rejected")
        self.assertIn("rejection_reason", rejected_fact)


class TestChangedFactClassification(unittest.TestCase):
    """Test the changed fact classification path."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.extracts_dir = Path(self.test_dir) / "extracts"
        self.concepts_dir = Path(self.test_dir) / "concepts"
        self.validated_dir = Path(self.test_dir) / "validated"
        self.cache_dir = Path(self.test_dir) / "cache"

        for dir_path in [self.extracts_dir, self.concepts_dir, self.validated_dir, self.cache_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Create cache file
        self.cache_file = self.cache_dir / "test-source.txt"
        self.cache_file.write_text("Test content")

        self.run_id = "20260812-changed-test"

    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir)

    def create_extraction_artifact(self, run_id, facts, source_id="sp-official"):
        """Create a test extraction artifact."""
        # Get realistic source URL for genuine sources
        genuine_urls = {
            "sp-official": "https://advertising.amazon.com/solutions/products/sponsored-products",
            "sb-official": "https://advertising.amazon.com/solutions/products/sponsored-brands",
            "sd-official": "https://advertising.amazon.com/solutions/products/sponsored-display",
            "targeting-official": "https://advertising.amazon.com/library/guides/targeting-with-sponsored-products",
            "ppc-community": "https://www.junglescout.com/resources/articles/amazon-ppc/",
            "ads-api-notes": "https://advertising.amazon.com/API/docs/en-us/release-notes/index"
        }
        source_url = genuine_urls.get(source_id, f"https://example.com/{source_id}")

        artifact = {
            "version": "1.0",
            "run_id": run_id,
            "extracted_at": "2026-08-12T10:00:00Z",
            "source_id": source_id,
            "source_type": "official",
            "source_url": source_url,
            "cache_file": str(self.cache_file),
            "content_hash": "abc123",
            "facts": facts,
            "extraction_metadata": {}
        }

        run_dir = self.extracts_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        artifact_file = run_dir / f"{source_id}-20260812100000.json"
        with open(artifact_file, 'w') as f:
            json.dump(artifact, f)

        return str(artifact_file)

    def test_changed_fact_identified(self):
        """Test that changed facts (similar but different values) are identified with exact classification."""
        # Create concept with existing value
        concept_file = self.concepts_dir / "changed-concept.md"
        concept_content = """---
id: changed-concept
title: Changed Concept
---

# Changed Concept

- The minimum bid amount is set to $0.02 for most campaigns.
"""
        concept_file.write_text(concept_content)

        # Create extraction artifact with changed value (similar but different)
        facts = [
            {
                "fact": "The minimum bid amount is now $0.05 for most campaigns according to updates",
                "concept": "changed-concept",
                "quote": "minimum bid is now $0.05",
                "extracted_at": "2026-08-12T10:00:00Z"
            }
        ]

        self.create_extraction_artifact(self.run_id, facts)

        results, summary, artifact_path = validate_extraction.validate_extraction_artifacts(
            self.run_id,
            extracts_dir=str(self.extracts_dir),
            concepts_dir=str(self.concepts_dir),
            output_dir=str(self.validated_dir)
        )

        # MUST be classified as changed (similar but different values)
        self.assertEqual(summary["changed_count"], 1, "Must be classified as changed")
        self.assertEqual(summary["new_count"], 0, "Must not be classified as new")
        self.assertEqual(summary["duplicate_count"], 0, "Must not be classified as duplicate")
        self.assertEqual(summary["conflict_count"], 0, "Must not be classified as conflict")

        # Verify changed record structure
        changed_record = results["changed"][0]
        self.assertEqual(changed_record["classification"], "changed")
        self.assertIn("existing_line", changed_record)
        self.assertIn("fact", changed_record)
        self.assertIn("concept", changed_record)
        self.assertIn("source_id", changed_record)
        self.assertIn("overlap_ratio", changed_record)


class TestValidationDeterminism(unittest.TestCase):
    """Test that validation is deterministic."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.extracts_dir = Path(self.test_dir) / "extracts"
        self.concepts_dir = Path(self.test_dir) / "concepts"
        self.validated_dir = Path(self.test_dir) / "validated"
        self.cache_dir = Path(self.test_dir) / "cache"

        for dir_path in [self.extracts_dir, self.concepts_dir, self.validated_dir, self.cache_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Create cache file
        self.cache_file = self.cache_dir / "test-source.txt"
        self.cache_file.write_text("Test content")

        self.run_id = "20260812-determinism-test"

    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir)

    def create_extraction_artifact(self, run_id, facts, source_id="sp-official"):
        """Create a test extraction artifact."""
        # Get realistic source URL for genuine sources
        genuine_urls = {
            "sp-official": "https://advertising.amazon.com/solutions/products/sponsored-products",
            "sb-official": "https://advertising.amazon.com/solutions/products/sponsored-brands",
            "sd-official": "https://advertising.amazon.com/solutions/products/sponsored-display",
            "targeting-official": "https://advertising.amazon.com/library/guides/targeting-with-sponsored-products",
            "ppc-community": "https://www.junglescout.com/resources/articles/amazon-ppc/",
            "ads-api-notes": "https://advertising.amazon.com/API/docs/en-us/release-notes/index"
        }
        source_url = genuine_urls.get(source_id, f"https://example.com/{source_id}")

        artifact = {
            "version": "1.0",
            "run_id": run_id,
            "extracted_at": "2026-08-12T10:00:00Z",
            "source_id": source_id,
            "source_type": "official",
            "source_url": source_url,
            "cache_file": str(self.cache_file),
            "content_hash": "abc123",
            "facts": facts,
            "extraction_metadata": {}
        }

        run_dir = self.extracts_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        artifact_file = run_dir / f"{source_id}-20260812100000.json"
        with open(artifact_file, 'w') as f:
            json.dump(artifact, f)

        return str(artifact_file)

    def test_validation_is_deterministic(self):
        """Test that validation produces the same results for the same input."""
        facts = [
            {
                "fact": "A test fact for determinism checking about campaign optimization",
                "concept": "determinism-test",
                "quote": "campaign optimization",
                "extracted_at": "2026-08-12T10:00:00Z"
            }
        ]

        self.create_extraction_artifact(self.run_id, facts)

        # Run validation twice
        results1, summary1, artifact_path1 = validate_extraction.validate_extraction_artifacts(
            self.run_id,
            extracts_dir=str(self.extracts_dir),
            concepts_dir=str(self.concepts_dir),
            output_dir=str(self.validated_dir)
        )

        results2, summary2, artifact_path2 = validate_extraction.validate_extraction_artifacts(
            self.run_id,
            extracts_dir=str(self.extracts_dir),
            concepts_dir=str(self.concepts_dir),
            output_dir=str(self.validated_dir)
        )

        # Results should be identical - exact classification
        self.assertEqual(summary1["total_facts"], 1, "First run must process 1 fact")
        self.assertEqual(summary2["total_facts"], 1, "Second run must process 1 fact")
        self.assertEqual(summary1["new_count"], 1, "First run must classify 1 fact as new")
        self.assertEqual(summary2["new_count"], 1, "Second run must classify 1 fact as new")
        self.assertEqual(summary1, summary2, "Summaries must be identical")

        # Fact content must be identical
        self.assertEqual(len(results1["new"]), len(results2["new"]), "New fact counts must match")
        self.assertEqual(results1["new"][0]["fact"], results2["new"][0]["fact"], "Fact content must be identical")


if __name__ == "__main__":
    unittest.main()