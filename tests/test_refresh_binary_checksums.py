# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""pinned_value() must fail loudly on a bad path instead of masking it as "no pin found".

A typo'd file argument used to silently resolve to an empty match (grep's exit 1 "no match"
and exit >=2 "read error" were both swallowed by `2>/dev/null ... || true`), so the only
backstop was the end-of-run `processed -eq 0` check — which doesn't trip if at least one
*other* argument in the same invocation legitimately has pins.
"""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

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
