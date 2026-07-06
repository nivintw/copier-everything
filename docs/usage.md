<!--
SPDX-FileCopyrightText: © 2026 Tyler Nivin
SPDX-License-Identifier: MIT
-->

# Usage & adoption

Generate a new project, pull template improvements into an existing one, pick the right
canonical shape, and — when you already have a repo — adopt the template without losing your
history.

## Prerequisites

You need [uv](https://docs.astral.sh/uv/), which ships the `uvx` runner. No global Copier
install is required — `uvx` fetches and caches Copier on demand.

| Tool | Install | Why |
| --- | --- | --- |
| `uv` / `uvx` | [astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/) | Runs Copier via `uvx`; also manages the generated project's Python env. |
| `git` | System package or [git-scm.com](https://git-scm.com/) | Required for the post-copy `git init` / scaffold commit tasks and for `copier update`. |

## Generate a new project

Interactive — prompts for every answer:

```bash
uvx copier copy --trust gh:nivintw/copier-everything path/to/new-project
```

Copier asks the [template questions](questions.md), renders the project tree, then runs the
post-copy tasks (because you passed `--trust`).

### What the post-copy tasks do

The `_tasks` block in `copier.yml` runs automatically with `--trust`. Each task is gated and
only fires during the initial `copy` operation:

| Task | Gate | What it does |
| --- | --- | --- |
| `git init` | `initialize_repository = true` | Creates a fresh git repo in the destination directory. |
| `uv sync` | Project contains Python (`has_python`) | Creates the virtual env and installs all dev dependencies. |
| `git add -A` + scaffold commit | `initialize_repository = true` | Stages everything and commits `chore: scaffold <slug>` using the author identity from your answers. The commit runs *before* hook install so the `no-commit-to-branch` hook cannot block the first commit to main. |
| `uvx prek install` | Always on copy; no-ops gracefully if no `.git` present | Wires up the pre-commit and commit-msg hooks so the quality gate runs locally on every subsequent commit. |

!!! tip "Skipping --trust"
    Without `--trust` the tasks are skipped. The post-copy message prints the exact manual
    steps: `git init`, `uv sync`, `git add -A && git commit`, then `uvx prek install` — run
    them in that order (commit before installing hooks).

### Non-interactive use

Two flags make `copier copy` fully non-interactive, useful in CI or scripting:

Use all template defaults (no prompts):

```bash
uvx copier copy --trust --defaults gh:nivintw/copier-everything path/to/new-project
```

Pre-fill answers from a YAML file:

```bash
uvx copier copy --trust --data-file my-answers.yml gh:nivintw/copier-everything path/to/new-project
```

A data file is a plain YAML mapping of question name to value — the same format as the
[canonical shape files](#canonical-project-shapes) in `tests/answers/`. Unspecified questions
fall back to their template defaults.

## Pin a release

By default `copier copy` uses the latest template revision (HEAD of the default branch). To
pin to a specific release:

```bash
uvx copier copy --trust --vcs-ref v1.2.0 gh:nivintw/copier-everything path/to/new-project
```

The pinned ref is stored in `.copier-answers.yml` and becomes the baseline for future
`copier update` runs. See [GitHub Releases](https://github.com/nivintw/copier-everything/releases)
for the available tags.

## Update an existing generated project

Pull template improvements into a project you already generated:

```bash
cd path/to/your-project
uvx copier update
```

Copier reads your answers from `.copier-answers.yml` (committed at generation time), fetches
the latest template revision (or the pinned `_commit` if you used `--vcs-ref`), re-renders the
template with your answers, and three-way merges the diff into your working tree.

### The `.copier-answers.yml` file

This file is generated at copy time, committed into your repo, and read back on every
subsequent `copier update`. It records every answer and the template ref used, so updates are
reproducible without re-prompting. Treat it like any other committed config — do not delete
it.

### Conflict handling

When the template has changed a file you also edited, Copier writes the merged result and
leaves standard `<<<<<<<` / `>>>>>>>` conflict markers for you to resolve. The update never
auto-commits, so you review and stage the result yourself before committing.

!!! note "Run the gate after updating"
    After resolving conflicts, run `uvx prek run --all-files` to verify the merged tree is
    clean before you commit.

## Canonical project shapes

Every shape in the table below is a CI-verified answer set under `tests/answers/`. The test
matrix renders each shape and runs the full quality gate against it on every PR, so these are
not aspirational examples — they are live fixtures. Copy the answers that match your use case
as a starting point for `--data-file` or for answering the interactive prompts. (For just the
Python/testing shapes with a deeper design rationale, see
[the four canonical Python shapes](design.md#the-four-canonical-python-shapes) in the design
model.)

The key [template questions](questions.md) that differentiate shapes are: `test_frameworks`,
`contains_python`, `python_source`, `is_package`, and the opt-in module flags. See
[Modules & levers](modules.md) for the full list.

| Shape | Key answers | What it exercises |
| --- | --- | --- |
| `baseline-only` | `test_frameworks: []`; `contains_python: false` | The bare language-agnostic baseline — no Python, no tests, no `pyproject.toml`. The right starting point for a docs, config, or infrastructure-only repo. |
| `baseline-frontmatter` | `test_frameworks: []`; `contains_python: false`; `markdown_has_frontmatter: true` | Bare baseline where Markdown files carry YAML frontmatter on line 1 (e.g. Claude Code skills, Jekyll/Hugo). Licenses Markdown via `REUSE.toml` instead of inline SPDX headers so frontmatter is never broken. |
| `shell-bats` | `test_frameworks: [bats]`; `contains_python: false` | Pure-shell repo with bats tests. No `pyproject.toml`, no Python toolchain. The minimal shape for shell scripts, dotfiles helpers, or CLI wrappers that need a test suite. |
| `app-pytest` | `test_frameworks: [pytest]`; `python_source: false` | Non-package repo where `pyproject.toml` exists only to host pytest and tooling (ruff, ty) — no `src/` layout. Typical for a scripts repo or a config-driven project that uses Python tests. |
| `app-pytest-bats` | `test_frameworks: [pytest, bats]`; `python_source: false` | pytest + bats together, non-package — the dotfiles model. Mixed-language project with both a Python tooling layer and shell tests; no installable `src/`. |
| `pkg-unpublished` | `test_frameworks: [pytest]`; `python_source: true`; `is_package: false` | Python source in a `src/` layout that is installed locally (editable install) but not built as a distributable package — no dist metadata, no `publish.yml`. The `uv --package` style. |
| `pkg` | `test_frameworks: [pytest]`; `python_source: true`; `is_package: true`; `publish_to_pypi: true` (default); `repo_name: demo-repo` | Installable package with `src/` layout + pytest. The default `publish_to_pypi=true` emits a `publish.yml` workflow (OIDC Trusted Publishing to PyPI). Also exercises `repo_name != project_slug` so GitHub URLs are built from the repo name while the distribution name stays independent. |
| `apache-pkg` | `license: Apache-2.0`; `test_frameworks: [pytest, bats]`; `python_source: true`; `is_package: true`; `publish_to_pypi: false` | Installable package under Apache-2.0 (the non-default license path) + pytest + bats. With `publish_to_pypi=false` no `publish.yml` is emitted — the package is distributable but the CI publish step is omitted. |
| `docker-shell` | `test_frameworks: [bats]`; `contains_python: false`; `include_docker: true` | Docker on the bare baseline with no Python. Exercises the alpine/non-root Dockerfile branch, `hadolint` hook, and `trivy config` scan. Distinct from `full-modules`, which uses the Python Dockerfile branch. |
| `terraform` | `test_frameworks: []`; `contains_python: false`; `include_terraform: true` | Terraform module on the bare baseline with no Python. Exercises the `antonbabenko/pre-commit-terraform` fmt/validate/tflint hooks in isolation, unlike `full-modules`, which only covers Terraform bundled with everything else. |
| `helm` | `test_frameworks: []`; `contains_python: false`; `include_helm: true` | Helm module on the bare baseline with no Python. Exercises `helm lint` and the `check-yaml`/`yamllint` Go-template exclusions in isolation, unlike `full-modules`, which only covers Helm bundled with everything else. |
| `sql` | `test_frameworks: []`; `contains_python: false`; `include_sql: true`; `sql_dialect: sqlite`; `include_devcontainer: true` | SQL module on the bare baseline (no Python). Exercises the dialect-aware `.sqlfluff`, `sqlfluff` lint/fix hooks, REUSE compliance on `.sqlfluff`, and the no-Python devcontainer branch. |
| `sql-dbt` | `test_frameworks: []`; `contains_python: false`; `include_sql: true`; `sql_dialect: snowflake`; `sql_use_dbt: true` | SQL module with the dbt templater. Renders `templater = dbt` into `.sqlfluff` and adds `sqlfluff-templater-dbt` as an additional dependency. Bring your own dbt project and models — this shape guards the render; the dbt templater itself is not exercised without `.sql` files. |
| `no-docs-site` | `test_frameworks: []`; `contains_python: false`; `include_docs_site: false` | Opts **out** of the docs site module on the bare baseline. Every other shape exercises `include_docs_site`'s default-`true` path implicitly; this is the one shape that asserts `mkdocs.yml` and `docs/` are absent when it's turned off. |
| `full-modules` | `python_source: true`; `is_package: true`; `include_terraform: true`; `include_docker: true`; `include_helm: true`; `include_sql: true`; `include_devcontainer: true` | An installable Python package with every module enabled. Exercises module scaffolding REUSE compliance, the Helm `check-yaml` exclusion, and the Python Dockerfile branch. This shape runs first in the test matrix to warm the shared prek and uv caches. |
| `ansible-collection` | `contains_python: false`; `contains_ansible: true`; `ansible_kind: collection` | Ansible collection scaffold. No `pyproject.toml` or Python toolchain. Exercises ansible-lint (production profile), the molecule skeleton, and the `publish-galaxy.yml` workflow (Galaxy publish on release, gated on an `ANSIBLE_GALAXY_API_KEY` repo secret). |
| `ansible-role` | `contains_python: false`; `contains_ansible: true`; `ansible_kind: role`; `publish_to_galaxy: false` | Standalone Ansible role. Exercises ansible-lint over `meta/galaxy_info`, argument specs, and handlers, plus the molecule skeleton. With `publish_to_galaxy=false` no `publish-galaxy.yml` is emitted — the Galaxy publish opt-out path (`ansible-collection` above covers the default opt-in). No Python toolchain. |
| `ansible-playbooks` | `contains_python: false`; `contains_ansible: true`; `ansible_kind: playbooks` | Playbook-centric repo (no collection or role wrapper). Exercises ansible-lint over `playbooks/` and `inventory/`. No molecule, no Galaxy publish step, no Python toolchain. |

## Ansible projects

Ansible projects (collection, role, or playbooks) carry no `pyproject.toml` and no Python
toolchain — `uv sync` is skipped by the post-copy tasks. The quality gate runs through
[ansible-lint](https://ansible.readthedocs.io/projects/lint/) (production profile) wired in
via pre-commit.

### Quality gate

Wire up hooks (includes ansible-lint) — run once after generation:

```bash
uvx prek install
```

Install Galaxy content dependencies (once you add entries to `requirements.yml`):

```bash
uvx --from ansible-core ansible-galaxy install -r requirements.yml
```

Run the full lint pass — same check CI runs:

```bash
uvx prek run ansible-lint --all-files
```

### Testing

The testing step depends on the kind:

| Kind | Command |
| --- | --- |
| collection, role | `uvx --from molecule --with 'molecule-plugins[docker]' molecule test` — converge, idempotence, verify (requires Docker) |
| playbooks | `ansible-playbook playbooks/site.yml` — run the play against your inventory |

### Publishing to Galaxy

Collection and role projects emit a `publish-galaxy.yml` workflow that fires on each GitHub
Release and publishes to [Ansible Galaxy](https://galaxy.ansible.com/). Unlike the PyPI path
there is no OIDC Trusted Publishing — add an `ANSIBLE_GALAXY_API_KEY` repo secret before
cutting your first release.

!!! note "Playbooks do not publish"
    The playbooks kind has no Galaxy publish step — `publish_to_galaxy` is `false` and no
    `publish-galaxy.yml` is emitted.

## Adopting into an existing repo

The template is optimized for greenfield generation: `copier copy` onto an empty directory,
tasks run `git init`, stage everything, and make the first commit. Adopting it into a repo
that **already exists** — one with its own git history, real `pyproject.toml`, source, and
tests — is a deliberate manual reconcile, not an automatic merge.

!!! warning "Answer NO to `initialize_repository`"
    When adopting, the most important answer is `initialize_repository: false`. This skips
    the `git init`, `git add -A`, and scaffold-commit tasks so your existing git history is
    left untouched. It is also stored in `.copier-answers.yml`, so future `copier update` runs
    stay in adoption mode.

### Step 1 — Generate with tasks off

Invoke `copier copy` with `--skip-tasks --overwrite` and pass `initialize_repository=false`
explicitly:

```bash
uvx copier copy --skip-tasks --overwrite \
  --data initialize_repository=false \
  gh:nivintw/copier-everything .
```

`--overwrite` lets Copier write scaffold files over your tree without prompting per-file —
you'll reconcile the real-content files in the next step. `--skip-tasks` ensures no tasks run
even if you forgot `--trust`, as an extra safeguard.

!!! note "Proof repo"
    [`nivintw/ddns`](https://github.com/nivintw/ddns) was the first adoption and surfaced
    every step in this guide. See
    [ddns PR #17](https://github.com/nivintw/ddns/pull/17) for the real adoption diff.

### Step 2 — Reconcile real-content files by hand

`copier copy` overwrites these with scaffold stubs. Diff each against what you had (your VCS
has the pre-adoption version) and merge your real content back in:

- **`pyproject.toml`** — restore your real dependencies, scripts, and version; keep the
  template's tool config (ruff, ty, pytest, build-system) where it is an upgrade. Keep the
  distribution `name` equal to your `project_slug` answer: the emitted `__init__.py` reads
  `__version__` via `importlib.metadata.version("<project_slug>")`, so if the two drift the
  installed package reports `0.0.0+unknown` silently.
- **`README.md`**, **`CHANGELOG.md`** — keep your real content; take the template's structure
  only where you want it.
- **`src/<pkg>/__init__.py`** — if you are an installable package, the template derives
  `__version__` from installed metadata rather than a stale literal; keep your real module
  body.
- **`.copier-answers.yml`** — commit this file; it is what makes `copier update` work going
  forward.

!!! note "Prefer answers over hand-edits"
    Anything an adopter must customize should be a copier answer, not a post-render
    hand-edit — an edit `copier update` would re-clobber on every run. If you find yourself
    patching a generated value repeatedly (e.g. a repo URL), that is a missing question. Repo
    URLs already come from `repo_name`, decoupled from the distribution name.

### Step 3 — Expect a lint/type fix pass

The template's defaults are strict by design: ruff with broad rule selection and ty, with
test files only lightly exempted. Pointed at an existing suite this will surface findings —
the first adoption of `ddns` produced hundreds on first run. Plan for one of:

- A real **fix pass**: `uv run ruff check --fix`, then resolve what remains by hand.
- A **baseline** if you would rather adopt incrementally (ruff and ty both support per-file
  ignores and inline suppressions as a bridge).

Run your tests (`uv run pytest`) before and after the lint pass so the churn does not change
behavior.

### Step 4 — Commit on your own branch

With `initialize_repository=false` nothing was committed for you. Stage your reconciled tree
and commit on a feature branch, then wire up the hooks:

```bash
uv sync                       # dev toolchain (idempotent; safe to re-run)
uvx prek run --all-files      # the same gate CI runs
uvx prek install              # install the pre-commit hooks
git add -A && git commit -m "chore: adopt copier-everything"
```

Open it as a PR like any other change — adoption is a reviewed diff against your real
history, not a fresh scaffold.
