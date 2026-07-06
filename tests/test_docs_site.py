# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""Presence/absence invariants for the include_docs_site module.

render-matrix.sh renders tests/answers/no-docs-site.yml and runs the full gate on it, but
gate-passes-cleanly is not the same as "the docs scaffold is actually absent" — a regression
that rendered mkdocs.yml/docs/ even with the flag off would still pass reuse/hawkeye/prek.
These tests assert presence and absence directly.
"""

from __future__ import annotations

import tomllib
from typing import TYPE_CHECKING

import yaml
from conftest import on_key

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
    workflow = project_dir / ".github" / "workflows" / "docs.yml"
    assert workflow.is_file()
    workflow_yaml = yaml.safe_load(workflow.read_text())
    push_trigger = on_key(workflow_yaml)["push"]
    assert push_trigger["branches"] == ["main"]
    assert push_trigger["paths"] == ["docs/**", "mkdocs.yml"]

    mkdocs_yaml = yaml.safe_load((project_dir / "mkdocs.yml").read_text())
    # docs/superpowers/** holds dev-only brainstorming specs, never site content — must be
    # excluded or `mkdocs build --strict` fails on any repo that has that convention's files.
    assert mkdocs_yaml["exclude_docs"] == ["superpowers/"]
    # asciinema-player assets aren't vendored by default — wiring extra_css/extra_javascript
    # unconditionally 404s every page until a repo actually embeds its first cast.
    assert "extra_css" not in mkdocs_yaml
    assert "extra_javascript" not in mkdocs_yaml

    # The docs design deliberately relies on raw HTML in Markdown (castify cast embeds,
    # version-badge spans) — MD033 must be off or the lint gate fails on either pattern.
    rumdl_toml = tomllib.loads((project_dir / ".config" / "rumdl.toml").read_text())
    assert "MD033" in rumdl_toml["global"]["disable"]


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

    # rumdl.toml is always scaffolded regardless of include_docs_site — but a repo with no
    # docs site has no reason to relax MD033 and should keep the stricter default.
    rumdl_toml = tomllib.loads((project_dir / ".config" / "rumdl.toml").read_text())
    assert "MD033" not in rumdl_toml["global"]["disable"]
