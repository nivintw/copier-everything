# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""Static config-content invariants for the generated ansible.cfg.

ansible-lint's static analysis doesn't resolve or require a working inventory, so it wouldn't
catch a missing `inventory =` setting (nor would it catch a regression reintroducing one).
"""

from __future__ import annotations

import configparser
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


def test_ansible_cfg_sets_inventory_path(
    template_dir: Path,
    output_dir_module_scope: Path,
    render_template: Callable[..., Path],
) -> None:
    """Verify ansible.cfg sets an inventory path for the playbooks quickstart.

    The documented `ansible-playbook playbooks/site.yml` quickstart needs `inventory =` under
    [defaults], or it silently falls back to Ansible's implicit localhost-only inventory
    instead of the scaffolded inventory/ directory.
    """
    project_dir = render_template(
        template_dir,
        output_dir_module_scope,
        data={
            "project_name": "Ansible Playbooks",
            "project_description": "ansible playbook project shape",
            "test_frameworks": [],
            "contains_python": False,
            "contains_ansible": True,
            "ansible_kind": "playbooks",
        },
        skip_tasks=True,
    )
    config = configparser.ConfigParser()
    config.read(project_dir / "ansible.cfg")
    assert config.get("defaults", "inventory") == "./inventory"
