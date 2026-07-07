"""PreToolUse guard: block a hand-edit that moves the release-please version off canonical.

release-please owns the version bump. A stray hand-edit that changes it is only caught
indirectly today — via a later release-please conflict. This guard blocks an Edit/Write that
sets the version-of-record (the `.config/.release-please-manifest.json` value, or any file
release-please mirrors it into via `extra-files`) to a value OTHER than the canonical one.
Rewriting the identical value is allowed. If canonical can't be resolved, it fails open loudly.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

# _hooklib is the sibling module in this same dir; it resolves both when Claude Code runs this
# as a script (the script's dir is on sys.path) and when the test harness imports it after
# putting this dir on sys.path.
from _hooklib import (
    allow,
    deny,
    edited_path,
    project_root,
    read_event,
    resulting_content,
    warn_allow,
)

MANIFEST_REL = Path(".config") / ".release-please-manifest.json"
CONFIG_REL = Path(".config") / "release-please-config.json"


def _manifest_version(data: dict) -> str | None:
    """The single-package version from a release-please manifest ('.' key, or the sole entry)."""
    if "." in data:
        return data["."]
    return next(iter(data.values())) if len(data) == 1 else None


def canonical_version(root: Path) -> tuple[str | None, str | None]:
    """(version, error): the manifest's canonical version, or (None, reason) if unresolvable."""
    manifest = root / MANIFEST_REL
    try:
        data = json.loads(manifest.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"could not read {MANIFEST_REL}: {exc}"
    version = _manifest_version(data)
    if not version:
        return None, f"no single-package version in {MANIFEST_REL}"
    return version, None


def version_carriers(root: Path) -> set[Path]:
    """Every file that carries the version: the manifest + release-please's `extra-files`.

    Derived from THIS repo's own release-please-config.json (not a hardcoded list), so it tracks
    whatever a given project actually syncs — pyproject.toml / uv.lock for Python, galaxy.yml for
    an Ansible collection, nothing extra for a config-only repo.
    """
    carriers = {(root / MANIFEST_REL).resolve()}
    try:
        config = json.loads((root / CONFIG_REL).read_text())
    except OSError, json.JSONDecodeError:
        return carriers
    for package in (config.get("packages") or {}).values():
        for extra in package.get("extra-files") or []:
            path = extra.get("path") if isinstance(extra, dict) else extra
            if path:
                carriers.add((root / path).resolve())
    return carriers


def version_in(content: str, file: Path) -> str | None:
    """The version this file's post-edit `content` declares, by the file's own convention."""
    name = file.name.lower()
    if name == MANIFEST_REL.name:
        try:
            return _manifest_version(json.loads(content))
        except json.JSONDecodeError, AttributeError:
            return None
    if name == "pyproject.toml":
        # `$.project.version` — the first line-anchored `version = "..."` (the [project] one;
        # dependency pins are inline tables, never a bare top-of-line assignment).
        match = re.search(r'(?m)^\s*version\s*=\s*["\']([^"\']+)["\']', content)
        return match.group(1) if match else None
    if name == "galaxy.yml":
        match = re.search(r'(?m)^version:\s*["\']?([^"\'\s]+)', content)
        return match.group(1) if match else None
    return None


def decide(event: dict) -> tuple[str, str]:
    """Pure decision: returns (action, message) where action is allow|deny|warn_allow."""
    path = edited_path(event)
    if not path:
        return "allow", ""
    file = Path(path).resolve()
    root = project_root(file.parent)
    if root is None or file not in version_carriers(root):
        return "allow", ""
    canonical, error = canonical_version(root)
    if canonical is None:
        return (
            "warn_allow",
            f"guard_version_bumps: can't resolve the canonical version ({error}); allowing the edit (fail-open).",
        )
    content = resulting_content(event, file)
    if content is None:
        return "allow", ""
    new_version = version_in(content, file)
    if new_version is None or new_version == canonical:
        return "allow", ""
    rel = file.name
    return "deny", (
        f"Blocked: this edit sets the version in {rel} to {new_version}, but release-please's "
        f"canonical version is {canonical}. release-please owns version bumps — don't hand-edit "
        f"the version (rewriting the same value is fine). To release, let release-please's PR bump it."
    )


def main() -> None:
    action, message = decide(read_event())
    {
        "allow": lambda: allow(),
        "deny": lambda: deny(message),
        "warn_allow": lambda: warn_allow(message),
    }[action]()


if __name__ == "__main__":
    main()
