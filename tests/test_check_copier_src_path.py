# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""The check_copier_src_path pre-commit hook must accept remote `_src_path`, reject local.

The hook ships as `template/scripts/check_copier_src_path.py.jinja`, so it can't be run as-is:
its SPDX header carries Jinja placeholders and its body is wrapped in `{% raw %}`/`{% endraw %}`.
We render it the cheap, robust way — substitute the three SPDX placeholders and drop the raw
markers — then drive the resulting script as a subprocess against fixture `.copier-answers.yml`
files, exactly as pre-commit would invoke it.
"""

from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path


def _is_raw_marker(line: str) -> bool:
    """A `{% raw %}` / `{% endraw %}` tag on its own line, in any whitespace-control variant."""
    stripped = line.strip()
    return stripped.startswith(("{% raw", "{%- raw", "{% endraw", "{%- endraw"))


def _render_script(template_dir: Path, dest: Path) -> Path:
    """Render the `.py.jinja` hook to runnable Python: fill SPDX placeholders, strip raw markers."""
    src = template_dir / "template" / "scripts" / "check_copier_src_path.py.jinja"
    out_lines: list[str] = []
    for line in src.read_text(encoding="utf-8").splitlines(keepends=True):
        if _is_raw_marker(line):
            continue
        rendered = (
            line.replace("{{ year }}", "2026")
            .replace("{{ author_name }}", "Tyler Nivin")
            .replace("{{ license }}", "MIT")
        )
        out_lines.append(rendered)
    dest.write_text("".join(out_lines), encoding="utf-8")
    return dest


@pytest.fixture
def script(template_dir: Path, tmp_path: Path) -> Path:
    """The rendered, runnable hook script."""
    return _render_script(template_dir, tmp_path / "check_copier_src_path.py")


def _run(script: Path, *answer_files: Path) -> subprocess.CompletedProcess[str]:
    """Invoke the hook the way pre-commit does: `python3 <script> <answers-file>...`."""
    return subprocess.run(  # noqa: S603
        [sys.executable, str(script), *(str(f) for f in answer_files)],
        capture_output=True,
        text=True,
        check=False,
    )


def _answers(tmp_path: Path, src_path: str, *, name: str = ".copier-answers.yml") -> Path:
    """Write a minimal `.copier-answers.yml` with the given `_src_path` line."""
    file = tmp_path / name
    file.write_text(f"# Changes here will be overwritten by Copier\n_src_path: {src_path}\n")
    return file


def test_gh_shorthand_passes(script: Path, tmp_path: Path) -> None:
    """A `gh:owner/repo` shorthand is a remote source — it must pass."""
    result = _run(script, _answers(tmp_path, "gh:nivintw/copier-everything"))
    assert result.returncode == 0, result.stdout + result.stderr


def test_https_url_passes(script: Path, tmp_path: Path) -> None:
    """An https:// git URL is remote — it must pass."""
    result = _run(script, _answers(tmp_path, "https://github.com/nivintw/copier-everything.git"))
    assert result.returncode == 0, result.stdout + result.stderr


def test_scp_like_git_url_passes(script: Path, tmp_path: Path) -> None:
    """A scp-like `git@host:owner/repo` URL is remote — it must pass."""
    result = _run(script, _answers(tmp_path, "git@github.com:nivintw/copier-everything.git"))
    assert result.returncode == 0, result.stdout + result.stderr


def test_quoted_remote_value_passes(script: Path, tmp_path: Path) -> None:
    """Surrounding quotes must be stripped before classifying the value."""
    result = _run(script, _answers(tmp_path, '"gh:nivintw/copier-everything"'))
    assert result.returncode == 0, result.stdout + result.stderr


def test_absolute_local_path_fails(script: Path, tmp_path: Path) -> None:
    """An absolute filesystem path must fail with a helpful, value-naming message."""
    result = _run(script, _answers(tmp_path, "/Users/someone/workspace/copier-everything"))
    assert result.returncode == 1
    assert "LOCAL path" in result.stderr
    assert "/Users/someone/workspace/copier-everything" in result.stderr
    assert "gh:nivintw/copier-everything" in result.stderr  # names the remedy


def test_relative_local_path_fails(script: Path, tmp_path: Path) -> None:
    """A relative `../tpl` path must fail — it resolves nowhere for other clones."""
    result = _run(script, _answers(tmp_path, "../tpl"))
    assert result.returncode == 1
    assert "LOCAL path" in result.stderr
    assert "'../tpl'" in result.stderr


def test_missing_src_path_key_fails_loudly(script: Path, tmp_path: Path) -> None:
    """An answers file with no `_src_path:` key must fail loudly, not pass silently."""
    file = tmp_path / ".copier-answers.yml"
    file.write_text("_commit: v1.2.3\nproject_name: x\n")
    result = _run(script, file)
    assert result.returncode == 1
    assert "no `_src_path:` key" in result.stderr


def test_missing_file_fails_loudly(script: Path, tmp_path: Path) -> None:
    """A missing answers file must fail loudly with a clear message."""
    result = _run(script, tmp_path / "does-not-exist.yml")
    assert result.returncode == 1
    assert "file not found" in result.stderr


def test_empty_file_fails_loudly(script: Path, tmp_path: Path) -> None:
    """An empty answers file must fail loudly."""
    file = tmp_path / ".copier-answers.yml"
    file.write_text("")
    result = _run(script, file)
    assert result.returncode == 1
    assert "empty" in result.stderr
