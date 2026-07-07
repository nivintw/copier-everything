# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""`copier update` seed behavior — `_exclude`-on-update + `_skip_if_exists` (issues #225/#231).

The template ships one-time SEED files (``CHANGELOG.md``, ``tests/test_smoke.py``,
``tests/smoke.bats``): rendered on the first `copier copy`, but the user owns them thereafter.
copier.yml keeps a routine `copier update` from touching them via ``_exclude`` entries gated on
``_copier_operation == 'update'`` (complemented by ``_skip_if_exists`` for the adopt-into-an-
existing-repo copy path).

This test PROVES that behavior end-to-end: it snapshots the real template into a throwaway v1→v2
repo (v2 carrying a genuine NON-seed sentinel delta so the update isn't vacuous), copies v1 into a
project, then in the project MODIFIES one seed and DELETES another before updating to v2. It then
asserts the sentinel propagated (update ran, git ≥ 2.54 flake mitigated), the CHANGELOG edit
survived un-clobbered, and the deleted smoke test was not resurrected. See update_support for the
harness and the flake mitigation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from update_support import (
    FLAKE_UNMITIGATED_MSG,
    SEED_CHANGELOG,
    SEED_SMOKE_TEST,
    SENTINEL_FILENAME,
    SENTINEL_MARKER,
    build_two_version_template,
    copy_v1_into_project,
    git,
    update_project_to_v2,
)

if TYPE_CHECKING:
    from pathlib import Path

# A user-owned CHANGELOG entry (the sort release-please writes) that `copier update` must not
# revert to the pristine seed.
USER_CHANGELOG_EDIT = "\n## 0.1.0\n\n- A user-owned entry `copier update` must not clobber.\n"


def test_update_preserves_edited_and_deleted_seeds(
    template_dir: Path,
    tmp_path: Path,
) -> None:
    """A modified seed keeps the user's edit and a deleted seed stays deleted across `update`."""
    template = build_two_version_template(template_dir, tmp_path / "template")
    project = tmp_path / "project"
    copy_v1_into_project(template, project)

    changelog = project / SEED_CHANGELOG
    smoke_test = project / SEED_SMOKE_TEST
    # Precondition: both seeds are rendered on the initial copy.
    assert changelog.is_file()
    assert smoke_test.is_file()
    seeded_changelog = changelog.read_text()

    # The user grows one seed and deletes another, then commits — `copier update` diffs against
    # the committed working tree.
    changelog.write_text(seeded_changelog + USER_CHANGELOG_EDIT)
    smoke_test.unlink()
    git("add", "-A", cwd=project)
    git("commit", "-q", "-m", "chore: user edits to seed files", cwd=project)

    update_project_to_v2(template, project)

    # (a) The NON-seed sentinel delta propagated: the update genuinely ran (no git >= 2.54 no-op).
    # This is also the "pattern matched nothing" tripwire — if the update carried no changes, the
    # sentinel is absent and this fails loudly instead of passing vacuously.
    sentinel = project / SENTINEL_FILENAME
    assert sentinel.is_file(), FLAKE_UNMITIGATED_MSG
    assert SENTINEL_MARKER in sentinel.read_text()

    # (b) The user's CHANGELOG edit is intact and NOT reverted to the seed, with no 3-way-merge
    # conflict markers or `.rej` litter (the seed is excluded from the update render entirely).
    final_changelog = changelog.read_text()
    assert final_changelog == seeded_changelog + USER_CHANGELOG_EDIT
    assert "<<<<<<<" not in final_changelog

    # (c) The deleted smoke test was NOT resurrected.
    assert not smoke_test.exists()

    # No conflict/reject files anywhere in the project.
    assert list(project.rglob("*.rej")) == []

    # The update recorded the new template version in the answers file.
    assert template.v2_tag in (project / ".copier-answers.yml").read_text()
