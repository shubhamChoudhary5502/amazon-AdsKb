#!/usr/bin/env python3
"""
Utility for merger agents to load validated results from state/validated/
This ensures the merger only processes facts that passed validation.
"""

import json
import sys
from pathlib import Path

def load_validation_artifact(run_id, validated_dir="state/validated"):
    """
    Load the validation artifact for a specific run from the validated directory.

    Args:
        run_id: The run identifier to load
        validated_dir: Base directory for validation artifacts

    Returns: (validation_artifact, artifact_path) or (None, None) if not found
    """
    validated_path = Path(validated_dir) / run_id
    if not validated_path.exists():
        return None, None

    # Find the validation artifact for this run
    artifacts = list(validated_path.glob("validation-*.json"))
    if not artifacts:
        return None, None

    # Load the artifact
    artifact_file = artifacts[0]
    with open(artifact_file) as f:
        artifact = json.load(f)

    # Verify run_id matches
    if artifact.get("run_id") != run_id:
        return None, None

    return artifact, str(artifact_file)

def get_validated_facts_for_merge(run_id, validated_dir="state/validated"):
    """
    Get facts that passed validation for merging from a specific run.

    Args:
        run_id: The run identifier to load
        validated_dir: Base directory for validation artifacts

    Returns: facts suitable for merging, grouped by concept
    """
    artifact, artifact_path = load_validation_artifact(run_id, validated_dir)
    if not artifact:
        return {}

    results = artifact.get("validation_results", {})

    # Only process new and changed facts
    valid_facts = {}
    for fact_record in results.get("new", []) + results.get("changed", []):
        concept = fact_record["concept"]
        if concept not in valid_facts:
            valid_facts[concept] = []

        valid_facts[concept].append({
            "fact": fact_record["fact"],
            "source_id": fact_record["source_id"],
            "classification": fact_record["classification"]
        })

    return valid_facts

def check_validation_completed(run_id, validated_dir="state/validated"):
    """
    Check if validation has been completed for a specific run and results are available.

    Args:
        run_id: The run identifier to check
        validated_dir: Base directory for validation artifacts

    Returns: (bool, str) where str is the artifact path if True
    """
    artifact, artifact_path = load_validation_artifact(run_id, validated_dir)
    if artifact and artifact_path:
        return True, artifact_path
    return False, None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: load_validation_results.py <run_id>")
        sys.exit(1)

    run_id = sys.argv[1]

    completed, path = check_validation_completed(run_id)
    if completed:
        print(f"Validation completed: {path}")
        facts = get_validated_facts_for_merge(run_id)
        print(f"Validated facts for {len(facts)} concepts ready for merge")
        sys.exit(0)
    else:
        print("No validation artifacts found", file=sys.stderr)
        sys.exit(1)