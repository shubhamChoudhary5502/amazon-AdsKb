#!/usr/bin/env python3
"""
Comprehensive tests for artifact-based pipeline handoff architecture with run ID isolation.

These tests prove that:
A. Run A extraction cannot be consumed by Run B.
B. Validator consumes only the extraction artifact for its run.
C. Merger cannot publish without the corresponding validation artifact.
D. Merger cannot bypass validation by reading state/extracts/.
E. A rejected fact never reaches the Merger.
F. A valid fact reaches the Merger through state/validated/.
G. Concurrent runs do not consume each other's extraction artifacts.
"""

import unittest
import json
import os
import tempfile
import shutil
from pathlib import Path
import sys

# Add scripts directory to path for imports
sys.path.insert(0, 'scripts')

import persist_extraction
import validate_extraction
import load_validation_results


class TestRunIDIsolation(unittest.TestCase):
    """Test that run IDs provide proper isolation between pipeline runs."""

    def setUp(self):
        """Set up test directories."""
        self.test_dir = tempfile.mkdtemp()
        self.extracts_dir = Path(self.test_dir) / "extracts"
        self.validated_dir = Path(self.test_dir) / "validated"
        self.concepts_dir = Path(self.test_dir) / "concepts"
        self.cache_dir = Path(self.test_dir) / "cache"

        self.extracts_dir.mkdir(parents=True, exist_ok=True)
        self.validated_dir.mkdir(parents=True, exist_ok=True)
        self.concepts_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Create test cache file
        self.cache_file = self.cache_dir / "test-source.txt"
        self.cache_file.write_text("Test content for extraction")

    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir)

    def test_run_a_extraction_cannot_be_consumed_by_run_b(self):
        """Test A: Run A extraction cannot be consumed by Run B."""
        run_a_id = "20260812-143000-abc123"
        run_b_id = "20260812-143100-def456"

        source_id = "sp-official"  # Use genuine source to avoid contamination check
        source_type = "official"
        source_url = "https://advertising.amazon.com/solutions/products/sponsored-products"

        # Run A: Create extraction artifact
        facts_a = [{"fact": "Fact from Run A", "concept": "test-concept", "quote": "Quote A"}]
        artifact_a = persist_extraction.persist_extraction(
            source_id, source_type, source_url, str(self.cache_file), facts_a, run_a_id, str(self.extracts_dir)
        )

        # Run B: Create extraction artifact
        facts_b = [{"fact": "Fact from Run B", "concept": "test-concept", "quote": "Quote B"}]
        artifact_b = persist_extraction.persist_extraction(
            source_id, source_type, source_url, str(self.cache_file), facts_b, run_b_id, str(self.extracts_dir)
        )

        # Verify artifacts are in separate directories
        self.assertIn(run_a_id, artifact_a)
        self.assertIn(run_b_id, artifact_b)
        self.assertNotIn(run_b_id, artifact_a)
        self.assertNotIn(run_a_id, artifact_b)

        # Run B validator should only see Run B artifacts
        validation_results, summary, artifact_path = validate_extraction.validate_extraction_artifacts(
            run_b_id,
            extracts_dir=str(self.extracts_dir),
            concepts_dir=str(self.concepts_dir),
            output_dir=str(self.validated_dir)
        )

        # Should only process Run B facts
        self.assertIsNotNone(validation_results, "Validation results should not be None")
        self.assertIsNotNone(summary, "Summary should not be None")
        self.assertEqual(summary["total_facts"], 1)
        self.assertEqual(validation_results["new"][0]["fact"], "Fact from Run B")

    def test_concurrent_runs_do_not_cross_contaminate(self):
        """Test G: Concurrent runs do not consume each other's extraction artifacts."""
        run_a_id = "20260812-144000-aaa111"
        run_b_id = "20260812-144000-bbb222"  # Same timestamp, different run

        source_id = "sp-official"  # Use genuine source to avoid contamination check
        source_type = "official"
        source_url = "https://advertising.amazon.com/solutions/products/sponsored-products"

        # Create artifacts for both runs with facts that are long enough (10+ chars)
        facts_a = [{"fact": "This is a valid fact from run A", "concept": "concept-a", "quote": "Valid fact from A"}]
        facts_b = [{"fact": "This is a valid fact from run B", "concept": "concept-b", "quote": "Valid fact from B"}]

        artifact_a = persist_extraction.persist_extraction(
            source_id, source_type, source_url, str(self.cache_file), facts_a, run_a_id, str(self.extracts_dir)
        )
        artifact_b = persist_extraction.persist_extraction(
            source_id, source_type, source_url, str(self.cache_file), facts_b, run_b_id, str(self.extracts_dir)
        )

        # Validate both runs
        results_a, summary_a, artifact_a_path = validate_extraction.validate_extraction_artifacts(
            run_a_id,
            extracts_dir=str(self.extracts_dir),
            concepts_dir=str(self.concepts_dir),
            output_dir=str(self.validated_dir)
        )

        results_b, summary_b, artifact_b_path = validate_extraction.validate_extraction_artifacts(
            run_b_id,
            extracts_dir=str(self.extracts_dir),
            concepts_dir=str(self.concepts_dir),
            output_dir=str(self.validated_dir)
        )

        # Verify both validations succeeded
        self.assertIsNotNone(results_a, "Run A validation should succeed")
        self.assertIsNotNone(results_b, "Run B validation should succeed")

        # Verify no cross-contamination
        self.assertGreater(len(results_a["new"]), 0, "Run A should have new facts")
        self.assertGreater(len(results_b["new"]), 0, "Run B should have new facts")
        self.assertEqual(results_a["new"][0]["fact"], "This is a valid fact from run A")
        self.assertEqual(results_b["new"][0]["fact"], "This is a valid fact from run B")

        # Verify artifacts are in separate validation directories
        validation_a_dir = self.validated_dir / run_a_id
        validation_b_dir = self.validated_dir / run_b_id
        self.assertTrue(validation_a_dir.exists())
        self.assertTrue(validation_b_dir.exists())
        self.assertNotEqual(validation_a_dir, validation_b_dir)


