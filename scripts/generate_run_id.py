#!/usr/bin/env python3
"""
Generate a unique run ID for each pipeline execution.

Run IDs ensure isolation between pipeline runs so that:
- Run A cannot consume Run B's extraction artifacts
- Tests don't interfere with live runs
- Concurrent runs don't cross-contaminate

Format: timestamp-random (e.g., 20260812-143052-a3b5f7d2)
"""
import sys
import uuid
from datetime import datetime


def generate_run_id():
    """Generate a unique run ID."""
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    unique_suffix = uuid.uuid4().hex[:8]
    return f"{timestamp}-{unique_suffix}"


if __name__ == "__main__":
    print(generate_run_id())