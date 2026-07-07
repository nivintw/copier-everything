# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""The main.yml stranded-Release-PR guard's jq filters must classify authorship correctly.

The "Close any stranded (DIRTY) Release PRs" step is two jq filters embedded in a workflow: a
phase-1 candidate selector and a phase-2 non-bot-author extractor. Both are subtle enough to
have shipped bugs (a GraphQL node-budget blowout from bundling `commits` into the bulk list, an
empty-string `.email` collapsing a human commit to "verified bot-only", a null `.commits`
iteration crash) — so the filters are extracted from the workflow source and driven directly
with synthetic GitHub API JSON, no live PRs needed.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

APP = "myapp[bot]"
# The stranded-PR step embeds two jq programs: candidate selector + author extractor.
EXPECTED_JQ_PROGRAMS = 2

pytestmark = pytest.mark.skipif(shutil.which("jq") is None, reason="jq not installed")


def _jq_filters(template_dir: Path) -> tuple[str, str]:
    """Extract the two `jq -r --arg app ...` programs (candidate selector, author extractor)."""
    text = (template_dir / "template" / ".github" / "workflows" / "main.yml.jinja").read_text()
    # Each program is a single-quoted jq string on the line after its `jq -r --arg app ... \`.
    # The programs contain no single quotes, so a non-greedy '([^']*)' capture is unambiguous.
    programs = re.findall(r"jq -r --arg app[^\n]*\\\n\s*'([^']*)'", text)
    assert len(programs) == EXPECTED_JQ_PROGRAMS, (
        f"expected {EXPECTED_JQ_PROGRAMS} jq programs in main.yml, found {len(programs)}"
    )
    return programs[0], programs[1]


def _run_jq(program: str, payload: object) -> str:
    result = subprocess.run(  # noqa: S603
        ["jq", "-r", "--arg", "app", APP, program],  # noqa: S607
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _pr(
    number: int, *, login: str = APP, label: str = "autorelease: pending", state: str = "DIRTY"
) -> dict:
    return {
        "number": number,
        "author": {"login": login},
        "labels": [{"name": label}],
        "mergeStateStatus": state,
    }


def test_candidate_selector_matches_only_bot_authored_dirty_pending(template_dir: Path) -> None:
    """Phase 1 selects only the release bot's DIRTY, autorelease:pending PRs — by number."""
    candidates, _ = _jq_filters(template_dir)
    payload = [
        _pr(5),  # match
        _pr(6, state="CLEAN"),  # not DIRTY
        _pr(7, login="alice"),  # not the bot
        _pr(8, label="dependencies"),  # not a pending release
        _pr(9),  # match
    ]
    assert _run_jq(candidates, payload).split() == ["5", "9"]


def test_author_extractor_bot_only_commits_yield_empty(template_dir: Path) -> None:
    """A PR whose only commits are the release bot's → empty string → eligible to close."""
    _, extractor = _jq_filters(template_dir)
    payload = {"commits": [{"authors": [{"login": APP}]}]}
    assert _run_jq(extractor, payload) == ""


def test_author_extractor_empty_email_does_not_mask_a_human_commit(template_dir: Path) -> None:
    """The #207 Bug 2 case: login null + email "" must NOT collapse to "verified bot-only".

    jq's `//` treats "" as truthy, so guarding only `.login` (not `.email`) would fall through
    to the empty `.email` and yield "", misclassifying a real human commit as bot-only and
    auto-closing it. The empty-string guard on `.email` makes it fall through to `.name`.
    """
    _, extractor = _jq_filters(template_dir)
    payload = {"commits": [{"authors": [{"login": None, "email": "", "name": "Alice"}]}]}
    assert _run_jq(extractor, payload) == "Alice"


def test_author_extractor_email_fallback_still_works(template_dir: Path) -> None:
    """A non-empty `.email` is still used when `.login` is absent."""
    _, extractor = _jq_filters(template_dir)
    payload = {"commits": [{"authors": [{"login": None, "email": "a@b.c", "name": "Alice"}]}]}
    assert _run_jq(extractor, payload) == "a@b.c"


def test_author_extractor_null_commits_is_fail_safe(template_dir: Path) -> None:
    """The #210 gap: a null/absent `.commits` must resolve to a non-empty "unknown" marker.

    A degraded API response (`.commits == null`) must take the warn-and-leave-open path, not
    silently read as "verified bot-only" (which a naive `.commits[]?` would do) and auto-close
    a PR the check couldn't verify.
    """
    _, extractor = _jq_filters(template_dir)
    assert "unknown-authors" in _run_jq(extractor, {"commits": None})


def test_author_extractor_real_login_is_reported(template_dir: Path) -> None:
    """A human commit with a real login reports that login (→ leave the PR open)."""
    _, extractor = _jq_filters(template_dir)
    payload = {"commits": [{"authors": [{"login": APP}, {"login": "alice"}]}]}
    assert _run_jq(extractor, payload) == "alice"