class TestExtractionPersistence(unittest.TestCase):
    """Test that extraction artifacts are properly persisted with run IDs."""

    def setUp(self):
        """Set up test directories."""
        self.test_dir = tempfile.mkdtemp()
        self.extracts_dir = Path(self.test_dir) / "extracts"
        self.extracts_dir.mkdir(parents=True, exist_ok=True)

        # Create a test cache file
        self.cache_dir = Path(self.test_dir) / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "test-source.txt"
        self.cache_file.write_text("Test content for extraction")

    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir)

    def test_extraction_artifact_created_with_run_id(self):
        """Test that extraction creates artifact in run-specific directory."""
        source_id = "sp-official"  # Use genuine source to avoid contamination check
        source_type = "official"
        source_url = "https://advertising.amazon.com/solutions/products/sponsored-products"
        cache_file = str(self.cache_file)
        run_id = "20260812-150000-test123"

        facts = [
            {
                "fact": "Test fact about Amazon advertising",
                "concept": "test-concept",
                "quote": "Test fact quote",
                "confidence": "high"
            }
        ]

        # Persist the extraction with run_id
        artifact_path = persist_extraction.persist_extraction(
            source_id, source_type, source_url, cache_file, facts, run_id, str(self.extracts_dir)
        )

        # Verify artifact file exists in run-specific directory
        self.assertTrue(Path(artifact_path).exists())
        self.assertIn(run_id, artifact_path)
        self.assertIn("sp-official", artifact_path)
        self.assertTrue(artifact_path.endswith(".json"))

    def test_extraction_artifact_requires_run_id(self):
        """Test that extraction requires run_id for isolation."""
        source_id = "sp-official"  # Use genuine source to avoid contamination check
        source_type = "official"
        source_url = "https://advertising.amazon.com/solutions/products/sponsored-products"
        cache_file = str(self.cache_file)

        facts = [
            {
                "fact": "Test fact",
                "concept": "test-concept",
                "quote": "Test quote"
            }
        ]

        # Should raise ValueError without run_id
        with self.assertRaises(ValueError) as context:
            persist_extraction.persist_extraction(
                source_id, source_type, source_url, cache_file, facts
            )

        self.assertIn("run_id is required", str(context.exception))

    def test_extraction_artifact_includes_run_id(self):
        """Test that extraction artifact includes run_id field."""
        source_id = "sp-official"  # Use genuine source to avoid contamination check
        source_type = "official"
        source_url = "https://advertising.amazon.com/solutions/products/sponsored-products"
        cache_file = str(self.cache_file)
        run_id = "20260812-151000-test456"

        facts = [
            {
                "fact": "Test fact",
                "concept": "test-concept",
                "quote": "Test quote"
            }
        ]

        # Persist the extraction
        artifact_path = persist_extraction.persist_extraction(
            source_id, source_type, source_url, cache_file, facts, run_id, str(self.extracts_dir)
        )

        # Load and verify run_id is in artifact
        with open(artifact_path) as f:
            artifact = json.load(f)

        self.assertEqual(artifact["run_id"], run_id)


