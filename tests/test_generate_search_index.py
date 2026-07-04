# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""Unit tests for scripts/generate-search-index.py against synthetic docs/ fixtures.

CI's `--check` step only proves the script's output matches the committed docs/search-index.js
— it can't catch a logic bug that's regenerated and committed in the same PR (both sides would
be wrong in the same way). These tests pin the expected output against small, hand-written
HTML fixtures instead of the real docs/ tree, so a regression in heading/entity/nav parsing
fails here regardless of what's committed.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture(scope="module")
def gsi(template_dir):  # noqa: ANN001, ANN201
    """Load scripts/generate-search-index.py as a module (its filename isn't importable)."""
    spec = importlib.util.spec_from_file_location(
        "generate_search_index", template_dir / "scripts" / "generate-search-index.py"
    )
    assert spec, "failed to load scripts/generate-search-index.py as a module"
    assert spec.loader, "loaded spec has no loader"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def fixture_docs(tmp_path: Path, gsi, monkeypatch: pytest.MonkeyPatch) -> Path:  # noqa: ANN001
    """A synthetic 2-page docs/ dir, with DOCS_DIR and PAGES pointed at it."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    (docs_dir / "index.html").write_text(
        "<title>Home Page Title</title>\n"
        "<h1>Home</h1>\n"
        '<nav class="toc">\n'
        '<a href="index.html">Home</a>\n'
        '<a href="questions.html">Questions</a>\n'
        '<a href="https://github.com/example/repo">GitHub repo &#8599;</a>\n'
        "</nav>\n"
        '<h2 id="anchored">Anchored Section <a class="anchor" href="#anchored">#</a></h2>\n'
        "<h3>Bare Section</h3>\n"
    )
    (docs_dir / "questions.html").write_text(
        "<title>Questions Title</title>\n"
        "<h1>Questions &amp; Answers</h1>\n"
        '<h2 id="q1">First &amp; Second</h2>\n'
    )

    monkeypatch.setattr(gsi, "DOCS_DIR", docs_dir)
    monkeypatch.setattr(gsi, "PAGES", ["index.html", "questions.html"])
    return docs_dir


@pytest.mark.usefixtures("fixture_docs")
def test_title_and_h1_entries(gsi) -> None:  # noqa: ANN001
    """Every page contributes its <title> and <h1> as bare-page (no-anchor) entries."""
    entries = gsi.build_entries()
    assert {"title": "Home Page Title", "page": "Home", "url": "index.html"} in entries
    assert {"title": "Home", "page": "Home", "url": "index.html"} in entries
    assert {
        "title": "Questions Title",
        "page": "Questions & Answers",
        "url": "questions.html",
    } in entries


@pytest.mark.usefixtures("fixture_docs")
def test_anchored_heading_gets_fragment_url(gsi) -> None:  # noqa: ANN001
    """A <h2 id="..."> heading's entry URL includes the #id fragment."""
    entries = gsi.build_entries()
    assert {"title": "Anchored Section", "page": "Home", "url": "index.html#anchored"} in entries


@pytest.mark.usefixtures("fixture_docs")
def test_unanchored_heading_points_at_bare_page(gsi) -> None:  # noqa: ANN001
    """A bare <h3> with no id still gets indexed, pointing at the page with no fragment."""
    entries = gsi.build_entries()
    assert {"title": "Bare Section", "page": "Home", "url": "index.html"} in entries


@pytest.mark.usefixtures("fixture_docs")
def test_html_entities_are_unescaped(gsi) -> None:  # noqa: ANN001
    """&amp; in a heading/title becomes a literal & in the indexed title."""
    entries = gsi.build_entries()
    assert {
        "title": "First & Second",
        "page": "Questions & Answers",
        "url": "questions.html#q1",
    } in entries


@pytest.mark.usefixtures("fixture_docs")
def test_nav_link_to_other_page_uses_real_target(gsi) -> None:  # noqa: ANN001
    """index.html's nav link to another page indexes that page's real URL, not index.html."""
    entries = gsi.build_entries()
    assert {"title": "Questions", "page": "Home", "url": "questions.html"} in entries


@pytest.mark.usefixtures("fixture_docs")
def test_nav_self_link_is_excluded(gsi) -> None:  # noqa: ANN001
    """The nav's link back to index.html itself isn't indexed a second time."""
    entries = gsi.build_entries()
    home_self_links = [e for e in entries if e["title"] == "Home" and e["url"] == "index.html"]
    # Exactly one: the <h1>Home</h1> entry. The nav's self-link ("Home" -> index.html) must
    # not add a second, indistinguishable duplicate.
    assert len(home_self_links) == 1


@pytest.mark.usefixtures("fixture_docs")
def test_nav_external_link_is_indexed(gsi) -> None:  # noqa: ANN001
    """An external nav link (not index.html-prefixed) is indexed with its real external URL."""
    entries = gsi.build_entries()
    assert {
        "title": "GitHub repo ↗",
        "page": "Home",
        "url": "https://github.com/example/repo",
    } in entries


@pytest.mark.usefixtures("fixture_docs")
def test_render_is_idempotent(gsi) -> None:  # noqa: ANN001
    """Rendering the same entries twice produces byte-identical output."""
    entries = gsi.build_entries()
    assert gsi.render(entries) == gsi.render(entries)


@pytest.mark.usefixtures("fixture_docs")
def test_render_round_trips_through_json(gsi) -> None:  # noqa: ANN001
    """The rendered JS array parses back to the same entries (valid JSON, no stray commas)."""
    entries = gsi.build_entries()
    rendered = gsi.render(entries)
    body = re.sub(r"^.*?window\.SEARCH_INDEX = ", "", rendered, flags=re.DOTALL)
    body = body.strip().rstrip(";")
    assert json.loads(body) == entries


def test_check_passes_when_index_matches(gsi, fixture_docs, monkeypatch, capsys) -> None:  # noqa: ANN001
    """`--check` exits 0 and prints "up to date" when the committed file matches the render."""
    (fixture_docs / "search-index.js").write_text(gsi.render(gsi.build_entries()))
    monkeypatch.setattr(sys, "argv", ["generate-search-index.py", "--check"])
    gsi.main()
    assert "up to date" in capsys.readouterr().out


def test_check_fails_when_index_is_stale(gsi, fixture_docs, monkeypatch) -> None:  # noqa: ANN001
    """`--check` exits 1 when the committed file doesn't match the current docs content."""
    (fixture_docs / "search-index.js").write_text("window.SEARCH_INDEX = [];\n")
    monkeypatch.setattr(sys, "argv", ["generate-search-index.py", "--check"])
    with pytest.raises(SystemExit) as exc_info:
        gsi.main()
    assert exc_info.value.code == 1


def test_pages_out_of_sync_fails_loudly(gsi, fixture_docs) -> None:  # noqa: ANN001
    """A docs/*.html page that exists on disk but isn't in PAGES fails instead of vanishing.

    This is the regression check_pages_are_current() exists for: without it, a new page nobody
    remembered to add to PAGES would be silently skipped forever, with `--check` staying green.
    """
    (fixture_docs / "orphan.html").write_text("<title>Orphan</title>\n<h1>Orphan</h1>\n")
    with pytest.raises(SystemExit, match=re.escape("orphan.html")):
        gsi.build_entries()
