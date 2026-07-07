# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""Generated CI secret-scan job (#232) and issue-form header hygiene (#230).

Both are render-shape assertions: the template must emit a full-history, checksum-pinned
gitleaks scan, and its issue-form YAML must begin with the form keys (a leading comment makes
GitHub's issue-form parser silently fall back to a blank issue).
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest
import yaml

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

ISSUE_FORMS = ("bug_report.yml", "feature_request.yml", "config.yml")


@pytest.fixture(scope="module")
def project(
    template_dir: Path,
    output_dir_module_scope: Path,
    render_template: Callable[..., Path],
) -> Path:
    """A default render (docs site on, pytest + bats) exercising both the CI and issue forms."""
    return render_template(
        template_dir,
        output_dir_module_scope,
        data={"project_name": "CI Demo", "test_frameworks": ["pytest", "bats"]},
        skip_tasks=True,
    )


def test_ci_has_full_history_pinned_gitleaks_scan(project: Path) -> None:
    """#232: CI runs a full-history, checksum-pinned, --redact gitleaks scan with a shallow guard."""
    ci = yaml.safe_load((project / ".github" / "workflows" / "ci.yml").read_text())
    assert "secret-scan" in ci["jobs"], "no secret-scan job — CI ships no effective secret scan"
    steps = ci["jobs"]["secret-scan"]["steps"]

    checkout = next(s for s in steps if "actions/checkout" in s.get("uses", ""))
    assert checkout["with"]["fetch-depth"] == 0, "gitleaks needs full history (fetch-depth: 0)"

    scan = next(s for s in steps if "gitleaks" in s.get("name", "").lower())
    assert re.fullmatch(r"[0-9a-f]{64}", scan["env"]["GITLEAKS_SHA256"]), "gitleaks not SHA256-pinned"
    run = scan["run"]
    assert "is-shallow-repository" in run, "no shallow-checkout guard — a shallow clone scans nothing"
    assert "sha256sum -c" in run, "gitleaks download not checksum-verified"
    assert "git --redact --verbose" in run, "expected a --redact full-history `gitleaks git` scan"


def test_issue_forms_do_not_start_with_a_comment(project: Path) -> None:
    """#230: an issue-form YAML that begins with a comment is silently rejected by GitHub."""
    for name in ISSUE_FORMS:
        text = (project / ".github" / "ISSUE_TEMPLATE" / name).read_text()
        first = next(line for line in text.splitlines() if line.strip())
        assert not first.lstrip().startswith("#"), (
            f"{name} begins with a comment ({first!r}) — GitHub's form parser would reject it"
        )


def test_issue_forms_are_still_valid_yaml_forms(project: Path) -> None:
    """The forms still parse and carry their form keys after dropping the SPDX header."""
    for name in ("bug_report.yml", "feature_request.yml"):
        doc = yaml.safe_load((project / ".github" / "ISSUE_TEMPLATE" / name).read_text())
        assert {"name", "description", "body"} <= doc.keys(), f"{name} lost its form keys"
    config = yaml.safe_load((project / ".github" / "ISSUE_TEMPLATE" / "config.yml").read_text())
    assert config["blank_issues_enabled"] is False
