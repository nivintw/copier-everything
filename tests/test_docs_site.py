# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""Presence/absence invariants for the include_docs_site module.

render-matrix.sh renders tests/answers/no-docs-site.yml and runs the full gate on it, but
gate-passes-cleanly is not the same as "the docs scaffold is actually absent" — a regression
that rendered mkdocs.yml/docs/ even with the flag off would still pass reuse/hawkeye/prek.
These tests assert presence and absence directly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    import pytest


def test_docs_site_files_present_by_default(
    template_dir: Path,
    output_dir_module_scope: Path,
    render_template: Callable[..., Path],
) -> None:
    """include_docs_site defaults true — a plain render gets the full scaffold."""
    project_dir = render_template(
        template_dir,
        output_dir_module_scope,
        data={"project_name": "Docs Site On"},
        skip_tasks=True,
    )
    assert (project_dir / "mkdocs.yml").is_file()
    assert (project_dir / "docs" / "index.md").is_file()
    assert (project_dir / "docs" / "assets" / "favicon.svg").is_file()
    assert (project_dir / ".github" / "workflows" / "docs.yml").is_file()


def test_docs_site_files_absent_when_disabled(
    template_dir: Path,
    tmp_path_factory: pytest.TempPathFactory,
    render_template: Callable[..., Path],
) -> None:
    """include_docs_site: false must scaffold none of the docs-site files."""
    project_dir = render_template(
        template_dir,
        tmp_path_factory.mktemp("rendered_no_docs_site"),
        data={"project_name": "Docs Site Off", "include_docs_site": False},
        skip_tasks=True,
    )
    assert not (project_dir / "mkdocs.yml").exists()
    assert not (project_dir / "docs").exists()
    assert not (project_dir / ".github" / "workflows" / "docs.yml").exists()