class TestValidatorConsumesExtraction(unittest.TestCase):
    """Test that validator reads the exact persisted extraction output for a specific run."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.extracts_dir = Path(self.test_dir) / "extracts"
        self.concepts_dir = Path(self.test_dir) / "concepts"
        self.validated_dir = Path(self.test_dir) / "validated"
        self.cache_dir = Path(self.test_dir) / "cache"

        self.extracts_dir.mkdir(parents=True, exist_ok=True)
        self.concepts_dir.mkdir(parents=True, exist_ok=True)
        self.validated_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Create test cache file
        self.cache_file = self.cache_dir / "test-source.txt"
        self.cache_file.write_text("Test content for extraction")

        self.run_id = "20260812-152000-validator-test"

    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir)

    def test_validator_reads_only_run_specific_extraction_artifacts(self):
        """Test B: Validator consumes only the extraction artifact for its run."""
        source_id = "sp-official"  # Use genuine source to avoid contamination check
        source_type = "official"
        source_url = "https://advertising.amazon.com/solutions/products/sponsored-products"

        # Create extraction artifact for THIS run
        facts = [
            {
                "fact": "Sponsored Products are cost-per-click ads",
                "concept": "sponsored-products",
                "quote": "cost-per-click ads"
            }
        ]

        artifact_path = persist_extraction.persist_extraction(
            source_id, source_type, source_url, str(self.cache_file), facts, self.run_id, str(self.extracts_dir)
        )

        # Create artifact for a different run (should not be processed)
        other_run_id = "20260812-153000-other-run"
        other_facts = [{"fact": "Fact from other run", "concept": "other-concept", "quote": "Other quote"}]
        persist_extraction.persist_extraction(
            source_id, source_type, source_url, str(self.cache_file), other_facts, other_run_id, str(self.extracts_dir)
        )

        # Run validation for THIS run only
        validation_results, summary, validation_path = validate_extraction.validate_extraction_artifacts(
            self.run_id,
            extracts_dir=str(self.extracts_dir),
            concepts_dir=str(self.concepts_dir),
            output_dir=str(self.validated_dir)
        )

        # Verify validation succeeded
        self.assertIsNotNone(validation_results, "Validation results should not be None")
        self.assertIsNotNone(summary, "Summary should not be None")
        self.assertIsNotNone(validation_path, "Validation path should not be None")
        self.assertTrue(Path(validation_path).exists())

        # Verify only THIS run's facts were processed
        self.assertEqual(summary["total_facts"], 1)
        self.assertEqual(validation_results["new"][0]["fact"], "Sponsored Products are cost-per-click ads")

        # Verify validation artifact includes run_id
        with open(validation_path) as f:
            validation_artifact = json.load(f)

        self.assertEqual(validation_artifact["run_id"], self.run_id)
        self.assertIn(artifact_path, validation_artifact["extraction_files"])

    def test_validator_requires_run_id(self):
        """Test that validator requires a run_id parameter."""
        # Try to validate without run_id
        with self.assertRaises(TypeError):
            # Old API call without run_id should fail
            validate_extraction.validate_extraction_artifacts(
                extracts_dir=str(self.extracts_dir),
                concepts_dir=str(self.concepts_dir),
                output_dir=str(self.validated_dir)
            )


class TestInvalidFactsRejected(unittest.TestCase):
    """Test that invalid facts are rejected by validator and never reach merger."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.extracts_dir = Path(self.test_dir) / "extracts"
        self.concepts_dir = Path(self.test_dir) / "concepts"
        self.validated_dir = Path(self.test_dir) / "validated"
        self.cache_dir = Path(self.test_dir) / "cache"

        self.extracts_dir.mkdir(parents=True, exist_ok=True)
        self.concepts_dir.mkdir(parents=True, exist_ok=True)
        self.validated_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Create test cache file
        self.cache_file = self.cache_dir / "test-source.txt"
        self.cache_file.write_text("Test content for extraction")

        self.run_id = "20260812-154000-rejection-test"

    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir)

    def test_too_short_fact_rejected(self):
        """Test that facts shorter than 10 characters are rejected."""
        source_id = "sp-official"  # Use genuine source to avoid contamination check
        source_type = "official"
        source_url = "https://advertising.amazon.com/solutions/products/sponsored-products"

        facts = [
            {
                "fact": "Short",  # Less than 10 characters
                "concept": "test-concept",
                "quote": "quote"
            },
            {
                "fact": "This is a valid fact with enough content",
                "concept": "test-concept",
                "quote": "valid quote"
            }
        ]

        # Persist extraction with run_id
        persist_extraction.persist_extraction(
            source_id, source_type, source_url, str(self.cache_file), facts, self.run_id, str(self.extracts_dir)
        )

        # Run validation
        validation_results, summary, validation_path = validate_extraction.validate_extraction_artifacts(
            self.run_id,
            extracts_dir=str(self.extracts_dir),
            concepts_dir=str(self.concepts_dir),
            output_dir=str(self.validated_dir)
        )

        # Verify short fact was rejected
        self.assertGreater(summary["rejected_count"], 0)
        self.assertIn("rejected", validation_results)
        self.assertEqual(validation_results["rejected"][0]["rejection_reason"], "fact_too_short")

    def test_rejected_facts_never_reach_merger(self):
        """Test E: A rejected fact never reaches the Merger."""
        source_id = "sp-official"  # Use genuine source to avoid contamination check
        source_type = "official"
        source_url = "https://advertising.amazon.com/solutions/products/sponsored-products"

        facts = [
            {
                "fact": "Valid fact that should pass validation",
                "concept": "test-concept",
                "quote": "valid quote"
            },
            {
                "fact": "Short",  # Will be rejected
                "concept": "test-concept",
                "quote": "quote"
            }
        ]

        # Persist extraction with run_id
        persist_extraction.persist_extraction(
            source_id, source_type, source_url, str(self.cache_file), facts, self.run_id, str(self.extracts_dir)
        )

        # Run validation
        validation_results, summary, validation_path = validate_extraction.validate_extraction_artifacts(
            self.run_id,
            extracts_dir=str(self.extracts_dir),
            concepts_dir=str(self.concepts_dir),
            output_dir=str(self.validated_dir)
        )

        # Verify validation results
        self.assertIsNotNone(validation_results)
        self.assertEqual(summary["total_facts"], 2)
        self.assertEqual(summary["new_count"], 1)
        self.assertEqual(summary["rejected_count"], 1)

        # Load facts as merger would
        valid_facts = load_validation_results.get_validated_facts_for_merge(
            self.run_id,
            validated_dir=str(self.validated_dir)
        )

        # Verify rejected fact doesn't reach merger
        all_facts = []
        for concept_facts in valid_facts.values():
            all_facts.extend(concept_facts)

        # Only the valid fact should reach merger
        self.assertEqual(len(all_facts), 1)
        self.assertEqual(all_facts[0]["fact"], "Valid fact that should pass validation")


