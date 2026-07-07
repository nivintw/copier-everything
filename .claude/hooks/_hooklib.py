"""Shared helpers for the PreToolUse guard hooks (Claude Code hook contract).

Each guard is a standalone module: importable (its functions unit-tested directly, no
`__main__` side effects) and runnable as a `command` hook that reads the PreToolUse JSON
event on stdin and decides allow / deny / fail-open-loud. This module is the thin, shared
I/O + path-resolution layer so the three guards stay consistent.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Tools that write to a file — the only ones any of these guards act on.
FILE_WRITE_TOOLS = frozenset({"Edit", "Write", "MultiEdit"})


def read_event() -> dict:
    """Parse the PreToolUse JSON event from stdin; an empty/invalid payload → {}."""
    try:
        return json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError, ValueError:
        return {}


def edited_path(event: dict) -> str | None:
    """The absolute file_path an Edit/Write/MultiEdit targets, else None (not a file write)."""
    if event.get("tool_name") not in FILE_WRITE_TOOLS:
        return None
    return (event.get("tool_input") or {}).get("file_path")


def project_root(start: Path) -> Path | None:
    """The nearest ancestor of `start` (inclusive) containing a `.git`, else None.

    Root-anchoring on the edited file's own repo — not the session cwd — is what makes the
    guards copier-path aware: an edit to a path inside a generated project resolves its managed
    set against that project's root even when Claude's cwd is elsewhere.
    """
    for directory in (start, *start.parents):
        if (directory / ".git").exists():
            return directory
    return None


def resulting_content(event: dict, file: Path) -> str | None:
    """The file's content AFTER the pending edit, or None if it can't be reconstructed.

    Write carries the whole `content`; Edit/MultiEdit are applied to the current on-disk file
    the same way Claude Code will apply them (first-occurrence replace, or all when replace_all).
    """
    tool_input = event.get("tool_input") or {}
    if "content" in tool_input:  # Write
        return tool_input["content"]
    try:
        current = file.read_text()
    except OSError:
        return None
    if "new_string" in tool_input:  # Edit
        old, new = tool_input.get("old_string", ""), tool_input["new_string"]
        return (
            current.replace(old, new)
            if tool_input.get("replace_all")
            else current.replace(old, new, 1)
        )
    if "edits" in tool_input:  # MultiEdit
        for edit in tool_input["edits"]:
            old, new = edit.get("old_string", ""), edit.get("new_string", "")
            current = (
                current.replace(old, new)
                if edit.get("replace_all")
                else current.replace(old, new, 1)
            )
        return current
    return None


def allow() -> None:
    """Permit the tool call (no output is the default-allow contract)."""
    sys.exit(0)


def deny(reason: str) -> None:
    """Block the tool call, surfacing `reason` to Claude."""
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )
    sys.exit(0)


def warn_allow(message: str) -> None:
    """Fail OPEN but loudly: permit the call while surfacing a warning — never silently allow.

    Used when a guard can't establish the fact it needs to make a safe decision (e.g. the
    canonical version can't be resolved). Blocking on uncertainty would trap legitimate work;
    a silent allow would defeat the guard — so allow, but say so.
    """
    print(json.dumps({"systemMessage": message}))
    print(message, file=sys.stderr)
    sys.exit(0)
