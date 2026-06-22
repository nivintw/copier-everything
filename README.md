<!--
SPDX-FileCopyrightText: © 2026 Tyler Nivin
SPDX-License-Identifier: MIT
-->

<!-- rumdl-disable-file MD033 MD041 -->

<div align="center">

# 🦴 scaffold

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
uvx copier copy gh:nivintw/scaffold path/to/new-project

# or, if you keep copier as a uv tool
copier copy gh:nivintw/scaffold path/to/new-project
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
| **prek hooks** (`.pre-commit-config.yaml`) | Git hygiene, secret scanning (gitleaks), spelling (typos), markdown (rumdl), license headers, shell lint + format (shellcheck, shfmt), and workflow lint + security-audit (actionlint, zizmor) — run identically locally and in CI. |
| **REUSE licensing** (`licenserc.toml`, `REUSE.toml`, `LICENSES/`) | Every file carries an SPDX header; `hawkeye` maintains them, `reuse` verifies. |
| **CI** (`.github/workflows/`) | Each generated repo gets a reusable `ci.yml` gate called by `pr.yml` (every PR) and `main.yml` (push to main → automated, signed commitizen release). Every action is SHA-pinned with a version comment. The template itself is tested by its own root `.github/workflows/ci.yml` (see `tests/`). |
| **Renovate** (`.github/renovate.json`) | Automates the pins (pre-commit hook revs + action digests) and groups `ruff` bumps so a new lint rule lands as a reviewable PR, not a surprise red. |
| **Security scanning** | Dependency-CVE scanning (`uv audit`, `osv-scanner`), Terraform IaC misconfig (`checkov`, `trivy`), and Dockerfile lint (`hadolint`) — wired as gate hooks wherever the matching shape/module is present. |
| **commitizen + gitmoji** (`.cz.toml`) | Conventional commits enforced at commit-msg time; version + `CHANGELOG.md` computed from history. Language-agnostic — lives in `.cz.toml`, present even with no Python. |
| **uv + ruff** (Python shapes) | When the project has Python, `pyproject.toml` hosts the ruff/ty/pytest config and a uv-managed dev environment; source shapes get a `pytest-cov` coverage gate (`--cov-fail-under`). A no-Python repo ships no `pyproject.toml`. |
| **`.editorconfig`, `_typos.toml`, `.rumdl.toml`** | Editor + linter config that agrees with the hooks. |

## 🧩 Shape & modules

The Python/testing shape is set by three decoupled levers, so you can scaffold an
installable package, a pyproject-only-for-pytest repo, a pytest + bats repo (the
`dotfiles` model), or a no-Python repo with no `pyproject.toml` at all:

| Question | Scaffolds |
| --- | --- |
| `test_frameworks` (`pytest`/`bats`) | the `tests/` suites; empty ⇒ no `tests/`. `pytest` implies Python |
| `python_source` | `src/<package>` Python source + src assumptions in `pyproject.toml` |
| `is_package` | `[build-system]` + distribution metadata (installable/publishable) |
| `include_terraform` | `terraform/` with `versions.tf`, `variables.tf`, `outputs.tf`, `main.tf` + `checkov`/`trivy` IaC scanning |
| `include_docker` | `Dockerfile`, `.dockerignore`, `compose.yaml` + `hadolint` lint |
| `include_helm` | A starter Helm chart under `helm/<slug>/` |

The spine (prek hooks, REUSE licensing, `.cz.toml` commitizen release, CI) is
language-agnostic and ships with every shape. See [`REVIEW.md`](REVIEW.md) for the model.

---

## 🗂️ Template layout

- **`copier.yml`** — questions, module toggles, post-copy `_tasks`.
- **`template/`** — the rendered project tree (`_subdirectory`). Conditional dirs use
  `{% raw %}{% if <condition> %}...{% endif %}{% endraw %}` in their names; templated
  files end in `.jinja`.
- **`tests/`** — the scaffold's own test suite: `render-matrix.sh` renders every
  `answers/*.yml` shape and runs the full gate. Wired into CI.
- **`REVIEW.md`** — the design model, decisions/assumptions, and open follow-ups.

## 📄 License

[MIT](LICENSE).
