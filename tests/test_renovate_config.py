# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""The Renovate shims and caller must pin repo-management to one consistent release.

Every Renovate rule lives in nivintw/repo-management (renovate/default.json5, plus
copier-template.json5 for this repo); the generated project's .github/renovate.json5 and this
repo's own only extend those at a release tag, and .github/workflows/renovate.yml calls the
reusable workflow at that release's commit. If the three pins drifted apart, a repo would run
one release's workflow (its allowedCommands, its Renovate version) against another release's
rules. Renovate moves them together in one PR, so they must start out in lockstep.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pyjson5
import yaml

if TYPE_CHECKING:
    from pathlib import Path

PRESET = re.compile(
    r"^github>nivintw/repo-management//renovate/(?P<name>[\w-]+)\.json5#(?P<tag>v\d+\.\d+\.\d+)$"
)
CALLER_USES = re.compile(
    r"uses: nivintw/repo-management/\.github/workflows/reusable-renovate\.yml"
    r"@(?P<sha>[0-9a-f]{40}) # (?P<tag>v\d+\.\d+\.\d+)$",
    re.MULTILINE,
)


def _render_shim(template_dir: Path) -> str:
    """The template shim with its two header placeholders filled, as copier would."""
    text = (template_dir / "template/.github/renovate.json5.jinja").read_text()
    return (
        text.replace("{{ year }}", "2026")
        .replace("{{ author_name }}", "x")
        .replace("{{ license }}", "MIT")
    )


def _preset_tags(config: dict) -> dict[str, str]:
    tags = {}
    for entry in config["extends"]:
        match = PRESET.match(entry)
        assert match, f"extends entry {entry!r} isn't a tag-pinned repo-management preset"
        tags[match["name"]] = match["tag"]
    return tags


def test_template_shim_extends_only_the_shared_default(template_dir: Path) -> None:
    """A generated project carries no rules of its own: just default.json5 at a tag."""
    config = pyjson5.decode(_render_shim(template_dir))
    assert set(config) <= {"$schema", "extends"}
    assert list(_preset_tags(config)) == ["default"]
    assert not (template_dir / "template/.github/renovate.json").exists()


def test_root_shim_adds_only_the_copier_template_preset(template_dir: Path) -> None:
    """This repo extends default.json5 plus copier-template.json5, both at the same tag."""
    config = pyjson5.decode((template_dir / ".github/renovate.json5").read_text())
    assert set(config) <= {"$schema", "extends"}
    tags = _preset_tags(config)
    assert list(tags) == ["default", "copier-template"]
    assert len(set(tags.values())) == 1


def test_shims_and_caller_pin_the_same_release(template_dir: Path) -> None:
    """Template shim, root shim, template caller and root caller all name one release."""
    tags = set(_preset_tags(pyjson5.decode(_render_shim(template_dir))).values())
    tags |= set(
        _preset_tags(pyjson5.decode((template_dir / ".github/renovate.json5").read_text())).values()
    )
    for caller in (
        template_dir / "template/.github/workflows/renovate.yml.jinja",
        template_dir / ".github/workflows/renovate.yml",
    ):
        match = CALLER_USES.search(caller.read_text())
        assert match, (
            f"{caller} doesn't call reusable-renovate.yml pinned by SHA with a tag comment"
        )
        tags.add(match["tag"])
    assert len(tags) == 1, f"repo-management pins disagree: {sorted(tags)}"


def test_caller_fails_closed_and_passes_only_the_renovate_credentials(template_dir: Path) -> None:
    """No RENOVATE_CLIENT_ID means no run; only the Renovate App's key is passed, never inherit."""
    doc = yaml.safe_load((template_dir / ".github/workflows/renovate.yml").read_text())
    job = doc["jobs"]["renovate"]
    assert job["if"] == "vars.RENOVATE_CLIENT_ID != ''"
    assert job["secrets"] == {"RENOVATE_APP_PRIVATE_KEY": "${{ secrets.RENOVATE_APP_PRIVATE_KEY }}"}
    assert doc["permissions"] == {}
