# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""Offline JSON-schema validation of the rendered pyproject.toml, for BOTH render shapes.

The heavy bash gate validates the rendered pyproject via the `validate-pyproject` CLI, but never
in pytest, never per render-shape. This validates it in-process for both shapes copier can emit —
a build-backed installable package, and the tooling-only (non-package) shape — catching a
malformed [project]/[build-system] the render might produce (a bad requires-python, a wrong-typed
field). It's fully offline and hermetic: validate-pyproject bundles the PEP 621 + build-backend
schemas, pinned by the dev-dependency version, so no network and no vendored schema files.
"""

from __future__ import annotations

import tomllib
from typing import TYPE_CHECKING

import pytest
from validate_pyproject import api, errors

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

# The two Python render shapes: a build-backed installable dist, and tooling/tests-only (no
# build-system, no dist metadata). Both still render a pyproject.toml (has_python is true via the
# default pytest framework), and both must be schema-valid.
SHAPES: dict[str, dict[str, object]] = {
    "package": {"python_source": True, "is_package": True, "publish_to_pypi": False},
    "non_package": {"python_source": False},
}

_BASE_ANSWERS: dict[str, object] = {
    "project_name": "schema-demo",
    "author_name": "Tyler Nivin",
    "author_email": "tyler@nivin.tech",
    "repo_owner": "nivintw",
    "year": 2026,
}


@pytest.mark.parametrize("shape", list(SHAPES), ids=list(SHAPES))
def test_rendered_pyproject_is_schema_valid(
    shape: str,
    template_dir: Path,
    tmp_path_factory: pytest.TempPathFactory,
    render_template: Callable[..., Path],
) -> None:
    """The rendered pyproject.toml validates against the PEP 621/build-backend schema, offline."""
    output = render_template(
        template_dir,
        tmp_path_factory.mktemp(f"schema_{shape}"),
        data={**_BASE_ANSWERS, **SHAPES[shape]},
        skip_tasks=True,
    )
    pyproject = output / "pyproject.toml"
    assert pyproject.is_file(), f"the {shape} shape rendered no pyproject.toml"
    parsed = tomllib.loads(pyproject.read_text())
    # Raises validate_pyproject.errors.ValidationError on a schema-invalid pyproject.
    api.Validator()(parsed)


def test_validator_actually_rejects_a_bad_pyproject() -> None:
    """Guard the guard: a deliberately-malformed pyproject must fail, or the check is vacuous."""
    # `version` must be a string, not an int — a schema violation the validator has to catch.
    with pytest.raises(errors.ValidationError):
        api.Validator()({"project": {"name": "x", "version": 123}})
