#!/usr/bin/env python3
"""
Validator script that reads persisted extraction artifacts and validates them
against existing knowledge bundle, producing validation artifacts.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
import re
import glob

def check_for_test_source_contamination(artifacts):
    """
    Check if any extraction artifacts are from test sources.

    Test source contamination is detected by:
    - source_id starting with or containing "test-source"
    - source_url containing "example.com", "localhost", or "127.0.0.1"

    Note: run_id is NOT checked because legitimate test runs have "test" in their run_id.
    We only validate that the source data itself is from genuine sources.

    Args:
        artifacts: List of (artifact_file, artifact_dict) tuples

    Returns: (is_contaminated, contaminated_files)
    """
    contaminated_files = []
    test_source_patterns = ["test-source", "example.com", "localhost", "127.0.0.1"]

    for artifact_file, artifact in artifacts:
        source_id = artifact.get("source_id", "").lower()
        source_url = artifact.get("source_url", "").lower()

        # Check for test source indicators in source_id and source_url only
        # NOT run_id, since test runs legitimately have "test" in their run_id
        if any(indicator in source_id or indicator in source_url
               for indicator in test_source_patterns):
            contaminated_files.append(artifact_file)

    return len(contaminated_files) > 0, contaminated_files

def load_extraction_artifacts(run_id, extracts_dir="state/extracts"):
    """Load extraction artifacts from a specific run's extracts directory."""
    extracts_path = Path(extracts_dir) / run_id
    if not extracts_path.exists():
        return []

    artifacts = []
    for artifact_file in extracts_path.glob("*.json"):
        with open(artifact_file) as f:
            artifact = json.load(f)
            artifacts.append((str(artifact_file), artifact))

    return artifacts

def load_concept_documents(concepts_dir="knowledge/concepts"):
    """Load all existing concept documents."""
    concepts_path = Path(concepts_dir)
    if not concepts_path.exists():
        return {}

    concepts = {}
    for concept_file in concepts_path.glob("*.md"):
        with open(concept_file) as f:
            content = f.read()
            # Parse frontmatter
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    # Simple YAML parsing
                    concept_id = None
                    for line in frontmatter.split("\n"):
                        if line.startswith("id:"):
                            concept_id = line.split(":", 1)[1].strip()
                            break
                    if concept_id:
                        concepts[concept_id] = {
                            "file": str(concept_file),
                            "content": content
                        }

    return concepts

def normalize_fact_text(fact):
    """Normalize fact text for comparison."""
    # Remove citation markers
    fact = re.sub(r'\[S\d+\]', '', fact)
    # Remove bullet points and list markers
    fact = re.sub(r'^[\s]*[-*+•]\s*', '', fact)
    # Remove extra whitespace
    fact = ' '.join(fact.split())
    return fact.lower().strip()

def classify_fact(fact, concept_slug, source_id, existing_concepts):
    """
    Classify a fact as new, changed, duplicate, or conflict.

    Returns: (classification, details_dict)
    """
    normalized_fact = normalize_fact_text(fact)
    fact_words = set(normalized_fact.split())

    # Check if concept exists
    if concept_slug not in existing_concepts:
        return "new", {"reason": "concept_does_not_exist"}

    concept_doc = existing_concepts[concept_slug]["content"]

    # Check for duplicate (exact match or very close)
    for line in concept_doc.split("\n"):
        if line.strip().startswith("-"):
            line_text = normalize_fact_text(line)
            line_words = set(line_text.split())

            # Check for exact match
            if normalized_fact == line_text:
                return "duplicate", {
                    "existing_line": line.strip(),
                    "match_type": "exact"
                }

            # Check for substantial word overlap (80%+)
            if fact_words and line_words:
                overlap = len(fact_words & line_words) / max(len(fact_words), len(line_words))
                if overlap >= 0.8:
                    return "duplicate", {
                        "existing_line": line.strip(),
                        "match_type": "overlap",
                        "overlap_ratio": overlap
                    }

    # Check for conflicts (contradictory statements)
    # A conflict occurs when the same concept is stated differently
    conflict_keywords = ["however", "but", "although", "contrast", "differs", "opposite", "contradicts", "disagrees", "whereas", "yet"]
    doc_lower = concept_doc.lower()

    if any(keyword in doc_lower for keyword in conflict_keywords):
        # Look for statements that might contradict
        lines = concept_doc.split("\n")
        for i, line in enumerate(lines):
            line_lower = line.lower()
            # Check if line contains conflict keywords
            if any(keyword in line_lower for keyword in conflict_keywords):
                # Check if our fact has substantial overlap with this line
                line_text = normalize_fact_text(line)
                line_words = set(line_text.split())
                if fact_words and line_words:
                    overlap = len(fact_words & line_words) / max(len(fact_words), len(line_words))
                    if overlap >= 0.3:  # At least 30% word overlap with conflicting statement
                        return "conflict", {
                            "conflicting_line": line.strip(),
                            "overlap_ratio": overlap
                        }

    # Check for changed facts (similar but different values/numbers)
    for line in concept_doc.split("\n"):
        if line.strip().startswith("-"):
            line_words = set(normalize_fact_text(line).split())
            fact_words = set(normalized_fact.split())
            # If they share most words but not all, it might be a change
            overlap = len(line_words & fact_words) / max(len(line_words), len(fact_words))
            if 0.6 < overlap < 1.0:
                return "changed", {
                    "existing_line": line.strip(),
                    "overlap_ratio": overlap
                }

    return "new", {"reason": "no_match_found"}

