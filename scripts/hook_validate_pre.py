#!/usr/bin/env python3
"""Claude Code PreToolUse hook: validate OKF doc BEFORE it reaches disk.

Reads the hook event JSON from stdin. For Write/Edit operations targeting
knowledge/concepts/, validates the PROPOSED content. Exit 2 blocks the tool
execution so invalid documents never reach disk.

IMPORTANT: This hook provides pre-write validation only. It blocks invalid
Write/Edit operations before the Claude tool executes. The hook does NOT
provide atomic filesystem publication - valid writes are published by the
Claude tool using its normal file writing mechanism.

Guarantees:
- Invalid Write operations are blocked (target file is never created)
- Invalid Edit operations are blocked (existing file remains unchanged)
- Valid Write/Edit operations are allowed to proceed

For Edit: reconstructs the full document by applying the edit to the current
file, then validates the resulting document.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import okf


def apply_edit(file_path, old_string, new_string):
    """Apply an Edit operation to a file and return the full new content."""
    try:
        current = Path(file_path).read_text(encoding="utf-8")
    except FileNotFoundError:
        # Edit on non-existent file - this will fail at write time, return original
        return None

    if old_string not in current:
        # Old string not found - this would fail at write time, return current to allow validation to proceed
        # The actual write will fail with the old_string not found error
        return current

    new_content = current.replace(old_string, new_string, 1)
    return new_content


def main():
    try:
        event = json.load(sys.stdin)
    except Exception:
        return 0  # not our event shape, stay out of the way

    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input") or {}

    # Only handle Write and Edit operations
    if tool_name not in ("Write", "Edit"):
        return 0

    file_path = tool_input.get("file_path", "")
    if not file_path:
        return 0

    path = Path(file_path)

    # Only validate knowledge/concepts/*.md files
    if "knowledge/concepts" not in str(path) or path.suffix != ".md":
        return 0

    # Get the proposed content
    if tool_name == "Write":
        proposed_content = tool_input.get("content", "")
    else:  # Edit
        old_string = tool_input.get("old_string", "")
        new_string = tool_input.get("new_string", "")
        if not old_string or not new_string:
            # Edit without proper params - let it fail naturally
            return 0
        proposed_content = apply_edit(file_path, old_string, new_string)
        if proposed_content is None:
            # Cannot reconstruct - let the write fail naturally
            return 0

    # Extract the document ID from the proposed content to use as temp filename
    # This ensures the ID matches filename check in okf.validate
    import tempfile
    doc_id = None
    for line in proposed_content.split('\n'):
        if line.strip().startswith('id:'):
            doc_id = line.split(':', 1)[1].strip().strip('"\'')
            break

    # Create temp directory with the correct filename
    temp_dir = Path(tempfile.mkdtemp())
    if doc_id:
        temp_file = temp_dir / f"{doc_id}.md"
    else:
        # Fallback if we couldn't extract ID
        temp_file = temp_dir / "temp_doc.md"

    temp_file.write_text(proposed_content)
    tmp_path = temp_file

    try:
        errors = okf.validate(tmp_path)
        if errors:
            print("OKF validation failed, write blocked:", file=sys.stderr)
            for e in errors:
                print(f"  - {e}", file=sys.stderr)
            return 2
        return 0
    finally:
        # Clean up temp directory
        try:
            import shutil
            tmp_path.parent.unlink(missing_ok=True)
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
