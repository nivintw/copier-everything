# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""Pytest fixtures for the template-rendering tests.

These render copier-everything from `tests/render`-style temp dirs and let the sync and
generated-project-state tests assert against the output. `template_dir` is the repo root
(where copier.yml lives); copier reads `_subdirectory: template` from there.
"""

import subprocess
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def template_dir() -> Path:
    """Path to the template repo root (the directory holding copier.yml)."""
    return Path(__file__).parent.parent


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    """A fresh temporary output directory for a single test."""
    return tmp_path / "rendered_template"


@pytest.fixture(scope="module")
def output_dir_module_scope(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A module-scoped temporary output directory (render once, reuse across a module)."""
    return tmp_path_factory.mktemp("rendered_template_module_scope")


@pytest.fixture
def initialized_git_repo_output_dir(output_dir: Path) -> Path:
    """An output directory with a git identity configured (for post-copy task tests)."""
    output_dir.mkdir(parents=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"],  # noqa: S607
        check=True,
        cwd=output_dir,
    )
    subprocess.run(
        ["git", "config", "user.email", "testuser@example.com"],  # noqa: S607
        check=True,
        cwd=output_dir,
    )
    return output_dir
