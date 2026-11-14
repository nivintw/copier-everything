# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""dependabot-auto-merge.yml must auto-merge every Dependabot PR, fail-closed, behind CI.

Dependabot PRs here are security updates only (no dependabot.yml ships) and are CVE-driven, so
none of them waits on a severity gate or a release-age hold: each gets GitHub-native auto-merge
and lands once its required checks pass. Each assertion pins one property that, if it regressed,
would silently break the floor (merge nothing, or merge unchecked):

- pull_request_target, not pull_request — a Dependabot `pull_request` run gets a read-only
  token and NO Actions secrets, so it can neither mint the App token nor enable auto-merge.
- the merge goes through native auto-merge (`gh pr merge --auto`), which waits for the required
  checks and never uses the App's ruleset bypass rights.
- the template ships NO dependabot.yml — the floor is security-only; version freshness is
  Renovate's, and a version-updates dependabot.yml would collide with it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import yaml
from conftest import on_key

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


def test_dependabot_auto_merge_is_a_fail_closed_severity_gated_floor(
    template_dir: Path,
    output_dir_module_scope: Path,
    render_template: Callable[..., Path],
) -> None:
    """Every property the security floor relies on to merge the right PRs and nothing else."""
    project_dir = render_template(
        template_dir,
        output_dir_module_scope,
        data={"project_name": "Dependabot Auto Merge Check"},
        skip_tasks=True,
    )
    workflow = project_dir / ".github" / "workflows" / "dependabot-auto-merge.yml"
    assert workflow.is_file()
    text = workflow.read_text()
    doc = yaml.safe_load(text)

    # pull_request_target (the documented workaround for Dependabot's read-only token + no
    # secrets), never plain pull_request.
    trigger = on_key(doc)
    assert "pull_request_target" in trigger
    assert "pull_request" not in trigger

    job = doc["jobs"]["auto-merge"]
    # Trust gate: only Dependabot's own same-repo PRs.
    assert "dependabot[bot]" in job["if"]
    assert "github.event.pull_request.head.repo.full_name == github.repository" in job["if"]

    # Least privilege: the workflow's OWN token is read-only for a pull_request_target run; the
    # App token minted below carries the writes.
    assert doc["permissions"] == {"pull-requests": "read"}

    steps = job["steps"]

    # Fail-closed self-disable chain: the App-token step is gated on the App being configured,
    # and each later step is gated on the prior one having actually run — so an unconfigured repo
    # skips the whole chain cleanly (skipped != success) rather than erroring. Asserting each
    # guard directly, since removing any one would silently break the fail-closed posture.
    app_token = next(s for s in steps if "actions/create-github-app-token@" in s.get("uses", ""))
    assert "vars.CI_CLIENT_ID != ''" in app_token["if"]
    # The App token is what can enable auto-merge on a Dependabot PR; it needs only this one
    # permission.
    assert app_token["with"]["permission-pull-requests"] == "write"

    # No advisory lookup and no severity gate: every Dependabot PR is CVE-driven.
    assert not any("dependabot/fetch-metadata@" in s.get("uses", "") for s in steps)
    assert "permission-vulnerability-alerts" not in app_token["with"]
    assert "CVSS" not in text
    assert "ghsa" not in text.lower()

    # The merge step is gated on the token step, so it never runs on an unconfigured repo, and it
    # uses native auto-merge (the required checks gate it), after checking both repo settings
    # that `gh pr merge --auto --rebase` needs, fail-closed.
    merge = next(s for s in steps if "gh pr merge" in s.get("run", ""))
    assert "app-token.outcome == 'success'" in merge["if"]
    assert "allow_auto_merge" in merge["run"]
    assert "allow_rebase_merge" in merge["run"]
    assert "--auto --rebase" in merge["run"]

    # The floor is security-only: no version-updates dependabot.yml anywhere in the render.
    assert not list(project_dir.rglob("dependabot.yml")), (
        "the template must not ship a dependabot.yml — version updates are Renovate's job"
    )
