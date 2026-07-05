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
import subprocess
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


def test_renovate_checksum_postupgradetask_sets_base_ref(renovate_configs: dict[str, dict]) -> None:
    """The postUpgradeTask command must set BASE_REF.

    Otherwise refresh-binary-checksums.sh's supply-chain tamper gate is silently off on this
    automated path (only a human running the script locally would set it themselves).
    """
    for name, config in renovate_configs.items():
        commands = _checksum_rule(config)["postUpgradeTasks"]["commands"]
        assert any("BASE_REF=" in command for command in commands), (
            f"{name}'s checksum postUpgradeTask command doesn't set BASE_REF — "
            "the tamper gate would be silently off"
        )


def test_renovate_checksum_postupgradetask_fails_loudly_without_origin_head(
    tmp_path: Path, renovate_configs: dict[str, dict]
) -> None:
    """The BASE_REF computation must fail the whole command, not silently resolve empty.

    `BASE_REF="$(git merge-base HEAD origin/HEAD)" scripts/refresh-binary-checksums.sh` (the
    pre-fix form) still exits 0 if the merge-base fails — a command-substitution failure
    inside an env-var-prefix position doesn't propagate to the outer command's exit status.
    A runner whose clone never set up the `origin/HEAD` symref (git fetch, unlike git clone,
    doesn't create it) would silently degrade back to the tamper gate being off. Reproduce
    that exact git state — no `origin/HEAD` — and confirm the command now fails instead.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)  # noqa: S607
    subprocess.run(["git", "config", "user.email", "test@test"], cwd=repo, check=True)  # noqa: S607
    subprocess.run(["git", "config", "user.name", "test"], cwd=repo, check=True)  # noqa: S607
    (repo / "f").write_text("x")
    subprocess.run(["git", "add", "f"], cwd=repo, check=True)  # noqa: S607
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)  # noqa: S607
    # No `origin` remote at all, so `origin/HEAD` cannot resolve — the scenario this test guards.

    # A real stub (not a missing-file 127) so a silently-empty BASE_REF is distinguishable
    # from a correctly-blocked run purely by whether the stub actually executed — a missing
    # script file would coincidentally also make the pre-fix command's exit status non-zero,
    # for an unrelated reason, and mask the very regression this test exists to catch.
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir()
    stub = scripts_dir / "refresh-binary-checksums.sh"
    stub.write_text("#!/bin/sh\necho STUB_RAN\n")
    stub.chmod(0o755)

    for name, config in renovate_configs.items():
        command = _checksum_rule(config)["postUpgradeTasks"]["commands"][0]
        result = subprocess.run(  # noqa: S602
            command, shell=True, cwd=repo, capture_output=True, text=True, check=False
        )
        assert result.returncode != 0, (
            f"{name}'s postUpgradeTask command must fail when BASE_REF can't be computed, "
            f"not silently continue with the tamper gate off (stdout={result.stdout!r})"
        )
        assert "STUB_RAN" not in result.stdout, (
            f"{name}'s command ran the script despite BASE_REF failing to resolve — "
            "the tamper gate would have silently been off"
        )
        assert "could not compute BASE_REF" in result.stderr, (
            f"{name}'s failure should name the BASE_REF computation as the cause: {result.stderr!r}"
        )
