#!/usr/bin/env bash
# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT
#
# Render every answer set in tests/answers/ and run the full quality gate on each
# generated project. Which checks run is derived from what the render produced (a
# pyproject → uv/ruff/ty/pytest; *.bats → bats), so adding a new shape is just a new
# answers file. This is the scaffold's own test suite — run locally or in CI.
#
#   Run:  tests/render-matrix.sh
#
# Requires: copier, uv (provides uvx), reuse, hawkeye, taplo, bats, git.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ANSWERS_DIR="$REPO_ROOT/tests/answers"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# Render from a .git-less copy so the WORKING TREE is what gets tested (Copier would
# otherwise render the last commit of a git source, hiding uncommitted changes).
SRC="$WORK/src"
rsync -a --exclude '.git' --exclude '.venv' "$REPO_ROOT/" "$SRC/"

missing=()
for tool in copier uv uvx reuse hawkeye taplo bats git rsync; do
  command -v "$tool" >/dev/null 2>&1 || missing+=("$tool")
done
if [ "${#missing[@]}" -gt 0 ]; then
  echo "ERROR: missing required tools: ${missing[*]}" >&2
  exit 1
fi

total_fail=0
run() { # label, dir, cmd...
  local label="$1" dir="$2"; shift 2
  if (cd "$dir" && "$@" >"$WORK/out.log" 2>&1); then
    echo "    ✅ $label"
  else
    echo "    ❌ $label"; sed 's/^/        /' "$WORK/out.log" | tail -15
    total_fail=$((total_fail + 1))
  fi
}

shopt -s nullglob
for answers in "$ANSWERS_DIR"/*.yml; do
  name="$(basename "$answers" .yml)"
  out="$WORK/render/$name"
  echo "═══ shape: $name ═══"
  if ! copier copy --defaults --data-file "$answers" --skip-tasks "$SRC" "$out" >"$WORK/render.log" 2>&1; then
    echo "    ❌ render FAILED"; tail -15 "$WORK/render.log"; total_fail=$((total_fail + 1)); continue
  fi
  (cd "$out" && git init -q && git add -A)

  # Always: licensing + TOML formatting (system tools; prek skips them so they run here).
  run "reuse lint"        "$out" reuse lint
  run "hawkeye check"     "$out" hawkeye check
  run "taplo fmt --check" "$out" taplo fmt --check
  run "prek (all hooks)"  "$out" env SKIP=taplo,hawkeye-format,no-commit-to-branch uvx prek run --all-files

  # Python checks, only if the render produced a pyproject.
  if [ -f "$out/pyproject.toml" ]; then
    run "uv sync"             "$out" uv sync
    run "ruff check"          "$out" uv run ruff check .
    run "ruff format --check" "$out" uv run ruff format --check .
    run "ty check"            "$out" uv run ty check .
    run "validate-pyproject"  "$out" uvx validate-pyproject pyproject.toml
    if compgen -G "$out/tests/test_*.py" >/dev/null; then
      run "pytest" "$out" uv run pytest -q
    fi
  fi

  # bats, only if the render produced shell tests.
  if compgen -G "$out/tests/*.bats" >/dev/null; then
    run "bats tests/" "$out" bats tests/
  fi
done

echo "═══════════════════════════════"
if [ "$total_fail" -eq 0 ]; then
  echo "ALL SHAPES GREEN ✅"
else
  echo "FAILURES: $total_fail check(s) failed ❌"
fi
exit "$total_fail"