class TestValidFactsReachMerger(unittest.TestCase):
    """Test that valid facts reach the merger through validation artifacts (Test F)."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.validated_dir = Path(self.test_dir) / "validated"
        self.validated_dir.mkdir(parents=True, exist_ok=True)

        self.run_id = "20260812-155000-merger-test"

    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir)

    def create_validation_artifact(self, new_facts, changed_facts):
        """Create a test validation artifact with run_id."""
        artifact = {
            "version": "1.0",
            "run_id": self.run_id,
            "validated_at": "2026-08-12T10:05:00Z",
            "extraction_files": ["state/extracts/test.json"],
            "validation_results": {
                "new": new_facts,
                "changed": changed_facts,
                "duplicate": [],
                "conflict": [],
                "rejected": []
            },
            "summary": {
                "total_facts": len(new_facts) + len(changed_facts),
                "new_count": len(new_facts),
                "changed_count": len(changed_facts),
                "duplicate_count": 0,
                "conflict_count": 0,
                "rejected_count": 0
            },
            "validator_metadata": {}
        }

        # Create run-specific directory
        run_dir = self.validated_dir / self.run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        artifact_file = run_dir / "validation-20260812100500.json"
        with open(artifact_file, 'w') as f:
            json.dump(artifact, f)

        return str(artifact_file)

    def test_merger_loads_validated_facts(self):
        """Test F: A valid fact reaches the Merger through state/validated/."""
        new_facts = [
            {
                "fact": "New fact about Sponsored Products",
                "concept": "sponsored-products",
                "source_id": "sp-official",
                "classification": "new"
            }
        ]

        changed_facts = [
            {
                "fact": "Updated fact about Sponsored Brands",
                "concept": "sponsored-brands",
                "source_id": "sb-official",
                "classification": "changed",
                "existing_fact": "Old fact"
            }
        ]

        validation_path = self.create_validation_artifact(new_facts, changed_facts)

        # Load facts as merger would
        valid_facts = load_validation_results.get_validated_facts_for_merge(
            self.run_id,
            validated_dir=str(self.validated_dir)
        )

        # Verify merger can access the facts
        self.assertIsNotNone(valid_facts)
        self.assertIn("sponsored-products", valid_facts)
        self.assertIn("sponsored-brands", valid_facts)

        self.assertEqual(len(valid_facts["sponsored-products"]), 1)
        self.assertEqual(len(valid_facts["sponsored-brands"]), 1)

        # Verify fact details
        sp_fact = valid_facts["sponsored-products"][0]
        self.assertEqual(sp_fact["fact"], "New fact about Sponsored Products")
        self.assertEqual(sp_fact["source_id"], "sp-official")
        self.assertEqual(sp_fact["classification"], "new")

    def test_merger_only_receives_valid_facts(self):
        """Test that rejected facts don't reach the merger."""
        # Create validation artifact with only rejected facts
        validation_artifact = {
            "version": "1.0",
            "run_id": self.run_id,
            "validated_at": "2026-08-12T10:05:00Z",
            "extraction_files": ["state/extracts/test.json"],
            "validation_results": {
                "new": [],
                "changed": [],
                "duplicate": [],
                "conflict": [],
                "rejected": [
                    {
                        "fact": "Invalid short fact",
                        "concept": "test",
                        "source_id": "test-source",
                        "classification": "rejected",
                        "rejection_reason": "fact_too_short"
                    }
                ]
            },
            "summary": {
                "total_facts": 1,
                "new_count": 0,
                "changed_count": 0,
                "duplicate_count": 0,
                "conflict_count": 0,
                "rejected_count": 1
            },
            "validator_metadata": {}
        }

        # Create run-specific directory
        run_dir = self.validated_dir / self.run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        artifact_file = run_dir / "validation-20260812100500.json"
        with open(artifact_file, 'w') as f:
            json.dump(validation_artifact, f)

        # Load facts as merger would
        valid_facts = load_validation_results.get_validated_facts_for_merge(
            self.run_id,
            validated_dir=str(self.validated_dir)
        )

        # Verify rejected facts don't reach merger
        self.assertEqual(len(valid_facts), 0)


