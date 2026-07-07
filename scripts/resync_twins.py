#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""Fix twin drift: re-render the dogfood answer set and copy the byte-identical twins over root.

copier-everything dogfoods its own template — certain files exist as both a templated source
under `template/` and a rendered copy at the repo root ("twins"). tests/test_synced_files.py
DETECTS drift in CI; this is the FIXER. It renders the template (via the shared render module the
tests use, so there's no second render path to drift) and copies each TRIVIALLY_EQUAL twin — the
ones that must be byte-for-byte identical — over its root copy. `--check` reports drift and writes
nothing (exit 1 on drift), for use as a gate.

Only the byte-identical (TRIVIALLY_EQUAL) twins are resynced: the STRUCTURALLY_TESTED ones differ
from the template by design (documented deviations), so blindly copying them would clobber that.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tests"))

# These live under tests/, put on sys.path just above; ty can't follow that runtime insertion.
from render_support import DOGFOOD_DATA, render  # noqa: E402 # ty: ignore[unresolved-import]
from test_synced_files import TRIVIALLY_EQUAL  # noqa: E402 # ty: ignore[unresolved-import]


def _drifted(rendered: Path) -> list[str]:
    """The TRIVIALLY_EQUAL twins whose root copy differs from a fresh render."""
    drift = []
    for relative in sorted(TRIVIALLY_EQUAL):
        source = rendered / relative
        if not source.exists():
            continue  # not produced for this render shape
        destination = REPO / relative
        old = destination.read_bytes() if destination.exists() else None
        if source.read_bytes() != old:
            drift.append(relative)
    return drift


def main() -> int:
    """Resync (or, with --check, report) the dogfood twins; return a process exit code."""
    parser = argparse.ArgumentParser(description="Resync copier-everything's dogfood twins.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report drift and write nothing; exit 1 if any twin has drifted.",
    )
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        rendered = render(REPO, Path(tmp), data=dict(DOGFOOD_DATA), skip_tasks=True)
        drift = _drifted(rendered)

        if args.check:
            if not drift:
                print("All twins in sync.")
                return 0
            print("Twin drift — the repo root differs from a fresh template render:")
            print("\n".join(f"  {relative}" for relative in drift))
            print("Run `python scripts/resync_twins.py` (no --check) to copy the render over root.")
            return 1

        if not drift:
            print("All twins already in sync.")
            return 0
        for relative in drift:
            destination = REPO / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(rendered / relative, destination)
        print("Resynced twins:")
        print("\n".join(f"  {relative}" for relative in drift))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
