# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""Verify publish_to_galaxy actually gates publish-galaxy.yml's presence.

render-matrix.sh's quality gate (reuse/hawkeye/ansible-lint/etc.) passes regardless of whether
this workflow file exists, so a `when:` regression that always emits (or always omits) it would
go undetected without a direct presence/absence assertion.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    import pytest


def test_publish_to_galaxy_false_omits_workflow(
    template_dir: Path,
    output_dir_module_scope: Path,
    render_template: Callable[..., Path],
) -> None:
    """tests/answers/ansible-role.yml's publish_to_galaxy: false path (Galaxy publish opt-out)."""
    project_dir = render_template(
        template_dir,
        output_dir_module_scope,
        data={
            "project_name": "Ansible Role",
            "project_description": "ansible role shape",
            "test_frameworks": [],
            "contains_python": False,
            "contains_ansible": True,
            "ansible_kind": "role",
            "publish_to_galaxy": False,
        },
        skip_tasks=True,
    )
    assert not (project_dir / ".github/workflows/publish-galaxy.yml").exists(), (
        "publish_to_galaxy: false still emitted publish-galaxy.yml"
    )


def test_publish_to_galaxy_default_true_emits_workflow(
    template_dir: Path,
    tmp_path_factory: pytest.TempPathFactory,
    render_template: Callable[..., Path],
) -> None:
    """ansible-collection.yml's default: publish_to_galaxy tracks ansible_role_based."""
    project_dir = render_template(
        template_dir,
        tmp_path_factory.mktemp("rendered_galaxy_publish_true"),
        data={
            "project_name": "Ansible Collection",
            "project_description": "ansible collection shape",
            "test_frameworks": [],
            "contains_python": False,
            "contains_ansible": True,
            "ansible_kind": "collection",
        },
        skip_tasks=True,
    )
    assert (project_dir / ".github/workflows/publish-galaxy.yml").is_file(), (
        "publish_to_galaxy's default (ansible_role_based) didn't emit publish-galaxy.yml"
    )
