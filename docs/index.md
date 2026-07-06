<!--
SPDX-FileCopyrightText: © 2026 Tyler Nivin
SPDX-License-Identifier: MIT
-->

# copier-everything

A [Copier](https://copier.readthedocs.io/) template that scaffolds *any* project — Python or
not — with a strong, language-agnostic quality baseline and decoupled, opt-in modules.
Generate once, then pull template improvements forever with `copier update`.

[Quick start](#quick-start){ .md-button .md-button--primary }
[Template reference](questions.md){ .md-button }
[Why it's built this way](design.md){ .md-button }

## Quick start

You need [uv](https://docs.astral.sh/uv/) (which provides `uvx`). No global install of Copier
is required.

Generate a new project:

```bash
uvx copier copy --trust gh:nivintw/copier-everything path/to/new-project
```

Copier asks the [template questions](questions.md), renders the project, and — because
`--trust` lets the post-copy tasks run (and unless you opt out) — initializes a git repo,
runs `uv sync`, makes the first commit, and installs the prek hooks. Omit `--trust` and
Copier just prints those steps for you to run by hand.

Later, pull template improvements into that project:

```bash
cd path/to/new-project
uvx copier update
```

!!! tip "Adopting an existing repo?"
    Answer **no** to *"initialize a fresh git repo"* and follow the
    [adoption guide](usage.md#adopting-into-an-existing-repo) — copier-everything can layer
    its baseline onto a repo you already have.

## The model in one minute

Two ideas do all the work. A **language-agnostic baseline** every project gets, and a set of
**decoupled levers** you turn on only when you need them — so a shell-only dotfiles repo and
a published Python package come off the same template without carrying each other's baggage.

<div class="grid cards" markdown>

-   :material-shield-check-outline:{ .lg .middle } **The quality baseline**

    ---

    Always on. prek hooks, REUSE licensing, Conventional Commits + release-please, hardened
    CI, Renovate, and secret/vulnerability scanning — regardless of language.

    [:octicons-arrow-right-24: Quality baseline](baseline.md)

-   :material-format-list-checks:{ .lg .middle } **Template questions**

    ---

    Reference. Every `copier.yml` question: what it asks, its type and default, and exactly
    what it drives in the generated project.

    [:octicons-arrow-right-24: Template questions](questions.md)

-   :material-puzzle-outline:{ .lg .middle } **Modules & levers**

    ---

    Opt-in. Python (source / package / publish), Ansible (collection / role / playbooks),
    Terraform, Docker, Helm, SQL (+ dbt), and a dev container — each gated behind one question.

    [:octicons-arrow-right-24: Modules & levers](modules.md)

-   :material-rocket-launch-outline:{ .lg .middle } **Usage & adoption**

    ---

    Guide. The `copier copy` / `copier update` flow, the canonical project shapes, and how to
    adopt the template into an existing repo.

    [:octicons-arrow-right-24: Usage & adoption](usage.md)

-   :material-lightbulb-on-outline:{ .lg .middle } **Design model**

    ---

    Rationale. The levers model, the canonical shapes, and the decisions and trade-offs
    behind the template — surfaced from the project's design record.

    [:octicons-arrow-right-24: Design model](design.md)

-   :octicons-mark-github-16:{ .lg .middle } **GitHub**

    ---

    Source. Issues, releases, and the template source. Pin a release with
    `copier copy --vcs-ref vX.Y.Z`.

    [:octicons-arrow-right-24: nivintw/copier-everything](https://github.com/nivintw/copier-everything)

</div>

## What every project gets

| Area | What you get |
| --- | --- |
| Quality gate | A `prek` (pre-commit) hook set — formatting, linting, git hygiene, shell/YAML/TOML checks — that runs identically locally and in CI. |
| Licensing | [REUSE](https://reuse.software/)-compliant SPDX headers, enforced by `hawkeye` + `reuse lint`. |
| Releases | Conventional Commits enforced by commitizen; automated versioning, changelog, and tags via `release-please`. |
| CI | A reusable, hardened GitHub Actions gate; SHA-pinned and checksum-verified third-party binaries. |
| Dependencies | Renovate keeps actions, hooks, and pinned binaries current. |
| Security | gitleaks (secrets), zizmor (workflow audit), plus osv-scanner / trivy when the relevant modules are on. |

See the [quality baseline reference](baseline.md) for the full picture.
