# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""Ensure files that should stay in sync between the template and this repo's own root do.

copier-everything dogfoods its own template: the repo root is meant to track what a generated
project receives, so a tooling change lands in BOTH places. There is no automated render of the
root (it carries deliberate divergences), so these tests are the guard — they render the
template and compare the output against the repo's own root files.

Every file the render produces (for the shape this repo is) is classified into exactly one of
three buckets, and ``test_every_rendered_file_is_classified`` fails if the render produces a
file in none of them — so a newly added template file that renders into this shape can't
silently fall through the guard (files gated behind other answers — ``src/``, Docker, the
publish workflow — aren't rendered here, and are correctly absent from this repo's root):

- ``TRIVIALLY_EQUAL`` — must be byte-for-byte identical (``test_trivially_equal_files``).
- ``STRUCTURALLY_TESTED`` — legitimately differs; a dedicated test below asserts the rest
  matches after subtracting the documented deviation.
- ``NOT_SYNCED`` — differs substantially by design, or is generated; intentionally not asserted
  (reasons grouped inline below).

copier renders the template's current **working-tree** state (uncommitted changes included; it
emits a DirtyLocalWarning, which the render helper suppresses), and the root side is read off
disk too — so both sides are the working tree and the comparison is self-consistent whether or
not the tree is clean.
"""

from __future__ import annotations

import re
import tomllib
from typing import TYPE_CHECKING

import pyjson5
import pytest
import yaml

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

# Must be byte-for-byte identical between this repo's root and a render.
TRIVIALLY_EQUAL = {
    ".config/rumdl.toml",
    ".config/yamllint.yaml",
    ".github/workflows/approve-bot-prs.yml",
    ".github/workflows/label-hygiene.yml",
    "LICENSE",
    "LICENSES/MIT.txt",
}

# Legitimately differs; the named test subtracts the documented deviation and compares the rest.
STRUCTURALLY_TESTED = {
    "pyproject.toml",  # test_pyproject_toml
    ".config/lychee.toml",  # test_lychee_toml
    ".cz.toml",  # test_cz_toml
    ".vscode/settings.json",  # test_vscode_settings
    ".vscode/extensions.json",  # test_vscode_extensions
    ".github/workflows/pr.yml",  # test_pr_workflow
    ".github/workflows/link-check.yml",  # test_link_check_workflow
    ".editorconfig",  # test_editorconfig (rules identical; only a dogfooding comment differs)
    "scripts/refresh-binary-checksums.sh",  # test_refresh_binary_checksums_sh
}

# Differs substantially by design, or is generated — intentionally not asserted.
NOT_SYNCED = {
    # Root's CI is the template's own render-matrix gate + release flow, not a generated
    # project's lint-and-test gate — fundamentally different workflows.
    ".github/workflows/ci.yml",
    ".github/workflows/main.yml",
    # Root's authoring config is specialized for the template tree (excludes template/**,
    # handles json5, carries its own version/bootstrap, etc.).
    ".pre-commit-config.yaml",
    ".config/typos.toml",
    ".config/licenserc.toml",
    "REUSE.toml",
    ".config/release-please-config.json",
    ".config/.release-please-manifest.json",
    ".github/renovate.json",  # root uses renovate.json5 (json5 comments)
    # Prose — repo-specific or release-generated.
    "README.md",
    "AGENTS.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    # Root ships its own or deliberately omits these.
    ".gitignore",
    ".envrc",
    ".python-version",
    ".copier-answers.yml",
    ".github/CODEOWNERS",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".config/markdown-header.toml",
    # The template ships a smoke test; this repo has its own suite (you are reading it).
    "tests/conftest.py",
    "tests/test_smoke.py",
}


@pytest.fixture(scope="module")
def generated_project_dir(
    template_dir: Path,
    output_dir_module_scope: Path,
    render_template: Callable[..., Path],
) -> Path:
    """Render the "pytest, no python source" shape — the shape this repo's own root is."""
    return render_template(
        template_dir,
        output_dir_module_scope,
        data={"project_name": "copier-everything", "python_source": False},
        skip_tasks=True,
    )


def _toml(path: Path) -> dict:
    return tomllib.loads(path.read_text())


def _json5(path: Path) -> dict:
    return pyjson5.decode(path.read_text())


