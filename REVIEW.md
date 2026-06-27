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
own native config file (`.cz.toml`, `.config/typos.toml`, `.config/rumdl.toml`, `.editorconfig`,
`.config/licenserc.toml`, `REUSE.toml`), identical across Python/Rust/shell repos. `pyproject.toml`
exists **only** when there's Python and holds only Python-specific config (ruff, ty,
pytest, `[build-system]`, `[project]`, `[tool.uv]`).

### The four canonical shapes (all CI-verified — see `tests/answers/`)

1. **Installable package** — `python_source=T, is_package=T`: `src/<pkg>`, `[build-system]`, wheel.
2. **pyproject-only-for-pytest** — `python_source=F, [pytest]`: no `src/`, `package=false`, flat `tests/` + `conftest.py`.
3. **pytest + bats (dotfiles model)** — `python_source=F, [pytest, bats]`.
4. **No Python** — `contains_python=F`: **no `pyproject.toml`**; the version of record lives only in `.config/.release-please-manifest.json` + tags.

### release-please (versioning) + commitizen (commit-msg only)

release-please owns versioning: `.config/release-please-config.json` (`release-type: simple`) +
`.config/.release-please-manifest.json` hold the version of record. On push to `main` it maintains
a Release PR that bumps the version + `CHANGELOG.md` and auto-merges (`--auto --rebase`)
once its required checks pass — continuous releases — cutting the `vX.Y.Z` tag + GitHub
Release. For Python shapes an `extra-files` TOML updater
mirrors the version into `pyproject.toml [project].version` (what a wheel build reads);
no-Python shapes keep the version in the manifest + tags only. commitizen stays solely as
the commit-msg linter (`.cz.toml`, `cz_conventional_commits`) — plain Conventional Commits,
**no gitmoji**, because release-please can't parse a leading emoji. Auth is a release
GitHub App (`CI_CLIENT_ID` + `CI_APP_PRIVATE_KEY`); an App-token commit is GitHub-verified,
so it replaces the old GraphQL signed-commit dance.

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
  double-newline EOF. Headers added (+ `.helmignore` mapped in `.config/licenserc.toml`), `check-yaml`
  now excludes `helm/*/templates/` (validated by `helm lint`), and the `{%- endraw %}` trim
  fixes the EOF. `.dockerignore` also still listed `.mypy_cache` → now `.ty_cache`.

## Self-test

`tests/render-matrix.sh` renders every `tests/answers/*.yml` shape and runs the full gate
(reuse, hawkeye, taplo, prek, and — derived from the render — uv/ruff/ty/pytest/bats/helm
lint). The matrix covers the 4 canonical Python/testing shapes, the unpublished-package and
bare-spine edges, the Apache-license path, and a full terraform+docker+helm build. Run it
locally or let `.github/workflows/ci.yml` run it on every PR.

The shapes are independent, so the harness **warms the shared prek/uv caches on one shape
(`full-modules`, the superset of hooks) then runs the rest in parallel** (`xargs -P`,
re-invoking itself per shape — no bash-4 job control). CI additionally caches `~/.cache/prek`
for the render job, so hook envs aren't cold-bootstrapped every run.

## CI / supply-chain hardening (issue #3)

The workflow/release pipeline and dependency pins are hardened end-to-end:

- **Workflow lint + audit as prek hooks** — `actionlint` (lints workflows, shellchecks
  `run:` blocks), `zizmor` (security audit), and `shfmt` (shell formatter, complementing
  shellcheck). All three are pip-backed (`actionlint-py`, `zizmor`, `shfmt-py`) so they
  **self-bootstrap a pinned env** — no new `language: system` exceptions, and `render-matrix`
  exercises them on every rendered shape with no new CI tooling.
- **zizmor runs `--offline`** in the hook: the AST audits (template-injection,
  excessive-permissions, artipacked, blanket App-token) run with no network; the audits that
  need a GH token (known-vulnerable-actions, ref-confusion) are skipped there and instead run
  **online in the template repo's own `lint-workflows` CI job** for full coverage. This keeps
  a generated repo's local gate deterministic and token-free.
