# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""Shared harness for the `copier update` end-to-end tests.

These are the first tests in this repo to exercise `copier update` (the rest only render a
fresh copy). An update needs TWO template versions and a git-tracked project, so this module
builds a **throwaway** template repo — a `git archive HEAD` snapshot of this repo's own
`copier.yml` + `template/` tree, git-init'd and tagged `v1` — then layers a genuine, NON-seed
template-side change on top and tags it `v2`. Tests `copier copy` v1 into a project, git-init
it, then `copier update` it to v2.

The git ≥ 2.54 no-op flake
--------------------------
On git ≥ 2.54, a naive `copier update` against a throwaway repo can silently apply NOTHING:
git's detached background auto-maintenance interferes with the temporary branches copier uses
to compute the 3-way diff. `harden_repo` neutralizes it (disables `maintenance.auto` and
`gc.auto`) in every throwaway repo, and every test asserts the v2 sentinel actually landed
(`FLAKE_UNMITIGATED_MSG`) — a positive tripwire that fails loudly rather than passing vacuously
if the update no-ops.
"""

from __future__ import annotations

import functools
import json
import subprocess
import warnings
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING

from copier import run_copy, run_update
from copier.errors import DirtyLocalWarning

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

# Two PEP 440-parseable tags (copier derives a template's version from git tags and ignores
# non-PEP-440 ones, so bare `v1`/`v2` would leave the version undefined and skip migrations).
V1_TAG = "v1.0.0"
V2_TAG = "v2.0.0"

# The v2 delta: a genuine template-side change to a NON-seed file, rendered unconditionally on
# the output side. It carries a real diff through the update so copier's 3-way merge isn't
# vacuous, and its presence after the update is the proof that the update actually ran.
SENTINEL_FILENAME = "TEMPLATE_SENTINEL.md"
SENTINEL_MARKER = "template-side sentinel change introduced in v2"

# The one-time SEED files, mirroring copier.yml's `_exclude` (gated on `_copier_operation ==
# 'update'`) and `_skip_if_exists` lists. On update copier must leave a user's edits/deletions
# to these alone.
SEED_CHANGELOG = "CHANGELOG.md"
SEED_SMOKE_TEST = "tests/test_smoke.py"

# The answer set: pytest + no python source — the smallest shape that still renders the pytest
# seeds (CHANGELOG.md, tests/test_smoke.py) this suite asserts on.
PROJECT_DATA: dict[str, object] = {
    "project_name": "downstream-project",
    "python_source": False,
    "author_name": "Downstream Dev",
    "author_email": "dev@example.invalid",
    "repo_owner": "downstream-owner",
    "year": 2026,
}

# Fail message when the v2 sentinel does NOT appear after an update: the update no-op'd, which on
# git ≥ 2.54 means the detached-auto-maintenance flake beat the `harden_repo` mitigation.
FLAKE_UNMITIGATED_MSG = (
    f"{SENTINEL_FILENAME} did not appear after `copier update`: the update applied NO changes. "
    "On git >= 2.54 this is the detached auto-maintenance no-op flake — the harness mitigation "
    "(harden_repo disabling maintenance.auto/gc.auto) is no longer neutralizing it."
)

# Git config applied to every throwaway repo: neutralize the git >= 2.54 flake, and pin a clean,
# self-contained identity so commits succeed without the host machine's global git config (and a
# host signing key can't break the throwaway commits).
_THROWAWAY_GIT_CONFIG: dict[str, str] = {
    "maintenance.auto": "false",
    "gc.auto": "0",
    "user.name": "Copier Update Test",
    "user.email": "copier-update-test@example.invalid",
    "commit.gpgsign": "false",
}

# Text-mode, raises on non-zero exit. `git()` wraps this so every call site stays a one-liner.
_run = functools.partial(subprocess.run, check=True, capture_output=True, text=True)


def git(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run a git subcommand in ``cwd``, returning the completed process (raises on failure).

    Args:
        *args: Arguments after ``git`` (e.g. ``"commit", "-q", "-m", "..."``).
        cwd: Working directory to run in.

    Returns:
        The completed process, with captured text ``stdout``/``stderr``.
    """
    return _run(["git", *args], cwd=cwd)


def harden_repo(repo: Path) -> None:
    """Neutralize the git ≥ 2.54 auto-maintenance flake and pin a clean identity on ``repo``.

    Applies :data:`_THROWAWAY_GIT_CONFIG`. See the module docstring for why disabling
    ``maintenance.auto``/``gc.auto`` is what keeps `copier update` from silently no-op'ing.

    Args:
        repo: A freshly ``git init``-ed throwaway repository.
    """
    for key, value in _THROWAWAY_GIT_CONFIG.items():
        git("config", key, value, cwd=repo)


@dataclass(frozen=True)
class ThrowawayTemplate:
    """A throwaway template git repo with two tagged versions (v1 → v2).

    Attributes:
        root: The template repo root (holds ``copier.yml``); pass to copier as the source.
        v1_tag: The initial-snapshot tag.
        v2_tag: The tag carrying the sentinel (and optional migration) delta.
    """

    root: Path
    v1_tag: str = V1_TAG
    v2_tag: str = V2_TAG


@contextmanager
def _suppress_dirty_local_warning() -> Iterator[None]:
    """Silence copier's ``DirtyLocalWarning`` for the duration of the block."""
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DirtyLocalWarning)
        yield


