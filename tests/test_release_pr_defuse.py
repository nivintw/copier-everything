# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""The main.yml "Defuse closing keywords" perl rewrite must neutralize exactly the right refs.

The release job rewrites the Release PR body so that GitHub's native auto-close doesn't close
issues a released commit merely *referenced* (release-please renders every `#N` as `closes #N`).
That rewrite is a single load-bearing perl substitution embedded in the workflow — subtle enough
(word boundaries, keyword-variant alternation, a `[?#<digit>` lookahead, and deliberately leaving a
keyword-less `([#N])` self-link intact) to deserve the same extract-and-run coverage the stranded-PR
jq gets in test_main_release_guard.py. The program is pulled straight from the workflow source and
driven with synthetic PR bodies, so a regression in the regex fails here, not silently in a release.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.skipif(shutil.which("perl") is None, reason="perl not installed")


def _defuse_program(template_dir: Path) -> str:
    """Extract the single `perl -0777 -pe '...'` defuse program from main.yml.jinja."""
    text = (template_dir / "template" / ".github" / "workflows" / "main.yml.jinja").read_text()
    # The program is single-quoted and contains no single quotes, so `'([^']*)'` is unambiguous.
    programs = re.findall(r"perl -0777 -pe '([^']*)'", text)
    assert len(programs) == 1, f"expected exactly 1 perl defuse program, found {len(programs)}"
    return programs[0]


def _run_perl(program: str, body: str) -> str:
    result = subprocess.run(  # noqa: S603
        ["perl", "-0777", "-pe", program],  # noqa: S607
        input=body,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def _canary_pattern(template_dir: Path) -> str:
    """Extract the `close_ref='...'` canary pattern (the fail-loud residual check)."""
    text = (template_dir / "template" / ".github" / "workflows" / "main.yml.jinja").read_text()
    patterns = re.findall(r"close_ref='([^']*)'", text)
    assert len(patterns) == 1, f"expected exactly 1 close_ref canary pattern, found {len(patterns)}"
    return patterns[0]


def _canary_fires(pattern: str, body: str) -> bool:
    """Whether the canary matches `body` (→ the step fails loud).

    Mirrors the workflow's own check, which runs the pattern through perl (grep -E's word
    boundaries are not portable) — so this exercises the exact engine the workflow uses. The
    pattern is passed via the environment so its own `/` characters can't break the delimiter.
    """
    result = subprocess.run(
        ["perl", "-0777", "-ne", "exit($_ =~ /$ENV{CANARY}/i ? 0 : 1)"],  # noqa: S607
        input=body,
        text=True,
        env={**os.environ, "CANARY": pattern},
        check=False,  # we read returncode as the match verdict; a non-match (exit 1) is expected
    )
    return result.returncode == 0


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ("closes #5", "refs #5"),
        ("Closes #5", "refs #5"),  # case-insensitive
        ("closed #5", "refs #5"),
        ("close #5", "refs #5"),
        ("fixes #5", "refs #5"),
        ("fixed #5", "refs #5"),
        ("fix #5", "refs #5"),
        ("resolves #5", "refs #5"),
        ("resolved #5", "refs #5"),
        ("resolve #5", "refs #5"),
        ("closes [#5]", "refs [#5]"),  # the markdown-link form release-please emits
    ],
    ids=[
        "closes",
        "Closes",
        "closed",
        "close",
        "fixes",
        "fixed",
        "fix",
        "resolves",
        "resolved",
        "resolve",
        "closes-link",
    ],
)
def test_every_closing_keyword_variant_is_neutralized(
    template_dir: Path, body: str, expected: str
) -> None:
    """Each closing-keyword variant, before a `#N`/`[#N]`, becomes the non-keyword refs."""
    assert _run_perl(_defuse_program(template_dir), body) == expected


def test_keywordless_self_link_is_left_intact(template_dir: Path) -> None:
    """A PR's own `([#N])` self-link (no closing keyword) must survive untouched."""
    body = "* **feat:** add thing ([#243](https://x/pull/243))"
    assert _run_perl(_defuse_program(template_dir), body) == body


