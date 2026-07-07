# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""The release_model question renders a single- or multi-package release-please config (#234).

single (the default) keeps today's single `.` package. multi-package renders one release-please
package (in both the config and the manifest) per declared release_packages path, and the
release_packages list is validated (non-empty, repo-relative paths) when that model is chosen.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

_BASE: dict[str, object] = {
    "project_name": "release-demo",
    "author_name": "Tyler Nivin",
    "author_email": "tyler@nivin.tech",
    "repo_owner": "nivintw",
    "year": 2026,
    "test_frameworks": [],
    "contains_python": False,
}


def _release_config(project: Path) -> dict:
    return json.loads((project / ".config" / "release-please-config.json").read_text())


def _manifest(project: Path) -> dict:
    return json.loads((project / ".config" / ".release-please-manifest.json").read_text())


def test_single_model_is_unchanged(
    template_dir: Path,
    tmp_path_factory: pytest.TempPathFactory,
    render_template: Callable[..., Path],
) -> None:
    """The default (single) model still renders exactly one `.` package."""
    project = render_template(
        template_dir,
        tmp_path_factory.mktemp("release_single"),
        data={**_BASE, "release_model": "single"},
        skip_tasks=True,
    )
    assert list(_release_config(project)["packages"]) == ["."]
    assert _manifest(project) == {".": "0.0.0"}


def test_multi_package_model_declares_each_package(
    template_dir: Path,
    tmp_path_factory: pytest.TempPathFactory,
    render_template: Callable[..., Path],
) -> None:
    """multi-package renders one release-please package per declared path, in config + manifest."""
    project = render_template(
        template_dir,
        tmp_path_factory.mktemp("release_multi"),
        data={
            **_BASE,
            "release_model": "multi-package",
            "release_packages": "packages/api, packages/cli",
        },
        skip_tasks=True,
    )
    assert list(_release_config(project)["packages"]) == ["packages/api", "packages/cli"]
    assert _manifest(project) == {"packages/api": "0.0.0", "packages/cli": "0.0.0"}


@pytest.mark.parametrize("bad", ["", "  ", "/abs/path", "../escape", "has space"])
def test_release_packages_is_validated(
    bad: str,
    template_dir: Path,
    tmp_path_factory: pytest.TempPathFactory,
    render_template: Callable[..., Path],
) -> None:
    """An empty or non-repo-relative release_packages is rejected for the multi-package model."""
    with pytest.raises(ValueError, match="release_packages"):
        render_template(
            template_dir,
            tmp_path_factory.mktemp("release_bad"),
            data={**_BASE, "release_model": "multi-package", "release_packages": bad},
            skip_tasks=True,
        )
