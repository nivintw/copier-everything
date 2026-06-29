# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""Ensure files that should stay in sync between the template and this repo's own root do.

copier-everything dogfoods its own template: the repo root is meant to track what a generated
project receives, so a tooling change lands in BOTH places. There is no automated render of the
root (it carries deliberate divergences), so these tests are the guard — they render the
template and compare the output against the repo's own root files. Files that legitimately
differ are compared structurally with the deviation documented and asserted; files that differ
substantially by design are listed in NOT-SYNCED below and intentionally not tested.

The render reflects HEAD (committed state), so run these on a clean tree (as CI does) — a dirty
working tree can produce spurious diffs.

NOT SYNCED (differ substantially by design, or are generated) — intentionally untested:
- .github/workflows/ci.yml, main.yml: root's CI is the template's own render-matrix gate
  (and release flow), not a generated project's lint-and-test gate — fundamentally different.
- .pre-commit-config.yaml: root's prek config is specialized for authoring the template.
- .config/typos.toml, .config/licenserc.toml, REUSE.toml: root's spellcheck/licensing config
  is specialized for the template tree (excludes template/**, handles json5, etc.).
- .config/release-please-config.json, .config/.release-please-manifest.json: root carries its
  own bootstrap-sha and real version, not a freshly-scaffolded 0.0.0 project.
- README.md, AGENTS.md, CHANGELOG.md, CONTRIBUTING.md, SECURITY.md: prose — repo-specific or
  release-generated.
- .gitignore, .envrc, .python-version, .copier-answers.yml, .editorconfig, .github/CODEOWNERS,
  .github/ISSUE_TEMPLATE/**, .github/PULL_REQUEST_TEMPLATE.md, .config/markdown-header.toml:
  root ships its own or deliberately omits these (.editorconfig differs only in a comment).
- tests/**: the template ships a smoke test; this repo has its own suite (you are reading it).
"""

from __future__ import annotations

import tomllib
import warnings
from typing import TYPE_CHECKING

import pyjson5
import pytest
import yaml
from copier import run_copy
from copier.errors import DirtyLocalWarning

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture(scope="module")
def generated_project_dir(template_dir: Path, output_dir_module_scope: Path) -> Path:
    """Render the template once (module scope) for the whole sync comparison.

    Renders the "pytest, no python source" shape — the shape this repo's own root is — so the
    rendered tree is the right thing to compare the root against.
    """
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DirtyLocalWarning)
        run_copy(
            str(template_dir),
            str(output_dir_module_scope),
            data={"project_name": "copier-everything", "python_source": False},
            defaults=True,
            unsafe=True,
            vcs_ref="HEAD",
            skip_tasks=True,
        )
    return output_dir_module_scope


def _toml(path: Path) -> dict:
    return tomllib.loads(path.read_text())


def _json5(path: Path) -> dict:
    return pyjson5.decode(path.read_text())


def _yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def test_trivially_equal_files(template_dir: Path, generated_project_dir: Path) -> None:
    """Files that must be byte-for-byte identical between root and a render."""
    trivially_equal_files = [
        ".config/rumdl.toml",
        ".config/yamllint.yaml",
        ".github/workflows/label-hygiene.yml",
        "LICENSE",
        "LICENSES/MIT.txt",
    ]
    for relative_path in trivially_equal_files:
        root_text = (template_dir / relative_path).read_text()
        render_text = (generated_project_dir / relative_path).read_text()
        assert root_text == render_text, f"{relative_path} is not synced (raw content differs)!"


def test_pyproject_toml(template_dir: Path, generated_project_dir: Path) -> None:
    """pyproject.toml: tooling config (ruff/pytest/uv) synced; metadata + deps may differ."""
    root = _toml(template_dir / "pyproject.toml")
    render = _toml(generated_project_dir / "pyproject.toml")

    # Deviation: [project] values differ (description, etc.), but the keys must match.
    assert set(root["project"].keys()) == set(render["project"].keys()), (
        "pyproject [project] keys are not synced!"
    )
    # Deviation: [dependency-groups] contents differ (root adds copier/pyjson5/pytest-xdist for
    # the template's own test suite), but the group keys must match.
    assert set(root["dependency-groups"].keys()) == set(render["dependency-groups"].keys()), (
        "pyproject [dependency-groups] keys are not synced!"
    )

    # Everything else (the [tool.*] tables that actually configure the shared tooling) must match.
    del root["project"], render["project"]
    del root["dependency-groups"], render["dependency-groups"]
    assert root == render, "pyproject.toml [tool.*] config is not synced!"


def test_lychee_toml(template_dir: Path, generated_project_dir: Path) -> None:
    """Lychee excludes: the root's set is a superset of the template's shared excludes."""
    root = _toml(template_dir / ".config/lychee.toml")
    render = _toml(generated_project_dir / ".config/lychee.toml")

    root_excludes = set(root["exclude"])
    render_excludes = set(render["exclude"])

    # The template's excludes (own /compare/ URLs + the REUSE /info/ endpoint) must all be
    # present in the root's set; the root adds its own repo-specific hosts on top.
    assert render_excludes <= root_excludes, (
        "lychee.toml: the template's excludes are not all present in the root config!"
    )
    assert "api\\.reuse\\.software/info/" in root_excludes, (
        "lychee.toml: the REUSE /info/ exclude (the #85 fix) is missing from the root config!"
    )


def test_vscode_settings(template_dir: Path, generated_project_dir: Path) -> None:
    """.vscode/settings.json: shared editor settings synced; Python-package settings excepted."""
    root = _json5(template_dir / ".vscode/settings.json")
    render = _json5(generated_project_dir / ".vscode/settings.json")

    # Deviation: this template-authoring repo has no Python package, so it omits the [python]
    # editor block and the python.testing.* settings a generated Python project gets.
    for python_only_key in (
        "[python]",
        "python.testing.pytestArgs",
        "python.testing.unittestEnabled",
        "python.testing.pytestEnabled",
    ):
        render.pop(python_only_key, None)

    assert root == render, ".vscode/settings.json is not synced (beyond the Python-only keys)!"


def test_vscode_extensions(template_dir: Path, generated_project_dir: Path) -> None:
    """.vscode/extensions.json: language-agnostic recommendations synced; known swaps excepted."""
    root = _json5(template_dir / ".vscode/extensions.json")
    render = _json5(generated_project_dir / ".vscode/extensions.json")

    # Deviation: the root recommends jinjahtml (for editing template/**); a generated Python
    # project instead recommends the Python extensions. The language-agnostic core must match.
    root_only = {"samuelcolvin.jinjahtml"}
    render_only = {"charliermarsh.ruff", "ms-python.python", "njpwerner.autodocstring"}
    assert (
        set(root["recommendations"]) - root_only == set(render["recommendations"]) - render_only
    ), ".vscode/extensions.json language-agnostic recommendations are not synced!"
    assert root.get("unwantedRecommendations") == render.get("unwantedRecommendations"), (
        ".vscode/extensions.json unwantedRecommendations are not synced!"
    )


def test_cz_toml(template_dir: Path, generated_project_dir: Path) -> None:
    """.cz.toml: commitizen config is identical (the files differ only in comments)."""
    assert _toml(template_dir / ".cz.toml") == _toml(generated_project_dir / ".cz.toml"), (
        ".cz.toml commitizen config is not synced!"
    )


def test_pr_workflow(template_dir: Path, generated_project_dir: Path) -> None:
    """pr.yml: the open-PR pipeline is identical (the files differ only in comments)."""
    assert _yaml(template_dir / ".github/workflows/pr.yml") == _yaml(
        generated_project_dir / ".github/workflows/pr.yml"
    ), ".github/workflows/pr.yml is not synced!"


def test_refresh_binary_checksums_workflow(template_dir: Path, generated_project_dir: Path) -> None:
    """refresh-binary-checksums.yml: synced except the root also watches the template tree."""
    root = _yaml(template_dir / ".github/workflows/refresh-binary-checksums.yml")
    render = _yaml(generated_project_dir / ".github/workflows/refresh-binary-checksums.yml")

    # YAML parses the `on:` key as the boolean True (YAML 1.1 truthy).
    on_key = True
    root_paths = root[on_key]["push"]["paths"]
    render_paths = render[on_key]["push"]["paths"]
    # Deviation: the root additionally refreshes the template's own pinned workflows.
    assert "template/.github/workflows/**" in root_paths, (
        "root refresh workflow should also watch template/.github/workflows/**!"
    )
    assert [p for p in root_paths if p != "template/.github/workflows/**"] == render_paths, (
        "refresh-binary-checksums.yml trigger paths are not synced (beyond the template watch)!"
    )

    # The rest of the workflow (the job that runs the script) must match.
    del root[on_key], render[on_key]
    assert root == render, "refresh-binary-checksums.yml job is not synced!"


def test_link_check_workflow(template_dir: Path, generated_project_dir: Path) -> None:
    """link-check.yml: both source excludes from .config/lychee.toml; trigger/tuning differ."""
    root = _yaml(template_dir / ".github/workflows/link-check.yml")
    render = _yaml(generated_project_dir / ".github/workflows/link-check.yml")

    def lychee_args(doc: dict) -> str:
        return doc["jobs"]["lychee"]["steps"][1]["with"]["args"]

    # The #87 fix must be synced on both sides: excludes sourced from the config file, no inline
    # --exclude (which would reintroduce lychee's CLI-vs-config merge ambiguity).
    for name, doc in (("root", root), ("render", render)):
        args = lychee_args(doc)
        assert "--config .config/lychee.toml" in args, f"{name} link-check must use --config!"
        assert "--exclude" not in args, f"{name} link-check must not pass inline --exclude!"

    # Deviation: the root triggers on every PR and omits --max-retries/--timeout; the template
    # path-filters to Markdown and tunes retries. Both differences are intentional.
    on_key = True
    del root[on_key], render[on_key]
    root["jobs"]["lychee"]["steps"][1]["with"]["args"] = ""
    render["jobs"]["lychee"]["steps"][1]["with"]["args"] = ""
    assert root == render, "link-check.yml is not synced (beyond trigger + lychee args tuning)!"
