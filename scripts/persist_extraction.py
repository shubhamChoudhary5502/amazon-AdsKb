#!/usr/bin/env python3
"""
Utility for extractor agents to persist their output to state/extracts/
This ensures the validator has access to the exact extraction results.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
import hashlib

def validate_extraction_artifact(data):
    """Validate extraction artifact against schema."""
    schema_path = Path("state/extracts-schema.json")
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")

    with open(schema_path) as f:
        schema = json.load(f)

    # Basic validation (in production, use jsonschema library)
    required = ["version", "extracted_at", "source_id", "source_type", "source_url", "cache_file", "content_hash", "facts"]
    for field in required:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    if data["version"] != "1.0":
        raise ValueError(f"Unsupported version: {data['version']}")

    # Validate facts array
    if not isinstance(data["facts"], list):
        raise ValueError("facts must be an array")

    for i, fact in enumerate(data["facts"]):
        fact_required = ["fact", "concept", "quote", "extracted_at"]
        for field in fact_required:
            if field not in fact:
                raise ValueError(f"Fact {i} missing required field: {field}")

def persist_extraction(source_id, source_type, source_url, cache_file, facts, metadata=None):
    """
    Persist extraction results to state/extracts/<source-id>-<timestamp>.json

    Args:
        source_id: Source identifier from sources.yaml
        source_type: Source kind (official/community/api)
        source_url: URL that was fetched
        cache_file: Path to cached content
        facts: List of fact dicts with keys: fact, concept, quote, [confidence]
        metadata: Optional dict with extractor_agent, extraction_duration_ms, content_size_bytes

    Returns:
        Path to the persisted artifact file
    """
    extracts_dir = Path("state/extracts")
    extracts_dir.mkdir(parents=True, exist_ok=True)

    # Calculate content hash
    cache_path = Path(cache_file)
    if cache_path.exists():
        with open(cache_path, 'rb') as f:
            content_hash = hashlib.sha256(f.read()).hexdigest()
    else:
        content_hash = "unknown"

    # Create artifact
    timestamp = datetime.utcnow().isoformat() + "Z"
    artifact = {
        "version": "1.0",
        "extracted_at": timestamp,
        "source_id": source_id,
        "source_type": source_type,
        "source_url": source_url,
        "cache_file": cache_file,
        "content_hash": content_hash,
        "facts": [],
        "extraction_metadata": metadata or {}
    }

    # Add facts with timestamps
    for fact_data in facts:
        fact_record = {
            "fact": fact_data["fact"],
            "concept": fact_data["concept"],
            "quote": fact_data["quote"],
            "extracted_at": timestamp,
            "confidence": fact_data.get("confidence", "medium")
        }
        artifact["facts"].append(fact_record)

    # Validate artifact
    validate_extraction_artifact(artifact)

    # Write artifact
    filename = f"{source_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"
    artifact_path = extracts_dir / filename

    with open(artifact_path, 'w') as f:
        json.dump(artifact, f, indent=2)

    return str(artifact_path)

if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Usage: persist_extraction.py <source_id> <source_type> <source_url> <cache_file> <facts_json> [metadata_json]")
        sys.exit(1)

    source_id = sys.argv[1]
    source_type = sys.argv[2]
    source_url = sys.argv[3]
    cache_file = sys.argv[4]
    facts = json.loads(sys.argv[5])
    metadata = json.loads(sys.argv[6]) if len(sys.argv) > 6 else None

    try:
        artifact_path = persist_extraction(source_id, source_type, source_url, cache_file, facts, metadata)
        print(f"Extraction persisted to: {artifact_path}")
        sys.exit(0)
    except Exception as e:
        print(f"Error persisting extraction: {e}", file=sys.stderr)
        sys.exit(1)