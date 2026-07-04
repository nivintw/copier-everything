# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""Static invariants over tests/answers/*.yml that don't need a render or the full gate.

These are checked here (fast, no external tools) in addition to the runtime tripwire in
tests/render-matrix.sh (which catches the same violation for anyone running the matrix
directly without running pytest first).
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def test_exactly_one_sql_use_dbt_fixture(template_dir: Path) -> None:
    """render-matrix.sh's cache-warming step only warms ONE dbt-templater hook env.

    full-modules.yml (the shape warmed before fan-out) sets sql_use_dbt:false, so the only
    un-warmed env is the dbt-templater variant, needed by exactly one shape today. A second
    sql_use_dbt:true shape would race to bootstrap that env concurrently — see the invariant
    comment in tests/render-matrix.sh.
    """
    answers_dir = template_dir / "tests/answers"
    matches = [
        f.name
        for f in answers_dir.glob("*.yml")
        if re.search(r"^sql_use_dbt:\s*true\s*$", f.read_text(), re.MULTILINE)
    ]
    assert matches == ["sql-dbt.yml"], (
        f"expected exactly tests/answers/sql-dbt.yml to set sql_use_dbt: true, got {matches} — "
        "warm the new shape's dbt-templater env too, or the cache-warming invariant breaks"
    )
