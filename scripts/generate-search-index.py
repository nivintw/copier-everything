# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

# A standalone CLI script, not an importable package.
# ruff: noqa: INP001

"""Regenerate docs/search-index.js from the docs/*.html pages listed in PAGES below.

`--check` is wired into CI ("Check docs search index is up to date" in ci.yml), so a docs
edit that adds/removes/renames a heading and forgets to regenerate the index fails the build
instead of silently drifting; check_pages_are_current() closes the one gap that check alone
wouldn't catch — a new docs/*.html page nobody added to PAGES, which would otherwise be
silently un-indexed forever. Indexes every page's <title> and <h1>, every <h2>/<h3>
(anchored ones get a `#id` URL, unanchored ones point at the bare page), and — for
index.html only — its nav links to the other five pages plus any external links in the nav
(e.g. the GitHub repo link), so a search for e.g. "questions" finds the real questions.html
page, not just index.html's self-referential summary card of the same name.

Usage:
  uv run python scripts/generate-search-index.py          # regenerate in place
  uv run python scripts/generate-search-index.py --check  # exit 1 if out of date
"""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path
from typing import NoReturn

DOCS_DIR = Path(__file__).parent.parent / "docs"

PAGES = [
    "index.html",
    "questions.html",
    "modules.html",
    "baseline.html",
    "usage.html",
    "design.html",
]


def clean(fragment: str) -> str:
    """Strip HTML tags (including the heading permalink `#` anchor) and unescape entities."""
    fragment = re.sub(r'<a class="anchor"[^>]*>.*?</a>', "", fragment, flags=re.DOTALL)
    fragment = re.sub(r"<[^>]+>", "", fragment)
    return html.unescape(fragment).strip()


def page_label(page: str, h1_text: str) -> str:
    """Display name shown next to each search result — index.html is "Home", else its <h1>."""
    return "Home" if page == "index.html" else h1_text


def _fail(message: str) -> NoReturn:
    """Exit with a clear message. A plain `assert` would compile away under `python -O`."""
    sys.exit(f"generate-search-index.py: {message}")


def check_pages_are_current() -> None:
    """PAGES is a hand-maintained allowlist — fail loudly if it drifts from docs/*.html.

    Without this, a new docs page nobody adds to PAGES is silently never indexed, and
    `--check` stays green forever since it only compares the script's output against itself.
    """
    actual = {p.name for p in DOCS_DIR.glob("*.html")}
    if actual != set(PAGES):
        missing_from_pages = actual - set(PAGES)
        missing_on_disk = set(PAGES) - actual
        detail = []
        if missing_from_pages:
            detail.append(f"in docs/ but not in PAGES: {sorted(missing_from_pages)}")
        if missing_on_disk:
            detail.append(f"in PAGES but not in docs/: {sorted(missing_on_disk)}")
        _fail("PAGES is out of sync with docs/*.html — " + "; ".join(detail))


def _title_and_h1(page: str, content: str) -> tuple[str, str]:
    """Extract and validate a page's <title> and <h1> text — fails loudly if either is missing."""
    title_match = re.search(r"<title>(.*?)</title>", content, re.DOTALL)
    h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", content, re.DOTALL)
    if not title_match:
        _fail(f"{page}: no <title> found")
    if not h1_match:
        _fail(f"{page}: no <h1> found")
    title_text = clean(title_match.group(1))
    h1_text = clean(h1_match.group(1))
    if not title_text:
        _fail(f"{page}: <title> is empty after stripping tags")
    if not h1_text:
        _fail(f"{page}: <h1> is empty after stripping tags")
    return title_text, h1_text


def _heading_entries(page: str, page_name: str, content: str) -> list[dict[str, str]]:
    """One entry per <h2>/<h3> — anchored ones get a `#id` URL, unanchored ones the bare page."""
    entries = []
    for match in re.finditer(r"<h[23]([^>]*)>(.*?)</h[23]>", content, re.DOTALL):
        attrs, heading_html = match.groups()
        heading_text = clean(heading_html)
        id_match = re.search(r'id="([^"]+)"', attrs)
        url = f"{page}#{id_match.group(1)}" if id_match else page
        entries.append({"title": heading_text, "page": page_name, "url": url})
    return entries


def _nav_link_entries(page: str, content: str) -> list[dict[str, str]]:
    """index.html's own nav links to the other pages (and any external links alongside them)."""
    nav_match = re.search(r'<nav class="toc">(.*?)</nav>', content, re.DOTALL)
    if not nav_match:
        _fail(f"{page}: no <nav class='toc'> found")
    entries = []
    for match in re.finditer(r'<a href="([^"]+)"[^>]*>(.*?)</a>', nav_match.group(1), re.DOTALL):
        href, label_html = match.groups()
        if href.startswith("index.html"):
            continue
        entries.append({"title": clean(label_html), "page": "Home", "url": href})
    return entries


def build_entries() -> list[dict[str, str]]:
    """Scan every page's title/h1/headings, plus index.html's nav links, into search entries."""
    check_pages_are_current()
    entries: list[dict[str, str]] = []

    for page in PAGES:
        content = (DOCS_DIR / page).read_text()
        title_text, h1_text = _title_and_h1(page, content)
        page_name = page_label(page, h1_text)

        entries.append({"title": title_text, "page": page_name, "url": page})
        entries.append({"title": h1_text, "page": page_name, "url": page})
        entries.extend(_heading_entries(page, page_name, content))
        if page == "index.html":
            entries.extend(_nav_link_entries(page, content))

    return entries


def render(entries: list[dict[str, str]]) -> str:
    """Render entries as the window.SEARCH_INDEX JS array, matching the file's existing style."""
    # REUSE-IgnoreStart — this string literally contains an SPDX-License-Identifier line (it's
    # the header written into the generated search-index.js); without the guard, `reuse lint`
    # tries to parse this Python file's own source as carrying that expression.
    header = (
        "/*\n"
        " * SPDX-FileCopyrightText: © 2026 Tyler Nivin\n"
        " * SPDX-License-Identifier: MIT\n"
        " */\n\n"
    )
    # REUSE-IgnoreEnd
    # Built by hand (not json.dumps(entries, indent=2)) to reproduce the file's existing
    # one-key-per-line, no-trailing-comma-on-last-entry layout, so regenerating doesn't churn
    # the whole file's formatting on every run.
    lines = ["window.SEARCH_INDEX = ["]
    for i, entry in enumerate(entries):
        comma = "," if i < len(entries) - 1 else ""
        lines.append(
            "{\n"
            f'"title": {json.dumps(entry["title"], ensure_ascii=False)},\n'
            f'"page": {json.dumps(entry["page"], ensure_ascii=False)},\n'
            f'"url": {json.dumps(entry["url"], ensure_ascii=False)}\n'
            f"}}{comma}"
        )
    lines.append("];")
    return header + "\n".join(lines) + "\n"


def main() -> None:
    """Regenerate docs/search-index.js in place, or verify it's current with `--check`."""
    index_path = DOCS_DIR / "search-index.js"
    entries = build_entries()
    rendered = render(entries)

    if "--check" in sys.argv[1:]:
        if index_path.read_text() != rendered:
            print(  # noqa: T201
                "docs/search-index.js is out of date — run: "
                "uv run python scripts/generate-search-index.py"
            )
            sys.exit(1)
        print("docs/search-index.js is up to date")  # noqa: T201
        return

    index_path.write_text(rendered)
    print(f"wrote {len(entries)} entries to docs/search-index.js")  # noqa: T201


if __name__ == "__main__":
    main()
