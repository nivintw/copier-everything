<!--
SPDX-FileCopyrightText: © 2026 Tyler Nivin
SPDX-License-Identifier: MIT
-->

# Adopting copier-everything into an existing repo

The template is optimized for **greenfield** generation: `copier copy` onto an empty
directory, and the post-copy `_tasks` run `git init`, stage everything, and make a
`chore: scaffold <slug>` commit. Adopting it into a repo that **already exists** — one with
its own git history, real `pyproject.toml`, source, and tests — is a deliberate manual
reconcile, not an automatic merge. This is the repeatable procedure.

> Proof repo: [`nivintw/ddns`](https://github.com/nivintw/ddns) was the first adoption
> (PR [#17](https://github.com/nivintw/ddns/pull/17)); it surfaced every step below.

## 1. Generate with the greenfield tasks turned off

Answer **`initialize_repository: false`** and invoke with `--skip-tasks --overwrite`:

```console
copier copy --skip-tasks --overwrite \
  --data initialize_repository=false \
  gh:nivintw/copier-everything .
```

- `initialize_repository=false` skips the repo-initializing tasks (`git init`, `git add -A`,
  the scaffold commit) so your existing git history is left untouched. (`--skip-tasks` also
  skips them; setting the answer too keeps it recorded in `.copier-answers.yml`, so future
  `copier update` runs stay in adoption mode.)
- `--overwrite` lets Copier write scaffold files over your tree without prompting per file —
  you'll reconcile the real-content ones in the next step.

## 2. Reconcile the real-content files by hand

`copier copy` overwrites these with scaffold stubs. Diff each against what you had (your VCS
has the pre-adoption version) and merge your real content back in:

- **`pyproject.toml`** — restore your real dependencies, scripts/entry points, and version;
  keep the template's tool config (ruff, ty, pytest, build-system) where it's an upgrade. Keep
  the distribution `name` equal to your `project_slug` answer — the emitted
  `__init__.py` reads `__version__` via `importlib.metadata.version("<project_slug>")`, so if
  the two drift the installed package reports `0.0.0+unknown` (silently, no error).
- **`README.md`**, **`CHANGELOG.md`** — keep your real content; take the template's structure
  only where you want it.
- **`src/<pkg>/__init__.py`** — if you're an installable package, the template now derives
  `__version__` from installed metadata (no stale literal); keep your real module body.
- **`.copier-answers.yml`** — committed, so `copier update` works going forward.

Anything an adopter *must* customize should be a copier **answer**, not a post-render
hand-edit — an edit `copier update` would re-clobber every run. If you find yourself patching
a generated value repeatedly (e.g. a repo URL), that's a missing question; prefer
`repo_name`, `project_slug`, etc. over hand-edits. (Repo URLs already come from `repo_name`,
decoupled from the distribution name.)

## 3. Expect a lint/type fix pass on existing code

The template's defaults are strict by design — `ruff` with broad rule selection and `ty`,
with test files only lightly exempted (`[tool.ruff.lint.per-file-ignores]` with
`"tests/**" = ["S101", "INP001"]`). That's correct for *new, clean* code, but pointed at an
existing suite it will surface a lot (ddns's adoption produced hundreds of findings on first
run). Plan for one of:

- a real **fix pass** (`uv run ruff check --fix`, then resolve what's left by hand), or
- a **baseline** if you'd rather adopt incrementally.

Your tests are the behavior guard through this — run them (`uv run pytest`) before and after
so the lint churn doesn't change behavior.

## 4. Commit on your own branch

With `initialize_repository=false` nothing was committed for you. Stage your reconciled tree
and commit on a feature branch, then run the gate and wire up hooks:

```console
uv sync                       # dev toolchain (idempotent; safe to run)
uvx prek run --all-files      # the same gate CI runs
uvx prek install              # install the pre-commit hooks
git add -A && git commit -m "chore: adopt copier-everything"
```

Open it as a PR like any other change — adoption is a reviewed diff against your real
history, not a fresh scaffold.
