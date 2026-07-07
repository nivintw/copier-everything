# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""End-to-end `copier update` round-trip + dual-stream output capture (issue #224).

`copier update` emits on TWO independent streams, and a naive capture catches only one:

* copier's **own** progress/console output ("Updating to template version 2.0.0", task lines)
  is written at the **Python level** — ``print(..., file=sys.stderr)`` in this copier version.
* a ``_migrations`` **subprocess** inherits and writes to the **OS-level file descriptor** for
  stdout (fd 1); copier does not capture it.

So capturing must happen at the file-descriptor level to see both. ``capfd`` (which replaces the
OS fds) captures copier's Python-level writes AND the subprocess's fd-level writes; ``capsys``
(Python-level only) would miss the subprocess stream entirely. The first test asserts both halves
via ``capfd``; the second independently proves the OS-fd half with an explicit ``os.dup2``
redirection, the mechanism ``capfd`` uses under the hood.

Every test also asserts the v2 sentinel landed — the positive tripwire that the update wasn't a
git ≥ 2.54 no-op (see update_support).
"""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from typing import TYPE_CHECKING

from update_support import (
    FLAKE_UNMITIGATED_MSG,
    SENTINEL_FILENAME,
    build_two_version_template,
    copy_v1_into_project,
    update_project_to_v2,
)

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    import pytest

# A migration that echoes a unique marker to stdout (OS fd 1) — the subprocess half of the
# dual stream.
MIGRATION_SENTINEL = "COPIER_MIGRATION_OS_FD_SENTINEL_a3f1"
MIGRATION_COMMAND = ["sh", "-c", f"echo {MIGRATION_SENTINEL}"]


@contextmanager
def _redirect_os_stdout(path: Path) -> Iterator[None]:
    """Redirect OS-level stdout (fd 1) into ``path`` for the duration of the block.

    Duplicates fd 1 aside, points it at ``path``, then restores it — so any subprocess that
    inherits fd 1 (like a copier ``_migrations`` command) writes into ``path`` regardless of
    pytest's own capture. This is the fd-level mechanism ``capfd`` automates.

    Args:
        path: File to receive everything written to fd 1 while active.

    Yields:
        None.
    """
    sys.stdout.flush()
    saved_fd = os.dup(1)
    with path.open("wb") as sink:
        os.dup2(sink.fileno(), 1)
        try:
            yield
        finally:
            sys.stdout.flush()
            os.dup2(saved_fd, 1)
            os.close(saved_fd)


def test_update_captures_console_and_migration_streams(
    template_dir: Path,
    tmp_path: Path,
    capfd: pytest.CaptureFixture[str],
) -> None:
    """`capfd` captures BOTH copier's console output and a migration subprocess's fd-1 output."""
    template = build_two_version_template(
        template_dir, tmp_path / "template", migration_command=MIGRATION_COMMAND
    )
    project = tmp_path / "project"
    copy_v1_into_project(template, project)

    capfd.readouterr()  # discard the copy-phase output; assert only on the update
    update_project_to_v2(template, project)
    captured = capfd.readouterr()

    # Python-level stream: copier's own "Updating to template version 2.0.0" (goes to stderr).
    assert "Updating to template version" in captured.err
    assert template.v2_tag.lstrip("v") in captured.err
    # OS-fd stream: the migration subprocess wrote to fd 1 — only fd-level capture sees it.
    assert MIGRATION_SENTINEL in captured.out

    # The round-trip actually applied the v2 delta (not a git >= 2.54 no-op).
    assert (project / SENTINEL_FILENAME).is_file(), FLAKE_UNMITIGATED_MSG


def test_update_migration_writes_to_os_fd_stdout(
    template_dir: Path,
    tmp_path: Path,
) -> None:
    """An explicit ``os.dup2`` redirection of fd 1 captures the migration subprocess's output.

    Proves the OS-fd half directly, without relying on pytest's fixtures — the mechanism a
    Python-level capture (``capsys``) would miss.
    """
    template = build_two_version_template(
        template_dir, tmp_path / "template", migration_command=MIGRATION_COMMAND
    )
    project = tmp_path / "project"
    copy_v1_into_project(template, project)

    fd_capture = tmp_path / "os_fd_stdout.log"
    with _redirect_os_stdout(fd_capture):
        update_project_to_v2(template, project)

    assert MIGRATION_SENTINEL in fd_capture.read_text()
    assert (project / SENTINEL_FILENAME).is_file(), FLAKE_UNMITIGATED_MSG


def test_update_console_output_captured_without_migrations(
    template_dir: Path,
    tmp_path: Path,
    capfd: pytest.CaptureFixture[str],
) -> None:
    """The round-trip + capture still work when the template defines no ``_migrations``.

    The template today has no ``_migrations``; the harness must still exercise the update and
    capture copier's own update output.
    """
    template = build_two_version_template(template_dir, tmp_path / "template")
    project = tmp_path / "project"
    copy_v1_into_project(template, project)

    capfd.readouterr()
    update_project_to_v2(template, project)
    captured = capfd.readouterr()

    assert "Updating to template version" in captured.err
    assert (project / SENTINEL_FILENAME).is_file(), FLAKE_UNMITIGATED_MSG
