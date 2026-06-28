<!--
SPDX-FileCopyrightText: © 2026 Tyler Nivin
SPDX-License-Identifier: MIT
-->

<!-- rumdl-disable-file MD033 MD041 -->

<div align="center">

# 🦴 copier-everything

**_The bones of every project I start — clone the spine, snap on the parts._**

A [Copier](https://copier.readthedocs.io) template that scaffolds a new repo with a
batteries-included quality spine, plus opt-in modules for Python, Terraform, Docker,
and Helm.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

</div>

---

## ⚡ Quick start

```bash
# one-off (uvx) — no install needed
uvx copier copy gh:nivintw/copier-everything path/to/new-project

# or, if you keep copier as a uv tool
copier copy gh:nivintw/copier-everything path/to/new-project
```

Answer the prompts (project name, author, license, and which modules to include) and
Copier renders a ready-to-commit project.

To pull template updates into a project later:

```bash
cd path/to/new-project
copier update
```

---

## 🧱 What you always get (the spine)

The cross-cutting quality infrastructure, lifted from
[`nivintw/dotfiles`](https://github.com/nivintw/dotfiles) and de-personalized:

| Piece | What it gives you |
| --- | --- |
| **prek hooks** (`.pre-commit-config.yaml`) | Git hygiene, secret scanning (gitleaks), spelling (typos), markdown (rumdl), YAML style (yamllint), license headers, shell lint + format (shellcheck, shfmt), and workflow lint + security-audit (actionlint, zizmor) — run identically locally and in CI. |
| **REUSE licensing** (`.config/licenserc.toml`, `REUSE.toml`, `LICENSES/`) | Every file carries an SPDX header; `hawkeye` maintains them, `reuse` verifies. |
| **CI** (`.github/workflows/`) | Each generated repo gets a reusable `ci.yml` gate called by `pr.yml` (every PR) and `main.yml` (push to main → release-please). Every action is SHA-pinned with a version comment. The template itself uses the same shape — a reusable root `ci.yml` called by `pr.yml` and `main.yml` (which also runs release-please) (see `tests/`). |
| **Renovate** (`.github/renovate.json`) | Automates the pins (pre-commit hook revs + action digests) and groups `ruff` bumps so a new lint rule lands as a reviewable PR, not a surprise red. |
| **Security scanning** | Dependency-CVE scanning (`uv audit`, `osv-scanner`), Terraform IaC misconfig (`checkov`, `trivy`), Dockerfile lint + misconfig (`hadolint`, `trivy config`) and image-layer CVEs (`trivy image`, in CI) — wired wherever the matching shape/module is present. |
| **Link checking** (`link-check.yml`) | `lychee` checks the Markdown docs for dead links. A separate CI workflow (not the deterministic gate) since it's a network operation — make `ci` required in branch protection, leave `link-check` advisory. |
| **Conventional Commits + release-please** (`.cz.toml`, `.config/release-please-config.json`) | Plain Conventional Commits enforced at commit-msg time (commitizen, in `.cz.toml`); release-please derives the version + `CHANGELOG.md` from commit history and publishes via an auto-merged Release PR — continuous releases once checks pass (→ `vX.Y.Z` tag + GitHub Release). Language-agnostic — present even with no Python. |
| **Governance files** | `CODEOWNERS`, `SECURITY.md`, `CONTRIBUTING.md`, a PR template, and YAML issue forms — every repo starts with the standard hygiene/DX baseline. |
| **uv + ruff** (Python shapes) | When the project has Python, `pyproject.toml` hosts the ruff/ty/pytest config and a uv-managed dev environment; source shapes get a `pytest-cov` coverage gate (`--cov-fail-under`). A no-Python repo ships no `pyproject.toml`. |
| **`.editorconfig`, `.config/typos.toml`, `.config/rumdl.toml`** | Editor + linter config that agrees with the hooks. |

## 🧩 Shape & modules

The Python/testing shape is set by three decoupled levers, so you can scaffold an
installable package, a pyproject-only-for-pytest repo, a pytest + bats repo (the
`dotfiles` model), or a no-Python repo with no `pyproject.toml` at all:

| Question | Scaffolds |
| --- | --- |
| `test_frameworks` (`pytest`/`bats`) | the `tests/` suites; empty ⇒ no `tests/`. `pytest` implies Python |
| `python_source` | `src/<package>` Python source + src assumptions in `pyproject.toml` |
| `is_package` | `[build-system]` + distribution metadata (installable/publishable) |
| `include_terraform` | `terraform/` with `versions.tf`, `variables.tf`, `outputs.tf`, `main.tf` + `terraform fmt`/`validate`/`tflint` and `checkov`/`trivy` IaC scanning |
| `include_docker` | `Dockerfile` (non-root), `.dockerignore`, `compose.yaml` + `hadolint`/`trivy config` lint and a `trivy image` CVE scan in CI |
| `include_helm` | A starter Helm chart under `helm/<slug>/` + `helm lint` and `kubeconform` manifest validation (CI) |
| `include_sql` | `sql/` with a dialect-aware `.sqlfluff` + `sqlfluff` lint/fix (optional dbt templater) |
| `include_devcontainer` | `.devcontainer/devcontainer.json` for Codespaces / VS Code |

The spine (prek hooks, REUSE licensing, Conventional-Commit linting + release-please
releases, CI) is language-agnostic and ships with every shape. See
[`REVIEW.md`](REVIEW.md) for the model.

---

## 🗂️ Template layout

- **`copier.yml`** — questions, module toggles, post-copy `_tasks`.
- **`template/`** — the rendered project tree (`_subdirectory`). Conditional dirs use
  `{% raw %}{% if <condition> %}...{% endif %}{% endraw %}` in their names; templated
  files end in `.jinja`.
- **`tests/`** — copier-everything's own test suite: `render-matrix.sh` renders every
  `answers/*.yml` shape and runs the full gate. Wired into CI.
- **`REVIEW.md`** — the design model, decisions/assumptions, and open follow-ups.

## 🛠️ Developing this template

This repo dogfoods its own spine. Install the hooks once, then commit via a branch:

```bash
uvx prek install            # wire up the pre-commit + commit-msg hooks
uvx prek run --all-files    # run the gate on demand
```

> **Two system tools:** the `taplo` and `hawkeye` hooks are `language: system`, so install
> both locally before running the gate — those hooks fail without them. `taplo`
> (`brew install taplo` / `cargo install taplo-cli`) and `hawkeye`
> (`brew install korandoru/tap/hawkeye` / [release binary](https://github.com/korandoru/hawkeye/releases)).
> Every other hook self-bootstraps. (CI installs both as their own steps.)

Commits use plain Conventional Commits (no gitmoji — release-please can't parse a leading
emoji). The template repo itself is versioned by `main.yml` (release-please): push to `main`
runs the gate, then maintains a Release PR that auto-merges (rebase) once checks pass, cutting
the `vX.Y.Z` tag consumers pin with `copier copy --vcs-ref` / `copier update`.

## 📄 License

[MIT](LICENSE).
