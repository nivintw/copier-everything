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
| **prek hooks** (`.pre-commit-config.yaml`) | Git hygiene, secret scanning (gitleaks), spelling (typos), markdown (rumdl), license headers — run identically locally and in CI. |
| **REUSE licensing** (`licenserc.toml`, `REUSE.toml`, `LICENSES/`) | Every file carries an SPDX header; `hawkeye` maintains them, `reuse` verifies. |
| **CI** (`.github/workflows/`) | A reusable `ci.yml` gate called by `pr.yml` (every PR) and `main.yml` (push to main → automated, signed commitizen release). |
| **commitizen + gitmoji** | Conventional commits enforced at commit-msg time; version + `CHANGELOG.md` computed from history. |
| **uv + ruff** | `pyproject.toml` hosts the shared tooling config and a managed dev environment, package or not. |
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
| `include_terraform` | `terraform/` with `versions.tf`, `variables.tf`, `outputs.tf`, `main.tf` |
| `include_docker` | `Dockerfile`, `.dockerignore`, `compose.yaml` |
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