- **Findings fixed in the generated release workflow** (`main.yml`): the release tag is routed
  through `env:` (was interpolated into the `gh release create` shell — template-injection);
  the App token is scoped `permission-contents: write` (was inheriting blanket installation
  permissions); checkouts set `persist-credentials: false` (artipacked).
- **Actions are SHA-pinned** with a `# vX.Y.Z` comment so Renovate maintains the digest.
- **Renovate** — the generated repo ships `.github/renovate.json` (pre-commit + action-digest
  managers, ruff grouped). The template repo dogfoods a root `.github/renovate.json5`: its own
  `ci.yml` is handled by the native managers, but the pins **inside `template/**/*.jinja`** need
  `customManagers` (regex) because Renovate's native managers don't parse `.jinja`. The pinned
  hawkeye/taplo release binaries are bumped via `# renovate:` comment annotations.

## Module + dependency-CVE scanning (issue #4)

The modules linted *syntax* but didn't scan for *security*; the dependency tree wasn't
scanned at all (ruff `ALL` lints code, not deps). Added, each gated to its shape/module:

- **hadolint** (docker) — the Dockerfile analog of shellcheck. `hadolint-py` is pip-backed
  so it self-bootstraps (no Docker). The uv stage image is pinned off `:latest` (DL3007).
- **checkov + trivy** (terraform) — IaC misconfig (e.g. a public bucket) that `fmt`/`validate`
  miss. checkov self-bootstraps (pip); **trivy is a system release binary** (Brewfile locally,
  CI install), like hawkeye/taplo. trivy needs `--exit-code 1` to fail the gate.
- **uv audit + osv-scanner** (deps) — `uv audit` (native, PyPA advisories) plus osv-scanner
  (system binary; reads `uv.lock` directly and also non-Python lockfiles). Both gate on
  `has_python`.
- **pytest-cov** — a `--cov-fail-under=80` gate, **only for `python_source` shapes** (a
  pytest-only-no-src repo has no package to measure).

Design notes:

- **render-matrix now runs `uv lock` before the gate** for Python shapes (and stages the lock),
  so the osv-scanner hook — which keys off a committed `uv.lock` — is actually exercised. This
  mirrors a real generated repo, whose `_tasks` run `uv sync` before the first commit.
- **System tools** (trivy, osv-scanner) follow the hawkeye/taplo pattern: local via the
  dotfiles Brewfile, CI via a pinned curl install. render-matrix's tool-presence check now
  lists them so a missing binary fails loudly instead of mid-hook.
- **Renovate**: new pre-commit hooks (hadolint, checkov) and the uv image are picked up by the
  native managers / existing customManagers; trivy/osv-scanner CI-install versions use a
  `# renovate:`-annotated **env-var** pattern (their release assets embed the version, so a
  URL-path bump would desync). A second customManager handles that pattern; the URL one was
  tightened so the two never bind the wrong version.
- **Trade-off — CVE scans are time-varying *and* network-dependent**: a newly-published
  advisory in a (dev-only) dep can turn a green gate red with no code change — inherent to CVE
  scanning (the scaffold has no runtime deps, so only dev-tool deps are audited). The flip side:
  uv audit / osv-scanner hit remote advisory APIs and `trivy config` pulls its checks bundle
  from a registry, so a registry/API **outage** also fails the gate with zero advisory changes.
- **`uv audit` is an experimental command** (uv 0.11.x; the `--preview-features audit-command`
  flag only silences the preview warning today). Renovate auto-bumps uv, and an experimental
  CLI surface is the most likely thing to rename/remove a flag and break the hook — watch uv
  release notes when its `audit` bumps land.

## SQL module (issue #5)

A new `include_sql` toggle, modeled on terraform/docker/helm:

- **sqlfluff-fix + sqlfluff-lint** (pip-backed, self-bootstrapping) — the ruff check+format
  pattern for SQL: fix autofixes, lint catches the rest.
