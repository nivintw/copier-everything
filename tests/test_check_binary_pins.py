# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""scripts/check-binary-pins.sh must fail when a release-binary pin moves without its version.

Runs the real script against a throwaway git repo: a base commit with a pinned tool, then a
head commit that changes the workflow in a particular way.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "check-binary-pins.sh"
GIT = shutil.which("git") or "git"

BASE = """jobs:
  lint:
    steps:
      - env:
          TRIVY_VERSION: "0.70.0"
          TRIVY_SHA256: "aaaa"
          BATS_VERSION: "1.12.0"
          BATS_COMMIT: "1111"
"""


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(  # noqa: S603 - fixed test inputs, no shell
        [GIT, *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()


def _run(tmp_path: Path, head: str | None, extra: dict[str, str] | None = None) -> int:
    repo = tmp_path / "repo"
    workflows = repo / ".github" / "workflows"
    workflows.mkdir(parents=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")
    (workflows / "ci.yml").write_text(BASE)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "base")
    base = _git(repo, "rev-parse", "HEAD")
    if head is not None:
        (workflows / "ci.yml").write_text(head)
    for name, text in (extra or {}).items():
        (workflows / name).write_text(text)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "head", "--allow-empty")
    return subprocess.run(  # noqa: S603 - fixed test inputs, no shell
        [SCRIPT, base], cwd=repo, capture_output=True, check=False
    ).returncode


@pytest.mark.parametrize(
    "head",
    [
        BASE.replace('"0.70.0"', '"0.71.0"').replace('"aaaa"', '"bbbb"'),  # version bump + re-pin
        BASE.replace('"1.12.0"', '"1.13.0"').replace('"1111"', '"2222"'),  # same, *_COMMIT pin
        BASE.replace("lint:", "build:"),  # unrelated change
    ],
)
def test_pins_that_move_with_their_version_pass(tmp_path: Path, head: str) -> None:
    """A pin that moves together with its version, or no pin change at all, passes."""
    assert _run(tmp_path, head) == 0


@pytest.mark.parametrize(
    "head",
    [
        BASE.replace('"aaaa"', '"bbbb"'),  # SHA swapped under an unchanged version
        BASE.replace('"1111"', '"2222"'),  # commit swapped under an unchanged version
    ],
)
def test_a_pin_that_moves_alone_fails(tmp_path: Path, head: str) -> None:
    """A swapped asset under an unchanged version fails, for both pin kinds."""
    assert _run(tmp_path, head) == 1


def test_a_new_workflow_file_has_nothing_to_compare(tmp_path: Path) -> None:
    """A workflow file that's new in the PR has no earlier pin, so it can't fail the check."""
    assert _run(tmp_path, None, {"new.yml": BASE.replace('"aaaa"', '"cccc"')}) == 0