def _yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def _drop_triggers(doc: dict) -> None:
    """Remove the ``on:`` key under either representation (bool ``True`` or the string ``"on"``)."""
    doc.pop(True, None)
    doc.pop("on", None)


def _non_comment_lines(path: Path, *, strip: bool = False) -> list[str]:
    """Lines that aren't blank or a ``#`` comment.

    For files where comment wording is allowed to differ between the root and a render but
    the actual content must match.
    """
    lines = [
        line
        for line in path.read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    return [line.strip() for line in lines] if strip else lines


def test_every_rendered_file_is_classified(generated_project_dir: Path) -> None:
    """Every file a render produces must be in exactly one sync bucket.

    This turns the buckets into an enforced partition: add a file to the template and this fails
    until it's classified, so the dogfooding guard can't silently stop covering a new file.
    """
    # The buckets must be disjoint (a file classified twice is a bookkeeping bug).
    seen: set[str] = set()
    for bucket in (TRIVIALLY_EQUAL, STRUCTURALLY_TESTED, NOT_SYNCED):
        dupes = seen & bucket
        assert not dupes, f"files classified in more than one sync bucket: {sorted(dupes)}"
        seen |= bucket

    rendered = {
        str(path.relative_to(generated_project_dir))
        for path in generated_project_dir.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(generated_project_dir).parts
    }
    # Guard against a vacuous pass (empty render → empty difference → green inspecting nothing).
    assert {"pyproject.toml", "LICENSE"} <= rendered, "render produced no/too few files"
    unclassified = rendered - seen
    assert not unclassified, (
        "rendered files not classified as TRIVIALLY_EQUAL / STRUCTURALLY_TESTED / NOT_SYNCED "
        f"in test_synced_files.py — add each to the right bucket: {sorted(unclassified)}"
    )


def test_trivially_equal_files(template_dir: Path, generated_project_dir: Path) -> None:
    """Files that must be byte-for-byte identical between root and a render."""
    for relative_path in sorted(TRIVIALLY_EQUAL):
        root_text = (template_dir / relative_path).read_text()
        render_text = (generated_project_dir / relative_path).read_text()
        assert root_text == render_text, f"{relative_path} is not synced (raw content differs)!"


def test_editorconfig(template_dir: Path, generated_project_dir: Path) -> None:
    """.editorconfig: the indent/charset rules are identical; only a dogfooding comment differs."""
    # .editorconfig isn't cleanly INI/TOML-parseable (`root = true` precedes any section), so
    # compare the meaningful lines — everything that isn't a comment or blank.
    assert _non_comment_lines(template_dir / ".editorconfig", strip=True) == _non_comment_lines(
        generated_project_dir / ".editorconfig", strip=True
    ), ".editorconfig rules are not synced (beyond the dogfooding comment)!"


def test_refresh_binary_checksums_sh(template_dir: Path, generated_project_dir: Path) -> None:
    """refresh-binary-checksums.sh: code must match; comments + the one glob deviation may differ.

    Root additionally scans template/.github/workflows/*.jinja (it refreshes both its own
    ci.yml AND the template's ci.yml.jinja); the generated copy has no template/ dir to scan.
    """

    def code_lines(path: Path) -> list[str]:
        # The one documented functional deviation: root's glob loop additionally scans
        # template/.github/workflows/*.jinja. Normalize it away so the rest can compare equal.
        return [
            line.replace(" template/.github/workflows/*.jinja", "")
            for line in _non_comment_lines(path)
        ]

    root_path = template_dir / "scripts/refresh-binary-checksums.sh"
    render_path = generated_project_dir / "scripts/refresh-binary-checksums.sh"

    # _non_comment_lines() strips the shebang too (it starts with "#"), so check it explicitly
    # — it's semantically significant (selects the interpreter) but would otherwise be silently
    # excluded from the comparison below.
    root_shebang = root_path.read_text().splitlines()[0]
    render_shebang = render_path.read_text().splitlines()[0]
    assert root_shebang == render_shebang == "#!/usr/bin/env bash", (
        "refresh-binary-checksums.sh shebang is not synced!"
    )

    root = code_lines(root_path)
    render = code_lines(render_path)
    assert root == render, "refresh-binary-checksums.sh code is not synced (beyond comments)!"


def test_pyproject_toml(template_dir: Path, generated_project_dir: Path) -> None:
    """pyproject.toml: tooling config (ruff/pytest/uv) synced; metadata + deps may differ."""
    root = _toml(template_dir / "pyproject.toml")
    render = _toml(generated_project_dir / "pyproject.toml")

    # Deviation: only the project IDENTITY differs (name/description/authors). Every other
    # [project] field is a shared contract and must match by VALUE — notably requires-python,
    # which is the same Python-floor contract as ruff's target-version in [tool.ruff].
    identity_keys = {"name", "description", "authors"}
    assert set(root["project"].keys()) == set(render["project"].keys()), (
        "pyproject [project] keys are not synced!"
    )
    root_project = {k: v for k, v in root["project"].items() if k not in identity_keys}
    render_project = {k: v for k, v in render["project"].items() if k not in identity_keys}
    assert root_project == render_project, (
        "pyproject [project] shared fields (requires-python, version, license, classifiers, "
        "dependencies) are not synced!"
    )
    # Deviation: the root's dev group is a superset (adds copier/pyjson5 for the template's own
    # test suite), but every dependency floor the template ships must be present in the root's.
    assert set(root["dependency-groups"].keys()) == set(render["dependency-groups"].keys()), (
        "pyproject [dependency-groups] keys are not synced!"
    )
    assert set(render["dependency-groups"]["dev"]) <= set(root["dependency-groups"]["dev"]), (
        "pyproject dev dependency floors are not synced (template has a dep the root lacks)!"
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


def test_cz_toml(template_dir: Path, generated_project_dir: Path) -> None:
    """Commitizen config is identical between root and render (files differ only in comments)."""
    assert _toml(template_dir / ".cz.toml") == _toml(generated_project_dir / ".cz.toml"), (
        ".cz.toml commitizen config is not synced!"
    )


def test_vscode_settings(template_dir: Path, generated_project_dir: Path) -> None:
    """VS Code settings: shared editor config synced; the Python-package settings excepted."""
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
    """VS Code recommendations: language-agnostic set synced; per-language swaps excepted."""
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


def test_pr_workflow(template_dir: Path, generated_project_dir: Path) -> None:
    """The open-PR pipeline (pr.yml) is identical (the files differ only in comments)."""
    assert _yaml(template_dir / ".github/workflows/pr.yml") == _yaml(
        generated_project_dir / ".github/workflows/pr.yml"
    ), ".github/workflows/pr.yml is not synced!"


def test_link_check_workflow(template_dir: Path, generated_project_dir: Path) -> None:
    """Link-check: both source excludes from .config/lychee.toml; only trigger + tuning differ."""
    root = _yaml(template_dir / ".github/workflows/link-check.yml")
    render = _yaml(generated_project_dir / ".github/workflows/link-check.yml")

    def lychee_step(doc: dict) -> dict:
        # Locate the step by its action (not a hard-coded index) so reordering/inserting steps
        # doesn't break the test when the workflow is still correct.
        steps = doc["jobs"]["lychee"]["steps"]
        return next(s for s in steps if "lycheeverse/lychee-action" in s.get("uses", ""))

    def get_args(doc: dict) -> str:
        return lychee_step(doc)["with"]["args"]

    def set_args(doc: dict, value: str) -> None:
        lychee_step(doc)["with"]["args"] = value

    # The #87 fix must be synced on both sides: excludes sourced from the config file, no inline
    # --exclude (which would reintroduce lychee's CLI-vs-config merge ambiguity).
    for name, doc in (("root", root), ("render", render)):
        args = get_args(doc)
        assert "--config .config/lychee.toml" in args, f"{name} link-check must use --config!"
        assert "--exclude" not in args, f"{name} link-check must not pass inline --exclude!"

    # Deviation: the template tunes --max-retries/--timeout; the root omits them. Strip those
    # flags + their values from BOTH sides (value- and order-agnostic) so everything else in the
    # args (--no-progress, --config, the Markdown glob) still gets compared.
    def strip_tuning(args: str) -> str:
        for flag in ("--max-retries", "--timeout"):
            args = re.sub(rf"\s*{flag}\s+\S+", "", args)
        return args

    set_args(root, strip_tuning(get_args(root)))
    set_args(render, strip_tuning(get_args(render)))
    # Deviation: the root triggers on every PR; the template path-filters to Markdown.
    _drop_triggers(root)
    _drop_triggers(render)
    assert root == render, "link-check.yml is not synced (beyond the trigger + retry/timeout)!"
