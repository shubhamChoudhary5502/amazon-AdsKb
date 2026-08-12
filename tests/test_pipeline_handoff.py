#!/usr/bin/env python3
"""
Comprehensive tests for pipeline handoff architecture.

These tests prove that:
1. Extraction artifacts are persisted to state/extracts/
2. Validator reads the exact persisted extraction output
3. Invalid facts are rejected by validator
4. Valid facts reach the merger through validation artifacts
5. Merger cannot bypass validation by reading extraction artifacts directly
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


class TestExtractionPersistence(unittest.TestCase):
    """Test that extraction artifacts are properly persisted."""

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

    def test_extraction_artifact_created(self):
        """Test that extraction creates a valid artifact file."""
        source_id = "test-source"
        source_type = "official"
        source_url = "https://example.com/test"
        cache_file = str(self.cache_file)

        facts = [
            {
                "fact": "Test fact about Amazon advertising",
                "concept": "test-concept",
                "quote": "Test fact quote",
                "confidence": "high"
            }
        ]

        # Persist the extraction
        artifact_path = persist_extraction.persist_extraction(
            source_id, source_type, source_url, cache_file, facts
        )

        # Verify artifact file exists
        self.assertTrue(Path(artifact_path).exists())
        self.assertIn("test-source", artifact_path)
        self.assertTrue(artifact_path.endswith(".json"))

    def test_extraction_artifact_structure(self):
        """Test that extraction artifact has correct structure."""
        source_id = "test-source"
        source_type = "official"
        source_url = "https://example.com/test"
        cache_file = str(self.cache_file)

        facts = [
            {
                "fact": "Test fact about Amazon advertising",
                "concept": "test-concept",
                "quote": "Test fact quote"
            }
        ]

        # Persist the extraction
        artifact_path = persist_extraction.persist_extraction(
            source_id, source_type, source_url, cache_file, facts
        )

        # Load and verify structure
        with open(artifact_path) as f:
            artifact = json.load(f)

        # Required fields
        self.assertIn("version", artifact)
        self.assertIn("extracted_at", artifact)
        self.assertIn("source_id", artifact)
        self.assertIn("source_type", artifact)
        self.assertIn("source_url", artifact)
        self.assertIn("cache_file", artifact)
        self.assertIn("content_hash", artifact)
        self.assertIn("facts", artifact)

        # Verify values
        self.assertEqual(artifact["source_id"], source_id)
        self.assertEqual(artifact["source_type"], source_type)
        self.assertEqual(artifact["source_url"], source_url)
        self.assertEqual(len(artifact["facts"]), 1)

    def test_extraction_artifact_content_hash(self):
        """Test that extraction artifact includes correct content hash."""
        source_id = "test-source"
        source_type = "official"
        source_url = "https://example.com/test"
        cache_file = str(self.cache_file)

        facts = [
            {
                "fact": "Test fact",
                "concept": "test-concept",
                "quote": "Test quote"
            }
        ]

        # Persist extraction
        artifact_path = persist_extraction.persist_extraction(
            source_id, source_type, source_url, cache_file, facts
        )

        # Load artifact
        with open(artifact_path) as f:
            artifact = json.load(f)

        # Verify hash is present and not empty
        self.assertIn("content_hash", artifact)
        self.assertNotEqual(artifact["content_hash"], "")
        self.assertNotEqual(artifact["content_hash"], "unknown")
        self.assertEqual(len(artifact["content_hash"]), 64)  # SHA256 hash length

    def test_multiple_facts_persisted(self):
        """Test that multiple facts are persisted correctly."""
        source_id = "test-source"
        source_type = "official"
        source_url = "https://example.com/test"
        cache_file = str(self.cache_file)

        facts = [
            {
                "fact": "First test fact",
                "concept": "concept-one",
                "quote": "Quote one"
            },
            {
                "fact": "Second test fact",
                "concept": "concept-two",
                "quote": "Quote two"
            },
            {
                "fact": "Third test fact",
                "concept": "concept-one",
                "quote": "Quote three"
            }
        ]

        # Persist extraction
        artifact_path = persist_extraction.persist_extraction(
            source_id, source_type, source_url, cache_file, facts
        )

        # Load and verify
        with open(artifact_path) as f:
            artifact = json.load(f)

        self.assertEqual(len(artifact["facts"]), 3)
        self.assertEqual(artifact["facts"][0]["concept"], "concept-one")
        self.assertEqual(artifact["facts"][1]["concept"], "concept-two")
        self.assertEqual(artifact["facts"][2]["concept"], "concept-one")


class TestValidatorConsumesExtraction(unittest.TestCase):
    """Test that validator reads the exact persisted extraction output."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.extracts_dir = Path(self.test_dir) / "extracts"
        self.concepts_dir = Path(self.test_dir) / "concepts"
        self.validated_dir = Path(self.test_dir) / "validated"

        self.extracts_dir.mkdir(parents=True, exist_ok=True)
        self.concepts_dir.mkdir(parents=True, exist_ok=True)
        self.validated_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir)

    def create_test_extraction_artifact(self, source_id, facts):
        """Create a test extraction artifact."""
        artifact = {
            "version": "1.0",
            "extracted_at": "2026-08-12T10:00:00Z",
            "source_id": source_id,
            "source_type": "official",
            "source_url": f"https://example.com/{source_id}",
            "cache_file": f"state/cache/{source_id}.txt",
            "content_hash": "abc123",
            "facts": facts,
            "extraction_metadata": {
                "extractor_agent": "test-extractor",
                "extraction_duration_ms": 1000
            }
        }

        artifact_file = self.extracts_dir / f"{source_id}-20260812100000.json"
        with open(artifact_file, 'w') as f:
            json.dump(artifact, f)

        return str(artifact_file)

    def test_validator_reads_exact_extraction_artifact(self):
        """Test that validator reads the exact persisted extraction output."""
        # Create extraction artifact
        facts = [
            {
                "fact": "Sponsored Products are cost-per-click ads",
                "concept": "sponsored-products",
                "quote": "cost-per-click ads",
                "extracted_at": "2026-08-12T10:00:00Z"
            }
        ]

        artifact_path = self.create_test_extraction_artifact("test-source", facts)

        # Run validation
        validation_results, summary, validation_path = validate_extraction.validate_extraction_artifacts(
            extracts_dir=str(self.extracts_dir),
            concepts_dir=str(self.concepts_dir),
            output_dir=str(self.validated_dir)
        )

        # Verify validation artifact was created
        self.assertIsNotNone(validation_path)
        self.assertTrue(Path(validation_path).exists())

        # Verify extraction file was read
        with open(validation_path) as f:
            validation_artifact = json.load(f)

        self.assertIn(artifact_path, validation_artifact["extraction_files"])

    def test_validator_processes_multiple_extraction_artifacts(self):
        """Test that validator can process multiple extraction artifacts."""
        # Create multiple extraction artifacts
        facts1 = [{"fact": "Fact 1", "concept": "concept-a", "quote": "quote1", "extracted_at": "2026-08-12T10:00:00Z"}]
        facts2 = [{"fact": "Fact 2", "concept": "concept-b", "quote": "quote2", "extracted_at": "2026-08-12T10:01:00Z"}]

        artifact1_path = self.create_test_extraction_artifact("source-1", facts1)
        artifact2_path = self.create_test_extraction_artifact("source-2", facts2)

        # Run validation
        validation_results, summary, validation_path = validate_extraction.validate_extraction_artifacts(
            extracts_dir=str(self.extracts_dir),
            concepts_dir=str(self.concepts_dir),
            output_dir=str(self.validated_dir)
        )

        # Verify both artifacts were processed
        with open(validation_path) as f:
            validation_artifact = json.load(f)

        self.assertEqual(len(validation_artifact["extraction_files"]), 2)
        self.assertIn(artifact1_path, validation_artifact["extraction_files"])
        self.assertIn(artifact2_path, validation_artifact["extraction_files"])


