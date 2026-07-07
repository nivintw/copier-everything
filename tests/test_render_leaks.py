# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""Guard against leftover copier Jinja in rendered output — the "forgot the `.jinja` suffix" bug.

A template file that is missing its `.jinja` extension is copied verbatim instead of rendered, so
copier expressions like ``{{ project_name }}`` or ``{% if has_python %}`` survive literally into a
generated project. copier reports no error (a plain file copy always "succeeds"), so nothing else
in the suite catches it.

The scan cannot be a blanket "flag any ``{{ … }}``": a rendered project legitimately contains
foreign template languages that use the same braces — GitHub Actions ``${{ … }}`` expressions,
Helm Go-templates (``{{ .Values.x }}``), the MkDocs Material ``overrides/404.html`` theme template
(``{% extends %}`` / ``{{ base_url }}`` / ``{# … #}``), and the skywalking-eyes header template in
``.config/licenserc.toml`` (``{{ props["…"] }}``). The `$` negative-lookbehind alone only rules out
the GHA case; the rest would false-positive. The precise tell-tale of the *copier* bug is a copier
**question name** surviving inside braces, so the scanner flags a Jinja block only when it
references one of copier.yml's own question variables — which none of those foreign templates do.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest
import yaml

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from pathlib import Path

# Any Jinja delimiter block on a single line: an expression `{{ … }}` (but NOT GitHub Actions'
# `${{ … }}`, ruled out by the `$` negative-lookbehind), a statement `{% … %}`, or a comment
# `{# … #}`. Non-greedy so multiple blocks on one line match independently.
_JINJA_BLOCK = re.compile(r"(?<!\$)\{\{.*?\}\}|\{%.*?%\}|\{#.*?#\}")


def copier_variable_pattern(copier_yml: Path) -> re.Pattern[str]:
    """Build a whole-word regex matching any copier question name declared in copier.yml.

    Reads the question names straight from copier.yml (its non-underscore top-level keys) so the
    guard auto-covers new questions as they are added, rather than hardcoding a list that drifts.

    Args:
        copier_yml: Path to the template's copier.yml.

    Returns:
        A compiled pattern that matches any copier question name as a whole word.
    """
    config = yaml.safe_load(copier_yml.read_text(encoding="utf-8"))
    names = sorted(key for key in config if not key.startswith("_"))
    return re.compile(r"\b(?:" + "|".join(re.escape(name) for name in names) + r")\b")


def iter_copier_leaks(
    tree: Path,
    variable_pattern: re.Pattern[str],
) -> Iterator[tuple[Path, int, str]]:
    """Yield every leftover-copier-Jinja hit under `tree` as (file, line number, snippet).

    Skips the `.git` directory and binary files (anything that is not valid UTF-8). A hit is a
    Jinja delimiter block (see `_JINJA_BLOCK`) that also references a copier question variable.

    Args:
        tree: Root of the rendered project to scan.
        variable_pattern: The copier-question-name matcher from `copier_variable_pattern`.

    Yields:
        `(path, line_number, snippet)` for each offending Jinja block found.
    """
    for path in sorted(tree.rglob("*")):
        if not path.is_file() or ".git" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue  # binary (non-UTF-8) file — nothing to scan
        for line_number, line in enumerate(text.splitlines(), start=1):
            for match in _JINJA_BLOCK.finditer(line):
                block = match.group(0)
                if variable_pattern.search(block):
                    yield path, line_number, block


# A deliberately rich answer set: turn on every optional module so the scan sweeps the widest
# possible file surface (Helm, docs site, Ansible, Terraform, Docker, SQL, devcontainer, both
# test frameworks) — the more files rendered, the more places a missing `.jinja` could hide.
_RICH_ANSWERS: dict[str, object] = {
    "project_name": "Leak Scan Project",
    "test_frameworks": ["pytest", "bats"],
    "python_source": True,
    "is_package": True,
    "publish_to_pypi": True,
    "contains_ansible": True,
    "ansible_kind": "collection",
    "publish_to_galaxy": True,
    "include_terraform": True,
    "include_docker": True,
    "include_helm": True,
    "include_sql": True,
    "include_devcontainer": True,
    "include_docs_site": True,
}


@pytest.fixture(scope="module")
def rich_render(
    template_dir: Path,
    tmp_path_factory: pytest.TempPathFactory,
    render_template: Callable[..., Path],
) -> Path:
    """Render the template once with every optional module enabled; return the project dir."""
    out = tmp_path_factory.mktemp("leak_scan_render")
    return render_template(template_dir, out, data=_RICH_ANSWERS, skip_tasks=True)


def test_no_leftover_copier_jinja_in_rendered_output(
    template_dir: Path,
    rich_render: Path,
) -> None:
    """No rendered file leaks a copier expression — every template file rendered its Jinja away."""
    pattern = copier_variable_pattern(template_dir / "copier.yml")
    leaks = list(iter_copier_leaks(rich_render, pattern))
    detail = "\n".join(f"  {path}:{line}: {snippet}" for path, line, snippet in leaks)
    assert not leaks, (
        "Leftover copier Jinja in rendered output (a template file likely missing its `.jinja` "
        f"suffix):\n{detail}"
    )


def test_scanner_catches_a_planted_leak(
    template_dir: Path,
    tmp_path: Path,
) -> None:
    """Guard-the-guard: a file carrying un-rendered copier Jinja must be flagged.

    Plants exactly what a template file missing its `.jinja` suffix would leave behind — copier
    expressions verbatim — and asserts the scanner reports it. Without this, a scanner that never
    matched anything (a broken regex, a wrong variable set) would pass the happy-path test above
    while silently protecting nothing.
    """
    pattern = copier_variable_pattern(template_dir / "copier.yml")
    planted = tmp_path / "forgot_the_jinja_suffix.md"
    planted.write_text(
        "# SPDX-FileCopyrightText: © {{ year }} {{ author_name }}\n"
        "{% if has_python %}leak{% endif %}\n",
        encoding="utf-8",
    )
    leaks = list(iter_copier_leaks(tmp_path, pattern))
    assert leaks, "scanner failed to flag a planted un-`.jinja`'d copier template"
    snippets = [snippet for _, _, snippet in leaks]
    assert "{{ year }}" in snippets
    assert "{% if has_python %}" in snippets


def test_scanner_ignores_foreign_template_braces(
    template_dir: Path,
    tmp_path: Path,
) -> None:
    """Negative control: GHA `${{ }}`, Helm, and Material braces must NOT be flagged.

    These are the legitimate non-copier brace users that a naive `{{ }}` scan would false-positive
    on. None references a copier question variable, so none may be reported — the property that
    lets the scanner run over the real (Helm + docs-site) render without spurious failures.
    """
    pattern = copier_variable_pattern(template_dir / "copier.yml")
    innocent = tmp_path / "innocent.txt"
    innocent.write_text(
        'run: echo "${{ secrets.TOKEN }}"\n'
        "replicas: {{ .Values.replicaCount }}\n"
        '{% extends "main.html" %}\n'
        "{# a MkDocs Material theme comment #}\n",
        encoding="utf-8",
    )
    assert not list(iter_copier_leaks(tmp_path, pattern))
