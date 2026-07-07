# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""Exercise every `validator:` block in copier.yml (except `year`, covered by test_year_question).

copier.yml gates ~10 questions behind Jinja validators, but tests/render-matrix.sh only ever
feeds them *valid* answers — so a regex typo, an inverted condition, or a validator that silently
accepts everything (e.g. a `regex_search` anchored wrong) would ship undetected. Each validated
question below gets a rejecting case (bad input → copier raises `ValueError`, matched on the exact
message the validator surfaces) plus an accepting edge case (a valid boundary value renders), so
the suite as a whole closes the "a broken validator ships silently" hole.

Some questions are only *asked* under certain answers (python_package needs python_source; the
ansible_* pair needs contains_ansible + a role-based ansible_kind) — the enabling answers are
supplied via `data=` so the question is actually reached and its validator actually runs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


def _render(
    render_template: Callable[..., Path],
    template_dir: Path,
    out: Path,
    extra: dict[str, object],
) -> Path:
    """Render the template with `project_name` plus `extra` answers, tasks skipped.

    Args:
        render_template: The shared render helper (the `render_template` fixture).
        template_dir: The template repo root (the `template_dir` fixture).
        out: A fresh output directory to render into.
        extra: Answers layered on top of `project_name` — the values under test plus any
            enabling answers a gated question needs to be asked at all.

    Returns:
        The rendered project directory (`out`).
    """
    data: dict[str, object] = {"project_name": "Validator Test"}
    data.update(extra)
    return render_template(template_dir, out, data=data, skip_tasks=True)


# Questions whose validator does nothing but reject an empty string. Each entry is
# (question, the enabling answers needed to reach it). project_slug also has a *format* rule,
# tested separately below; here it stands in only for its empty-string branch.
_NON_EMPTY_QUESTIONS: list[tuple[str, dict[str, object]]] = [
    ("project_slug", {}),
    ("author_name", {}),
    ("author_email", {}),
    ("repo_owner", {}),
    ("repo_name", {}),
    ("python_package", {"python_source": True}),
    ("ansible_namespace", {"contains_ansible": True, "ansible_kind": "collection"}),
    ("ansible_name", {"contains_ansible": True, "ansible_kind": "collection"}),
]


@pytest.mark.parametrize(("question", "enabling"), _NON_EMPTY_QUESTIONS)
def test_validator_rejects_empty_value(
    template_dir: Path,
    tmp_path: Path,
    render_template: Callable[..., Path],
    question: str,
    enabling: dict[str, object],
) -> None:
    """Every non-empty validator rejects an empty answer with its own `<name> cannot be empty`."""
    with pytest.raises(ValueError, match=f"{question} cannot be empty"):
        _render(render_template, template_dir, tmp_path, {**enabling, question: ""})


def test_project_slug_rejects_uppercase_and_underscores(
    template_dir: Path,
    tmp_path: Path,
    render_template: Callable[..., Path],
) -> None:
    """project_slug's format rule rejects uppercase / underscores / spaces."""
    with pytest.raises(ValueError, match="project_slug must be lowercase"):
        _render(render_template, template_dir, tmp_path, {"project_slug": "Bad_Slug"})


def test_project_slug_accepts_lowercase_dashed(
    template_dir: Path,
    tmp_path: Path,
    render_template: Callable[..., Path],
) -> None:
    """A lowercase, dash-separated slug (the canonical shape) renders."""
    project_dir = _render(render_template, template_dir, tmp_path, {"project_slug": "my-project-1"})
    assert "project_slug: my-project-1" in (project_dir / ".copier-answers.yml").read_text()


@pytest.mark.parametrize(
    ("question", "value"),
    [
        ("author_name", "A"),
        ("author_email", "a@b.co"),
        ("repo_owner", "o"),
        ("repo_name", "r"),
    ],
)
def test_non_empty_questions_accept_minimal_value(
    template_dir: Path,
    tmp_path: Path,
    render_template: Callable[..., Path],
    question: str,
    value: str,
) -> None:
    """The identity/repo non-empty validators accept a minimal non-empty value."""
    project_dir = _render(render_template, template_dir, tmp_path, {question: value})
    assert f"{question}: {value}" in (project_dir / ".copier-answers.yml").read_text()


