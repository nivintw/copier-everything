# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""Verify copier.yml's `year` question: the dynamic default and its bounds validator.

Neither is exercised by tests/render-matrix.sh's fixtures (none of them override `year`), so a
regression in the strftime-derived default or an inverted/off-by-one bounds check would only
surface as an opaque render failure for a real user, with nothing pointing at the cause.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


def test_year_default_is_current_year(
    template_dir: Path,
    output_dir_module_scope: Path,
    render_template: Callable[..., Path],
) -> None:
    """An unanswered `year` question defaults to the render-time year, not a stale literal.

    copier.yml's `strftime` filter (jinja2_ansible_filters) formats `time.localtime()`, not
    UTC — bracket the render with before/after local-year captures (not a single UTC read) so
    the assertion can't flake around midnight, a DST transition, or a UTC/local mismatch.
    """
    before_year = time.localtime().tm_year
    project_dir = render_template(
        template_dir,
        output_dir_module_scope,
        data={"project_name": "Year Default Test"},
        skip_tasks=True,
    )
    after_year = time.localtime().tm_year
    answers = (project_dir / ".copier-answers.yml").read_text()
    assert any(f"year: {y}" in answers for y in {before_year, after_year}), (
        f"expected year to default to the current year ({before_year} or {after_year}), "
        f"got:\n{answers}"
    )


@pytest.mark.parametrize("year", [1999, 2101])
def test_year_validator_rejects_out_of_bounds(
    template_dir: Path,
    tmp_path_factory: pytest.TempPathFactory,
    render_template: Callable[..., Path],
    year: int,
) -> None:
    """The 2000-2100 bounds validator rejects implausible years just outside the range."""
    with pytest.raises(ValueError, match="plausible 4-digit year"):
        render_template(
            template_dir,
            tmp_path_factory.mktemp(f"rendered_year_{year}"),
            data={"project_name": "Year Bounds Test", "year": year},
            skip_tasks=True,
        )


@pytest.mark.parametrize("year", [2000, 2100])
def test_year_validator_accepts_boundary_values(
    template_dir: Path,
    tmp_path_factory: pytest.TempPathFactory,
    render_template: Callable[..., Path],
    year: int,
) -> None:
    """The 2000-2100 bounds validator accepts its own inclusive boundary values."""
    project_dir = render_template(
        template_dir,
        tmp_path_factory.mktemp(f"rendered_year_{year}"),
        data={"project_name": "Year Bounds Test", "year": year},
        skip_tasks=True,
    )
    assert f"year: {year}" in (project_dir / ".copier-answers.yml").read_text()
