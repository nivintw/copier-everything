# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""dependabot-auto-merge.yml must be a severity-gated, fail-closed security-floor merger.

The workflow auto-merges only CRITICAL/HIGH Dependabot *security* PRs, and only via a path
that actually works under GitHub's Dependabot hardening. Each assertion below pins one property
that, if it regressed, would silently break the floor (merge nothing, or merge too much):

- pull_request_target, not pull_request — a Dependabot `pull_request` run gets a read-only
  token and NO Actions secrets, so it can neither mint the App token nor enable auto-merge.
- the advisory lookup uses the App token (GITHUB_TOKEN cannot read Dependabot alerts) with the
  vulnerability-alerts read permission, and `alert-lookup: true`.
- the merge is gated on a real advisory (ghsa-id) AND CVSS >= 7.0, so version updates and
  Medium/Low security PRs are left open.
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
    # The App token is what makes the advisory lookup possible, and it must carry exactly the two
    # permissions the job needs — incl. vulnerability-alerts read, which GITHUB_TOKEN can't grant.
    assert app_token["with"]["permission-vulnerability-alerts"] == "read"
    assert app_token["with"]["permission-pull-requests"] == "write"

    # fetch-metadata must do the advisory lookup, gated on the token step, and use the App token
    # (not GITHUB_TOKEN, which can't read Dependabot alerts).
    meta = next(s for s in steps if "dependabot/fetch-metadata@" in s.get("uses", ""))
    assert "app-token.outcome == 'success'" in meta["if"]
    assert meta["with"]["alert-lookup"] is True
    assert "app-token" in meta["with"]["github-token"]
    assert "github.token" not in meta["with"]["github-token"]

    # The merge step is gated on the metadata step, so it never runs on an unconfigured repo.
    merge = next(s for s in steps if "gh pr merge" in s.get("run", ""))
    assert "meta.outcome == 'success'" in merge["if"]

    # Severity gate: a version update / unresolved advisory (empty ghsa-id) is left open; only a
    # real advisory at CVSS >= 7.0 (High/Critical) instant-merges; "Allow auto-merge" is checked
    # (fail-closed) before the rebase auto-merge. Assert the GUARDS themselves, not just the env
    # wiring — `GHSA:` alone would match the env line and prove nothing about the -z guard.
    assert '-z "${GHSA}"' in text  # empty-advisory guard → version updates left open
    assert ">= 7.0" in text  # the High/Critical CVSS threshold
    # Both repo settings that gate `gh pr merge --auto --rebase` are checked fail-closed.
    assert "allow_auto_merge" in text
    assert "allow_rebase_merge" in text
    assert "gh pr merge" in text
    assert "--auto --rebase" in text

    # The floor is security-only: no version-updates dependabot.yml anywhere in the render.
    assert not list(project_dir.rglob("dependabot.yml")), (
        "the template must not ship a dependabot.yml — version updates are Renovate's job"
    )
