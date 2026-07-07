<!--
SPDX-FileCopyrightText: © 2026 Tyler Nivin
SPDX-License-Identifier: MIT
-->

# Modules & levers

Seven decoupled opt-in modules sit on top of the [always-on quality baseline](baseline.md).
Each is gated behind a single `copier.yml` question — answer yes and you get the files,
hooks, and CI steps; answer no and none of that baggage enters your repo.

!!! note "How modules relate to the baseline"
    The [quality baseline](baseline.md) — prek hooks, REUSE licensing, Conventional Commits,
    hardened CI, Renovate, and secret/vulnerability scanning — is always on. The modules on
    this page are purely additive: they layer extra files and hooks on top without touching
    the baseline configuration.

## The modules at a glance

<div class="grid cards" markdown>

-   :material-language-python:{ .lg .middle } **[Python levers](#python-levers)**

    ---

    A five-deep dependency chain: test frameworks → Python detection → source layout →
    package build → PyPI publish. Each lever is only asked when its parent is true.

-   :material-cube-outline:{ .lg .middle } **[Terraform](#terraform)**

    ---

    A `terraform/` stub with fmt, validate, tflint, checkov, and trivy IaC scanning — all
    gated on `include_terraform`.

-   :material-cube-outline:{ .lg .middle } **[Docker](#docker)**

    ---

    Dockerfile, `.dockerignore`, and `compose.yaml` with hadolint + trivy config hooks and a
    CI image-layer CVE scan.

-   :material-cube-outline:{ .lg .middle } **[Helm](#helm)**

    ---

    A starter chart under `helm/<project_slug>/`, a helm-lint gate hook, and kubeconform
    manifest validation in CI.

-   :material-database-outline:{ .lg .middle } **[SQL](#sql)**

    ---

    A `sql/` directory with sqlfluff fix + lint hooks, a dialect selector, and an optional
    dbt templater.

-   :material-robot-outline:{ .lg .middle } **[Ansible](#ansible)**

    ---

    A first-class `contains_ansible` cascade — three archetypes (`collection`, `role`,
    `playbooks`), ansible-lint, and Molecule CI — orthogonal to Python.

-   :material-laptop:{ .lg .middle } **[Dev Container](#dev-container)**

    ---

    `.devcontainer/devcontainer.json` pre-wired to the Microsoft Python or Debian base image,
    with VS Code extensions.

-   :material-book-open-page-variant-outline:{ .lg .middle } **[Docs Site](#docs-site)**

    ---

    An MkDocs Material scaffold (`mkdocs.yml` + a placeholder page + a Pages build workflow)
    — on by default, unlike every module above.

</div>

## Python levers

Python is not a single yes/no toggle. Three independent choices — "do I have Python?", "do I
have Python *source*?", and "do I build a distribution?" — collapse to a single boolean in
most templates but are genuinely orthogonal here. copier-everything models them as a
dependency chain: each lever is only asked when its parent is on.

```text
test_frameworks ──(pytest selected?)──┐
                                      │ either lever forces
contains_python ──────────────────────┴──► has_python [hidden, computed]
"Does this project contain Python?"         = contains_python OR pytest selected
                                                       │
                                              ┌────────┴────────────┐
                                              │  when: has_python   │
                                              ▼                     ▼
                                       python_source          python_version
                                       "src/<pkg> layout?"   "Minimum MAJOR.MINOR"
                                              │
                                     ┌────────┴──────────┐
                                     │ when: python_source│
                                     ▼                    ▼
                                is_package          python_package
                                "build + dist?"     "import name"
                                     │
                                     │  when: is_package
                                     ▼
                              publish_to_pypi
                         ".github/workflows/publish.yml"
```

### Lever reference

| Question | Type | Default | Asked when | What it gates |
| --- | --- | --- | --- | --- |
| `test_frameworks` | multiselect | `[pytest]` | Always | `tests/` directory; selecting `pytest` forces `has_python` true even if `contains_python` is answered no. |
| `contains_python` | bool | `true` if pytest selected | Always | Enables the Python stack when you have Python but no test suite (e.g. a Python script repo without pytest). Feeds into `has_python`. |
| `has_python` | computed | `contains_python OR pytest` | Never (hidden) | The single guard everything Python gates on. Ensures pytest's tooling deps are never dropped by a stray `contains_python=no` answer. |
| `python_version` | str | `3.14` | `has_python` | Sets `requires-python` in `pyproject.toml` and ruff's `target-version`. Must be `MAJOR.MINOR` only (e.g. `3.14`). |
| `python_source` | bool | `has_python` | `has_python` | Renders `src/<python_package>/`, sets `[tool.uv] package = true`, adds `[build-system]` (hatchling), and enables the `pytest-cov` coverage gate. |
| `python_package` | str | `project_slug` (dashes → underscores) | `python_source` | The Python import name. Feeds into `src/<python_package>/__init__.py`, hatchling's wheel target, and the pytest coverage flag. |
| `is_package` | bool | `python_source` | `python_source` | Adds distribution metadata (`readme`, `classifiers`) to `pyproject.toml`. The `[build-system]` block is present for all `python_source` shapes; `is_package` just enriches the publishable metadata and gates `publish_to_pypi`. |
| `publish_to_pypi` | bool | `is_package` | `is_package` | Emits `.github/workflows/publish.yml`: fires on each GitHub Release and drives build once → publish to TestPyPI → smoke-install the built wheel → publish to PyPI, each publish stage in its own OIDC Trusted Publishing environment (no long-lived secret). When `false`, the package's `classifiers` instead carry `Private :: Do Not Upload` — PyPI rejects any upload bearing it server-side, so an accidental `uv publish` / `twine upload` of this deliberately-unpublished package fails at the index rather than leaking it. |

### Generated files

| File | Condition | Notes |
| --- | --- | --- |
| `pyproject.toml` | `has_python` | Always present when Python is on. Holds ruff, ty, pytest config; `[build-system]` and `[tool.uv] package = true` when `python_source`; distribution metadata when `is_package`. |
| `.python-version` | `has_python` | Pins the managed Python version for uv; mirrors `python_version`. |
| `src/<python_package>/__init__.py` | `python_source` | Minimal package init. Hatchling's wheel target is `src/<python_package>`. |
| `tests/test_smoke.py` | `pytest` in `test_frameworks` | A placeholder smoke test so pytest is green on arrival. |
| `tests/conftest.py` | `pytest` in `test_frameworks` AND NOT `python_source` | Needed for the pytest-only-no-src shape where there is no installable package. |
| `tests/smoke.bats` | `bats` in `test_frameworks` | Placeholder shell test for the bats suite. |
| `.github/workflows/publish.yml` | `publish_to_pypi` | Fires on `release: published`. Builds once, rehearses on TestPyPI, smoke-installs the wheel, then publishes to PyPI — each stage in its own OIDC Trusted Publishing environment (`testpypi` / `pypi`); one-time environment + Trusted Publisher setup required (see the generated README). Skips on forks via a `fork == false` guard. |

### Hooks & CI steps

| Hook / step | Condition | Where | What it does |
| --- | --- | --- | --- |
| `ruff-check` + `ruff-format` | `has_python` | prek gate | Lint (with `--fix`) and format Python. Ruff config lives in `pyproject.toml [tool.ruff]`, targeting `python_version`. |
| `validate-pyproject` | `has_python` | prek gate | Validates `pyproject.toml` against the full schema store (including ruff, uv, hatchling sections). |
| `ty` | `has_python` | prek gate | Type-checks with `uv run ty check .` (system hook). |
| `uv-lock` | `has_python` | prek gate | Keeps `uv.lock` in sync with `pyproject.toml`. |
| `uv-audit` | `has_python` | prek gate (system) | Scans resolved dependencies against PyPA advisory database. Runs on changes to `pyproject.toml` or `uv.lock`. |
| `osv-scanner` | `has_python` | prek gate (system) + CI install | Cross-checks `uv.lock` against the OSV database. System binary; SHA256-checksum-pinned CI install (`osv-scanner_linux_amd64`). |
| `pytest` with coverage gate | `python_source` + `pytest` in `test_frameworks` | prek gate + CI | Pytest runs with `--cov=<python_package> --cov-fail-under=80` (configured in `[tool.pytest.ini_options] addopts`). The coverage gate only applies to `python_source` shapes — a pytest-only-no-src repo has no package to measure. |

!!! tip "The four canonical Python shapes"
    1. **Installable package** — `python_source=true, is_package=true`: `src/<pkg>`, full
       distribution metadata, optional PyPI publish.

    2. **Installed, unpublished** — `python_source=true, is_package=false`: has
       `[build-system]` so it's importable with `uv`, but no readme/classifiers and no
       publish workflow.

    3. **Tooling / tests only** — `python_source=false, has_python=true`: no `src/`,
       `package = false`, flat `tests/` + `conftest.py`. The dotfiles model.

    4. **No Python** — `has_python=false`: no `pyproject.toml` at all; the version of record
       lives only in `.config/.release-please-manifest.json` and tags.

## Terraform

Gating question: [`include_terraform`](questions.md#include_terraform) bool — default
`false`.

Scaffolds a minimal Terraform workspace with syntax, style, and security checks layered on
top of `fmt`/`validate`.

### Generated files

| File | Purpose |
| --- | --- |
| `terraform/versions.tf` | Terraform version constraint block (no providers declared in the stub). |
| `terraform/variables.tf` | Placeholder variables block. |
| `terraform/outputs.tf` | Placeholder outputs block. |
| `terraform/main.tf` | Main resource block (empty stub). |
| `terraform/README.md` | Module README with SPDX header. |

### Hooks & CI steps

| Hook / step | Where | What it does |
| --- | --- | --- |
| `terraform_fmt` | prek gate | Auto-formats `.tf` files with `terraform fmt` (via `antonbabenko/pre-commit-terraform`). |
| `terraform_validate` | prek gate | Validates the configuration with `terraform validate`. Runs `terraform init -backend=false` automatically — offline while no providers are declared; add a provider and this becomes a network operation. |
| `terraform_tflint` | prek gate | Lints with tflint's bundled rules (offline; `tflint --init` is only needed for cloud plugins, which the stub ships none of). |
| `checkov` | prek gate (pip-backed) | Scans Terraform for IaC misconfigurations (e.g. a public bucket) that fmt/validate miss. Pip-backed — self-bootstraps, no system install. |
| `trivy` (IaC) | prek gate (system) | Second IaC security scan layer via `trivy config --exit-code 1 --skip-check-update terraform`. No `--severity` filter (unlike the Dockerfile hook) — IaC misconfigs are the user's own resources where blocking even MEDIUM is worthwhile. |
| Install trivy (CI) | CI | SHA256-checksum-pinned binary install (`trivy_VERSION_Linux-64bit.tar.gz`). Shared with the Docker module if both are enabled. |
| Set up Terraform (CI) | CI | `hashicorp/setup-terraform` with `terraform_wrapper: false` — the default output wrapper breaks `terraform_validate`'s JSON parsing. |
| Set up tflint (CI) | CI | `terraform-linters/setup-tflint` makes the tflint binary available to the prek gate. |

## Docker

Gating question: [`include_docker`](questions.md#include_docker) bool — default `false`.

A production-ready Dockerfile stub (non-root user, Python-aware) with two lint/security
layers: hadolint catches Dockerfile best-practice violations, trivy catches
misconfigurations, and a CI step builds the real image and scans its layers for CVEs.

### Generated files

| File | Purpose |
| --- | --- |
| `Dockerfile` | Multi-stage build stub. Both the Python (uv) and alpine branches create and drop to a **non-root user** so `trivy config` (DS-0002: running as root) passes out of the box. |
| `.dockerignore` | Excludes `.venv`, `.ty_cache`, `__pycache__`, and other noise from the build context. |
| `compose.yaml` | A minimal Compose file for local development. |

### Hooks & CI steps

| Hook / step | Where | What it does |
| --- | --- | --- |
| `hadolint` | prek gate (pip-backed) | The Dockerfile analog of shellcheck. `hadolint-py` is pip-backed so it self-bootstraps — no Docker or system install required. |
| `trivy-dockerfile` | prek gate (system) | Scans the Dockerfile for misconfigurations: `trivy config --exit-code 1 --skip-check-update --severity HIGH,CRITICAL Dockerfile`. Runs offline (`--skip-check-update` uses bundled checks). LOW/MEDIUM advisories like "add a HEALTHCHECK" are app-specific and filtered out; remove `--severity` to surface them. |
| Install trivy (CI) | CI | SHA256-checksum-pinned binary install. Shared with the Terraform module if both are enabled. |
| Build image + scan for CVEs | CI only | `docker build -t <project_slug>:ci .` then `trivy image --exit-code 1 --ignore-unfixed --severity HIGH,CRITICAL <project_slug>:ci`. Image-layer CVE scanning requires a built image, so it cannot be a local hook. `--ignore-unfixed` skips base-image CVEs with no available fix, keeping the gate actionable. |

## Helm

Gating question: [`include_helm`](questions.md#include_helm) bool — default `false`.

A starter Helm chart with local lint and CI manifest validation. Helm Go-templates are not
valid YAML, so `check-yaml` and `yamllint` automatically exclude `helm/*/templates/` when
this module is on.

### Generated files

| File | Purpose |
| --- | --- |
| `helm/<project_slug>/.helmignore` | Standard Helm ignore patterns. |
| `helm/<project_slug>/Chart.yaml` | Chart metadata (name, version, description). |
| `helm/<project_slug>/values.yaml` | Default chart values. |
| `helm/<project_slug>/templates/_helpers.tpl` | Named template helpers. |
| `helm/<project_slug>/templates/deployment.yaml` | Deployment manifest stub. |
| `helm/<project_slug>/templates/service.yaml` | Service manifest stub. |

### Hooks & CI steps

| Hook / step | Where | What it does |
| --- | --- | --- |
| `helm-lint` | prek gate (system) | `helm lint helm/<project_slug>` — offline, triggers on any change under `helm/`. |
| Set up Helm (CI) | CI | `azure/setup-helm` makes the Helm binary available to both the prek gate and the kubeconform step. |
| Validate rendered manifests | CI only | `helm template helm/<project_slug> \| kubeconform -strict -ignore-missing-schemas -summary`. Validates rendered manifests against upstream Kubernetes schemas (a network fetch, so CI-only). SHA256-checksum-pinned kubeconform binary install. `-ignore-missing-schemas` skips CRDs/Custom Resources that have no upstream schema; `-strict` still rejects unknown fields on built-in kinds. |

## SQL

Gating question: [`include_sql`](questions.md#include_sql) bool — default `false`.

Two follow-up questions are asked when `include_sql` is true:

- **`sql_dialect`** — the sqlfluff dialect (28 choices, default `sqlite`). Rendered into
  `sql/.sqlfluff`, which requires a dialect to function.
- **`sql_use_dbt`** — bool, default `false`. Sets `templater = dbt` in `.sqlfluff` and adds
  `sqlfluff-templater-dbt` to the hooks' `additional_dependencies` (required because the hook
  runs in an isolated pip venv where a system-level dbt install is not visible).

### Generated files

| File | Condition | Purpose |
| --- | --- | --- |
| `sql/.sqlfluff` | `include_sql` | sqlfluff configuration: dialect set from `sql_dialect`; templater set to `dbt` when `sql_use_dbt`. Carries a `#` SPDX header (verified by reuse) but excluded from hawkeye, which does not map that filename. |
| `sql/example.sql` | `include_sql` AND NOT `sql_use_dbt` | A simple annotated example query so sqlfluff is exercised on arrival. Omitted for the dbt shape — sqlfluff has nothing to lint until you add dbt models. |
| `sql/README.md` | `include_sql` | SQL directory README with basic usage notes. |

### Hooks

| Hook | Where | What it does |
| --- | --- | --- |
| `sqlfluff-fix` | prek gate (pip-backed) | Auto-fixes SQL style violations. Pip-backed — self-bootstraps, no system install. With `sql_use_dbt`: `additional_dependencies: ["sqlfluff-templater-dbt"]`. |
| `sqlfluff-lint` | prek gate (pip-backed) | Reports violations that could not be auto-fixed. Mirrors the ruff check+format pattern for SQL: fix first, then lint. With `sql_use_dbt`: `additional_dependencies: ["sqlfluff-templater-dbt"]`. |

!!! note "dbt shape: no example.sql"
    When `sql_use_dbt` is true, `sql/example.sql` is not generated. sqlfluff's dbt templater
    needs a reachable dbt project and models to lint — without them it errors rather than
    passes. The module is green-on-arrival without that file; add your dbt project structure
    and models when you're ready.

## Ansible

Gating question: [`contains_ansible`](questions.md#contains_ansible) bool — default `false`.

Ansible is a first-class cascade — orthogonal to Python and modelled in the same
`contains_ansible` pattern as `contains_python`. Both can coexist in the same repo. A
follow-up question selects the archetype:

- **`ansible_kind`** — str (`collection` | `role` | `playbooks`), asked when
  `contains_ansible` is true. Determines the directory layout, Galaxy metadata files, and
  whether Molecule is included.

!!! note "Deliberately pyproject-free"
    The Ansible toolchain carries no `pyproject.toml`. ansible-lint runs as an official prek
    hook — no venv required. Molecule is invoked in CI via `uvx`-pinned commands. Both are
    Renovate-bumped without a Python lockfile. YAML style is owned by the standalone
    `yamllint` hook; ansible-lint defers its yaml rule to avoid duplication.

### Generated files

| File | Condition | Purpose |
| --- | --- | --- |
| `ansible.cfg` | all kinds | Ansible config (roles path + defaults). Galaxy dependencies install to Ansible's default path, where `ansible-lint`, Molecule, and `ansible-playbook` all resolve them. |
| `requirements.yml` | all kinds | Declares Galaxy collection and role dependencies. Installed by CI before the prek gate runs. |
| `.config/ansible-lint.yml` | all kinds | ansible-lint configuration (production profile). The yaml rule is disabled here — YAML style is owned by the standalone `yamllint` hook. |
| `galaxy.yml` | `collection` | Collection manifest (namespace, name, version, description). release-please bumps this file's `version` field. Publishable to Ansible Galaxy. |
| `meta/runtime.yml` | `collection` | Declares the minimum `requires_ansible` version. |
| `roles/example/` | `collection` | Starter role inside the collection (`tasks/main.yml`, `defaults/main.yml`). |
| `molecule/default/` | `collection`, `role` | Molecule scenario (`molecule.yml`, `converge.yml`, `verify.yml`). Not generated for `playbooks` — Molecule tests roles and collections, not playbooks. |
| `meta/main.yml` | `role` | Galaxy role metadata (`galaxy_info`: author, description, license, platforms). Publishable to Ansible Galaxy. |
| `meta/argument_specs.yml` | `role` | Formal argument spec for the role's entry point — enables `ansible-lint` argument validation. |
| `tasks/main.yml`, `defaults/main.yml`, `handlers/main.yml` | `role` | Standard role directory stubs. |
| `inventory/hosts.yml`, `inventory/group_vars/all.yml` | `playbooks` | Starter inventory and group variables. |
| `playbooks/site.yml` | `playbooks` | Main site playbook stub. The `playbooks` archetype is operational — it is not published to Galaxy and has no Molecule. |

### Hooks & CI steps

| Hook / step | Where | What it does |
| --- | --- | --- |
| `ansible-lint` | prek gate (official hook) | Lints all Ansible content at the `production` profile. The official hook runs in its own environment — no venv or pip extras required. Runs `--syntax-check` internally. Renovate bumps the pinned hook revision. |
| Install Galaxy content (CI) | CI | `ansible-galaxy install -r requirements.yml` (collections and roles) before the prek gate runs, so ansible-lint can resolve the collections and modules referenced in the content. |
| Molecule converge / idempotence / verify | CI — `collection` and `role` only | Runs the `molecule/default/` scenario via `uvx --with molecule-plugins[docker] molecule test` (converge, idempotence, then verify). Pinned via `uvx`; requires the Docker daemon (the CI runner provides it). Not run for the `playbooks` archetype. |
| Publish to Galaxy (`publish-galaxy.yml`) | CI — `collection` and `role` only | Fires on each GitHub Release. Publishes the built artifact to Ansible Galaxy. Requires the `ANSIBLE_GALAXY_API_KEY` repository secret — Galaxy has no OIDC equivalent, so a long-lived API key is unavoidable. |

!!! tip "VS Code integration"
    The `redhat.ansible` extension is added to `.devcontainer/devcontainer.json` when both
    `contains_ansible` and `include_devcontainer` are true. Outside the dev container, install
    it manually to get YAML validation, hover docs, and task autocompletion inside playbooks,
    roles, and collections.

## Dev Container

Gating question: [`include_devcontainer`](questions.md#include_devcontainer) bool — default
`false`.

Governance and DX baseline files (`CODEOWNERS`, `SECURITY.md`, `CONTRIBUTING.md`, pull-request
template, issue forms) are **always on**. The dev container is the one opinionated,
heavier-weight DX piece — it pulls a container image — so it is opt-in.

### Generated files

| File | Purpose |
| --- | --- |
| `.devcontainer/devcontainer.json` | VS Code / GitHub Codespaces dev container definition. Strict JSON (no comments) so `check-json` passes; covered by the existing `**/*.json` REUSE annotation. |

### Behavior by Python shape

| Setting | Python (`has_python`) | Non-Python |
| --- | --- | --- |
| `image` | `mcr.microsoft.com/devcontainers/python:<python_version>` | `mcr.microsoft.com/devcontainers/base:debian` |
| `postCreateCommand` | `pip install uv && uv sync` | — |
| VS Code `python.defaultInterpreterPath` | `.venv/bin/python` | — |
| VS Code extensions | `charliermarsh.ruff`, `tamasfe.even-better-toml` (both shapes) | `charliermarsh.ruff`, `tamasfe.even-better-toml` (both shapes) |

!!! tip "Codespaces support"
    The `devcontainer.json` is compatible with GitHub Codespaces out of the box. Open the
    repo in Codespaces and the Python environment (if applicable) is ready after the
    `postCreateCommand` runs.

## Docs Site

Gating question: [`include_docs_site`](questions.md#include_docs_site) bool — default
`true`.

Unlike every module above, this one is **opt-out**: every repo descended from this template
is meant to eventually carry a docs site, so the default flips the other way round. Set it to
`false` to skip it entirely.

This scaffolds the *mechanism* only — a shared theme (with a fleet-general
`theme.features`/`markdown_extensions`/`plugins` baseline and a custom 404-page mechanism), a
placeholder page, and a deploy workflow. Real navigation and content are authored per repo by
the `/dev-kit:generate-docs` skill, not by Copier.

### Generated files

| File | Purpose |
| --- | --- |
| `mkdocs.yml` | MkDocs Material config: one shared "Terminal Slate" theme (dark by default, light toggle, blue accent), the favicon/logo, `theme.features` and `markdown_extensions` (instant navigation, search enhancements, code-copy, content tabs, admonitions, Material's icon set, shared install-snippet fragments via `pymdownx.snippets`, auto-linked `owner/repo#N` references via `pymdownx.magiclink`, and more — the fleet-general baseline every adopter gets), an explicit `plugins:` list (`search`, per-page "last updated" dates via `git-revision-date-localized`, social-card generation, and `llms.txt` publishing via `llmstxt` — see [repo-management#85](https://github.com/nivintw/repo-management/issues/85) and its #94/#95/#97 sub-tickets), an `extra_css:` entry fixing a Material default that mangles long inline-code identifiers (e.g. `project_name`) mid-word inside narrow table columns, an `edit_uri` for "edit this page on GitHub", an `exclude_docs:` entry for `docs/superpowers/**` and `docs/includes/**` (dev-only specs and shared snippet fragments, neither is site content), and a minimal starter `nav:`. A page that embeds its first [asciinema-player](https://github.com/asciinema/asciinema-player) cast is expected to add its own `extra_javascript` entry at that point — that asset isn't wired unconditionally, since every page would otherwise load it regardless of whether it uses it. |
| `overrides/404.html` | A `theme.custom_dir` override providing the not-found page's *mechanism* — Material renders `404.html` as a static template straight from the theme, so a `docs/404.md` source file would build but its content is silently discarded. The scaffolded copy is a generic placeholder; write real per-repo copy once the site has real pages worth linking back to. |
| `docs/index.md` | Placeholder landing page (title + `project_description`) — replaced with real content by `/dev-kit:generate-docs`. |
| `docs/assets/favicon.svg` | The `>` prompt-glyph mark used as both favicon and header logo, identical across every repo on this theme. |
| `docs/stylesheets/extra.css` | The table-code-nowrap fix `mkdocs.yml`'s `extra_css:` entry wires in — fleet-identical, no per-repo content. |
| `docs/includes/install.md` | A starter fragment for `pymdownx.snippets` (`--8<-- "install.md"`) so install instructions can be shared across pages instead of duplicated — a mechanism placeholder; real content is authored per repo. |
| `.github/workflows/docs.yml` | Thin caller workflow — delegates the actual MkDocs build and GitHub Pages deploy to `nivintw/repo-management`'s reusable workflow, so a `mkdocs`/`mkdocs-material` version bump is one Renovate PR for the whole fleet rather than one per repo. Passes `extra-packages` for the two plugins that aren't part of `mkdocs-material` itself (`mkdocs-git-revision-date-localized-plugin`, `mkdocs-llmstxt`); the reusable workflow already checks out with full git history (needed for accurate per-page dates) and installs the social plugin's native imaging deps. Triggers on `push` to `main` (paths: `docs/**`, `mkdocs.yml`) and `workflow_dispatch` for manual runs. |

!!! note "Also touches `.config/rumdl.toml`"
    The docs design deliberately relies on raw HTML passing through Markdown unmodified
    (castify's `<figure class="cast">` embeds, a per-plugin `<span data-version="...">`
    version-badge convention). With `include_docs_site` on, `rumdl.toml` disables `MD033` (no
    inline HTML) alongside the always-off `MD013`, and adds a `per-file-ignores` entry
    scoping `MD033`/`MD046` to `docs/*.md` (`MD046` misfires on `pymdownx.tabbed`'s
    indentation-based content nesting). A repo without the docs site keeps rumdl's stricter
    default.

!!! tip "Part of a fleet-wide rollout"
    This module is one piece of a larger, staged migration replacing this template's own
    bespoke `docs/*.html` site with MkDocs across every repo descended from it. See
    [repo-management#85](https://github.com/nivintw/repo-management/issues/85) for the full
    architecture and rollout order. The theme/markdown baseline above was itself proven out
    first in a fleet repo and folded back here — see
    [design model](design.md#open-follow-ups).
