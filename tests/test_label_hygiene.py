# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""label-hygiene.yml must re-check the issue is still closed before stripping labels.

The workflow only triggers on the `closed` event, and reopening an issue doesn't emit a
second event to cancel or supersede that scheduled run — so without a live state check, a
reopen racing between the event firing and the step executing would still strip a now-active
issue's status:* label using stale trigger data.

These tests execute the extracted `run:` shell script directly (with a stubbed `gh` on
PATH), rather than just asserting the expected strings appear in the rendered workflow — a
static string/ordering check can't tell an inverted condition or a wrong jq path from a
working one, since the same substrings can be present either way.
"""

from __future__ import annotations

import json
import os
import subprocess
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

_FAKE_GH = r"""#!/bin/sh
set -e
if [ "$1" = "issue" ] && [ "$2" = "view" ]; then
  # The step re-checks state twice: once for the full state,labels blob (no --jq), and
  # again right before the mutating edit via --jq '.state' (matching real gh's raw-string
  # output for a scalar jq result) — so the stub reads from two independently-controlled
  # fixtures rather than just catting the same one both times, so a test can simulate a
  # reopen landing specifically in the window the second check exists to close.
  case "$*" in
    *--jq*) cat "$FAKE_GH_ISSUE_VIEW_STATE_RESPONSE" ;;
    *) cat "$FAKE_GH_ISSUE_VIEW_RESPONSE" ;;
  esac
  exit 0
fi
if [ "$1" = "issue" ] && [ "$2" = "edit" ]; then
  echo "$*" >> "$FAKE_GH_EDIT_CALLS_LOG"
  exit 0
fi
echo "unexpected gh invocation: $*" >&2
exit 1
"""


def _extract_run_script(
    template_dir: Path, output_dir: Path, render_template: Callable[..., Path]
) -> str:
    project_dir = render_template(
        template_dir,
        output_dir,
        data={"project_name": "Label Hygiene Check"},
        skip_tasks=True,
    )
    workflow = project_dir / ".github" / "workflows" / "label-hygiene.yml"
    assert workflow.is_file()
    workflow_yaml = yaml.safe_load(workflow.read_text())
    return workflow_yaml["jobs"]["strip-status-labels"]["steps"][0]["run"]


def _run_script(
    script: str, tmp_path: Path, *, issue_json: str, recheck_state: str | None = None
) -> tuple[subprocess.CompletedProcess, Path]:
    """Run the extracted step against a stubbed gh.

    `recheck_state` controls the SECOND `gh issue view` call (the one right before the
    mutating edit) independently of the first — defaulting to the first check's own state
    so existing callers don't need to care, but overridable to simulate a reopen landing
    specifically between the two checks.
    """
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    gh_stub = fake_bin / "gh"
    gh_stub.write_text(_FAKE_GH)
    gh_stub.chmod(0o755)

    issue_view_response = tmp_path / "issue_view_response.json"
    issue_view_response.write_text(issue_json)
    issue_view_state_response = tmp_path / "issue_view_state_response.txt"
    issue_view_state_response.write_text(recheck_state or json.loads(issue_json)["state"])
    edit_calls_log = tmp_path / "edit_calls.log"

    env = {
        **os.environ,
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
        "GH_TOKEN": "fake-token",
        "ISSUE": "42",
        "REPO": "owner/repo",
        "FAKE_GH_ISSUE_VIEW_RESPONSE": str(issue_view_response),
        "FAKE_GH_ISSUE_VIEW_STATE_RESPONSE": str(issue_view_state_response),
        "FAKE_GH_EDIT_CALLS_LOG": str(edit_calls_log),
    }
    result = subprocess.run(  # noqa: S603
        ["bash", "-c", script],  # noqa: S607
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    return result, edit_calls_log


def test_label_hygiene_skips_stripping_when_reopened(
    template_dir: Path,
    output_dir_module_scope: Path,
    render_template: Callable[..., Path],
    tmp_path: Path,
) -> None:
    """A reopen racing the scheduled run must leave the issue's labels untouched."""
    script = _extract_run_script(template_dir, output_dir_module_scope, render_template)
    issue_json = '{"state": "OPEN", "labels": [{"name": "status:in-progress"}]}'

    result, edit_calls_log = _run_script(script, tmp_path, issue_json=issue_json)

    assert result.returncode == 0, result.stderr
    assert not edit_calls_log.exists(), (
        "gh issue edit --remove-label must not run on a reopened issue"
    )
    assert "no longer closed" in result.stdout.lower()


def test_label_hygiene_skips_stripping_when_reopened_between_checks(
    template_dir: Path,
    output_dir_module_scope: Path,
    render_template: Callable[..., Path],
    tmp_path: Path,
) -> None:
    """A reopen landing between the checks must skip stripping too.

    This is the actual TOCTOU gap the second re-check exists to close (#195) — not just a
    reopen caught by the first check (test_label_hygiene_skips_stripping_when_reopened).
    """
    script = _extract_run_script(template_dir, output_dir_module_scope, render_template)
    issue_json = '{"state": "CLOSED", "labels": [{"name": "status:in-review"}]}'

    result, edit_calls_log = _run_script(
        script, tmp_path, issue_json=issue_json, recheck_state="OPEN"
    )

    assert result.returncode == 0, result.stderr
    assert not edit_calls_log.exists(), (
        "gh issue edit --remove-label must not run when the second re-check finds it reopened"
    )
    assert "no longer closed" in result.stdout.lower()


def test_label_hygiene_strips_labels_when_still_closed(
    template_dir: Path,
    output_dir_module_scope: Path,
    render_template: Callable[..., Path],
    tmp_path: Path,
) -> None:
    """The happy path — issue still closed — must still strip its status:* labels."""
    script = _extract_run_script(template_dir, output_dir_module_scope, render_template)
    issue_json = (
        '{"state": "CLOSED", "labels": '
        '[{"name": "status:in-review"}, {"name": "type:bug"}, {"name": "priority:high"}]}'
    )

    result, edit_calls_log = _run_script(script, tmp_path, issue_json=issue_json)

    assert result.returncode == 0, result.stderr
    assert edit_calls_log.exists(), "gh issue edit --remove-label must run on a still-closed issue"
    call = edit_calls_log.read_text()
    assert "--remove-label status:in-review" in call
    # type:*/priority:* are historical record and must never be removed.
    assert "type:bug" not in call
    assert "priority:high" not in call


def test_label_hygiene_noop_when_no_status_labels(
    template_dir: Path,
    output_dir_module_scope: Path,
    render_template: Callable[..., Path],
    tmp_path: Path,
) -> None:
    """No status:* label present must be a clean no-op, not an error."""
    script = _extract_run_script(template_dir, output_dir_module_scope, render_template)
    issue_json = '{"state": "CLOSED", "labels": [{"name": "type:bug"}]}'

    result, edit_calls_log = _run_script(script, tmp_path, issue_json=issue_json)

    assert result.returncode == 0, result.stderr
    assert not edit_calls_log.exists()
