# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""label-hygiene.yml must re-check the issue is still closed before stripping labels.

The workflow only triggers on the `closed` event, and reopening an issue doesn't emit a
second event to cancel or supersede that scheduled run — so without a live state check, a
reopen racing between the event firing and the step executing would still strip a now-active
issue's status:* label using stale trigger data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


def test_label_hygiene_rechecks_state_before_stripping(
    template_dir: Path,
    output_dir_module_scope: Path,
    render_template: Callable[..., Path],
) -> None:
    project_dir = render_template(
        template_dir,
        output_dir_module_scope,
        data={"project_name": "Label Hygiene Check"},
        skip_tasks=True,
    )
    workflow = project_dir / ".github" / "workflows" / "label-hygiene.yml"
    assert workflow.is_file()
    script = workflow.read_text()

    # Must fetch state alongside labels in the same call, then bail before stripping anything
    # if the issue is no longer closed.
    assert '--json state,labels' in script
    assert '"$state" != "CLOSED"' in script

    # The state check must come before the label-removal loop, not after.
    state_check_pos = script.index('"$state" != "CLOSED"')
    remove_label_pos = script.index("--remove-label")
    assert state_check_pos < remove_label_pos
