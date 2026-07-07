# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""Generic test harness for the PreToolUse guard hooks under `.claude/hooks/`.

Two ways to drive a guard, both exercised by the per-guard test modules:

- ``run_hook`` spawns the guard as a real SUBPROCESS, feeding the PreToolUse event as stdin
  JSON and parsing stdout exactly the way Claude Code does — so the full stdin/stdout contract
  (the `deny` payload, the `systemMessage` fail-open, the silent default-allow) is under test.
- ``import_hook`` imports the guard module in-process (its `main()` is `__main__`-guarded, so
  importing has no side effects) so its pure `decide()` and helpers can be unit-tested directly.

This is a helper module, not a test module (no `test_` prefix), so pytest imports it but never
collects it.
"""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import ModuleType

# `.claude/hooks/` resolved from the repo root (the parent of this `tests/` dir).
HOOKS_DIR = Path(__file__).resolve().parent.parent / ".claude" / "hooks"


@dataclass(frozen=True)
class Decision:
    """A guard's classified outcome: `outcome` is allow/deny/warn, with its message."""

    outcome: str
    message: str = ""


def _git_root(start: Path) -> Path | None:
    """The nearest ancestor of `start` (inclusive) holding a `.git`, like the guards' anchor."""
    for directory in (start, *start.parents):
        if (directory / ".git").exists():
            return directory
    return None


def _classify(stdout: str) -> Decision:
    """Map a guard's stdout to a Decision the same way Claude Code interprets the hook contract."""
    text = stdout.strip()
    if not text:  # no output == default-allow
        return Decision("allow")
    payload = json.loads(text)
    hook_specific = payload.get("hookSpecificOutput") or {}
    if hook_specific.get("permissionDecision") == "deny":
        return Decision("deny", hook_specific.get("permissionDecisionReason", ""))
    if "systemMessage" in payload:  # fail-open-loud (warn_allow)
        return Decision("warn", payload["systemMessage"])
    return Decision("allow")


def run_hook(hook_name: str, event: dict, cwd: str | Path | None = None) -> Decision:
    """Run guard `hook_name` as a subprocess against `event`, returning the classified Decision.

    `cwd` defaults to the git root of the event's target file (falling back to the file's own
    directory), so the child runs anchored in the repo the edit targets — exactly like Claude
    Code invoking the hook from the session's working tree.
    """
    if cwd is None:
        target = (event.get("tool_input") or {}).get("file_path")
        if target:
            parent = Path(target).resolve().parent
            cwd = _git_root(parent) or parent
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(HOOKS_DIR / f"{hook_name}.py")],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        cwd=None if cwd is None else str(cwd),
        check=False,
    )
    return _classify(result.stdout)


def import_hook(hook_name: str) -> ModuleType:
    """Import guard `hook_name` in-process (no `__main__` side effects) for direct `decide()` tests.

    `.claude/hooks/` is put on `sys.path` so the module's `from _hooklib import ...` resolves; the
    module is imported by bare name (not a package path), matching how it's run as a script.
    """
    hooks_dir = str(HOOKS_DIR)
    if hooks_dir not in sys.path:
        sys.path.insert(0, hooks_dir)
    return importlib.import_module(hook_name)


def write_event(file_path: str | Path, content: str) -> dict:
    """A PreToolUse event for a Write of `content` to `file_path`."""
    return {"tool_name": "Write", "tool_input": {"file_path": str(file_path), "content": content}}


def edit_event(
    file_path: str | Path, old_string: str, new_string: str, *, replace_all: bool = False
) -> dict:
    """A PreToolUse event for an Edit replacing `old_string` with `new_string` in `file_path`."""
    tool_input: dict = {
        "file_path": str(file_path),
        "old_string": old_string,
        "new_string": new_string,
    }
    if replace_all:
        tool_input["replace_all"] = True
    return {"tool_name": "Edit", "tool_input": tool_input}


def multiedit_event(file_path: str | Path, edits: list[tuple[str, str]]) -> dict:
    """A PreToolUse event for a MultiEdit applying `(old, new)` pairs in order to `file_path`."""
    return {
        "tool_name": "MultiEdit",
        "tool_input": {
            "file_path": str(file_path),
            "edits": [{"old_string": old, "new_string": new} for old, new in edits],
        },
    }
