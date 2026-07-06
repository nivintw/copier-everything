# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""Verify copier.yml's author_name/author_email/repo_owner default to generic placeholders.

None of tests/render-matrix.sh's fixtures override these, so a regression that re-hardcodes
the template author's own identity as the default would only surface as someone else's
name/email/GitHub handle silently leaking into every new repo generated from this template.

Copier's own per-user `defaults:` (settings.yml) take precedence over copier.yml's default
(see docs/questions.md) — on a machine that has one configured for these exact keys (e.g.
the maintainer's own), a plain render would reflect *that* file, not copier.yml, making this
test machine-dependent. Point COPIER_SETTINGS_PATH at a path that doesn't exist so the
render always falls through to copier.yml's own default, matching what a fresh machine (or
CI) sees.
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

from copier.errors import MissingSettingsWarning

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    import pytest


def test_author_identity_defaults_are_generic_not_the_maintainers_own(
    template_dir: Path,
    output_dir_module_scope: Path,
    render_template: Callable[..., Path],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """An unanswered render gets placeholder identity, never Tyler's real info."""
    no_settings_path = tmp_path_factory.mktemp("no_copier_settings") / "settings.yml"
    monkeypatch.setenv("COPIER_SETTINGS_PATH", str(no_settings_path))
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=MissingSettingsWarning)
        project_dir = render_template(
            template_dir,
            output_dir_module_scope,
            data={"project_name": "Author Identity Default Test"},
            skip_tasks=True,
        )
    answers = (project_dir / ".copier-answers.yml").read_text()
    assert "author_name: Your Name" in answers
    assert "author_email: you@example.com" in answers
    assert "repo_owner: your-github-username" in answers
    assert "Tyler Nivin" not in answers
    assert "tyler@nivin.tech" not in answers
    assert "nivintw" not in answers