def _archive_worktree_head(worktree_root: Path, dst: Path) -> None:
    """Materialize this repo's template source at HEAD into ``dst`` via ``git archive | tar``.

    ``git archive HEAD | tar -x`` yields a clean tree — the committed ``copier.yml`` + ``template/``
    with no ``.git``/``.venv`` — ready to git-init as an independent throwaway template repo.

    Args:
        worktree_root: A directory inside this repo's git worktree (holds ``copier.yml``).
        dst: Destination directory (created if absent).
    """
    dst.mkdir(parents=True, exist_ok=True)
    archive = subprocess.run(
        ["git", "archive", "HEAD"],  # noqa: S607 - `git` resolved off PATH, no untrusted input
        cwd=worktree_root,
        check=True,
        capture_output=True,
    )
    subprocess.run(  # noqa: S603 - fixed `tar` argv; only in-repo paths flow in
        ["tar", "-x", "-C", str(dst)],  # noqa: S607 - `tar` resolved off PATH, no untrusted input
        input=archive.stdout,
        check=True,
        capture_output=True,
    )


def _append_migration(copier_yml: Path, command: list[str]) -> None:
    """Append a ``_migrations`` block running ``command`` in copier's post-migration stage.

    The default ``when`` (``_stage == 'after'``) fires the command once, after the update's files
    are applied. ``command`` is JSON-encoded so it renders as a valid YAML flow sequence.

    Args:
        copier_yml: The throwaway template's ``copier.yml``.
        command: The argv list to run (e.g. ``["sh", "-c", "echo ..."]``).
    """
    block = (
        "\n_migrations:\n"
        f"  - command: {json.dumps(command)}\n"
        "    when: \"{{ _stage == 'after' }}\"\n"
    )
    copier_yml.write_text(copier_yml.read_text() + block)


def build_two_version_template(
    worktree_root: Path,
    dst: Path,
    *,
    migration_command: list[str] | None = None,
) -> ThrowawayTemplate:
    """Snapshot this repo's template into a throwaway repo tagged v1, then add a v2 delta.

    v1 is the template exactly as it is at ``worktree_root``'s HEAD. v2 adds the sentinel NON-seed
    file (:data:`SENTINEL_FILENAME`) and, when ``migration_command`` is given, a ``_migrations``
    subprocess — the two levers the update tests assert on.

    Args:
        worktree_root: A directory inside this repo's git worktree (holds ``copier.yml``).
        dst: Destination directory for the throwaway template repo.
        migration_command: Optional argv for a v2 ``_migrations`` subprocess.

    Returns:
        A :class:`ThrowawayTemplate` handle to the v1/v2 repo.
    """
    _archive_worktree_head(worktree_root, dst)
    git("init", "-q", cwd=dst)
    harden_repo(dst)
    git("add", "-A", cwd=dst)
    git("commit", "-q", "-m", "v1: template snapshot", cwd=dst)
    git("tag", V1_TAG, cwd=dst)

    # REUSE-IgnoreStart — this writes a template .jinja whose SPDX header carries Jinja
    # placeholders; without the guard, `reuse lint` tries to parse `{{ license }}` (in this
    # file's own source) as an SPDX expression and fails.
    (dst / "template" / f"{SENTINEL_FILENAME}.jinja").write_text(
        "<!--\n"
        "SPDX-FileCopyrightText: © {{ year }} {{ author_name }}\n"
        "SPDX-License-Identifier: {{ license }}\n"
        "-->\n\n"
        f"{SENTINEL_MARKER}\n"
    )
    # REUSE-IgnoreEnd
    if migration_command is not None:
        _append_migration(dst / "copier.yml", migration_command)
    git("add", "-A", cwd=dst)
    git("commit", "-q", "-m", "v2: sentinel non-seed change", cwd=dst)
    git("tag", V2_TAG, cwd=dst)
    return ThrowawayTemplate(root=dst)


def copy_v1_into_project(
    template: ThrowawayTemplate,
    project: Path,
    *,
    data: dict[str, object] | None = None,
) -> None:
    """`copier copy` the template's v1 into ``project``, then git-init and commit it.

    The committed working tree is the baseline the later `copier update` diffs against.

    Args:
        template: The throwaway template.
        project: Destination project directory (must not yet exist / be empty).
        data: Answer overrides; defaults to :data:`PROJECT_DATA`.
    """
    with _suppress_dirty_local_warning():
        run_copy(
            str(template.root),
            str(project),
            data=dict(data or PROJECT_DATA),
            defaults=True,
            unsafe=True,
            vcs_ref=template.v1_tag,
            skip_tasks=True,
        )
    git("init", "-q", cwd=project)
    harden_repo(project)
    git("add", "-A", cwd=project)
    git("commit", "-q", "-m", "chore: initial copy from template v1", cwd=project)


def update_project_to_v2(
    template: ThrowawayTemplate,
    project: Path,
    *,
    data: dict[str, object] | None = None,
) -> None:
    """`copier update` ``project`` from the template's v1 to v2.

    Args:
        template: The throwaway template.
        project: A project previously produced by :func:`copy_v1_into_project`.
        data: Answer overrides; defaults to :data:`PROJECT_DATA`.
    """
    with _suppress_dirty_local_warning():
        run_update(
            str(project),
            data=dict(data or PROJECT_DATA),
            defaults=True,
            unsafe=True,
            vcs_ref=template.v2_tag,
            overwrite=True,
            skip_tasks=True,
        )