class TestInvalidFactsRejected(unittest.TestCase):
    """Test that invalid facts are rejected by validator."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.extracts_dir = Path(self.test_dir) / "extracts"
        self.concepts_dir = Path(self.test_dir) / "concepts"
        self.validated_dir = Path(self.test_dir) / "validated"

        self.extracts_dir.mkdir(parents=True, exist_ok=True)
        self.concepts_dir.mkdir(parents=True, exist_ok=True)
        self.validated_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir)

    def create_test_extraction_artifact(self, source_id, facts):
        """Create a test extraction artifact."""
        artifact = {
            "version": "1.0",
            "extracted_at": "2026-08-12T10:00:00Z",
            "source_id": source_id,
            "source_type": "official",
            "source_url": f"https://example.com/{source_id}",
            "cache_file": f"state/cache/{source_id}.txt",
            "content_hash": "abc123",
            "facts": facts,
            "extraction_metadata": {}
        }

        artifact_file = self.extracts_dir / f"{source_id}-20260812100000.json"
        with open(artifact_file, 'w') as f:
            json.dump(artifact, f)

        return str(artifact_file)

    def test_too_short_fact_rejected(self):
        """Test that facts shorter than 10 characters are rejected."""
        facts = [
            {
                "fact": "Short",  # Less than 10 characters
                "concept": "test-concept",
                "quote": "quote",
                "extracted_at": "2026-08-12T10:00:00Z"
            },
            {
                "fact": "This is a valid fact with enough content",
                "concept": "test-concept",
                "quote": "valid quote",
                "extracted_at": "2026-08-12T10:00:00Z"
            }
        ]

        self.create_test_extraction_artifact("test-source", facts)

        # Run validation
        validation_results, summary, validation_path = validate_extraction.validate_extraction_artifacts(
            extracts_dir=str(self.extracts_dir),
            concepts_dir=str(self.concepts_dir),
            output_dir=str(self.validated_dir)
        )

        # Verify short fact was rejected
        self.assertGreater(summary["rejected_count"], 0)
        self.assertIn("rejected", validation_results)
        self.assertEqual(validation_results["rejected"][0]["rejection_reason"], "fact_too_short")

    def test_duplicate_facts_identified(self):
        """Test that duplicate facts are identified."""
        # Create an existing concept document with exact duplicate
        concept_file = self.concepts_dir / "sponsored-products.md"
        concept_content = """---