- **`sql_dialect`** (mandatory when `include_sql`) is the full sqlfluff dialect list, default
  `sqlite`; it renders into `.sqlfluff` (which *requires* a dialect). **`sql_use_dbt`** (opt-in)
  sets `templater = dbt` **and** adds `sqlfluff-templater-dbt` to the hooks'
  `additional_dependencies` (the hook runs in an isolated venv, so a global dbt install isn't
  visible to it). The dbt shape ships **no `example.sql`** — sqlfluff has nothing to lint until
  the user adds dbt models + a reachable dbt project, so it's green-on-arrival. The dbt templater
  *env build* isn't exercised by render-matrix (the `sql-dbt` shape has no `.sql` to trigger it);
  the non-dbt path is fully covered across all 29 dialects.
- A `sql/` dir (`example.sql` + `.sqlfluff` + README), a dedicated no-Python `sql` answer
  shape, and `include_sql` added to `full-modules`.

Licensing of the new file types was the fiddly part:

- **`example.sql`** uses hawkeye's *native* SQL header style — `--` delimiter lines wrapping
  the SPDX lines (hawkeye rewrites a bare `-- SPDX` header to that form, so the template emits
  it pre-shaped).
- **`.sqlfluff`** keeps its own `#` header (reuse-verified) but is **excluded from hawkeye**,
  which doesn't map that filename. The tempting fix — mapping it into `licenserc`'s
  `SCRIPT_STYLE` `filenames` array — pushes that single-line array past taplo's 80-col wrap
  point *only* when helm+sql coincide, so taplo would demand a multi-line array there but a
  single-line one elsewhere, and no static Jinja source satisfies both (taplo auto-collapses
  short arrays and auto-expands long ones). Excluding via the already-multi-line `excludes`
  array sidesteps the reflow entirely.

## Repo-hygiene / governance files (issue #6)

Every generated repo now starts with the standard governance + DX baseline. The docs are
**always-on** (governance is universal); the dev container is the one opinionated/heavier
piece, so it's behind an `include_devcontainer` toggle.

- **Always-on**: `.github/CODEOWNERS`, `SECURITY.md`, `CONTRIBUTING.md`,
  `.github/PULL_REQUEST_TEMPLATE.md`, and YAML issue forms (`bug_report` / `feature_request`
  / `config`). A new **`repo_owner`** question (GitHub login, default `nivintw`) drives
  CODEOWNERS and the repo links in SECURITY/CONTRIBUTING.
- **`include_devcontainer`** (opt-in) → `.devcontainer/devcontainer.json` (the Microsoft
  Python image + `uv` for Python shapes, the generic base image otherwise).

Licensing followed the established patterns:

- `.md` / `.yml` carry SPDX headers hawkeye maintains (`<!-- -->` / `#`).
- **`CODEOWNERS`** has no extension hawkeye maps, so — like `.sqlfluff` — it keeps its own
  `#` header (reuse-verified) and is added to hawkeye's `excludes`.
- **`devcontainer.json`** is strict JSON (no comments → `check-json` passes); the pre-existing
  `**/*.json` REUSE annotation + hawkeye exclude already cover it, so no header.
- The PR template has no H1 (it's section stubs), so it carries `<!-- rumdl-disable-file
  MD041 -->`, mirroring the README's disable.

## Open follow-ups (not blocking)

- **Release infra**: `main.yml` runs release-please. Each generated repo still needs a
  release GitHub App (Contents + Pull requests: read/write) + a `CI_CLIENT_ID` variable +
  a `CI_APP_PRIVATE_KEY` secret + a ruleset bypass before releases activate (the release
  job skips cleanly until then). The scaffold repo itself releases the same way via its
  own `main.yml` (reusable `ci.yml` + release-please), matching the template's shape. Apply
  the production rulesets once that App exists.
- **`python_version`** is a question (default `3.13`); bump to `3.14` to match dotfiles if wanted.
- **Rust module** is *enabled by* this architecture but unbuilt; so is a `docs` (mkdocs) module.
- Terraform/Docker/Helm are still minimal **stubs** (a single example resource, a generic
  image, a bare Deployment/Service) — now gate-clean and CI-covered, but flesh out per project.
