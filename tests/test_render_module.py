# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""Guard that the render logic stays in ONE importable module (tests/render_support.py).

The template is rendered from two places — the pytest `render_template` fixture and
scripts/resync_twins.py — so the render invariants live in render_support.render, and both
callers go through it. This guards against the fixture drifting back into a private
re-implementation: if someone inlines the render in conftest again, the identity check below
fails, because the fixture must BE render_support.render, not a copy of it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import render_support

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


def test_render_fixture_delegates_to_the_shared_module(
    render_template: Callable[..., Path],
) -> None:
    """The render_template fixture must return render_support.render, not a re-implementation."""
    assert render_template is render_support.render, (
        "the render_template fixture must delegate to render_support.render "
        "(don't re-implement the render — resync_twins.py shares that one module)"
    )


def test_shared_module_is_importable_by_non_test_code() -> None:
    """render_support exposes the render helper + dogfood answers for scripts/resync_twins."""
    assert callable(render_support.render)
    assert render_support.DOGFOOD_DATA["project_name"] == "copier-everything"