def test_only_the_leading_keyword_is_rewritten_in_a_ref_list(template_dir: Path) -> None:
    """`closes [#242] [#196]` → `refs [#242] [#196]`: neutralizing the keyword defuses the list.

    release-please renders a multi-issue reference as one keyword followed by several links; once
    the keyword is gone, the trailing links are keyword-less and GitHub won't auto-close them.
    """
    body = "desc, closes [#242](https://x/issues/242) [#196](https://x/issues/196)"
    expected = "desc, refs [#242](https://x/issues/242) [#196](https://x/issues/196)"
    assert _run_perl(_defuse_program(template_dir), body) == expected


def test_word_boundary_leaves_lookalike_words_untouched(template_dir: Path) -> None:
    """`prefixes #5` must NOT be rewritten — the word-boundary guard spares embedded lookalikes."""
    body = "prefixes #5"
    assert _run_perl(_defuse_program(template_dir), body) == body


def test_a_realistic_release_pr_line_defuses_only_the_close(template_dir: Path) -> None:
    """The whole-line case: the self-link stays, the `closes` reference is neutralized."""
    body = "* **feat:** thing ([#243](https://x/pull/243)), closes [#242](https://x/issues/242)"
    expected = "* **feat:** thing ([#243](https://x/pull/243)), refs [#242](https://x/issues/242)"
    assert _run_perl(_defuse_program(template_dir), body) == expected


def test_every_close_in_a_multi_commit_body_is_defused(template_dir: Path) -> None:
    """A real Release PR bundles many commits → many independent closing refs; ALL must go.

    This is the case a dropped `/g` flag (or any first-match-only regression) would break: only the
    first `closes` would be neutralized and every later issue would still auto-close on merge, on a
    green test run. Drives several keyword+ref pairs on separate lines; asserts each is rewritten.
    """
    body = "* a, closes #1\n* b, fixes [#2]\n* c, resolves #3"
    expected = "* a, refs #1\n* b, refs [#2]\n* c, refs #3"
    assert _run_perl(_defuse_program(template_dir), body) == expected


def test_colon_trailer_form_is_neutralized(template_dir: Path) -> None:
    """The git-trailer `Closes: #N` style — an optional colon between keyword and ref."""
    assert _run_perl(_defuse_program(template_dir), "Closes: #5") == "refs #5"


def test_keyword_without_a_following_ref_is_left_intact(template_dir: Path) -> None:
    """A closing keyword in prose (no issue ref after it) must survive untouched.

    Guards against the trailing ref group being loosened into over-matching that would corrupt body
    prose — e.g. `closes out the old API` must not become `refs out the old API`.
    """
    body = "This release closes out the old API"
    assert _run_perl(_defuse_program(template_dir), body) == body


@pytest.mark.parametrize(
    "survivor",
    ["closes GH-5", "closes owner/repo#5", "closes https://github.com/o/r/issues/5"],
    ids=["gh-shorthand", "cross-repo", "full-url"],
)
def test_canary_flags_closing_forms_the_rewrite_does_not_cover(
    template_dir: Path, survivor: str
) -> None:
    """The fail-loud canary must catch closing forms GitHub auto-closes on but the rewrite leaves.

    The perl rewrite deliberately targets only release-please's `#N`/`[#N]` output; these exotic
    forms (legacy `GH-N`, cross-repo, full URL) pass through un-defused. The canary is what turns
    that from a silent wrong-close into a red run — so it MUST match each of them.
    """
    assert _canary_fires(_canary_pattern(template_dir), survivor)


@pytest.mark.parametrize(
    "clean",
    [
        "refs #5",
        "refs [#5]",
        "* **feat:** thing ([#243](https://x/pull/243))",
        "This release closes out the old API",
        "prefixes #5",
    ],
    ids=["defused-hash", "defused-link", "self-link", "keyword-no-ref", "word-boundary"],
)
def test_canary_stays_quiet_on_clean_or_defused_content(template_dir: Path, clean: str) -> None:
    """The canary must NOT fire on defused output or ordinary prose (else every release reddens)."""
    assert not _canary_fires(_canary_pattern(template_dir), clean)


def test_rewrite_then_canary_is_quiet_on_normal_release_forms(template_dir: Path) -> None:
    """End-to-end: the forms release-please emits are fully defused, so the canary passes."""
    body = "* a, closes #1\n* b, fixes [#2]\n* c, resolves #3"
    defused = _run_perl(_defuse_program(template_dir), body)
    assert not _canary_fires(_canary_pattern(template_dir), defused)