def test_python_package_rejects_non_identifier(
    template_dir: Path,
    tmp_path: Path,
    render_template: Callable[..., Path],
) -> None:
    """A leading-digit name is not a valid Python identifier and is rejected."""
    with pytest.raises(ValueError, match="python_package must be a valid Python identifier"):
        _render(
            render_template,
            template_dir,
            tmp_path,
            {"python_source": True, "python_package": "9lives"},
        )


def test_python_package_rejects_reserved_keyword(
    template_dir: Path,
    tmp_path: Path,
    render_template: Callable[..., Path],
) -> None:
    """A valid-identifier-but-reserved keyword (`class`) is rejected by the keyword branch."""
    with pytest.raises(ValueError, match="python_package must not be a Python reserved keyword"):
        _render(
            render_template,
            template_dir,
            tmp_path,
            {"python_source": True, "python_package": "class"},
        )


def test_python_package_accepts_leading_underscore(
    template_dir: Path,
    tmp_path: Path,
    render_template: Callable[..., Path],
) -> None:
    """A bare underscore is a valid identifier and not a keyword — the accepting edge."""
    project_dir = _render(
        render_template,
        template_dir,
        tmp_path,
        {"python_source": True, "python_package": "_"},
    )
    assert "python_package: _" in (project_dir / ".copier-answers.yml").read_text()


def test_python_version_rejects_patch_component(
    template_dir: Path,
    tmp_path: Path,
    render_template: Callable[..., Path],
) -> None:
    """python_version must be MAJOR.MINOR — a three-part `3.14.2` is rejected."""
    with pytest.raises(ValueError, match=r"python_version must be MAJOR\.MINOR"):
        _render(render_template, template_dir, tmp_path, {"python_version": "3.14.2"})


def test_python_version_accepts_major_minor(
    template_dir: Path,
    tmp_path: Path,
    render_template: Callable[..., Path],
) -> None:
    """A two-part MAJOR.MINOR value renders."""
    project_dir = _render(render_template, template_dir, tmp_path, {"python_version": "3.9"})
    assert "python_version: '3.9'" in (project_dir / ".copier-answers.yml").read_text()


@pytest.mark.parametrize("question", ["ansible_namespace", "ansible_name"])
def test_ansible_identifier_rejects_dashes_and_uppercase(
    template_dir: Path,
    tmp_path: Path,
    render_template: Callable[..., Path],
    question: str,
) -> None:
    """Both Galaxy-name validators reject a dash/uppercase value (`Bad-Name`)."""
    with pytest.raises(ValueError, match=f"{question} must be lowercase ASCII"):
        _render(
            render_template,
            template_dir,
            tmp_path,
            {"contains_ansible": True, "ansible_kind": "collection", question: "Bad-Name"},
        )


@pytest.mark.parametrize("question", ["ansible_namespace", "ansible_name"])
def test_ansible_identifier_accepts_lowercase_underscored(
    template_dir: Path,
    tmp_path: Path,
    render_template: Callable[..., Path],
    question: str,
) -> None:
    """Both Galaxy-name validators accept a lowercase, underscored value."""
    project_dir = _render(
        render_template,
        template_dir,
        tmp_path,
        {"contains_ansible": True, "ansible_kind": "collection", question: "a_b_1"},
    )
    assert f"{question}: a_b_1" in (project_dir / ".copier-answers.yml").read_text()


def test_at_least_one_validator_actually_enforces(
    template_dir: Path,
    tmp_path: Path,
    render_template: Callable[..., Path],
) -> None:
    """Meta-guard: copier really *enforces* validators rather than swallowing bad input.

    Every reject test above assumes copier raises when a validator returns a non-empty message.
    If that machinery ever regressed — a copier upgrade changing how `validator:` is wired, the
    render helper accidentally suppressing the error — those tests would still "pass" only because
    nothing raised where a raise was expected, and the whole suite would be silently worthless.
    This anchors that assumption: a flagrantly invalid slug must raise, or the suite is a no-op.
    """
    with pytest.raises(ValueError, match="project_slug must be lowercase"):
        _render(render_template, template_dir, tmp_path, {"project_slug": "Definitely Invalid"})
