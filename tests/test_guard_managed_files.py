# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""guard_managed_files: block hand-edits to tool-owned files at the project root.

Each case is driven through BOTH harness modes — the real subprocess (`run_hook`) and the
in-process `decide()` (`import_hook`). This guard only ever allows or denies (no warn path).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from hook_harness import edit_event, import_hook, run_hook

if TYPE_CHECKING:
    from pathlib import Path

HOOK = "guard_managed_files"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A repo marker (a bare `.git` dir is all `project_root` needs to anchor)."""
    root = tmp_path / "repo"
    (root / ".git").mkdir(parents=True)
    return root


def _decide(event: dict) -> tuple[str, str]:
    return import_hook(HOOK).decide(event)


def _edit(path: Path) -> dict:
    return edit_event(path, "old", "new")


@pytest.mark.parametrize(
    "relative",
    ["uv.lock", "CHANGELOG.md", ".copier-answers.yml", "LICENSES/MIT.txt", "UV.LOCK"],
)
def test_managed_root_files_are_denied(repo: Path, relative: str) -> None:
    """The tool-owned root files (case-insensitively) are blocked from a hand-edit, both modes."""
    event = _edit(repo / relative)

    subprocess_decision = run_hook(HOOK, event)
    assert subprocess_decision.outcome == "deny"
    assert "owned by" in subprocess_decision.message

    action, _message = _decide(event)
    assert action == "deny"


def test_non_root_changelog_is_allowed(repo: Path) -> None:
    """A `docs/CHANGELOG.md` is user prose, not release-please's root file — allowed, both modes."""
    event = _edit(repo / "docs" / "CHANGELOG.md")

    assert run_hook(HOOK, event).outcome == "allow"
    assert _decide(event) == ("allow", "")


def test_ordinary_file_is_allowed(repo: Path) -> None:
    """A normal source file is untouched by the guard, both modes."""
    event = _edit(repo / "src" / "app.py")

    assert run_hook(HOOK, event).outcome == "allow"
    assert _decide(event) == ("allow", "")


def test_file_outside_any_git_repo_is_allowed(tmp_path: Path) -> None:
    """With no `.git` ancestor there is no project to anchor to, so the guard allows, both modes."""
    orphan = tmp_path / "orphan" / "uv.lock"  # a managed *name*, but under no repo root
    orphan.parent.mkdir(parents=True)
    event = _edit(orphan)

    assert run_hook(HOOK, event).outcome == "allow"
    assert _decide(event) == ("allow", "")
