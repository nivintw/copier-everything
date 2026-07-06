# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""Pytest fixtures for the template-rendering tests.

`template_dir` is the repo root (where copier.yml lives); copier reads `_subdirectory:
template` from there. `render_template` is the shared render helper both test modules use.
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

import pytest
import yaml
from copier import run_copy
from copier.errors import DirtyLocalWarning

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


class _TolerantSafeLoader(yaml.SafeLoader):
    """SafeLoader that shrugs off tags it doesn't need to validate.

    mkdocs.yml's pymdownx.emoji config carries `!!python/name:...` tags (Material's
    documented way to wire its icon set) — real Python-object tags that plain
    yaml.safe_load() rejects outright. Callers that only check nav/theme/extension *names*,
    not the emoji callables, can use `tolerant_yaml_load` below instead: unknown tags map to
    their scalar text rather than raising.
    """


_TolerantSafeLoader.add_multi_constructor(
    "tag:yaml.org,2002:python/name:",
    lambda _loader, suffix, _node: suffix,
)


def tolerant_yaml_load(text: str) -> dict:
    """Parse YAML that may carry mkdocs.yml's `!!python/name:...` tags (see above)."""
    return yaml.load(text, Loader=_TolerantSafeLoader)  # noqa: S506 - SafeLoader-derived


def mkdocs_extension_names(extensions: list) -> set[str]:
    """Extract each entry's name from an mkdocs.yml list that mixes bare strings and dicts.

    Used for both `markdown_extensions` and `plugins` — both share the same shape: an entry
    is either a bare string (`admonition`, `search`) or a single-key dict carrying config
    (`{pymdownx.highlight: {...}}`, `{social: {...}}`) — this normalizes either to just the
    name.
    """
    return {ext if isinstance(ext, str) else next(iter(ext)) for ext in extensions}


def on_key(doc: dict) -> dict:
    """The ``on:`` block, under either representation (bool ``True`` or the string ``"on"``).

    PyYAML resolves a bare ``on:`` key as the boolean ``True`` (YAML 1.1); this stays robust
    to a loader that doesn't. Mirrors ``tests/test_synced_files.py::_drop_triggers``, which
    removes rather than extracts the same key for a different purpose (diffing two rendered
    workflows with their triggers stripped out).
    """
    return doc[True] if True in doc else doc["on"]


@pytest.fixture(scope="session")
def template_dir() -> Path:
    """Path to the template repo root (the directory holding copier.yml)."""
    from pathlib import Path  # noqa: PLC0415

    return Path(__file__).parent.parent


@pytest.fixture(scope="module")
def output_dir_module_scope(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A module-scoped temporary output directory (render once, reuse across a module)."""
    return tmp_path_factory.mktemp("rendered_template_module_scope")


@pytest.fixture(scope="session")
def render_template() -> Callable[..., Path]:
    """Return a helper that renders the template into a directory and returns that directory.

    With ``vcs_ref="HEAD"`` against a dirty local checkout, copier renders the current
    **working-tree** state (uncommitted and untracked template changes included) and emits a
    DirtyLocalWarning saying so; the warning is suppressed (not asserted). Because the sync
    tests read the root side off the working tree too, both sides reflect the working tree and
    stay consistent whether or not it's clean. (On a clean checkout — e.g. CI — working tree
    and HEAD coincide.)
    """

    def _render(template_dir: Path, output_dir: Path, *, data: dict, skip_tasks: bool) -> Path:
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

    return _render
