<!--
SPDX-FileCopyrightText: © 2026 Tyler Nivin
SPDX-License-Identifier: MIT
-->

# Design model

The "why it's built this way" record — the architectural model, the key decisions, the
trade-offs, and what's still open.

## The core model

Two ideas do all the work. A **language-agnostic baseline** that every generated project
gets regardless of language, and a set of **decoupled opt-in levers** you turn on only when
you need them. A shell-only dotfiles repo and a published Python package come off the same
template without carrying each other's configuration baggage.

Every cross-cutting tool keeps its own native config file — `.cz.toml`, `.config/typos.toml`,
`.config/rumdl.toml`, `.editorconfig`, `.config/licenserc.toml`, `REUSE.toml` — identical
across Python, Rust, and shell repos. Language-specific tooling only appears when the
relevant lever is turned on.

See the [quality baseline reference](baseline.md) for everything every project gets, and
[modules & levers](modules.md) for the opt-in additions.

### The Python levers

The original design collapsed three independent choices into a single `include_python`
boolean — is-a-package, has-pytest, and src-layout were all conflated. They are now separate
questions with a clear dependency chain:

| Question | Type | Drives |
| --- | --- | --- |
| `test_frameworks` | multiselect (`pytest` / `bats`) | Which `tests/` suites exist; empty selection → no `tests/` directory |
| `contains_python` | bool (auto-true if pytest selected) | ruff/ty, Python pre-commit hooks, Python `.gitignore` |
| `python_source` | bool (only asked when Python is present) | The `src/<pkg>` package and src-layout assumptions in `pyproject.toml` |
| `is_package` | bool (only asked when `python_source`) | `[build-system]` distribution metadata — installable and publishable |

`has_python` is a **hidden computed flag** (`contains_python or pytest`). Everything
Python-specific gates on it. `pyproject.toml` is emitted only when `has_python` is true, and
it holds only Python-specific config: ruff, ty, pytest, `[build-system]`, `[project]`,
`[tool.uv]`. For a no-Python project, `pyproject.toml` does not exist at all — the version of
record lives only in `.config/.release-please-manifest.json` and tags.

See the [template questions reference](questions.md) for the full question list and what
each drives.

### The Ansible levers

The Ansible module is a first-class cascade orthogonal to Python — both can coexist. A repo
can be an Ansible collection that also has Python tests, or a pure Ansible playbook repo with
no Python at all. The lever chain mirrors Python's exactly:

| Question | Type | Drives |
| --- | --- | --- |
| `contains_ansible` | bool | ansible-lint pre-commit hook, `yamllint` as the single YAML owner, Ansible `.gitignore` additions |
| `ansible_kind` | choice (`collection` / `role` / `playbooks`) | Only asked when Ansible is present; determines the repo archetype and directory layout |
| `ansible_namespace` / `ansible_name` | str (only asked when `ansible_role_based`) | The Galaxy FQCN (`namespace.name`) used in `galaxy.yml` and CI publish targets |
| `publish_to_galaxy` | bool (only asked when `ansible_role_based`) | Adds a Galaxy publish job to CI; requires an `ANSIBLE_GALAXY_API_KEY` secret (Galaxy has no OIDC trusted publishing, unlike PyPI) |

`has_ansible` is a **hidden computed flag** (`contains_ansible`). Everything Ansible-specific
gates on it. `ansible_role_based` is a second hidden computed flag, true when `ansible_kind`
is `collection` or `role` — it gates the namespace, name, and Galaxy publish questions
exactly as `is_package` gates Python's distribution metadata. A playbooks repo triggers
neither flag and gets no Galaxy plumbing.

Deliberately, an Ansible-only repo gets **no `pyproject.toml`** — not even a stub. Linting is
the official `ansible-lint` pre-commit hook (no venv required). Molecule (collection/role
testing) and Galaxy publish run via `uvx`-pinned tools in CI. `yamllint` becomes the single
YAML owner (replacing any Python-centric YAML linting). This is a deliberate contrast with
the Python path, which is uv/pyproject-centric.

## The four canonical Python shapes