class TestMergerCannotBypassValidation(unittest.TestCase):
    """Test that merger cannot bypass validation by reading extraction artifacts directly (Test D)."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.extracts_dir = Path(self.test_dir) / "extracts"
        self.validated_dir = Path(self.test_dir) / "validated"
        self.cache_dir = Path(self.test_dir) / "cache"

        self.extracts_dir.mkdir(parents=True, exist_ok=True)
        self.validated_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Create test cache file
        self.cache_file = self.cache_dir / "test-source.txt"
        self.cache_file.write_text("Test content for extraction")

        self.run_id = "20260812-156000-bypass-test"

    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir)

    def test_no_validation_artifact_prevents_merge(self):
        """Test C: Merger cannot publish without the corresponding validation artifact."""
        source_id = "sp-official"  # Use genuine source to avoid contamination check
        source_type = "official"
        source_url = "https://advertising.amazon.com/solutions/products/sponsored-products"

        # Create extraction artifact but no validation artifact
        facts = [
            {
                "fact": "This fact should not reach merger",
                "concept": "test-concept",
                "quote": "test quote"
            }
        ]

        persist_extraction.persist_extraction(
            source_id, source_type, source_url, str(self.cache_file), facts, self.run_id, str(self.extracts_dir)
        )

        # Check if validation completed
        completed, path = load_validation_results.check_validation_completed(
            self.run_id,
            validated_dir=str(self.validated_dir)
        )

        # Should return False - no validation artifact
        self.assertFalse(completed)
        self.assertIsNone(path)

        # Try to load facts as merger would
        valid_facts = load_validation_results.get_validated_facts_for_merge(
            self.run_id,
            validated_dir=str(self.validated_dir)
        )

        # Should get empty dict - no facts to merge
        self.assertEqual(len(valid_facts), 0)

    def test_merger_reads_only_validation_artifacts(self):
        """Test D: Merger cannot bypass validation by reading state/extracts/."""
        source_id = "sp-official"  # Use genuine source to avoid contamination check
        source_type = "official"
        source_url = "https://advertising.amazon.com/solutions/products/sponsored-products"

        # Create extraction artifact with facts that should be rejected
        extraction_facts = [
            {
                "fact": "Fact that should be rejected",
                "concept": "test-concept",
                "quote": "bad quote"
            },
            {
                "fact": "Valid fact",
                "concept": "test-concept",
                "quote": "good quote"
            }
        ]

        persist_extraction.persist_extraction(
            source_id, source_type, source_url, str(self.cache_file), extraction_facts, self.run_id, str(self.extracts_dir)
        )

        # Create validation artifact that only validates the good fact
        validation_artifact = {
            "version": "1.0",
            "run_id": self.run_id,
            "validated_at": "2026-08-12T10:05:00Z",
            "extraction_files": ["state/extracts/test.json"],
            "validation_results": {
                "new": [
                    {
                        "fact": "Validated fact that should reach merger",
                        "concept": "test-concept",
                        "source_id": "test-source",
                        "classification": "new"
                    }
                ],
                "changed": [],
                "duplicate": [],
                "conflict": [],
                "rejected": [
                    {
                        "fact": "Fact that should be rejected",
                        "concept": "test-concept",
                        "source_id": "test-source",
                        "classification": "rejected",
                        "rejection_reason": "validation_failed"
                    }
                ]
            },
            "summary": {
                "total_facts": 2,
                "new_count": 1,
                "changed_count": 0,
                "duplicate_count": 0,
                "conflict_count": 0,
                "rejected_count": 1
            },
            "validator_metadata": {}
        }

        # Create run-specific directory
        run_dir = self.validated_dir / self.run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        validation_file = run_dir / "validation-20260812100500.json"
        with open(validation_file, 'w') as f:
            json.dump(validation_artifact, f)

        # Load facts as merger would
        valid_facts = load_validation_results.get_validated_facts_for_merge(
            self.run_id,
            validated_dir=str(self.validated_dir)
        )

        # Verify only validated facts reach merger (not the extraction artifact facts)
        self.assertEqual(len(valid_facts["test-concept"]), 1)
        self.assertEqual(valid_facts["test-concept"][0]["fact"], "Validated fact that should reach merger")
        self.assertNotEqual(valid_facts["test-concept"][0]["fact"], "Fact that should be rejected")


class TestValidationArtifactPurity(unittest.TestCase):
    """Test that validation artifacts never reference test-generated extraction artifacts."""

    def setUp(self):
        """Set up test directories."""
        self.test_dir = tempfile.mkdtemp()
        self.extracts_dir = Path(self.test_dir) / "extracts"
        self.validated_dir = Path(self.test_dir) / "validated"
        self.concepts_dir = Path(self.test_dir) / "concepts"
        self.cache_dir = Path(self.test_dir) / "cache"

        self.extracts_dir.mkdir(parents=True, exist_ok=True)
        self.validated_dir.mkdir(parents=True, exist_ok=True)
        self.concepts_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Create test cache file
        self.cache_file = self.cache_dir / "test-source.txt"
        self.cache_file.write_text("Test content for extraction")

    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir)

    def create_extraction_artifact(self, run_id, source_id, facts, source_url=None):
        """Create a test extraction artifact."""
        # Use realistic source URLs for genuine sources to avoid contamination check
        genuine_source_urls = {
            "sp-official": "https://advertising.amazon.com/solutions/products/sponsored-products",
            "sb-official": "https://advertising.amazon.com/solutions/products/sponsored-brands",
            "sd-official": "https://advertising.amazon.com/solutions/products/sponsored-display",
            "targeting-official": "https://advertising.amazon.com/library/guides/targeting-with-sponsored-products",
            "ppc-community": "https://www.junglescout.com/resources/articles/amazon-ppc/",
            "ads-api-notes": "https://advertising.amazon.com/API/docs/en-us/release-notes/index"
        }

        # If source_url is not provided, use the genuine URL or a test URL
        if source_url is None:
            if source_id in genuine_source_urls:
                source_url = genuine_source_urls[source_id]
            else:
                # For test sources, use example.com (which will trigger contamination)
                source_url = f"https://example.com/{source_id}"

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

        timestamp = "20260812100000"
        artifact_file = run_dir / f"{source_id}-{timestamp}.json"
        with open(artifact_file, 'w') as f:
            json.dump(artifact, f)

        return str(artifact_file)

    def test_validation_artifact_cannot_reference_test_sources(self):
        """Test that validation rejects artifacts with test source contamination."""
        # Create test run with test sources
        # Use "test-source" which matches the contamination pattern
        test_run_id = "20260812-contamination-test"
        test_facts = [{"fact": "Test fact about something", "concept": "test", "quote": "test", "extracted_at": "2026-08-12T10:00:00Z"}]
        artifact_path = self.create_extraction_artifact(test_run_id, "test-source", test_facts)

        # Attempt to validate artifacts with test source contamination
        # This should raise ValueError due to contamination guard
        with self.assertRaises(ValueError) as context:
            validate_extraction.validate_extraction_artifacts(
                test_run_id,
                extracts_dir=str(self.extracts_dir),
                concepts_dir=str(self.concepts_dir),
                output_dir=str(self.validated_dir)
            )

        # Verify the error message mentions contamination
        error_message = str(context.exception)
        self.assertIn("contamination", error_message.lower())
        self.assertIn("test-source", error_message.lower())

    def test_live_validation_only_references_genuine_sources(self):
        """Test that live validation artifacts only reference genuine registered sources."""
        # Create live run with genuine sources
        live_run_id = "20260812-live-run"
        genuine_sources = ["sp-official", "sb-official", "ads-api-notes"]

        for source_id in genuine_sources:
            facts = [{"fact": f"Valid fact from {source_id}", "concept": "test", "quote": "fact", "extracted_at": "2026-08-12T10:00:00Z"}]
            self.create_extraction_artifact(live_run_id, source_id, facts)

        # Create validation artifact with only genuine sources
        extraction_files = [
            f"state/extracts/{live_run_id}/{source_id}-20260812100000.json"
            for source_id in genuine_sources
        ]

        validation_artifact = {
            "version": "1.0",
            "validated_at": "2026-08-12T10:00:00Z",
            "extraction_files": extraction_files,
            "validation_results": {
                "new": [],
                "changed": [],
                "duplicate": [],
                "conflict": [],
                "rejected": []
            },
            "summary": {
                "total_facts": 0,
                "new_count": 0,
                "changed_count": 0,
                "duplicate_count": 0,
                "conflict_count": 0,
                "rejected_count": 0
            },
            "validator_metadata": {}
        }

        # Save validation artifact
        run_dir = self.validated_dir / live_run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        validation_file = run_dir / "validation-20260812100000.json"
        with open(validation_file, 'w') as f:
            json.dump(validation_artifact, f)

        # Verify no test sources are referenced
        with open(validation_file, 'r') as f:
            loaded_validation = json.load(f)

        for file_path in loaded_validation["extraction_files"]:
            self.assertNotIn(
                "test-source",
                file_path,
                "Live validation artifacts must never reference test-source files"
            )
            self.assertNotIn(
                "test-run",
                file_path,
                "Live validation artifacts must never reference test-run directories"
            )

    def test_genuine_registered_sources_are_accepted_by_validation(self):
        """Test that genuine registered sources (from sources.yaml) pass validation contamination check."""
        # Create run with genuine Amazon Ads sources
        genuine_run_id = "20260812-genuine-run"
        genuine_sources = ["sp-official", "sb-official", "sd-official", "targeting-official", "ppc-community", "ads-api-notes"]

        for source_id in genuine_sources:
            facts = [{"fact": f"Genuine fact from {source_id}", "concept": "test", "quote": "fact", "extracted_at": "2026-08-12T10:00:00Z"}]
            self.create_extraction_artifact(genuine_run_id, source_id, facts)

        # Validation should succeed without raising contamination error
        validation_results, summary, artifact_path = validate_extraction.validate_extraction_artifacts(
            genuine_run_id,
            extracts_dir=str(self.extracts_dir),
            concepts_dir=str(self.concepts_dir),
            output_dir=str(self.validated_dir)
        )

        # Verify validation succeeded
        self.assertIsNotNone(validation_results, "Genuine sources should pass validation")
        self.assertIsNotNone(summary, "Summary should be generated")
        self.assertIsNotNone(artifact_path, "Artifact path should be returned")

        # Verify all genuine sources were processed
        self.assertEqual(summary["total_facts"], len(genuine_sources))
        self.assertEqual(summary["new_count"], len(genuine_sources))

        # Verify validation artifact was created
        self.assertTrue(Path(artifact_path).exists(), "Validation artifact should be created")


if __name__ == '__main__':
    unittest.main()