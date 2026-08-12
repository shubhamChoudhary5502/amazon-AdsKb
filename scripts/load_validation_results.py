#!/usr/bin/env python3
"""
Utility for merger agents to load validated results from state/validated/
This ensures the merger only processes facts that passed validation.
"""

import json
import sys
from pathlib import Path

def load_latest_validation_artifact(validated_dir="state/validated"):
    """
    Load the most recent validation artifact from the validated directory.

    Returns: (validation_artifact, artifact_path) or (None, None) if not found
    """
    validated_path = Path(validated_dir)
    if not validated_path.exists():
        return None, None

    # Find the most recent validation artifact
    artifacts = sorted(validated_path.glob("validation-*.json"), reverse=True)
    if not artifacts:
        return None, None

    latest_artifact = artifacts[0]
    with open(latest_artifact) as f:
        artifact = json.load(f)

    return artifact, str(latest_artifact)

def get_validated_facts_for_merge(validated_dir="state/validated"):
    """
    Get facts that passed validation for merging.

    Returns: facts suitable for merging, grouped by concept
    """
    artifact, artifact_path = load_latest_validation_artifact(validated_dir)
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

def check_validation_completed(validated_dir="state/validated"):
    """
    Check if validation has been completed and results are available.

    Returns: (bool, str) where str is the artifact path if True
    """
    artifact, artifact_path = load_latest_validation_artifact(validated_dir)
    if artifact and artifact_path:
        return True, artifact_path
    return False, None

if __name__ == "__main__":
    completed, path = check_validation_completed()
    if completed:
        print(f"Validation completed: {path}")
        facts = get_validated_facts_for_merge()
        print(f"Validated facts for {len(facts)} concepts ready for merge")
        sys.exit(0)
    else:
        print("No validation artifacts found", file=sys.stderr)
        sys.exit(1)