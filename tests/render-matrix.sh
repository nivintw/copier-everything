#!/usr/bin/env bash
# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

# Render every answer set in tests/answers/ and run the full quality gate on each
# generated project. Which checks run is derived from what the render produced (a
# pyproject → uv/ruff/ty/pytest; *.bats → bats), so adding a new shape is just a new
# answers file. This is the scaffold's own test suite — run locally or in CI.
#
#   Run:  tests/render-matrix.sh
#
# Shapes are independent, so they run in PARALLEL: the orchestrator renders + gates one
# shape (full-modules, which enables every module) first to warm the shared prek/uv caches,
# then fans the rest out via `xargs -P` (cap = CPU count). Each shape re-invokes this script
# in single-shape mode (`--one`) as its own process — no bash-4 job control needed (macOS
# ships bash 3.2). Per-shape output is buffered to a log and printed grouped at the end.
#
# Requires: copier, uv (provides uvx), reuse, hawkeye, taplo, bats, git.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ANSWERS_DIR="$REPO_ROOT/tests/answers"

# ----------------------------------------------------------------------------------------
# Single-shape mode: `render-matrix.sh --one <answers> <src> <work>`. Renders + gates ONE
# shape, appending formatted results to <work>/logs/<name>.log and touching
# <work>/fail/<name> if any check fails. Invoked by the orchestrator (below), never by hand.
# ----------------------------------------------------------------------------------------
if [ "${1:-}" = "--one" ]; then
  answers="$2"
  SRC="$3"
  WORK="$4"
  name="$(basename "$answers" .yml)"
  out="$WORK/render/$name"
  log="$WORK/logs/$name.log"

  # A shape leaves a "done" marker ONLY when it reaches a known conclusion — the success
  # path's end or fail_exit. Deliberately NOT a `trap … EXIT`: that would also fire on an
  # abnormal exit (a `set -u` unbound-var error mid-run), masking it as completed. So any
  # path that doesn't reach a done() call — a SIGKILL (OOM), a `set -u` abort, or xargs
  # failing to exec the worker — leaves no marker and is caught as a failure downstream.
  done_mark() { touch "$WORK/done/$name"; }

  emit() { printf '%s\n' "$*" >>"$log"; } # append a line to this shape's log
  mark_fail() { touch "$WORK/fail/$name"; }
  fail_exit() { # label, [logfile-to-tail]
    emit "    ❌ $1"
    [ -n "${2:-}" ] && sed 's/^/        /' "$2" | tail -15 >>"$log"
    mark_fail
    done_mark
    exit 0
  }
  run() { # label, cmd...
    local label="$1"
    shift
    local cmdlog
    cmdlog="$(mktemp "$WORK/tmp.XXXXXX")"
    if (cd "$out" && "$@" >"$cmdlog" 2>&1); then
      emit "    ✅ $label"
    else
      emit "    ❌ $label"
      sed 's/^/        /' "$cmdlog" | tail -15 >>"$log"
      mark_fail
    fi
    rm -f "$cmdlog"
  }

  emit "═══ shape: $name ═══"

  rlog="$(mktemp "$WORK/tmp.XXXXXX")"
  copier copy --defaults --data-file "$answers" --skip-tasks "$SRC" "$out" >"$rlog" 2>&1 ||
    fail_exit "render FAILED" "$rlog"
  (cd "$out" && git init -q && git add -A) >"$rlog" 2>&1 ||
    fail_exit "git init/add FAILED" "$rlog"
  rm -f "$rlog"
  # Guard against a vacuous pass: the gate (prek/reuse/hawkeye) runs on tracked files, so
  # an empty index would let every check "pass" having inspected nothing.
  [ -n "$(cd "$out" && git diff --cached --name-only)" ] ||
    fail_exit "nothing staged — render/staging produced no files"

  # For Python shapes, materialize uv.lock the way a real generated repo does (its `_tasks`
  # run `uv sync` before the first commit) and stage it, so the gate runs against a realistic
  # tree. In particular the osv-scanner hook keys off a committed uv.lock.
  if [ -f "$out/pyproject.toml" ]; then
    run "uv lock" uv lock
    run "stage uv.lock" git add -A
  fi

  # Always: licensing + TOML formatting (system tools; prek skips them so they run here).
  run "reuse lint" reuse lint
  run "hawkeye check" hawkeye check --config .config/licenserc.toml
  run "taplo fmt --check" taplo fmt --check
  run "prek (all hooks)" env SKIP=taplo,hawkeye-format,no-commit-to-branch uvx prek run --all-files

  # Python checks, only if the render produced a pyproject.
  if [ -f "$out/pyproject.toml" ]; then
    run "uv sync" uv sync
    run "ruff check" uv run ruff check .
    run "ruff format --check" uv run ruff format --check .
    run "ty check" uv run ty check .
    run "validate-pyproject" uvx validate-pyproject pyproject.toml
    if compgen -G "$out/tests/test_*.py" >/dev/null; then
      run "pytest" uv run pytest -q
    fi
  fi

  # bats, only if the render produced shell tests.
  if compgen -G "$out/tests/*.bats" >/dev/null; then
    run "bats tests/" bats tests/
  fi

  # helm lint, only if the render produced a chart and helm is available.
  if command -v helm >/dev/null 2>&1; then
    for chart in "$out"/helm/*/; do
      [ -f "$chart/Chart.yaml" ] && run "helm lint $(basename "$chart")" helm lint "$chart"
    done
  fi

  done_mark # reached the end cleanly (failures, if any, are recorded as fail-markers)
  exit 0
fi

# ----------------------------------------------------------------------------------------
# Orchestrator mode.
# ----------------------------------------------------------------------------------------
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$WORK/logs" "$WORK/fail" "$WORK/render" "$WORK/done"

# Render from a .git-less copy so the WORKING TREE is what gets tested (Copier would
# otherwise render the last commit of a git source, hiding uncommitted changes).
SRC="$WORK/src"
rsync -a --exclude '.git' --exclude '.venv' "$REPO_ROOT/" "$SRC/"

missing=()
for tool in copier uv uvx reuse hawkeye taplo bats git rsync trivy osv-scanner; do
  command -v "$tool" >/dev/null 2>&1 || missing+=("$tool")
done
if [ "${#missing[@]}" -gt 0 ]; then
  echo "ERROR: missing required tools: ${missing[*]}" >&2
  exit 1
fi

shopt -s nullglob
shapes=("$ANSWERS_DIR"/*.yml)
if [ "${#shapes[@]}" -eq 0 ]; then
  echo "ERROR: no answer sets found in $ANSWERS_DIR" >&2
  exit 1
fi

# Warm the shared caches with one shape BEFORE fanning out, so the parallel workers don't
# each cold-bootstrap the same prek/uv hook envs at once. full-modules enables every module,
# so it pulls the superset of hook environments; fall back to the first shape if it's gone.
#
# INVARIANT this relies on: no two shapes share a hook env that full-modules does NOT warm.
# Today the only un-warmed env is sqlfluff's dbt-templater variant (full-modules sets
# sql_use_dbt:false), needed by exactly one shape (sql-dbt) — so it bootstraps alone, no
# race. If you add a SECOND sql_use_dbt:true shape, warm that variant too (or accept relying
# on prek's install-time locking for the concurrent same-env bootstrap).
warm="$ANSWERS_DIR/full-modules.yml"
[ -f "$warm" ] || warm="${shapes[0]}"
"$0" --one "$warm" "$SRC" "$WORK" || true

# Fan the remaining shapes out across CPUs. xargs -P is portable (BSD + GNU); -0 keeps paths
# safe. Each invocation is a fresh `--one` process sharing $SRC/$WORK.
rest=()
for s in "${shapes[@]}"; do
  [ "$(basename "$s")" = "$(basename "$warm")" ] && continue
  rest+=("$s")
done
if [ "${#rest[@]}" -gt 0 ]; then
  jobs="$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 4)"
  printf '%s\0' "${rest[@]}" |
    xargs -0 -P "$jobs" -I {} "$0" --one {} "$SRC" "$WORK"
fi

# Positive completion check: every shape must have left a done-marker. A missing one means
# its worker never finished (SIGKILL/OOM, or xargs failed to exec it) — treat that as a
# failure so a dead worker can't pass for green by simply leaving no fail-marker.
for s in "${shapes[@]}"; do
  n="$(basename "$s" .yml)"
  if [ ! -f "$WORK/done/$n" ]; then
    printf '═══ shape: %s ═══\n    ❌ did not complete (worker killed, or never ran)\n' "$n" >>"$WORK/logs/$n.log"
    touch "$WORK/fail/$n"
  fi
done

# Print every shape's buffered output, grouped, in a stable (alphabetical) order.
for log in "$WORK"/logs/*.log; do
  cat "$log"
done

echo "═══════════════════════════════"
# Exit status is a plain pass/fail driven by the fail markers (one per failed shape; a raw
# count could wrap to 0 mod 256 and turn a mass failure green).
fail_count=$(find "$WORK/fail" -type f | wc -l | tr -d ' ')
if [ "$fail_count" -eq 0 ]; then
  echo "ALL SHAPES GREEN ✅"
  exit 0
fi
echo "FAILURES: $fail_count shape(s) failed ❌"
exit 1
