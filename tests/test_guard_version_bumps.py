# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""guard_version_bumps: block a hand-edit that moves a version carrier off canonical.

Each case is driven through BOTH harness modes — the real subprocess (`run_hook`, the stdin/
stdout contract) and the in-process `decide()` (`import_hook`) — so the pure decision and its
wiring into the hook contract are both covered. `decide()` returns the raw action
(`allow`/`deny`/`warn_allow`); `run_hook` returns the classified outcome (`allow`/`deny`/`warn`).
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest
from hook_harness import edit_event, import_hook, run_hook, write_event

if TYPE_CHECKING:
    from pathlib import Path

CANONICAL = "1.11.2"
HOOK = "guard_version_bumps"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A single-package repo: manifest pinned to CANONICAL, pyproject.toml a version carrier."""
    root = tmp_path / "repo"
    (root / ".git").mkdir(parents=True)  # only the marker is needed; project_root just checks it
    config = root / ".config"
    config.mkdir()
    (config / ".release-please-manifest.json").write_text(json.dumps({".": CANONICAL}))
    (config / "release-please-config.json").write_text(
        json.dumps({"packages": {".": {"extra-files": ["pyproject.toml"]}}})
    )
    (root / "pyproject.toml").write_text(f'[project]\nname = "demo"\nversion = "{CANONICAL}"\n')
    return root


def _decide(event: dict) -> tuple[str, str]:
    return import_hook(HOOK).decide(event)


def test_edit_to_different_version_is_denied(repo: Path) -> None:
    """An Edit that moves pyproject.toml's version off canonical is blocked, both modes."""
    pyproject = repo / "pyproject.toml"
    event = edit_event(pyproject, f'version = "{CANONICAL}"', 'version = "2.0.0"')

    subprocess_decision = run_hook(HOOK, event)
    assert subprocess_decision.outcome == "deny"
    assert "2.0.0" in subprocess_decision.message
    assert CANONICAL in subprocess_decision.message

    action, message = _decide(event)
    assert action == "deny"
    assert "2.0.0" in message


def test_write_to_different_version_is_denied(repo: Path) -> None:
    """A Write of a whole pyproject.toml carrying a non-canonical version is blocked, both modes."""
    pyproject = repo / "pyproject.toml"
    event = write_event(pyproject, '[project]\nname = "demo"\nversion = "9.9.9"\n')

    assert run_hook(HOOK, event).outcome == "deny"
    assert run_hook(HOOK, event).message.count("9.9.9") >= 1

    action, message = _decide(event)
    assert action == "deny"
    assert "9.9.9" in message


def test_rewriting_the_same_value_is_allowed(repo: Path) -> None:
    """Rewriting the identical canonical version is a no-op the guard permits, both modes."""
    pyproject = repo / "pyproject.toml"
    event = edit_event(pyproject, f'version = "{CANONICAL}"', f'version = "{CANONICAL}"')

    assert run_hook(HOOK, event).outcome == "allow"
    assert _decide(event) == ("allow", "")


def test_editing_a_non_carrier_file_is_allowed(repo: Path) -> None:
    """A file release-please doesn't own (README.md here) isn't the guard's concern, both modes."""
    readme = repo / "README.md"
    readme.write_text('# Demo\n\nversion = "5.5.5"\n')
    event = edit_event(readme, 'version = "5.5.5"', 'version = "6.6.6"')

    assert run_hook(HOOK, event).outcome == "allow"
    assert _decide(event) == ("allow", "")


def test_broken_manifest_fails_open_with_a_warning(repo: Path) -> None:
    """A carrier edit with an unresolvable canonical version fails OPEN loudly, both modes."""
    (repo / ".config" / ".release-please-manifest.json").write_text("{ this is not json")
    pyproject = repo / "pyproject.toml"
    event = edit_event(pyproject, f'version = "{CANONICAL}"', 'version = "2.0.0"')

    subprocess_decision = run_hook(HOOK, event)
    assert subprocess_decision.outcome == "warn"
    assert "can't resolve the canonical" in subprocess_decision.message

    action, message = _decide(event)
    assert action == "warn_allow"
    assert "can't resolve the canonical" in message


@pytest.fixture
def multi_package_repo(tmp_path: Path) -> Path:
    """A multi-package (monorepo) repo: the manifest carries several packages' versions."""
    root = tmp_path / "monorepo"
    (root / ".git").mkdir(parents=True)
    config = root / ".config"
    config.mkdir()
    (config / ".release-please-manifest.json").write_text(
        json.dumps({"packages/api": "1.4.0", "packages/cli": "2.1.0"})
    )
    (config / "release-please-config.json").write_text(
        json.dumps({"packages": {"packages/api": {}, "packages/cli": {}}})
    )
    return root


def test_multi_package_manifest_bump_is_denied(multi_package_repo: Path) -> None:
    """A hand-edit changing ONE package's version in a multi-package manifest is denied.

    The guard compares the whole manifest dict, so it covers a monorepo manifest (many non-`.`
    keys) — not just a single `.` package where an earlier version resolved a lone canonical.
    """
    manifest = multi_package_repo / ".config" / ".release-please-manifest.json"
    event = write_event(manifest, json.dumps({"packages/api": "9.9.9", "packages/cli": "2.1.0"}))

    assert run_hook(HOOK, event).outcome == "deny"
    assert "packages/api" in run_hook(HOOK, event).message
    assert _decide(event)[0] == "deny"


def test_multi_package_manifest_identical_rewrite_is_allowed(multi_package_repo: Path) -> None:
    """Rewriting the multi-package manifest with the same versions is allowed."""
    manifest = multi_package_repo / ".config" / ".release-please-manifest.json"
    event = write_event(manifest, json.dumps({"packages/api": "1.4.0", "packages/cli": "2.1.0"}))
    assert run_hook(HOOK, event).outcome == "allow"
