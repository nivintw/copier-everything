<!--
SPDX-FileCopyrightText: © 2026 Tyler Nivin
SPDX-License-Identifier: MIT
-->

# Scaffold — first-pass review notes

This is the initial extraction of the "spine" from `nivintw/dotfiles` into a Copier
template. It's meant to be reviewed and iterated on, not treated as final.

## What was ported (the spine, de-personalized)

- **prek hooks** (`.pre-commit-config.yaml`) — git hygiene, gitleaks, typos, rumdl,
  hawkeye/REUSE, commitizen+gitmoji, taplo. Python hooks (ruff, validate-pyproject,
  ty) are gated behind `include_python`. Dropped: fish, ssh-config guard.
- **REUSE licensing** — `licenserc.toml`, `REUSE.toml`, `LICENSES/`, templated
  `LICENSE`. Header text is driven by `year` / `author_name` / `license` answers.
- **CI** — reusable `ci.yml` gate; `pr.yml` (PRs) and `main.yml` (push→release).
  Dropped the dotfiles-only steps (fish/bats/playwright/ripgrep). Terraform/helm
  lint steps are gated behind their toggles.
- **commitizen release** — `pyproject.toml` `[tool.commitizen]` + the signed,
  App-authenticated release in `main.yml`.
- **Config** — `.editorconfig`, `_typos.toml`, `.rumdl.toml`, `markdown-header.toml`,
  `.gitignore` (with conditional per-module sections), `.envrc`.

## What was dropped (dotfiles-specific)

`home/`, `Brewfile`/`Brewfile.d/`, `install.sh`, `macos.sh`, `dock.sh`, `iterm2/`,
`software_list.md`, `claude_mcp.json`, the fish/ssh/bats/docs-site tests, the
asciinema docs site, and all caches (`.venv`, `.pytest_cache`, `.ruff_cache`).

## Decisions to confirm

1. **Module set**: python, terraform, docker, helm. Add docs (mkdocs)? Devcontainer?
2. **Python version**: defaulted to `>=3.13` (dotfiles uses 3.14). Bump if you want.
3. **Release machinery**: `main.yml` keeps the full signed-commit-via-App release.
   Every generated repo would need a release App + `CI_APP_ID`/`CI_APP_PRIVATE_KEY`
   secrets + ruleset bypass. Options: keep as-is, simplify to `cz bump && git push`
   with a PAT, or make the release stage another opt-in toggle.
4. **hawkeye/taplo** run as system binaries in the hooks (need local installs). They
   self-fetch in CI. Confirm you want them required by default.
5. **Helm + REUSE**: the Go-templated chart files carry `#` SPDX headers; verify
   `reuse lint` passes for a helm-enabled render, or annotate them in `REUSE.toml`.

## Known stubs (intentionally minimal — flesh out per project)

- Terraform: empty `required_providers`, a single example var/output.
- Docker: a reasonable uv-based Python image; generic Alpine otherwise.
- Helm: a minimal Deployment + Service + helpers.
- Python: `src/` layout with a smoke test.

## Bootstrapping this repo on GitHub

`scripts/bootstrap-github.sh` creates the public `nivintw/scaffold` repo and copies
the branch rulesets live from `nivintw/dotfiles` using your local `gh` auth. Review
it, then run it. It's a one-time helper — delete it afterward if you like.
