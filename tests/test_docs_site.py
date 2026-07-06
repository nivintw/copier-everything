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

from conftest import mkdocs_extension_names, on_key, tolerant_yaml_load

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
    assert (project_dir / "overrides" / "404.html").is_file()
    workflow = project_dir / ".github" / "workflows" / "docs.yml"
    assert workflow.is_file()
    workflow_yaml = tolerant_yaml_load(workflow.read_text())
    push_trigger = on_key(workflow_yaml)["push"]
    assert push_trigger["branches"] == ["main"]
    assert push_trigger["paths"] == ["docs/**", "mkdocs.yml"]

    mkdocs_yaml = tolerant_yaml_load((project_dir / "mkdocs.yml").read_text())
    # docs/superpowers/** holds dev-only brainstorming specs, never site content — must be
    # excluded or `mkdocs build --strict` fails on any repo that has that convention's files.
    # exclude_docs is mkdocs' PathSpec option: a gitignore-style multiline STRING, not a
    # YAML list (a list is a config error mkdocs rejects outright — see mkdocs.yml.jinja).
    assert mkdocs_yaml["exclude_docs"] == "superpowers/\nincludes/\n"
    # asciinema-player assets aren't vendored by default — wiring extra_css/extra_javascript
    # unconditionally 404s every page until a repo actually embeds its first cast.
    assert "extra_css" not in mkdocs_yaml
    assert "extra_javascript" not in mkdocs_yaml

    # Fleet-general theme/markdown_extensions baseline folded in from nivintw-claude-skills
    # (nivintw/copier-everything#178) — every include_docs_site adopter gets these by default.
    assert mkdocs_yaml["edit_uri"] == "edit/main/docs/"
    assert mkdocs_yaml["theme"]["custom_dir"] == "overrides"
    expected_features = {
        "content.code.copy",
        "navigation.instant",
        "navigation.instant.progress",
        "navigation.tracking",
        "navigation.top",
        "toc.follow",
        "search.suggest",
        "search.highlight",
        "search.share",
        "content.action.edit",
        "content.tooltips",
    }
    assert expected_features.issubset(set(mkdocs_yaml["theme"]["features"]))
    # Repo-specific extras (e.g. content.tabs.link) aren't part of the shared baseline —
    # only earn a place once a repo actually has the content that justifies them.
    assert "content.tabs.link" not in mkdocs_yaml["theme"]["features"]
    # Fleet docs-site plugins (nivintw/repo-management#85: #94 dates, #95 social cards,
    # #97 llms.txt) — adding `plugins:` at all drops mkdocs' implicit default (`search`
    # alone), so `search` must be explicit too or built-in search silently disappears.
    assert mkdocs_extension_names(mkdocs_yaml["plugins"]) == {
        "search",
        "git-revision-date-localized",
        "social",
        "llmstxt",
    }
    assert mkdocs_extension_names(mkdocs_yaml["markdown_extensions"]) == {
        "pymdownx.emoji",
        "admonition",
        "pymdownx.details",
        "pymdownx.superfences",
        "pymdownx.highlight",
        "pymdownx.inlinehilite",
        "pymdownx.tabbed",
        "attr_list",
        "md_in_html",
        "footnotes",
        "pymdownx.snippets",
        "pymdownx.magiclink",
    }
    snippets_config = next(
        ext["pymdownx.snippets"]
        for ext in mkdocs_yaml["markdown_extensions"]
        if isinstance(ext, dict) and "pymdownx.snippets" in ext
    )
    assert snippets_config["base_path"] == "docs/includes"

    # The docs design deliberately relies on raw HTML in Markdown (castify cast embeds,
    # version-badge spans) — MD033 must be off or the lint gate fails on either pattern.
    rumdl_toml = tomllib.loads((project_dir / ".config" / "rumdl.toml").read_text())
    assert "MD033" in rumdl_toml["global"]["disable"]
    # pymdownx.tabbed's indentation-based nesting misfires rumdl's MD046 (see #178) —
    # scoped to docs/*.md rather than disabled globally.
    assert rumdl_toml["per-file-ignores"]["docs/*.md"] == ["MD033", "MD046"]


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
    assert not (project_dir / "overrides").exists()
    assert not (project_dir / ".github" / "workflows" / "docs.yml").exists()

    # rumdl.toml is always scaffolded regardless of include_docs_site — but a repo with no
    # docs site has no reason to relax MD033 and should keep the stricter default.
    rumdl_toml = tomllib.loads((project_dir / ".config" / "rumdl.toml").read_text())
    assert "MD033" not in rumdl_toml["global"]["disable"]
    assert "per-file-ignores" not in rumdl_toml
