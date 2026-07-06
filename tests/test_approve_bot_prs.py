# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""approve-bot-prs.yml must trigger on pull_request_target, not pull_request.

pull_request executes the PR's OWN branch's copy of the workflow file — so a same-repo PR
that edits the trust-gate `if:` condition would have its own weakened version run for its
own approval, auto-approving itself via the github-actions[bot] identity (which sidesteps
GitHub's "can't approve your own PR" rule). pull_request_target anchors the workflow
DEFINITION to the base branch regardless of what the PR's branch contains, closing that gap.
This is safe specifically because the job does no checkout and holds no secrets.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


def _on_key(doc: dict) -> dict:
    """The ``on:`` block, under either representation (bool ``True`` or the string ``"on"``)."""
    return doc[True] if True in doc else doc["on"]


def test_approve_bot_prs_triggers_on_pull_request_target(
    template_dir: Path,
    output_dir_module_scope: Path,
    render_template: Callable[..., Path],
) -> None:
    """A same-repo PR must not be able to run its own weakened trust-gate condition."""
    project_dir = render_template(
        template_dir,
        output_dir_module_scope,
        data={"project_name": "Approve Bot PRs Check"},
        skip_tasks=True,
    )
    workflow = project_dir / ".github" / "workflows" / "approve-bot-prs.yml"
    assert workflow.is_file()
    workflow_yaml = yaml.safe_load(workflow.read_text())
    trigger = _on_key(workflow_yaml)

    assert "pull_request_target" in trigger, (
        "approve-bot-prs.yml must use pull_request_target, not pull_request — the latter "
        "lets a same-repo PR run its own weakened copy of the trust-gate condition"
    )
    assert "pull_request" not in trigger
