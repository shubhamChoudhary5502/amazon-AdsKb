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

def load_extraction_artifacts(extracts_dir="state/extracts"):
    """Load all extraction artifacts from the extracts directory."""
    extracts_path = Path(extracts_dir)
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
                return "duplicate", {"existing_line": line.strip()}

            # Check for substantial word overlap (80%+)
            if fact_words and line_words:
                overlap = len(fact_words & line_words) / max(len(fact_words), len(line_words))
                if overlap >= 0.8:
                    return "duplicate", {"existing_line": line.strip()}

    # Check for conflicts (contradictory statements)
    conflict_keywords = ["however", "but", "although", "contrast", "differs", "opposite"]
    if any(keyword in concept_doc.lower() for keyword in conflict_keywords):
        # Look for statements that might contradict
        lines = concept_doc.split("\n")
        for i, line in enumerate(lines):
            if fact_lower.split()[0] in line.lower() and "but" in line.lower():
                return "conflict", {"conflicting_line": line.strip()}

    # Check for changed facts (similar but different values/numbers)
    for line in concept_doc.split("\n"):
        if line.strip().startswith("-"):
            line_words = set(normalize_fact_text(line).split())
            fact_words = set(normalized_fact.split())
            # If they share most words but not all, it might be a change
            overlap = len(line_words & fact_words) / max(len(line_words), len(fact_words))
            if 0.6 < overlap < 1.0:
                return "changed", {"existing_line": line.strip()}

    return "new", {"reason": "no_match_found"}

def validate_extraction_artifacts(extracts_dir="state/extracts", concepts_dir="knowledge/concepts", output_dir="state/validated"):
    """
    Validate extraction artifacts against existing knowledge bundle.

    Returns: (validation_results, summary, artifact_path)
    """
    extracts_path = Path(extracts_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load extraction artifacts
    extraction_files = []
    for artifact_file in extracts_path.glob("*.json"):
        with open(artifact_file) as f:
            artifact = json.load(f)
            extraction_files.append(str(artifact_file))

    if not extraction_files:
        return None, {"error": "No extraction artifacts found"}, None

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

    for artifact_file in extraction_files:
        with open(artifact_file) as f:
            artifact = json.load(f)

        source_id = artifact["source_id"]

        for fact_data in artifact["facts"]:
            fact = fact_data["fact"]
            concept = fact_data["concept"]

            # Basic validation
            if len(fact.strip()) < 10:
                validation_results["rejected"].append({
                    "fact": fact,
                    "concept": concept,
                    "source_id": source_id,
                    "classification": "rejected",
                    "rejection_reason": "fact_too_short"
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
    try:
        results, summary, artifact_path = validate_extraction_artifacts()

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