# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""The `Private :: Do Not Upload` classifier is emitted only for an unpublished package (#213).

PyPI rejects any distribution carrying that classifier, so it's a server-side guard against an
accidental upload of a package deliberately kept off PyPI. It must appear when a Python package
sets publish_to_pypi=false, and must NOT appear for a real release (which PyPI would then reject)
or for a non-package (nothing to upload).
"""

from __future__ import annotations

import tomllib
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

_PRIVATE = "Private :: Do Not Upload"

# (answers beyond the base) → whether the guard classifier must be present.
CASES = {
    "unpublished_package": (
        {"python_source": True, "is_package": True, "publish_to_pypi": False},
        True,
    ),
    "published_package": (
        {"python_source": True, "is_package": True, "publish_to_pypi": True},
        False,
    ),
    "non_package": ({"python_source": False}, False),
}


@pytest.mark.parametrize(("answers", "expected"), CASES.values(), ids=list(CASES))
def test_private_classifier_gating(
    answers: dict,
    expected: bool,  # noqa: FBT001
    template_dir: Path,
    tmp_path_factory: pytest.TempPathFactory,
    render_template: Callable[..., Path],
) -> None:
    """The upload-guard classifier appears exactly when a package opts out of publishing."""
    output = render_template(
        template_dir,
        tmp_path_factory.mktemp("upload_guard"),
        data={
            "project_name": "guard-demo",
            "author_name": "Tyler Nivin",
            "author_email": "tyler@nivin.tech",
            "repo_owner": "nivintw",
            "year": 2026,
            "contains_python": True,
            **answers,
        },
        skip_tasks=True,
    )
    classifiers = tomllib.loads((output / "pyproject.toml").read_text())["project"]["classifiers"]
    assert (_PRIVATE in classifiers) is expected
