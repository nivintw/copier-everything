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
import tomllib
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


@pytest.fixture(scope="module")
def pkg_unpublished_project_dir(
    template_dir: Path,
    tmp_path_factory: pytest.TempPathFactory,
    render_template: Callable[..., Path],
) -> Path:
    """Render python_source=true, is_package=false WITH tasks, so uv sync actually installs it.

    This is the shape __init__.py.jinja's version-lookup condition must branch correctly on
    (see tests/answers/pkg-unpublished.yml's own comment: "the key autonomous assumption").
    Uses its own output dir — output_dir_module_scope is already claimed by
    generated_project_dir above, and both fixtures render different data into the same module.
    """
    return render_template(
        template_dir,
        tmp_path_factory.mktemp("rendered_pkg_unpublished"),
        data={
            "project_name": "Pkg Unpublished",
            "project_description": "installed but not published",
            "test_frameworks": ["pytest"],
            "contains_python": True,
            "python_source": True,
            "is_package": False,
        },
        skip_tasks=False,
    )


def test_version_lookup_reads_installed_metadata(pkg_unpublished_project_dir: Path) -> None:
    """Verify __version__ is read from installed package metadata, not hardcoded.

    python_source=true installs a real distribution even when is_package=false, so __version__
    must come from the installed metadata, not __init__.py.jinja's hand-edited "0.0.0"
    placeholder for source layouts that aren't installed.

    A regression to the wrong branch condition (is_package instead of python_source) renders
    the placeholder branch instead — which ALSO produces the string "0.0.0" today (the
    project's own starting version), so neither a bare ``isinstance(__version__, str)`` smoke
    test nor a same-value check would catch it. Asserting the source actually took the
    importlib.metadata branch is what makes this test discriminate the two.
    """
    src_dirs = [p for p in (pkg_unpublished_project_dir / "src").iterdir() if p.is_dir()]
    assert len(src_dirs) == 1, f"expected exactly one src/ package, found {src_dirs}"
    package_name = src_dirs[0].name

    init_py = pkg_unpublished_project_dir / "src" / package_name / "__init__.py"
    assert "importlib.metadata" in init_py.read_text(), (
        "__init__.py didn't take the importlib.metadata branch — check __init__.py.jinja's "
        "top-level condition is python_source, not is_package"
    )

    pyproject = tomllib.loads((pkg_unpublished_project_dir / "pyproject.toml").read_text())
    dist_name = pyproject["project"]["name"]

    uv = shutil.which("uv")
    assert uv is not None, "uv not found on PATH"
    result = subprocess.run(  # noqa: S603
        [
            uv,
            "run",
            "python",
            "-c",
            f"import importlib.metadata as m; from {package_name} import __version__ as v; "
            f"assert v == m.version({dist_name!r}), (v, m.version({dist_name!r}))",
        ],
        cwd=pkg_unpublished_project_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"__version__ doesn't match importlib.metadata.version() — {result.stderr}"
    )
