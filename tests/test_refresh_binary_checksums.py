# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""pinned_value()/pinned_value_at_base() must fail loudly, never mask a read error as empty.

A typo'd file argument used to silently resolve to an empty match (grep's exit 1 "no match"
and exit >=2 "read error" were both swallowed by `2>/dev/null ... || true`), so the only
backstop was the end-of-run `processed -eq 0` check — which doesn't trip if at least one
*other* argument in the same invocation legitimately has pins. `pinned_value_at_base()` had
the same class of gap one layer up: a `git cat-file -e` failure other than "path absent at
BASE_REF" (a corrupted object, a partial clone's missing blob), and a `git show` failure
downstream of a passing `cat-file -e`, were both swallowed too.
"""

from __future__ import annotations

import functools
import os
import subprocess
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path


def test_pinned_value_fails_loudly_on_missing_file(template_dir: Path) -> None:
    """A typo'd file argument must exit loudly, not silently resolve to empty."""
    script = template_dir / "scripts" / "refresh-binary-checksums.sh"
    result = subprocess.run(  # noqa: S603
        ["bash", str(script), "some/typo/path.yml"],  # noqa: S607
        cwd=template_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "no such file: some/typo/path.yml" in result.stderr


def test_pinned_value_fails_loudly_on_unreadable_file(template_dir: Path, tmp_path: Path) -> None:
    """A file that exists but can't be read must exit with a LABELED error, not cat's raw one.

    Regression guard for the diagnostics gap: the read is checked explicitly so the failure
    carries `pinned_value:` context like every other failure mode here, instead of bash's bare
    `set -e` abort surfacing only `cat: <file>: Permission denied`.
    """
    if os.geteuid() == 0:
        pytest.skip("root bypasses file mode bits, so the file stays readable")
    script = template_dir / "scripts" / "refresh-binary-checksums.sh"
    unreadable = tmp_path / "wf.yml"
    unreadable.write_text('TRIVY_VERSION: "1.2.3"\nTRIVY_SHA256: "' + "a" * 64 + '"\n')
    unreadable.chmod(0o000)
    try:
        result = subprocess.run(  # noqa: S603
            ["bash", str(script), str(unreadable)],  # noqa: S607
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        unreadable.chmod(0o644)
    assert result.returncode == 1
    assert "pinned_value: read failed" in result.stderr


def _extract_shell_function(script: Path, name: str) -> str:
    """Pull one top-level shell function's source out of the script for isolated testing.

    `pinned_value_at_base()` is only reachable through the full refresh run (which needs
    network access to fetch upstream checksums), so it's exercised directly here instead —
    sourced in isolation and called with controlled git-repo/object-store states.
    """
    lines = script.read_text().splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith(f"{name}() {{"))
    end = next(i for i in range(start, len(lines)) if lines[i] == "}")
    return "\n".join(lines[start : end + 1])


def _run_pinned_value_at_base(
    script: Path, repo: Path, *, var: str, file: str, base_ref: str
) -> subprocess.CompletedProcess[str]:
    # pinned_value_at_base() calls the shared _extract_pinned_value() helper — both must be
    # sourced, or a success-path call would fail with "command not found", not a real defect.
    fn_names = ("_extract_pinned_value", "pinned_value_at_base")
    fn = "\n".join(_extract_shell_function(script, name) for name in fn_names)
    return subprocess.run(  # noqa: S603
        ["bash", "-c", f'{fn}\npinned_value_at_base "$1" "$2" "$3"', "bash", var, file, base_ref],  # noqa: S607
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture
def git_repo_with_pin(tmp_path: Path) -> Path:
    """A one-commit git repo with a pinned-version file, for pinned_value_at_base() tests."""
    repo = tmp_path / "repo"
    repo.mkdir()
    run = functools.partial(subprocess.run, cwd=repo, check=True)
    run(["git", "init", "-q"])
    run(["git", "config", "user.email", "test@example.com"])
    run(["git", "config", "user.name", "test"])
    (repo / "pinned.yml").write_text('TRIVY_VERSION: "1.2.3"\n')
    run(["git", "add", "."])
    run(["git", "commit", "-q", "-m", "init"])
    return repo


def test_pinned_value_at_base_returns_value_when_present(
    template_dir: Path, git_repo_with_pin: Path
) -> None:
    """The success path: a value pinned at BASE_REF is extracted correctly.

    The three failure-path tests below never reach _extract_pinned_value(), so without
    this one a regression in the shared helper (or its wiring into pinned_value_at_base)
    would go uncaught.
    """
    script = template_dir / "scripts" / "refresh-binary-checksums.sh"
    result = _run_pinned_value_at_base(
        script, git_repo_with_pin, var="TRIVY_VERSION", file="pinned.yml", base_ref="HEAD"
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "1.2.3"
    assert result.stderr == ""


def test_pinned_value_at_base_returns_empty_when_path_never_existed(
    template_dir: Path, git_repo_with_pin: Path
) -> None:
    """A path absent everywhere is one of git's two distinct "absent" messages.

    (See the on-disk variant below for the other one.) Also a legitimate empty case.
    """
    script = template_dir / "scripts" / "refresh-binary-checksums.sh"
    result = _run_pinned_value_at_base(
        script, git_repo_with_pin, var="TRIVY_VERSION", file="nope.yml", base_ref="HEAD"
    )
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_pinned_value_at_base_returns_empty_when_path_new_on_disk_since_base(
    template_dir: Path, git_repo_with_pin: Path
) -> None:
    """The actual production scenario: a file introduced since BASE_REF, present on disk.

    The caller's `[ -f "$f" ]` guard already confirmed the file exists on disk before
    calling this function, so git picks a DIFFERENT message ("exists on disk, but not in")
    than when the path is absent everywhere ("does not exist in", covered above) — this is
    the message variant pinned_value_at_base() actually hits in real use, and a fix that
    only matches the other one silently regresses this exact legitimate case.
    """
    script = template_dir / "scripts" / "refresh-binary-checksums.sh"
    (git_repo_with_pin / "new-since-base.yml").write_text('TRIVY_VERSION: "9.9.9"\n')
    result = _run_pinned_value_at_base(
        script, git_repo_with_pin, var="TRIVY_VERSION", file="new-since-base.yml", base_ref="HEAD"
    )
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_pinned_value_at_base_fails_loudly_on_missing_blob(
    template_dir: Path, git_repo_with_pin: Path
) -> None:
    """A blob absent from the object store must error loudly.

    (Corrupted DB, partial clone.) Must not be folded into the "path absent at base" empty
    case — the gap #191 fixed.
    """
    script = template_dir / "scripts" / "refresh-binary-checksums.sh"
    blob = subprocess.run(
        ["git", "rev-parse", "HEAD:pinned.yml"],  # noqa: S607
        cwd=git_repo_with_pin,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    obj_path = git_repo_with_pin / ".git" / "objects" / blob[:2] / blob[2:]
    backup_path = obj_path.with_name(obj_path.name + ".bak")
    obj_path.rename(backup_path)
    try:
        result = _run_pinned_value_at_base(
            script, git_repo_with_pin, var="TRIVY_VERSION", file="pinned.yml", base_ref="HEAD"
        )
    finally:
        backup_path.rename(obj_path)
    assert result.returncode == 1
    assert "ERROR: pinned_value_at_base" in result.stderr


def test_pinned_value_at_base_does_not_swallow_a_show_failure(
    template_dir: Path, git_repo_with_pin: Path
) -> None:
    """The #193 gap: a trailing `|| true` used to swallow a real git show failure.

    A loose object with valid existence but corrupt (non-zlib) content makes
    `git cat-file -e` pass but `git show` fail — exactly the failure the old trailing
    `|| true` on the whole show|grep|head|sed pipeline masked (not just grep's legitimate
    "no match").
    """
    script = template_dir / "scripts" / "refresh-binary-checksums.sh"
    blob = subprocess.run(
        ["git", "rev-parse", "HEAD:pinned.yml"],  # noqa: S607
        cwd=git_repo_with_pin,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    obj_path = git_repo_with_pin / ".git" / "objects" / blob[:2] / blob[2:]
    obj_path.chmod(0o644)
    obj_path.write_bytes(b"not a valid zlib-compressed git object")
    result = _run_pinned_value_at_base(
        script, git_repo_with_pin, var="TRIVY_VERSION", file="pinned.yml", base_ref="HEAD"
    )
    assert result.returncode == 1
    assert "ERROR: pinned_value_at_base: git show" in result.stderr


def test_pinned_value_at_base_fails_loudly_on_unresolvable_ref(
    template_dir: Path, git_repo_with_pin: Path
) -> None:
    """#208: an unresolvable baseref must fail loudly, not collapse to "path absent → empty".

    A stale/GC'd SHA, a typo, or a shallow clone missing the commit makes `git cat-file -e
    <ref>:<path>` emit the SAME "exists on disk, but not in <ref>" text as a legitimately
    absent path — so without the ref-resolves-to-a-commit guard at the top of the function,
    the caller silently gets an empty value (gate disabled) instead of a hard error.
    """
    script = template_dir / "scripts" / "refresh-binary-checksums.sh"
    result = _run_pinned_value_at_base(
        script,
        git_repo_with_pin,
        var="TRIVY_VERSION",
        file="pinned.yml",
        base_ref="deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
    )
    assert result.returncode == 1
    assert "does not resolve to a commit" in result.stderr


# --- Harness for the offline-testable slice of the full script (issues #211, #236, #233) ------
#
# refresh_pin()/tool_versions_at_base()/fetch_commit()'s tag-parsing are only reachable through
# the whole run, whose real fetches hit the network. Source the script's function region (every
# def + module-level state, minus the network-bound CLI driver), then stub the fetches / `git
# ls-remote`, so the tamper gate, the *_COMMIT rewrite, and bash-3.2 execution can be driven
# deterministically offline.


def _function_region(script: Path) -> str:
    """The script's function defs + module-level state, minus the network-bound CLI driver."""
    text = script.read_text()
    start = text.index("\nlower() {")
    end = text.index('\nif [ "$#" -gt 0 ]; then')
    return text[start:end]


def _run_region(
    script: Path, body: str, *, repo: Path, bash_bin: str = "bash", base_ref: str = ""
) -> subprocess.CompletedProcess[str]:
    program = f'set -euo pipefail\nBASE_REF="{base_ref}"\n{_function_region(script)}\n{body}'
    return subprocess.run(  # noqa: S603
        [bash_bin, "-c", program],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture
def workflow_repo(tmp_path: Path) -> Path:
    """An empty one-commit git repo with a .github/workflows/ dir, for full-script tests."""
    repo = tmp_path / "wf"
    (repo / ".github" / "workflows").mkdir(parents=True)
    run = functools.partial(subprocess.run, cwd=repo, check=True, capture_output=True)
    run(["git", "init", "-q"])
    run(["git", "config", "user.email", "test@example.com"])
    run(["git", "config", "user.name", "test"])
    (repo / "seed").write_text("seed\n")
    run(["git", "add", "."])
    run(["git", "commit", "-q", "-m", "seed"])
    return repo


_SHA_A = "a" * 64
_SHA_C = "c" * 64


def test_tamper_gate_survives_file_rename(template_dir: Path, workflow_repo: Path) -> None:
    """#211: a same-version, changed-hash swap is still caught after the pinning file is renamed.

    The tamper gate keys on TOOL IDENTITY (the tool's *_VERSION anywhere at BASE_REF), so a pure
    `git mv old.yml new.yml` no longer makes a same-version/changed-hash re-pin look like a
    brand-new pin and slip past the gate.
    """
    script = template_dir / "scripts" / "refresh-binary-checksums.sh"
    wf = workflow_repo / ".github" / "workflows"
    run = functools.partial(subprocess.run, cwd=workflow_repo, check=True, capture_output=True)
    (wf / "old.yml").write_text(f'TRIVY_VERSION: "0.55.0"\nTRIVY_SHA256: "{_SHA_A}"\n')
    run(["git", "add", "."])
    run(["git", "commit", "-q", "-m", "pin trivy in old.yml"])
    base = run(["git", "rev-parse", "HEAD"]).stdout.decode().strip()
    # Innocent rename; version + SHA untouched in the working tree.
    run(["git", "mv", ".github/workflows/old.yml", ".github/workflows/new.yml"])
    run(["git", "commit", "-q", "-m", "rename old.yml -> new.yml"])
    # Stub the fetch to stand in for a compromised re-upload of the same v0.55.0 asset.
    body = (
        f'fetch_sha() {{ printf "%s" "{_SHA_C}"; }}\n'
        'refresh_pin ".github/workflows/new.yml" TRIVY SHA256 fetch_sha '
        "'^[0-9a-f]{64}$' SHA256\n"
    )
    result = _run_region(script, body, repo=workflow_repo, base_ref=base)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "TAMPER ALERT" in result.stderr


def test_tamper_gate_catches_sibling_file_version_mismatch(
    template_dir: Path, workflow_repo: Path
) -> None:
    """A same-version tamper is caught even when a SIBLING file pins the tool at another version.

    The identity search must test whether the CURRENT version is AMONG all base versions, not
    equal to the first file's — otherwise a tool pinned at 0.60.0 in one file and 0.71.2 in
    another lets a 0.71.2 same-version/changed-hash tamper slip through.
    """
    script = template_dir / "scripts" / "refresh-binary-checksums.sh"
    wf = workflow_repo / ".github" / "workflows"
    run = functools.partial(subprocess.run, cwd=workflow_repo, check=True, capture_output=True)
    (wf / "a.yml").write_text(f'TRIVY_VERSION: "0.60.0"\nTRIVY_SHA256: "{_SHA_A}"\n')
    (wf / "b.yml").write_text(f'TRIVY_VERSION: "0.71.2"\nTRIVY_SHA256: "{_SHA_A}"\n')
    run(["git", "add", "."])
    run(["git", "commit", "-q", "-m", "pin trivy at two versions in two files"])
    base = run(["git", "rev-parse", "HEAD"]).stdout.decode().strip()
    # b.yml's version is UNCHANGED (0.71.2); upstream hash is tampered.
    body = (
        f'fetch_sha() {{ printf "%s" "{_SHA_C}"; }}\n'
        'refresh_pin ".github/workflows/b.yml" TRIVY SHA256 fetch_sha '
        "'^[0-9a-f]{64}$' SHA256\n"
    )
    result = _run_region(script, body, repo=workflow_repo, base_ref=base)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "TAMPER ALERT" in result.stderr


def test_genuinely_new_pin_is_not_flagged_as_tamper(
    template_dir: Path, workflow_repo: Path
) -> None:
    """#211: a tool never pinned anywhere at BASE_REF is a legitimate new pin, not a tamper."""
    script = template_dir / "scripts" / "refresh-binary-checksums.sh"
    wf = workflow_repo / ".github" / "workflows"
    run = functools.partial(subprocess.run, cwd=workflow_repo, check=True, capture_output=True)
    base = run(["git", "rev-parse", "HEAD"]).stdout.decode().strip()  # TRIVY absent here
    (wf / "ci.yml").write_text(f'TRIVY_VERSION: "0.55.0"\nTRIVY_SHA256: "{_SHA_A}"\n')
    run(["git", "add", "."])
    run(["git", "commit", "-q", "-m", "add trivy pin"])
    body = (
        f'fetch_sha() {{ printf "%s" "{_SHA_C}"; }}\n'
        'refresh_pin ".github/workflows/ci.yml" TRIVY SHA256 fetch_sha '
        "'^[0-9a-f]{64}$' SHA256\n"
    )
    result = _run_region(script, body, repo=workflow_repo, base_ref=base)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "TAMPER" not in result.stderr
    assert (wf / "ci.yml").read_text().count(_SHA_C) == 1  # rewritten to the new hash


@pytest.mark.parametrize("bash_bin", ["bash", "/bin/bash"])
def test_commit_pin_is_refreshed(template_dir: Path, workflow_repo: Path, bash_bin: str) -> None:
    """#236 + #233: a *_COMMIT pin is rewritten by the script, verified running under bash 3.2.

    Runs once under PATH bash (CI's 5.x) and once under /bin/bash (macOS's system 3.2.57, skipped
    where /bin/bash isn't 3.2) — proving the 3.2-safe rewrite (no associative arrays, no `${,,}`)
    actually executes there, not just parses.
    """
    version = subprocess.run(  # noqa: S603
        [bash_bin, "--version"], capture_output=True, text=True, check=False
    )
    if bash_bin == "/bin/bash" and "version 3.2" not in version.stdout:
        pytest.skip("/bin/bash is not the bash-3.2 this test targets")
    script = template_dir / "scripts" / "refresh-binary-checksums.sh"
    wf = workflow_repo / ".github" / "workflows"
    old_commit, new_commit = "1" * 40, "2" * 40
    (wf / "ci.yml").write_text(f'BATS_VERSION: "1.13.0"\nBATS_COMMIT: "{old_commit}"\n')
    # No BASE_REF (local run), so the gate just recomputes; stub the network commit resolution.
    body = (
        f'fetch_commit() {{ printf "%s" "{new_commit}"; }}\n'
        'refresh_pin ".github/workflows/ci.yml" BATS COMMIT fetch_commit '
        "'^([0-9a-f]{40}|[0-9a-f]{64})$' \"commit id\"\n"
    )
    result = _run_region(script, body, repo=workflow_repo, bash_bin=bash_bin)
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"BATS 1.13.0 -> {new_commit}" in result.stdout
    assert f'BATS_COMMIT: "{new_commit}"' in (wf / "ci.yml").read_text()


def test_fetch_commit_prefers_dereferenced_annotated_tag(
    template_dir: Path, workflow_repo: Path
) -> None:
    """#236: fetch_commit resolves an annotated tag to its underlying commit (the `^{}` row).

    `git` is stubbed to emit a canned `git ls-remote` for both an annotated tag (a `^{}` deref
    row is present → that commit wins) and a lightweight tag (no deref row → the plain row's
    commit). No network.
    """
    script = template_dir / "scripts" / "refresh-binary-checksums.sh"
    tag, deref, plain = "3" * 40, "d" * 40, "e" * 40
    # Annotated: both rows present → the ^{} (deref) commit is the real one.
    rows = f'%s\\trefs/tags/v1.13.0\\n%s\\trefs/tags/v1.13.0^{{}}\\n" "{plain}" "{deref}'
    annotated = f'git() {{ printf "{rows}"; }}\nfetch_commit BATS 1.13.0\n'
    r1 = _run_region(script, annotated, repo=workflow_repo)
    assert r1.returncode == 0, r1.stderr
    assert r1.stdout.strip() == deref
    # Lightweight: only the plain row → its commit.
    lightweight = (
        f'git() {{ printf "%s\\trefs/tags/v1.13.0\\n" "{tag}"; }}\nfetch_commit BATS 1.13.0\n'
    )
    r2 = _run_region(script, lightweight, repo=workflow_repo)
    assert r2.returncode == 0, r2.stderr
    assert r2.stdout.strip() == tag
