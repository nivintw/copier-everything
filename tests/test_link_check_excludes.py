# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""The generic lychee excludes cover the doc universals with a correct anti-spoof anchor (#235).

localhost/127.0.0.1, RFC 2606 example domains, and a private *.pages.github.io preview are safe
to exclude in any project's docs. The pages.github.io pattern must match a real subdomain but NOT
a look-alike host that merely embeds the string (e.g. evil-pages.github.io.attacker.com).
"""

from __future__ import annotations

import re
import tomllib
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


@pytest.fixture(scope="module")
def excludes(
    template_dir: Path,
    output_dir_module_scope: Path,
    render_template: Callable[..., Path],
) -> list[str]:
    """The rendered lychee.toml exclude patterns for a default project."""
    output = render_template(
        template_dir,
        output_dir_module_scope,
        data={"project_name": "link-demo"},
        skip_tasks=True,
    )
    return tomllib.loads((output / ".config" / "lychee.toml").read_text())["exclude"]


def _matches(patterns: list[str], url: str) -> bool:
    return any(re.search(pattern, url) for pattern in patterns)


def test_doc_universal_hosts_are_excluded(excludes: list[str]) -> None:
    """Loopback and example-domain links are excluded (they never resolve in CI)."""
    assert _matches(excludes, "http://localhost:8000/x")
    assert _matches(excludes, "https://127.0.0.1/x")
    assert _matches(excludes, "https://example.com/x")
    assert _matches(excludes, "https://sub.example.org")


def test_private_pages_excluded_but_spoof_is_not(excludes: list[str]) -> None:
    """A real *.pages.github.io host is excluded; a spoof that merely embeds the string is not."""
    assert _matches(excludes, "https://myproject.pages.github.io/")
    assert _matches(excludes, "https://myproject.pages.github.io")
    assert not _matches(excludes, "https://evil-pages.github.io.attacker.com/phish")


def test_no_work_specific_host(excludes: list[str]) -> None:
    """The downstream's work-specific *.surescripts.tech exclude is not carried over."""
    assert not any("surescripts" in pattern for pattern in excludes)
