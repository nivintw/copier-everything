# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""Pytest fixtures for the template-rendering tests.

`template_dir` is the repo root (where copier.yml lives); copier reads `_subdirectory:
template` from there. `render_template` is the shared render helper both test modules use.
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

import pytest
from copier import run_copy
from copier.errors import DirtyLocalWarning

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


@pytest.fixture(scope="session")
def template_dir() -> Path:
    """Path to the template repo root (the directory holding copier.yml)."""
    from pathlib import Path  # noqa: PLC0415

    return Path(__file__).parent.parent


@pytest.fixture(scope="module")
def output_dir_module_scope(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A module-scoped temporary output directory (render once, reuse across a module)."""
    return tmp_path_factory.mktemp("rendered_template_module_scope")


@pytest.fixture(scope="session")
def render_template() -> Callable[..., Path]:
    """Return a helper that renders the template into a directory and returns that directory.

    Renders from HEAD (committed state) — run on a clean tree, as CI does. The
    DirtyLocalWarning that copier emits on a dirty source tree is suppressed (not asserted),
    so a dirty working tree doesn't error the render, it just renders the committed state.
    """

    def _render(template_dir: Path, output_dir: Path, *, data: dict, skip_tasks: bool) -> Path:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=DirtyLocalWarning)
            run_copy(
                str(template_dir),
                str(output_dir),
                data=data,
                defaults=True,
                unsafe=True,
                vcs_ref="HEAD",
                skip_tasks=skip_tasks,
            )
        return output_dir

    return _render
