# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""guard_config_drift: warn on twin drift, block language-agnostic config in pyproject.toml.

Each case is driven through BOTH harness modes — the real subprocess (`run_hook`) and the
in-process `decide()` (`import_hook`). Plus an acceptance test that the guard's WATCHED twin set
is exactly `tests/test_synced_files.py`'s sync buckets, so the two can't silently drift apart.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from hook_harness import edit_event, import_hook, run_hook, write_event

if TYPE_CHECKING:
    from pathlib import Path

HOOK = "guard_config_drift"


def _repo(tmp_path: Path, *, with_template: bool) -> Path:
    """A repo marker; `with_template` adds the `template/` dir that turns twin-drift warnings on."""
    root = tmp_path / "repo"
    (root / ".git").mkdir(parents=True)
    if with_template:
        (root / "template").mkdir()
    return root


@pytest.fixture
def dogfood_repo(tmp_path: Path) -> Path:
    """A repo that HAS a `template/` dir — copier-everything's own dogfood shape."""
    return _repo(tmp_path, with_template=True)


@pytest.fixture
def plain_repo(tmp_path: Path) -> Path:
    """A generated-project shape: no `template/` dir, so behavior-1 (twin drift) is off."""
    return _repo(tmp_path, with_template=False)


def _decide(event: dict) -> tuple[str, str]:
    return import_hook(HOOK).decide(event)


def test_editing_a_watched_twin_warns(dogfood_repo: Path) -> None:
    """Touching a watched twin in the dogfood repo warns, naming its partner, both modes."""
    twin = dogfood_repo / ".config" / "rumdl.toml"
    twin.parent.mkdir()
    event = edit_event(twin, "old", "new")

    subprocess_decision = run_hook(HOOK, event)
    assert subprocess_decision.outcome == "warn"
    assert "twin" in subprocess_decision.message
    assert "template/.config/rumdl.toml" in subprocess_decision.message

    action, message = _decide(event)
    assert action == "warn_allow"
    assert "template/.config/rumdl.toml" in message


def test_twin_without_template_dir_is_allowed(plain_repo: Path) -> None:
    """The same twin in a repo with NO `template/` dir is a plain file — allowed, both modes."""
    twin = plain_repo / ".config" / "rumdl.toml"
    twin.parent.mkdir()
    event = edit_event(twin, "old", "new")

    assert run_hook(HOOK, event).outcome == "allow"
    assert _decide(event) == ("allow", "")


def test_banned_table_in_root_pyproject_is_denied(plain_repo: Path) -> None:
    """Writing a language-agnostic `[tool.typos]` into root pyproject.toml is blocked, both."""
    pyproject = plain_repo / "pyproject.toml"
    event = write_event(pyproject, '[tool.typos]\nfoo = "bar"\n')

    subprocess_decision = run_hook(HOOK, event)
    assert subprocess_decision.outcome == "deny"
    assert ".config/typos.toml" in subprocess_decision.message

    action, message = _decide(event)
    assert action == "deny"
    assert ".config/typos.toml" in message


def test_ordinary_pyproject_edit_is_allowed(plain_repo: Path) -> None:
    """An edit to root pyproject.toml with no banned table is allowed (no `template/`), both."""
    pyproject = plain_repo / "pyproject.toml"
    pyproject.write_text("[tool.ruff]\nline-length = 100\n")
    event = edit_event(pyproject, "line-length = 100", "line-length = 88")

    assert run_hook(HOOK, event).outcome == "allow"
    assert _decide(event) == ("allow", "")


def test_watched_set_equals_synced_files_buckets() -> None:
    """Acceptance: WATCHED == test_synced_files' TRIVIALLY_EQUAL | STRUCTURALLY_TESTED.

    WATCHED is meant to be derived from the actual twin set the dogfooding sync tests assert; this
    pins them equal so neither can grow a file the other doesn't know about without failing here.
    """
    import test_synced_files  # noqa: PLC0415 - imported here to compare against the live buckets

    watched = import_hook(HOOK).WATCHED
    assert set(watched) == test_synced_files.TRIVIALLY_EQUAL | test_synced_files.STRUCTURALLY_TESTED