def validate_extraction_artifacts(run_id, extracts_dir="state/extracts", concepts_dir="knowledge/concepts", output_dir="state/validated"):
    """
    Validate extraction artifacts from a specific run against existing knowledge bundle.

    Args:
        run_id: The run identifier to validate (ensures isolation)
        extracts_dir: Base directory for extraction artifacts
        concepts_dir: Directory containing existing concept documents
        output_dir: Directory for validation artifacts

    Returns: (validation_results, summary, artifact_path) or (None, None, None) if no artifacts found or contaminated

    Raises:
        ValueError: If extraction artifacts contain test source contamination
    """
    # Load extraction artifacts for this specific run
    extraction_artifacts = load_extraction_artifacts(run_id, extracts_dir)

    if not extraction_artifacts:
        return None, None, None

    # Check for test source contamination
    is_contaminated, contaminated_files = check_for_test_source_contamination(extraction_artifacts)
    if is_contaminated:
        raise ValueError(
            f"Test source contamination detected. The following artifacts contain test sources "
            f"and cannot be used in production validation: {contaminated_files}"
        )

    # Create output directory for this run
    output_path = Path(output_dir) / run_id
    output_path.mkdir(parents=True, exist_ok=True)

    # Track extraction files
    extraction_files = [artifact_file for artifact_file, _ in extraction_artifacts]

    # Load existing concepts
    existing_concepts = load_concept_documents(concepts_dir)

    # Process all facts from all extraction artifacts
    validation_results = {
        "new": [],
        "changed": [],
        "duplicate": [],
        "conflict": [],
        "rejected": []
    }

    for artifact_file, artifact in extraction_artifacts:
        source_id = artifact["source_id"]
        source_url = artifact.get("source_url", "unknown")
        source_type = artifact.get("source_type", "unknown")

        for fact_data in artifact["facts"]:
            fact = fact_data["fact"]
            concept = fact_data["concept"]
            quote = fact_data.get("quote", "")
            extracted_at = fact_data.get("extracted_at", "")

            # Validate fact is not empty
            if not fact or not fact.strip():
                validation_results["rejected"].append({
                    "fact": fact,
                    "concept": concept,
                    "source_id": source_id,
                    "classification": "rejected",
                    "rejection_reason": "fact_is_empty"
                })
                continue

            # Validate fact has minimum length
            if len(fact.strip()) < 10:
                validation_results["rejected"].append({
                    "fact": fact,
                    "concept": concept,
                    "source_id": source_id,
                    "classification": "rejected",
                    "rejection_reason": "fact_too_short"
                })
                continue

            # Validate concept is not empty
            if not concept or not concept.strip():
                validation_results["rejected"].append({
                    "fact": fact,
                    "concept": concept,
                    "source_id": source_id,
                    "classification": "rejected",
                    "rejection_reason": "concept_is_empty"
                })
                continue

            # Validate quote is not empty
            if not quote or not quote.strip():
                validation_results["rejected"].append({
                    "fact": fact,
                    "concept": concept,
                    "source_id": source_id,
                    "classification": "rejected",
                    "rejection_reason": "quote_is_empty"
                })
                continue

            # Classify the fact
            classification, details = classify_fact(
                fact, concept, source_id, existing_concepts
            )

            fact_record = {
                "fact": fact,
                "concept": concept,
                "source_id": source_id,
                "source_url": source_url,
                "source_type": source_type,
                "quote": quote,
                "extracted_at": extracted_at,
                "classification": classification,
                **details
            }

            if classification == "new":
                validation_results["new"].append(fact_record)
            elif classification == "changed":
                validation_results["changed"].append(fact_record)
            elif classification == "duplicate":
                validation_results["duplicate"].append(fact_record)
            elif classification == "conflict":
                validation_results["conflict"].append(fact_record)

    # Create summary
    summary = {
        "total_facts": sum(len(results) for results in validation_results.values()),
        "new_count": len(validation_results["new"]),
        "changed_count": len(validation_results["changed"]),
        "duplicate_count": len(validation_results["duplicate"]),
        "conflict_count": len(validation_results["conflict"]),
        "rejected_count": len(validation_results["rejected"])
    }

    # Create validation artifact
    timestamp = datetime.utcnow().isoformat() + "Z"
    validation_artifact = {
        "version": "1.0",
        "run_id": run_id,
        "validated_at": timestamp,
        "extraction_files": extraction_files,
        "validation_results": validation_results,
        "summary": summary,
        "validator_metadata": {
            "validator_agent": "validate_extraction.py",
            "validation_duration_ms": 0,
            "concepts_checked": len(existing_concepts),
            "documents_updated": 0
        }
    }

    # Write validation artifact
    filename = f"validation-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"
    artifact_path = output_path / filename

    with open(artifact_path, 'w') as f:
        json.dump(validation_artifact, f, indent=2)

    return validation_results, summary, str(artifact_path)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: validate_extraction.py <run_id>")
        sys.exit(1)

    run_id = sys.argv[1]

    try:
        results, summary, artifact_path = validate_extraction_artifacts(run_id)

        if artifact_path:
            print(f"Validation artifact created: {artifact_path}")
            print(f"Summary: {summary}")
            sys.exit(0)
        else:
            print("No extraction artifacts to validate", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"Error during validation: {e}", file=sys.stderr)
        sys.exit(1)