id: sponsored-products
title: Sponsored Products
---

# Sponsored Products

- Sponsored Products are cost-per-click ads
- Another existing fact
"""
        concept_file.write_text(concept_content)

        facts = [
            {
                "fact": "Sponsored Products are cost-per-click ads",  # Exact match (no citation)
                "concept": "sponsored-products",
                "quote": "cost-per-click ads",
                "extracted_at": "2026-08-12T10:00:00Z"
            }
        ]

        self.create_test_extraction_artifact("test-source", facts)

        # Run validation
        validation_results, summary, validation_path = validate_extraction.validate_extraction_artifacts(
            extracts_dir=str(self.extracts_dir),
            concepts_dir=str(self.concepts_dir),
            output_dir=str(self.validated_dir)
        )

        # Verify duplicate or changed was identified (both are acceptable for similar facts)
        total_classified = summary["duplicate_count"] + summary["changed_count"]
        self.assertGreater(total_classified, 0, "Should identify duplicate or changed facts")

        # The fact should be found in either duplicate or changed category
        found_in_duplicate = any(f["concept"] == "sponsored-products" for f in validation_results.get("duplicate", []))
        found_in_changed = any(f["concept"] == "sponsored-products" for f in validation_results.get("changed", []))

        self.assertTrue(found_in_duplicate or found_in_changed,
                       "Should find fact classified as duplicate or changed")


class TestValidFactsReachMerger(unittest.TestCase):
    """Test that valid facts reach the merger through validation artifacts."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.validated_dir = Path(self.test_dir) / "validated"
        self.validated_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir)

    def create_validation_artifact(self, new_facts, changed_facts):
        """Create a test validation artifact."""
        artifact = {
            "version": "1.0",
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

        artifact_file = self.validated_dir / "validation-20260812100500.json"
        with open(artifact_file, 'w') as f:
            json.dump(artifact, f)

        return str(artifact_file)

    def test_merger_loads_validated_facts(self):
        """Test that merger can load validated facts."""
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

        artifact_file = self.validated_dir / "validation-20260812100500.json"
        with open(artifact_file, 'w') as f:
            json.dump(validation_artifact, f)

        # Load facts as merger would
        valid_facts = load_validation_results.get_validated_facts_for_merge(
            validated_dir=str(self.validated_dir)
        )

        # Verify rejected facts don't reach merger
        self.assertEqual(len(valid_facts), 0)


class TestMergerCannotBypassValidation(unittest.TestCase):
    """Test that merger cannot bypass validation by reading extraction artifacts directly."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.extracts_dir = Path(self.test_dir) / "extracts"
        self.validated_dir = Path(self.test_dir) / "validated"

        self.extracts_dir.mkdir(parents=True, exist_ok=True)
        self.validated_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir)

    def test_no_validation_artifact_prevents_merge(self):
        """Test that merger cannot proceed without validation artifact."""
        # Create extraction artifact but no validation artifact
        extraction_artifact = {
            "version": "1.0",
            "extracted_at": "2026-08-12T10:00:00Z",
            "source_id": "test-source",
            "source_type": "official",
            "source_url": "https://example.com/test",
            "cache_file": "state/cache/test.txt",
            "content_hash": "abc123",
            "facts": [
                {
                    "fact": "This fact should not reach merger",
                    "concept": "test-concept",
                    "quote": "test quote",
                    "extracted_at": "2026-08-12T10:00:00Z"
                }
            ],
            "extraction_metadata": {}
        }

        artifact_file = self.extracts_dir / "test-source-20260812100000.json"
        with open(artifact_file, 'w') as f:
            json.dump(extraction_artifact, f)

        # Check if validation completed
        completed, path = load_validation_results.check_validation_completed(
            validated_dir=str(self.validated_dir)
        )

        # Should return False - no validation artifact
        self.assertFalse(completed)
        self.assertIsNone(path)

    def test_merger_reads_only_validation_artifacts(self):
        """Test that merger reads from validated/ not extracts/."""
        # Create both extraction and validation artifacts
        extraction_artifact = {
            "version": "1.0",
            "extracted_at": "2026-08-12T10:00:00Z",
            "source_id": "test-source",
            "source_type": "official",
            "source_url": "https://example.com/test",
            "cache_file": "state/cache/test.txt",
            "content_hash": "abc123",
            "facts": [
                {
                    "fact": "Extracted fact that should be ignored",
                    "concept": "test-concept",
                    "quote": "test quote",
                    "extracted_at": "2026-08-12T10:00:00Z"
                }
            ],
            "extraction_metadata": {}
        }

        artifact_file = self.extracts_dir / "test-source-20260812100000.json"
        with open(artifact_file, 'w') as f:
            json.dump(extraction_artifact, f)

        # Create validation artifact with different facts
        validation_artifact = {
            "version": "1.0",
            "validated_at": "2026-08-12T10:05:00Z",
            "extraction_files": [str(artifact_file)],
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
                        "fact": "Extracted fact that should be ignored",
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

        validation_file = self.validated_dir / "validation-20260812100500.json"
        with open(validation_file, 'w') as f:
            json.dump(validation_artifact, f)

        # Load facts as merger would
        valid_facts = load_validation_results.get_validated_facts_for_merge(
            validated_dir=str(self.validated_dir)
        )

        # Verify only validated facts reach merger
        self.assertEqual(len(valid_facts["test-concept"]), 1)
        self.assertEqual(valid_facts["test-concept"][0]["fact"], "Validated fact that should reach merger")


if __name__ == '__main__':
    unittest.main()