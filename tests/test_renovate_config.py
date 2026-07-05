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


def _checksum_rule_commands(config: dict) -> list[str]:
    for rule in config["packageRules"]:
        if "postUpgradeTasks" in rule:
            return rule["postUpgradeTasks"]["commands"]
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


def test_renovate_checksum_postupgradetask_sets_base_ref(template_dir: Path) -> None:
    """The postUpgradeTask command must set BASE_REF, or refresh-binary-checksums.sh's
    supply-chain tamper gate is silently off on this automated path (only a human running the
    script locally would set it themselves).
    """
    template_config = json.loads((template_dir / "template/.github/renovate.json").read_text())
    root_config = pyjson5.decode((template_dir / ".github/renovate.json5").read_text())

    for name, config in [("template/.github/renovate.json", template_config), (".github/renovate.json5", root_config)]:
        commands = _checksum_rule_commands(config)
        assert any("BASE_REF=" in command for command in commands), (
            f"{name}'s checksum postUpgradeTask command doesn't set BASE_REF — "
            "the tamper gate would be silently off"
        )
