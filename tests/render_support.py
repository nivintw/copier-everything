# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""The shared render helper — the single place the template is rendered.

Both the pytest `render_template` fixture (tests/conftest.py) and the twin resync helper
(scripts/resync_twins.py) render through `render()` here, so the render invariants
(``vcs_ref="HEAD"``, DirtyLocalWarning suppression, ``unsafe``/``defaults``) live in ONE place
instead of being duplicated. tests/test_render_module.py guards the fixture against drifting
away from this module.
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

from copier import run_copy
from copier.errors import DirtyLocalWarning

if TYPE_CHECKING:
    from pathlib import Path

# The dogfood answer set: the shape copier-everything's own repo root is rendered as ("pytest,
# no python source"). author identity + year are pinned explicitly because copier.yml's own
# defaults are deliberately generic placeholders — a render meant to match this repo's real root
# needs its real identity, and `year` otherwise tracks the render-time clock (which would start
# failing every byte-for-byte twin comparison the moment the calendar rolls over).
DOGFOOD_DATA: dict[str, object] = {
    "project_name": "copier-everything",
    "python_source": False,
    "author_name": "Tyler Nivin",
    "author_email": "tyler@nivin.tech",
    "repo_owner": "nivintw",
    "year": 2026,
}


def render(template_dir: Path, output_dir: Path, *, data: dict, skip_tasks: bool) -> Path:
    """Render the template at its working-tree HEAD into `output_dir`; return `output_dir`.

    With ``vcs_ref="HEAD"`` against a dirty local checkout, copier renders the current
    working-tree state (uncommitted + untracked template changes included) and emits a
    DirtyLocalWarning saying so; the warning is suppressed (not asserted). Because callers read
    the root side off the working tree too, both sides reflect the working tree and stay
    consistent whether or not it's clean. On a clean checkout (e.g. CI) working tree and HEAD
    coincide.
    """
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DirtyLocalWarning)
        run_copy(
            str(template_dir),
            str(output_dir),
            data=data,
            defaults=True,
            unsafe=True,
            vcs_ref="HEAD",
            skip_tasks=skip_tasks,
        )
    return output_dir