All four shapes are CI-verified by `tests/render-matrix.sh` against committed answer sets in
`tests/answers/`. The matrix also covers edge cases: the unpublished-package variant, the
Apache-license path, and a full terraform+docker+helm build. These are the Python/testing
shapes specifically — for the full set of CI-verified fixtures across every module (Ansible,
Terraform, Docker, Helm, SQL, and combinations), see
[canonical project shapes](usage.md#canonical-project-shapes) in the usage guide.

<div class="grid cards" markdown>

-   **Shape 1: Installable package**

    ---

    `python_source=true, is_package=true` — `src/<pkg>` layout, `[build-system]`, wheel. Full
    distribution metadata including readme and classifiers.

-   **Shape 2: pyproject-only-for-pytest**

    ---

    `python_source=false` with pytest — no `src/`, `package=false`, flat `tests/` +
    `conftest.py`. Python tooling without a source package.

-   **Shape 3: pytest + bats (dotfiles model)**

    ---

    `python_source=false` with both pytest and bats selected. Python test tooling alongside
    shell test tooling; the project itself is not a Python package.

-   **Shape 4: No Python**

    ---

    `contains_python=false` — no `pyproject.toml` at all. Version lives in
    `.release-please-manifest.json` and tags only.

</div>

!!! note "Shape 1 variant: installed but unpublished"
    `python_source=true, is_package=false` is a valid combination meaning "installed but
    unpublished" — the `uv --package` style. It always has `[build-system]` and `package=true`
    so it is importable as a development install. The `is_package` lever only toggles
    distribution metadata (readme, classifiers, publish config). This was an autonomous
    assumption confirmed with the project owner.

## The three Ansible archetypes

When `contains_ansible` is true, `ansible_kind` selects one of three archetypes. All three
receive the language-agnostic baseline; only the Ansible-specific scaffolding differs.

<div class="grid cards" markdown>

-   **Archetype 1: Collection**

    ---

    `ansible_kind=collection` — standard `galaxy.yml`, `plugins/`, `roles/`, and Molecule.
    `ansible_role_based=true` so namespace, name, and optional Galaxy publish are enabled.

-   **Archetype 2: Role**

    ---

    `ansible_kind=role` — single-role layout with `meta/main.yml` and Molecule. Also
    `ansible_role_based=true`; Galaxy publish targets the role directly.

-   **Archetype 3: Playbooks**

    ---

    `ansible_kind=playbooks` — operational repo: `site.yml`, `inventory/`, `group_vars/`.
    `ansible_role_based=false`; no namespace, no Galaxy publish, no Molecule.

</div>

## release-please and commitizen

The versioning design deliberately splits responsibilities between two tools that each do
one thing well.

**release-please owns versioning.** It watches `main` for Conventional Commit messages,
maintains an open Release PR that accumulates the version bump and `CHANGELOG.md` entries,
and auto-merges that PR (`--auto --rebase`) once its required checks pass — enabling
continuous releases. On merge it cuts the `vX.Y.Z` tag and GitHub Release. Configuration
lives in `.config/release-please-config.json` (`release-type: simple`) and
`.config/.release-please-manifest.json`. For Python shapes, an `extra-files` TOML updater
mirrors the version into `pyproject.toml [project].version` — what a wheel build reads.

**Single or multi-package.** The default `release_model: single` declares one package at the
repo root — the `.` shape above. `release_model: multi-package` (with `release_packages`, a
comma-separated list of repo-relative paths) instead declares each path as an
independently-versioned release-please package, bootstrapped at `0.0.0`; `separate-pull-requests`
is set so each gets its own Release PR. This adds only the config side — the auto-merge/reconcile
flow in `main.yml` was already N-package generic. Per-package `extra-files` version-sync is
layout-specific and left for the consumer to wire. See
[template questions](questions.md#release-model).

**commitizen is the commit-message linter only.** It enforces Conventional Commit format
locally via a pre-commit hook (`.cz.toml`, `cz_conventional_commits`) — plain Conventional
Commits, no gitmoji. release-please cannot parse a leading emoji, so gitmoji is incompatible
with the automation. commitizen does not touch tags, versions, or changelogs; that is
release-please's job exclusively.

**Authentication uses a GitHub App.** The release job authenticates as a release GitHub App
(`CI_CLIENT_ID` + `CI_APP_PRIVATE_KEY`). A commit made by an App token is GitHub-verified,
replacing the old GraphQL signed-commit workaround. Until a generated repo has its release
App configured, the release job skips cleanly — the rest of CI is unaffected.

## Key decisions & assumptions

Several design decisions were made autonomously during development and later confirmed. They
are documented here so the reasoning is explicit and not rediscovered.

| Decision | Rationale |
| --- | --- |
| `is_package` and `python_source` defaults track their parent lever | A skipped Copier question still resolves its default. A literal `true` default would have leaked `src/` into no-Python repos. Defaults of `{{ python_source }}` and `{{ has_python }}` mean the default is always the safe no-op value. |
| `_tasks` ordering: initial commit before prek install | Auto-tasks run `git init → uv sync → git add → initial commit → prek install --trust`. The commit comes *before* `prek install` deliberately — the `no-commit-to-branch` hook would otherwise block the very first commit to `main`. |
| Author identity comes from answered questions | The initial commit uses the answered `author_name` / `author_email` values so the task works without a global `git config` — important for CI and fresh environments where no global identity is set. |
| `check-hooks-apply` is dropped | A freshly-scaffolded repo legitimately has hygiene hooks (e.g. `check-json`) that match zero files. That meta-hook fails on this condition. Dropping it keeps the gate green on arrival. |
| Branch protection is lighter than the dotfiles model | The full dotfiles branch rulesets assume a release GitHub App and bypass actors that don't exist on a fresh repo. Those rulesets would block automated merges for any generated repo without the App. Generated repo protection just requires the `ci` check and a PR. Production rulesets are a post-setup step once the App is configured. |
| `ansible_kind` and `publish_to_galaxy` defaults track their parent lever | Mirrors the Python `is_package`/`python_source` pattern. A skipped Copier question still resolves its default. Defaults collapse cleanly for non-Ansible repos so no Ansible scaffolding leaks into unrelated projects. |
| Ansible toolchain is deliberately pyproject-free | An Ansible-only repo has no `pyproject.toml`, `uv.lock`, or `.venv`. `ansible-lint` runs as the official pre-commit hook (no venv). Molecule and Galaxy publish use `uvx`-pinned tools in CI. This keeps the Python and Ansible tool-chains cleanly separated — a repo that is both gets both, not a merged hybrid. `yamllint` becomes the single YAML owner regardless of whether Python is also present. |
| Galaxy publish requires `ANSIBLE_GALAXY_API_KEY` | Ansible Galaxy has no OIDC trusted publishing equivalent (unlike PyPI's trusted publishers). An API key secret is the only supported authentication path. Generated repos must add the secret manually before the publish job can succeed — analogous to PyPI's legacy API-token path, not its OIDC path. |

## Local gate vs CI

A single principle governs where each check lives: **the local gate is deterministic and
offline; network-dependent and heavy checks go to CI.** This already governed zizmor
(offline AST audits locally; online checks requiring a GitHub token in CI). Applied
consistently across all modules:

| Check | Where | Why |
| --- | --- | --- |
| yamllint, terraform fmt/validate/tflint, helm lint, trivy config (Dockerfile misconfig) | Local gate | Run fully offline with the right flags; instant feedback without network |
| zizmor AST audits (template-injection, permissions, artipacked, blanket App token) | Local gate (`--offline`) | AST-only audits need no network; token-required audits run online in CI |
| trivy image (container layer CVE scan) | CI only | Requires a built image — `docker build` then `trivy image`; not a local-hook candidate |
| kubeconform (Helm manifest schema validation) | CI only | Validates rendered manifests against upstream Kubernetes schemas — a network fetch not worth vendoring |
| lychee (dead-link checking) | CI only — own `link-check.yml` workflow | Inherently network-flaky; kept advisory, separate from the required `ci` gate |

!!! warning "CVE scans are time-varying and network-dependent"
    A newly-published advisory in a (dev-only) dependency can turn a green gate red with no
    code change — that is inherent to CVE scanning. The flip side: `uv audit` / `osv-scanner`
    hit remote advisory APIs and `trivy config` pulls its check bundle from a registry, so a
    registry or API outage also fails the gate with zero advisory changes. copier-everything
    has no runtime dependencies, so only dev-tool deps are audited.

    Also note: `uv audit` is an experimental command as of uv 0.11.x. An experimental CLI
    surface is the most likely thing to rename or remove a flag and break a hook — watch uv
    release notes when the `audit` command stabilizes.

## Supply-chain hardening

Two layers of supply-chain hardening address different attack surfaces.

### SHA-pinned Actions

Every third-party GitHub Actions `uses:` is pinned to a full commit-SHA digest with a
`# vX.Y.Z` comment so the version stays human-readable. Renovate maintains the digests via
the native `github-actions` manager. Inside `template/**/*.jinja` files the same pinning
pattern is used, but Renovate's native managers don't parse `.jinja` — a `customManagers`
regex entry covers those separately.

### Checksum-verified CI binaries

Five release binaries CI installs by hand — trivy, osv-scanner, hawkeye, taplo, and
kubeconform — were previously pinned by version but fetched over streaming pipes
(`curl | tar`) with no integrity check. A tampered or MITM'd asset would have executed in CI
with no detection.

Each is now verified against a committed SHA256 that fails the step closed on mismatch. The
download pattern changed to download-to-file, `sha256sum -c`, then extract — a bad byte never
reaches `tar` or the executable. Every step runs `set -euo pipefail`. They normalize to a
`# renovate:`-annotated `*_VERSION` + adjacent `*_SHA256` env-var pair, covered by a single
`customManager`. A sixth SHA256-verified binary, **gitleaks**, later joined the set for the
full-history secret-scan CI job. A seventh tool, **bats**, publishes no downloadable asset to
hash, so it's pinned instead by the git commit its release tag points at (`BATS_VERSION` +
adjacent `BATS_COMMIT`, a `*_COMMIT` pin) — closing the previous unpinned, mutable
`apt-get install bats` gap; CI verifies the pinned commit really is `v${BATS_VERSION}`'s tag
before installing.

### Keeping hashes fresh

Renovate's `github-releases` datasource has no concept of asset digests, so it can bump
`*_VERSION` but cannot update `*_SHA256`. A version bump with a stale hash would fail CI on
the mismatch. `scripts/refresh-binary-checksums.sh` recomputes each SHA from its pinned
version — reading the upstream checksum file for trivy, osv-scanner, hawkeye, kubeconform, and
gitleaks; hashing the asset directly for taplo, which publishes no checksum file; and resolving
the tag's commit id for the asset-less `*_COMMIT` pin (bats). Renovate
runs the script as a `postUpgradeTask` (`executionMode: branch`), so the refreshed hash folds
into Renovate's **own** commit — no separate bot pushing onto the Renovate branch, which is
exactly what previously caused the self-re-trigger and `branchIsModified` rebase-halt
problems the earlier dedicated workflow ran into. The central self-hosted runner executes the
task and must authorize the script in its `allowedCommands`; without that the hash stays
stale and the fail-closed mismatch stands — re-pin by hand with the script.

A second gate catches a different failure mode: a swapped asset on an already-published,
unchanged version (the release stays at the same tag but its uploaded binary changes
underneath it). The `postUpgradeTask` command sets `BASE_REF` to the branch's merge-base with
the default branch, and the script refuses to re-pin a SHA whose adjacent `*_VERSION` is
unchanged versus that ref — it exits with a `TAMPER ALERT` instead of silently accepting the
new hash. Run without `BASE_REF` (a human re-pinning locally after a deliberate bump), the
gate is off by design, since there's no reliable base to diff against outside the automated
branch structure.

!!! warning "taplo's pin is weaker — by necessity"
    The other four binaries read an upstream-published checksum file, providing an
    independent attestation at pin time. taplo publishes no checksum file, so the script
    hashes whatever it downloads — trust-on-first-use. It still detects tampering *after* the
    pin is set (every CI run re-verifies), but it cannot give an independent guarantee at the
    moment of pinning. There is no fix until taplo ships checksums upstream. The asymmetry is
    explicit here so it is not silent.

## Open follow-ups

!!! note "Not blocking — recorded for honesty"
    The template is production-usable today. The following are known gaps and future work
    from the design record.

- **Rust module.** The lever architecture supports a Rust module but it is unbuilt.
- **Terraform, Docker, and Helm are minimal stubs.** All three modules are gate-clean and
  CI-covered, but they remain thin starting points — a single example resource, a generic
  image, a bare Deployment/Service. Flesh them out per project needs.
- **CI-only checks have a first-run coverage gap.** `render-matrix.sh` does not exercise
  lychee, `trivy image`, or kubeconform — they need a Docker daemon or network access. Their
  first real run happens when a generated repo's CI runs.
- **The docs-site module keeps evolving.** `include_docs_site` scaffolds the MkDocs Material
  *mechanism* only — theme, `plugins`, `markdown_extensions`, and the Pages build workflow. Fleet
  repos that go further (a homepage card grid, content tabs, a custom 404 page) prove
  improvements out locally first; the genuinely fleet-general ones get folded back into this
  template's baseline (see [modules & levers](modules.md#docs-site)) rather than staying a
  silent per-repo divergence.
