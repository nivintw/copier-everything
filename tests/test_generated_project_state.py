# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""Validate a generated project's state after the post-copy tasks run.

This is the one thing tests/render-matrix.sh deliberately does NOT cover: render-matrix renders
every shape with --skip-tasks and runs the quality gate on the result, but it never exercises
copier.yml's `_tasks` (git init → uv sync → scaffold commit → prek install). These tests render
WITH tasks once and assert the outcome a real `copier copy --trust` produces.

Scope is intentionally limited to the task outcomes. The quality gate itself (reuse, hawkeye,
taplo, prek, ruff, ty, pytest on the rendered tree) is render-matrix.sh's job and is not
duplicated here.
"""

from __future__ import annotations

import shutil
import subprocess
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


@pytest.fixture(scope="module")
def generated_project_dir(
    template_dir: Path,
    output_dir_module_scope: Path,
    render_template: Callable[..., Path],
) -> Path:
    """Render the default shape WITH post-copy tasks (git init, uv sync, commit, prek install)."""
    return render_template(
        template_dir,
        output_dir_module_scope,
        data={"project_name": "post-copy-tasks-test"},
        skip_tasks=False,
    )


def test_no_dirty_local_changes(generated_project_dir: Path) -> None:
    """The scaffold commit leaves a clean tree.

    This is a load-bearing single assertion: it proves a git repo was initialized, uv sync's
    uv.lock was staged and committed, and the scaffold commit succeeded (the commit runs before
    `prek install`, so the no-commit-to-branch hook can't block it) — all with nothing left
    uncommitted.
    """
    git = shutil.which("git")
    assert git is not None, "git not found on PATH"
    result = subprocess.run(  # noqa: S603
        [git, "status", "--porcelain"],
        cwd=generated_project_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "", (
        f"generated project has uncommitted changes after scaffold:\n{result.stdout}"
    )


def test_venv_and_lock_created(generated_project_dir: Path) -> None:
    """The uv sync task created a virtual environment and a committed uv.lock."""
    pyvenv_cfg = generated_project_dir / ".venv" / "pyvenv.cfg"
    assert pyvenv_cfg.is_file(), ".venv/pyvenv.cfg not found — uv sync task did not run"
    assert (generated_project_dir / "uv.lock").is_file(), "uv.lock not created by uv sync task"


def test_git_hooks_installed(generated_project_dir: Path) -> None:
    """The prek install task wired up the configured hook types (pre-commit, commit-msg)."""
    hooks_dir = generated_project_dir / ".git" / "hooks"
    # default_install_hook_types in the template's .pre-commit-config.yaml.
    for hook in ("pre-commit", "commit-msg"):
        assert (hooks_dir / hook).is_file(), f"{hook} hook was not installed by prek install"
