# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""pinned_value() and pinned_value_at_base() must fail loudly on a genuine read error
instead of masking it as "no pin found".

A typo'd file argument used to silently resolve to an empty match (grep's exit 1 "no match"
and exit >=2 "read error" were both swallowed by `2>/dev/null ... || true`), so the only
backstop was the end-of-run `processed -eq 0` check — which doesn't trip if at least one
*other* argument in the same invocation legitimately has pins. `pinned_value_at_base()` had
the same class of gap one layer up: a `git cat-file -e` failure other than "path absent at
BASE_REF" (a corrupted object, a partial clone's missing blob), and a `git show` failure
downstream of a passing `cat-file -e`, were both swallowed too.
"""

from __future__ import annotations

import functools
import subprocess
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path


def test_pinned_value_fails_loudly_on_missing_file(template_dir: Path) -> None:
    """A typo'd file argument must exit loudly, not silently resolve to empty."""
    script = template_dir / "scripts" / "refresh-binary-checksums.sh"
    result = subprocess.run(  # noqa: S603
        ["bash", str(script), "some/typo/path.yml"],  # noqa: S607
        cwd=template_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "no such file: some/typo/path.yml" in result.stderr


def _extract_shell_function(script: Path, name: str) -> str:
    """Pull one top-level shell function's source out of the script for isolated testing.

    `pinned_value_at_base()` is only reachable through the full refresh run (which needs
    network access to fetch upstream checksums), so it's exercised directly here instead —
    sourced in isolation and called with controlled git-repo/object-store states.
    """
    lines = script.read_text().splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith(f"{name}() {{"))
    end = next(i for i in range(start, len(lines)) if lines[i] == "}")
    return "\n".join(lines[start : end + 1])


def _run_pinned_value_at_base(
    script: Path, repo: Path, *, var: str, file: str, base_ref: str
) -> subprocess.CompletedProcess[str]:
    # pinned_value_at_base() calls the shared _extract_pinned_value() helper — both must be
    # sourced, or a success-path call would fail with "command not found", not a real defect.
    fn = "\n".join(
        _extract_shell_function(script, name) for name in ("_extract_pinned_value", "pinned_value_at_base")
    )
    result = subprocess.run(  # noqa: S603
        ["bash", "-c", f"{fn}\npinned_value_at_base \"$1\" \"$2\" \"$3\"", "bash", var, file, base_ref],  # noqa: S607
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    return result


@pytest.fixture
def git_repo_with_pin(tmp_path: Path) -> Path:
    """A one-commit git repo with a pinned-version file, for pinned_value_at_base() tests."""
    repo = tmp_path / "repo"
    repo.mkdir()
    run = functools.partial(subprocess.run, cwd=repo, check=True)  # noqa: S603
    run(["git", "init", "-q"])  # noqa: S607
    run(["git", "config", "user.email", "test@example.com"])  # noqa: S607
    run(["git", "config", "user.name", "test"])  # noqa: S607
    (repo / "pinned.yml").write_text('TRIVY_VERSION: "1.2.3"\n')
    run(["git", "add", "."])  # noqa: S607
    run(["git", "commit", "-q", "-m", "init"])  # noqa: S607
    return repo


def test_pinned_value_at_base_returns_value_when_present(template_dir: Path, git_repo_with_pin: Path) -> None:
    """The success path: a value pinned at BASE_REF is extracted correctly.

    The three failure-path tests below never reach _extract_pinned_value(), so without
    this one a regression in the shared helper (or its wiring into pinned_value_at_base)
    would go uncaught.
    """
    script = template_dir / "scripts" / "refresh-binary-checksums.sh"
    result = _run_pinned_value_at_base(script, git_repo_with_pin, var="TRIVY_VERSION", file="pinned.yml", base_ref="HEAD")
    assert result.returncode == 0
    assert result.stdout.strip() == "1.2.3"
    assert result.stderr == ""


def test_pinned_value_at_base_returns_empty_when_path_never_existed(
    template_dir: Path, git_repo_with_pin: Path
) -> None:
    """A path absent from both the working tree and BASE_REF: one of git's two distinct
    "absent" messages (see the on-disk variant below) — also a legitimate empty case."""
    script = template_dir / "scripts" / "refresh-binary-checksums.sh"
    result = _run_pinned_value_at_base(script, git_repo_with_pin, var="TRIVY_VERSION", file="nope.yml", base_ref="HEAD")
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_pinned_value_at_base_returns_empty_when_path_new_on_disk_since_base(
    template_dir: Path, git_repo_with_pin: Path
) -> None:
    """The actual production scenario: a workflow file introduced since BASE_REF exists on
    disk (the caller's `[ -f "$f" ]` guard already confirmed that) but not at BASE_REF.

    git picks a DIFFERENT message ("exists on disk, but not in") than when the path is
    absent everywhere ("does not exist in", covered above) — this is the message variant
    pinned_value_at_base() actually hits in real use, and a fix that only matches the other
    one silently regresses this exact legitimate case.
    """
    script = template_dir / "scripts" / "refresh-binary-checksums.sh"
    (git_repo_with_pin / "new-since-base.yml").write_text('TRIVY_VERSION: "9.9.9"\n')
    result = _run_pinned_value_at_base(
        script, git_repo_with_pin, var="TRIVY_VERSION", file="new-since-base.yml", base_ref="HEAD"
    )
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""
    assert result.stderr == ""


def test_pinned_value_at_base_fails_loudly_on_missing_blob(template_dir: Path, git_repo_with_pin: Path) -> None:
    """A blob absent from the object store (corrupted DB, partial clone) must error loudly,
    not be folded into the "path absent at base" empty case — the gap #191 fixed."""
    script = template_dir / "scripts" / "refresh-binary-checksums.sh"
    blob = subprocess.run(  # noqa: S603
        ["git", "rev-parse", "HEAD:pinned.yml"],  # noqa: S607
        cwd=git_repo_with_pin,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    obj_path = git_repo_with_pin / ".git" / "objects" / blob[:2] / blob[2:]
    backup_path = obj_path.with_name(obj_path.name + ".bak")
    obj_path.rename(backup_path)
    try:
        result = _run_pinned_value_at_base(script, git_repo_with_pin, var="TRIVY_VERSION", file="pinned.yml", base_ref="HEAD")
    finally:
        backup_path.rename(obj_path)
    assert result.returncode == 1
    assert "ERROR: pinned_value_at_base" in result.stderr


def test_pinned_value_at_base_does_not_swallow_a_show_failure(template_dir: Path, git_repo_with_pin: Path) -> None:
    """The #193 gap: a trailing `|| true` on the whole show|grep|head|sed pipeline used to
    swallow any downstream failure, not just grep's legitimate "no match". A loose object
    with valid existence but corrupt (non-zlib) content makes `git cat-file -e` pass but
    `git show` fail — exactly the failure the old trailing `|| true` masked."""
    script = template_dir / "scripts" / "refresh-binary-checksums.sh"
    blob = subprocess.run(  # noqa: S603
        ["git", "rev-parse", "HEAD:pinned.yml"],  # noqa: S607
        cwd=git_repo_with_pin,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    obj_path = git_repo_with_pin / ".git" / "objects" / blob[:2] / blob[2:]
    obj_path.chmod(0o644)
    obj_path.write_bytes(b"not a valid zlib-compressed git object")
    result = _run_pinned_value_at_base(script, git_repo_with_pin, var="TRIVY_VERSION", file="pinned.yml", base_ref="HEAD")
    assert result.returncode == 1
    assert "ERROR: pinned_value_at_base: git show" in result.stderr
