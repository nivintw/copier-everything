<!--
SPDX-FileCopyrightText: © 2026 Tyler Nivin
SPDX-License-Identifier: MIT
-->

# Scaffold — design notes & decisions

This template extracts the reusable "spine" from `nivintw/dotfiles` and makes the
language/testing/packaging shape configurable. This doc records the model, the
decisions taken (several made autonomously — see **Assumptions**), and open follow-ups.

## The model: a language-agnostic spine + decoupled Python levers

The original first pass collapsed three independent choices into one `include_python`
boolean (*is-a-package* + *has-pytest* + *src-layout*). They're now separate:

| Question | Type | Drives |
| --- | --- | --- |
| `test_frameworks` | multiselect `pytest`/`bats` | which `tests/` suites exist (empty ⇒ no `tests/`) |
| `contains_python` | bool (auto-true if `pytest`) | ruff/ty, Python pre-commit hooks, Python `.gitignore` |
| `python_source` | bool (`when` python) | the `src/<pkg>` package + src assumptions in `pyproject.toml` |
| `is_package` | bool (`when` source) | `[build-system]` distribution metadata (installable/publishable) |

`has_python` is a hidden computed flag (`contains_python or pytest`) that everything
Python gates on. **The spine is language-agnostic**: every cross-cutting tool keeps its
own native config file (`.cz.toml`, `_typos.toml`, `.rumdl.toml`, `.editorconfig`,
`licenserc.toml`, `REUSE.toml`), identical across Python/Rust/shell repos. `pyproject.toml`
exists **only** when there's Python and holds only Python-specific config (ruff, ty,
pytest, `[build-system]`, `[project]`, `[tool.uv]`).

### The four canonical shapes (all CI-verified — see `tests/answers/`)

1. **Installable package** — `python_source=T, is_package=T`: `src/<pkg>`, `[build-system]`, wheel.
2. **pyproject-only-for-pytest** — `python_source=F, [pytest]`: no `src/`, `package=false`, flat `tests/` + `conftest.py`.
3. **pytest + bats (dotfiles model)** — `python_source=F, [pytest, bats]`.
4. **No Python** — `contains_python=F`: **no `pyproject.toml`**; `.cz.toml` carries the release machinery.

### commitizen `version_provider`

commitizen lives in `.cz.toml` (always). `version_provider` is `uv` when Python is
present (reads `pyproject [project].version`), else `commitizen` (stores `version` in
`.cz.toml`, works on a tagless repo). A future Rust module would use `cargo`. All three
give gitmoji-conventional commits + auto-`CHANGELOG.md` + an annotated `v$version` tag.

## Assumptions made autonomously (no design owner present)

- **`python_source=T, is_package=F` = "installed, unpublished" (uv `--package` style).**
  Always has `[build-system]` + `package=true` so it's importable; `is_package` only
  toggles distribution metadata (readme, classifiers). Confirmed with the user.
- **`is_package` / `python_source` defaults track their parent** (`{{ python_source }}` /
  `{{ has_python }}`), because a skipped Copier question still resolves its default — a
  literal `true` would have leaked `src/` into no-Python repos.
- **`_tasks` auto-runs `git init → uv sync → git add → initial commit → prek install`**
  (with `--trust`). The commit happens *before* `prek install` deliberately:
  `no-commit-to-branch` would otherwise block the first commit to `main`. Identity comes
  from the answered `author_name`/`author_email` so it works without a global git config.
- **Dropped `check-hooks-apply`.** A freshly-scaffolded repo legitimately has hygiene
  hooks (e.g. `check-json`) that match zero files, which that meta-hook fails on.
- **The scaffold repo does not copy the full dotfiles branch rulesets.** Those assume a
  release GitHub App + bypass actors that don't exist on a fresh repo and would block an
  automated merge. Branch protection here just requires the `ci` check + a PR. Applying
  the production rulesets + release App is a follow-up (see below).

## Bugs found & fixed (pre-existing in the first pass; never validated post-render)

- **Apache-2.0 never rendered** — `LICENSE.jinja`'s `{% raw %}{% include 'LICENSES/Apache-2.0.txt' %}{% endraw %}`
  resolved against the clone root; corrected to `template/LICENSES/Apache-2.0.txt`.
- **Unused-license `reuse` failure** — both license texts were copied; the unchosen one is
  now dropped via templated `_exclude`.
- **`reuse`/`hawkeye` failures** — `.copier-answers.yml` had no SPDX header; `.py` files
  lacked the blank line after the header that hawkeye expects.
- **`end-of-file-fixer` rewrote `.copier-answers.yml` + `.gitignore`** on first run (double
  trailing newline); fixed with Jinja whitespace control.
- **Module shapes didn't pass their own gate** (found in review): `.dockerignore`/`.helmignore`
  had no SPDX header; Helm's Go-templated YAML tripped `check-yaml` and the templates left a
  double-newline EOF. Headers added (+ `.helmignore` mapped in `licenserc.toml`), `check-yaml`
  now excludes `helm/*/templates/` (validated by `helm lint`), and the `{%- endraw %}` trim
  fixes the EOF. `.dockerignore` also still listed `.mypy_cache` → now `.ty_cache`.

## Self-test

`tests/render-matrix.sh` renders every `tests/answers/*.yml` shape and runs the full gate
(reuse, hawkeye, taplo, prek, and — derived from the render — uv/ruff/ty/pytest/bats/helm
lint). The matrix covers the 4 canonical Python/testing shapes, the unpublished-package and
bare-spine edges, the Apache-license path, and a full terraform+docker+helm build. Run it
locally or let `.github/workflows/ci.yml` run it on every PR.

## Open follow-ups (not blocking)

- **Release infra**: `main.yml` keeps the full App-signed commitizen release. Each
  generated repo still needs a release App + `CI_APP_ID`/`CI_APP_PRIVATE_KEY` + a ruleset
  bypass before it works. Apply the production rulesets to this repo once that App exists.
- **`python_version`** is a question (default `3.13`); bump to `3.14` to match dotfiles if wanted.
- **Rust module** is *enabled by* this architecture but unbuilt. So are `docs`(mkdocs)/devcontainer.
- Terraform/Docker/Helm are still minimal **stubs** (a single example resource, a generic
  image, a bare Deployment/Service) — now gate-clean and CI-covered, but flesh out per project.
