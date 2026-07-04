# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""Guard against the checksum-tracked tool list silently drifting between its three copies.

The 5 release binaries with a `# renovate: ... depName=X` annotation in ci.yml.jinja (trivy,
osv-scanner, hawkeye, taplo, kubeconform) must match the `matchPackageNames` list on the
checksum-refresh `packageRules` entry in BOTH renovate configs — otherwise a 6th tool added to
one place goes untracked (postUpgradeTasks never fires for it) or the scoping silently widens.
"""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING

import pyjson5

if TYPE_CHECKING:
    from pathlib import Path


def _checksum_rule_package_names(config: dict) -> set[str]:
    for rule in config["packageRules"]:
        if "postUpgradeTasks" in rule:
            return set(rule["matchPackageNames"])
    msg = "no postUpgradeTasks-scoped packageRules entry found"
    raise AssertionError(msg)


def test_renovate_checksum_pins_match_ci_yml(template_dir: Path) -> None:
    """The checksum-scoped packageRule in both renovate configs must track the same tools."""
    ci_yml_jinja = (template_dir / "template/.github/workflows/ci.yml.jinja").read_text()
    # Scoped to datasource=github-releases: ci.yml.jinja also annotates pypi-sourced pins
    # (e.g. ansible-core, molecule, molecule-plugins, zizmor) that have no adjacent *_SHA256
    # and aren't part of the checksum-refresh script's TOOLS array — those correctly stay
    # untracked by this rule.
    annotated = set(re.findall(r"datasource=github-releases depName=(\S+)", ci_yml_jinja))
    assert annotated, "no github-releases depName annotations found in ci.yml.jinja — regex drift?"

    template_config = json.loads((template_dir / "template/.github/renovate.json").read_text())
    root_config = pyjson5.decode((template_dir / ".github/renovate.json5").read_text())

    assert annotated == _checksum_rule_package_names(template_config), (
        "template/.github/renovate.json's checksum packageRule has drifted from "
        "ci.yml.jinja's depName annotations"
    )
    assert annotated == _checksum_rule_package_names(root_config), (
        ".github/renovate.json5's checksum packageRule has drifted from "
        "ci.yml.jinja's depName annotations"
    )
