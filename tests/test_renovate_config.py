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
import pytest

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def renovate_configs(template_dir: Path) -> dict[str, dict]:
    """Both renovate configs, keyed by their path relative to the repo root."""
    template_json = template_dir / "template/.github/renovate.json"
    root_json5 = template_dir / ".github/renovate.json5"
    return {
        "template/.github/renovate.json": json.loads(template_json.read_text()),
        ".github/renovate.json5": pyjson5.decode(root_json5.read_text()),
    }


def _checksum_rule(config: dict) -> dict:
    for rule in config["packageRules"]:
        if "postUpgradeTasks" in rule:
            return rule
    msg = "no postUpgradeTasks-scoped packageRules entry found"
    raise AssertionError(msg)


def test_renovate_checksum_pins_match_ci_yml(
    template_dir: Path, renovate_configs: dict[str, dict]
) -> None:
    """The checksum-scoped packageRule in both renovate configs must track the same tools."""
    ci_yml_jinja = (template_dir / "template/.github/workflows/ci.yml.jinja").read_text()
    # Scoped to datasource=github-releases: ci.yml.jinja also annotates pypi-sourced pins
    # (e.g. ansible-core, molecule, molecule-plugins, zizmor) that have no adjacent *_SHA256
    # and aren't part of the checksum-refresh script's TOOLS array — those correctly stay
    # untracked by this rule.
    annotated = set(re.findall(r"datasource=github-releases depName=(\S+)", ci_yml_jinja))
    assert annotated, "no github-releases depName annotations found in ci.yml.jinja — regex drift?"

    for name, config in renovate_configs.items():
        package_names = set(_checksum_rule(config)["matchPackageNames"])
        assert annotated == package_names, (
            f"{name}'s checksum packageRule has drifted from ci.yml.jinja"
        )


# Copied from nivintw/repo-management's .github/renovate-global.json, which owns BASE_REF too.
CENTRAL_ALLOWED_COMMAND = re.compile(r"^scripts/refresh-binary-checksums\.sh$")


def test_renovate_checksum_postupgradetask_matches_central_allowlist(
    renovate_configs: dict[str, dict],
) -> None:
    """The postUpgradeTask command must be one the central runner's allowedCommands accepts.

    Anything else, such as a command that also sets BASE_REF inline, is refused by the runner,
    so the pin is never refreshed and CI's checksum check fails on every tool bump.
    """
    for name, config in renovate_configs.items():
        commands = _checksum_rule(config)["postUpgradeTasks"]["commands"]
        assert all(CENTRAL_ALLOWED_COMMAND.match(command) for command in commands), (
            f"{name}'s checksum postUpgradeTask commands {commands!r} would be refused by the "
            "central runner's allowedCommands"
        )
