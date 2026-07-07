<!--
SPDX-FileCopyrightText: © 2026 Tyler Nivin
SPDX-License-Identifier: MIT
-->

# Template questions

Full reference for every question in `copier.yml` — type, default, when it appears, any
validator, and what the answer drives in the generated project. Expand a row for the full
detail.

Questions are grouped into sections matching the sections in `copier.yml`, followed by
a short note on the Copier meta-settings that govern post-copy automation. For the broader
copy/update flow see [Usage & adoption](usage.md); for what each module actually scaffolds see
[Modules & levers](modules.md).

## Project identity

These eleven questions appear on every `copier copy` run regardless of which modules are
enabled. Together they establish the project's name, ownership, and licensing — every
generated file derives from them: SPDX headers, `README.md`, `pyproject.toml`,
`SECURITY.md`, `CODEOWNERS`, and CI configuration.

| Question | Type | Default | Purpose |
| --- | --- | --- | --- |
| `project_name` | str | *required* | Human-readable name used in docs and metadata |
| `project_slug` | str | `{{ project_name \| lower \| replace(' ', '-') \| replace('_', '-') }}` | Machine name for dirs, package, and repo |
| `project_description` | str | *empty string* | One-line tagline in README and pyproject.toml |
| `author_name` | str | `Your Name` | SPDX copyright holder; git identity for scaffold commit |
| `author_email` | str | `you@example.com` | SPDX copyright email; git identity for scaffold commit |
| `repo_owner` | str | `your-github-username` | GitHub user/org login for CODEOWNERS and repo URLs |
| `repo_name` | str | `{{ project_slug }}` | GitHub repo slug for all `github.com/owner/...` URLs |
| `year` | int | `2026` | Inception year in SPDX `FileCopyrightText` lines |
| `license` | str | `MIT` | SPDX license identifier; selects which `LICENSES/` file is kept |
| `markdown_has_frontmatter` | bool | `false` | Routes Markdown licensing through `REUSE.toml` to protect frontmatter |
| `initialize_repository` | bool | `true` | Gates git init + scaffold commit tasks; set false when adopting |

??? note "`project_name` — str. Human-readable project name (e.g. \"My Service\")"
    - default: none — required; placeholder shown: "My Project"
    - Help: Human-readable project name (e.g. "My Service")
    - Drives: Used verbatim in `README.md` and `pyproject.toml` metadata. Also seeds the
      default value of `project_slug` (lowercased, spaces and underscores replaced with
      dashes). Appears in the post-copy summary message.

??? note "`project_slug` — str. Machine name — used for dirs, package, and repo"
    - default: `{{ project_name | lower | replace(' ', '-') | replace('_', '-') }}`
    - validator: Must be lowercase; spaces and underscores are not permitted — use dashes. An
      empty value is also rejected.
    - Help: Machine name — used for dirs, package, and repo
    - Drives: The project directory name, the default `repo_name`, and the default Python
      import package name (`project_slug | replace('-', '_')`). All `github.com/<owner>/...`
      links and `pyproject.toml` metadata derive from this value.

    !!! note "Decoupled from repo_name on purpose"
        `project_slug` is the distribution/package name; `repo_name` is the GitHub
        repository name. They default to the same value but can differ — for example a
        package distributed as `digital-ocean-dynamic-dns` living at repo `ddns` — so that
        `copier update` never re-breaks hand-patched URLs.

??? note "`project_description` — str. One-line description of the project"
    - default: empty string
    - Help: One-line description of the project
    - Drives: README tagline and the `description` field in `pyproject.toml`.

??? note "`author_name` — str. Copyright holder / author name (SPDX headers)"
    - default: `Your Name`
    - validator: Cannot be empty — required for both SPDX headers and the git author identity
      used in the scaffold commit.
    - Help: Copyright holder / author name (SPDX headers)
    - Drives: The `SPDX-FileCopyrightText` line in every generated file, and the
      `-c user.name=...` flag passed to the scaffold `git commit` task so the first commit
      carries the correct author identity even without a global git config. Names containing
      backslashes or double-quotes are escaped automatically by the task command.

    !!! tip "Skip re-typing this every time"
        `author_name`/`author_email`/`repo_owner` all default to generic placeholders — the
        template intentionally doesn't hardcode any one person's identity. To have them
        pre-filled with your own info on every render, set copier's own user-level
        `defaults:` in its settings file — `~/Library/Application Support/copier/settings.yml`
        on macOS, `~/.config/copier/settings.yml` on Linux (or `$COPIER_SETTINGS_PATH`):

        ```yaml
        defaults:
          author_name: Jane Doe
          author_email: jane@example.com
          repo_owner: janedoe
        ```

        Copier checks this file before falling back to the template's own default, so it
        applies across every template you run, not just this one.

??? note "`author_email` — str. Author email"
    - default: `you@example.com`
    - validator: Cannot be empty.
    - Help: Author email
    - Drives: SPDX copyright contact in generated files and the `-c user.email=...` flag for
      the scaffold `git commit` task.

??? note "`repo_owner` — str. GitHub owner (user/org login) — for CODEOWNERS and repo links"
    - default: `your-github-username`
    - validator: Cannot be empty.
    - Help: GitHub owner (user/org login) — for CODEOWNERS and the repo links in
      SECURITY/CONTRIBUTING
    - Drives: The `CODEOWNERS` file, repository URLs in `SECURITY.md` and `CONTRIBUTING.md`,
      and any other generated file that links to `github.com/<repo_owner>/<repo_name>`.

??? note "`repo_name` — str. GitHub repository name — defaults to project_slug"
    - default: `{{ project_slug }}`
    - validator: Cannot be empty.
    - Help: GitHub repository name — for the repo URLs in SECURITY/link-check (defaults to
      project_slug)
    - Drives: All `github.com/<repo_owner>/<repo_name>` URLs in generated files:
      `SECURITY.md`, link-check configuration, and related CI references. Decoupled from
      `project_slug` so a project whose PyPI distribution name differs from its GitHub repo
      name gets correct links that `copier update` will never re-break.

??? note "`year` — int. Inception year (SPDX headers)"
    - default: `2026`
    - Help: Inception year (SPDX headers)
    - Drives: The year in `SPDX-FileCopyrightText: (c) YEAR Author` lines across every
      generated file. Update this when generating a project in a different year — the
      default is hardcoded, not dynamic.

??? note "`license` — str. License (SPDX identifier) — MIT or Apache-2.0"
    - default: `MIT`; choices: `MIT`, `Apache-2.0`
    - Help: License (SPDX identifier)
    - Drives: Which license text is placed in `LICENSES/` (the unchosen text is dropped via
      `_exclude` so `reuse lint` does not flag an unused license file) and the
      `SPDX-License-Identifier` header in every generated source file.

??? note "`markdown_has_frontmatter` — bool. Route Markdown licensing through REUSE.toml to protect YAML frontmatter"
    - default: `false`
    - Help: Markdown with YAML frontmatter on line 1 (Claude Code skills/agents/commands,
      Jekyll/Hugo)? If yes, markdown is licensed via REUSE.toml instead of an inline SPDX
      header, which would otherwise be inserted above the frontmatter and break it.
    - Drives: When `true`, a `REUSE.toml` entry covers `*.md` files so `hawkeye` does not
      insert inline `SPDX-FileCopyrightText` / `SPDX-License-Identifier` comment lines into
      them. When `false` (the default), inline headers are inserted directly into Markdown
      files. Enable this for repos that contain Claude Code agent/skill definitions,
      Jekyll/Hugo content, or any Markdown that must begin with `---` frontmatter.

??? note "`initialize_repository` — bool. Initialize a fresh git repo and make the first commit?"
    - default: `true`
    - Help: Initialize a fresh git repo and make the first commit? Answer NO when adopting
      into an existing repository (it already has git + history).
    - Drives: Whether the three repo-initializing post-copy tasks run: `git init`,
      `git add -A`, and the scaffold `git commit`. The `uv sync` and `prek install` tasks run
      regardless of this setting (they are idempotent). Set to `false` when layering the
      template onto a repository that already has git history — see the
      [adoption guide](usage.md#adopting-into-an-existing-repo) for the full procedure.

## Release model

Two questions declare how many packages release-please versions in the repo. The default —
`single` — is the one-package-at-the-repo-root shape every other page describes; `multi-package`
turns the repo into a monorepo where each declared path is versioned and released independently.
The auto-merge/reconcile flow in `main.yml` was already N-package generic; these two questions
add the config side. See [Design model](design.md#release-please-and-commitizen) for the rationale.

| Question | Type | Default | When shown |
| --- | --- | --- | --- |
| `release_model` | str | `single` | Always |
| `release_packages` | str | *empty string* | `when: {{ release_model == 'multi-package' }}` |

??? note "`release_model` — str. release-please model — single package or a multi-package monorepo"
    - default: `single`; choices: `single` (one package at the repo root), `multi-package`
      (several packages, each released independently)
    - Help: release-please model — one package at the repo root (default), or several packages
      each versioned and released independently (a monorepo).
    - Drives: The shape of `.config/release-please-config.json` and
      `.config/.release-please-manifest.json`. `single` renders the one `.` package with the
      layout-appropriate `extra-files` version-sync (`pyproject.toml` + `uv.lock` for Python,
      `galaxy.yml` for an Ansible collection). `multi-package` instead renders one config +
      manifest entry per path in `release_packages`, each bootstrapped at `0.0.0` with an empty
      `extra-files` — per-package version-sync is layout-specific, so it is left for you to wire
      (the single-package `.` branch shows the shape). `separate-pull-requests: true` is set
      regardless, so each package gets its own Release PR.

??? note "`release_packages` — str. Comma-separated package paths for the multi-package model"
    - default: empty string; when: `{{ release_model == 'multi-package' }}`
    - validator: Only asked and validated for the multi-package model. The value is split on
      commas and trimmed; it must list at least one path, and each entry must be a repo-relative
      path matching `^[A-Za-z0-9._/-]+$` — no leading slash, no `..`, no odd characters. The
      values are spliced straight into `release-please-config.json` /
      `.release-please-manifest.json`, so the strict pattern guards against a malformed path
      corrupting the generated JSON.
    - Help: Comma-separated package paths (relative to the repo root, e.g.
      `packages/api, packages/cli`) for the multi-package model.
    - Drives: Each path becomes an independently-versioned release-please package in both the
      config and the manifest (each bootstrapped at `0.0.0`, with an empty `extra-files` you
      fill in per package layout). Kept as a single comma-separated `str` answer rather than a
      list question; it is split and trimmed wherever it is rendered. Only shown for the
      `multi-package` model.

## Testing & Python shape

Three decoupled levers let you dial in exactly the Python shape you need.
`test_frameworks` controls which test suites are scaffolded. `contains_python` indicates
whether the project uses Python tooling at all. The hidden computed flag `has_python` ORs
both inputs and is the single gate every Python template checks. From there:
`python_source` adds a `src/` layout, `is_package` adds build and distribution metadata, and
`publish_to_pypi` emits a publishing workflow.

!!! note "Dependency chain"
    `test_frameworks` (pytest?) + `contains_python` → `has_python` (computed, hidden) →
    `python_source` → `is_package` → `publish_to_pypi`

| Question | Type | Default | When shown |
| --- | --- | --- | --- |
| `test_frameworks` | str, multiselect | `["pytest"]` | Always |
| `contains_python` | bool | `{{ 'pytest' in test_frameworks }}` | Always |
| `has_python` | bool | `{{ contains_python or ('pytest' in test_frameworks) }}` | Never — hidden/computed (`when: false`) |
| `python_source` | bool | `{{ has_python }}` | `when: {{ has_python }}` |
| `is_package` | bool | `{{ python_source }}` | `when: {{ python_source }}` |
| `publish_to_pypi` | bool | `{{ is_package }}` | `when: {{ is_package }}` |
| `python_package` | str | `{{ project_slug \| replace('-', '_') }}` | `when: {{ python_source }}` |
| `python_version` | str | `3.14` | `when: {{ has_python }}` |

??? note "`test_frameworks` — str, multiselect. Test suites to scaffold"
    - default: `["pytest"]`
    - choices: `pytest` (pytest — Python tests), `bats` (bats — shell/Bash tests)
    - Help: Test suites to scaffold (space toggles; none selected = no tests/ dir)
    - Drives: Scaffolds a `tests/` directory with the appropriate structure: a `conftest.py`
      and Python test stubs when `pytest` is selected; a `.bats` test file and BATS helper
      setup when `bats` is selected; both when both are selected. Selecting neither skips the
      entire `tests/` directory. Selecting `pytest` forces `has_python` true even if
      `contains_python` is `false`, because pytest tests cannot run without the Python
      toolchain.

    !!! tip "Selecting pytest forces Python"
        Even if you answer `false` to `contains_python`, selecting `pytest` here guarantees
        the full Python toolchain (`pyproject.toml`, ruff, uv) is scaffolded. The
        `has_python` computed flag enforces this invariant so the two levers cannot
        contradict each other.

??? note "`contains_python` — bool. Does this project contain Python? (forced yes when pytest is selected)"
    - default: `{{ 'pytest' in test_frameworks }}`
    - Help: Does this project contain Python? (forced yes when pytest is selected)
    - Drives: One of the two inputs to the `has_python` computed flag. Set this to `true` for
      projects that use Python tooling (ruff, mypy, uv) without necessarily having a `src/`
      layout — for example, an infrastructure repo that has Python helper scripts but no
      importable source package. Defaults to `true` automatically when `pytest` is in
      `test_frameworks`.

??? note "`has_python` — bool. Hidden/computed — never shown to the user (`when: false`)"
    - when: `false` — never displayed at the prompt
    - default: `{{ contains_python or ('pytest' in test_frameworks) }}`
    - Drives: The single internal gate that every Python-specific template checks:
      `pyproject.toml`, ruff config, `uv.lock`, Python CI steps, and the `uv sync` post-copy
      task. By ORing both inputs it prevents a stray `contains_python: false` answer from
      accidentally dropping pytest's dependencies when pytest was selected. A skipped
      question (`when: false`) still resolves its `default` expression, so this value is
      always available to downstream questions and templates.

    !!! note "Why a separate computed flag?"
        Gating all Python templates on a single computed value means the OR logic lives in
        one place and every downstream question — `python_source`, `python_version`, etc. —
        can depend on it cleanly without repeating the condition.

??? note "`python_source` — bool. Python source code? (src/<package> layout)"
    - default: `{{ has_python }}`; when: `{{ has_python }}`
    - Help: Python source code? (src/<package> layout) — No = tooling/tests only, like
      dotfiles
    - Drives: Whether a `src/<python_package>/` directory is scaffolded with an
      `__init__.py`. Answer `false` for a project that uses the Python toolchain and tests
      but has no importable source — for example, a dotfiles or infrastructure repo that
      wants ruff and pytest but no `src/` tree. The default tracks `has_python` so it
      defaults to `false` when Python is absent (preventing a stray `src/` directory from
      rendering).

??? note "`is_package` — bool. Build as an installable/distributable package?"
    - default: `{{ python_source }}`; when: `{{ python_source }}`
    - Help: Build as an installable/distributable package? (adds build-system + dist
      metadata)
    - Drives: Adds a `[build-system]` table and full distribution metadata to
      `pyproject.toml` (version, classifiers, URLs), enabling `uv build` and wheel
      distribution. Answer `false` for a project that has Python source but is never
      distributed as a package — an internal application that is deployed rather than
      installed, or a private tool.

??? note "`publish_to_pypi` — bool. Emit a PyPI publish workflow?"
    - default: `{{ is_package }}`; when: `{{ is_package }}`
    - Help: Emit a PyPI publish workflow (fires on each GitHub Release, OIDC Trusted
      Publishing)?
    - Drives: Adds `.github/workflows/publish.yml` — a GitHub Actions workflow that builds
      the package once, rehearses the release on TestPyPI (publish, then smoke-install the
      built wheel), and only then publishes to PyPI, on each GitHub Release. Each publish
      stage uses OIDC Trusted Publishing (no long-lived API tokens required) bound to its own
      GitHub deployment environment (`testpypi` / `pypi`). Answer `false` for a package that
      is not published to the public PyPI (private packages, internal tools). See
      [Modules & levers](modules.md) for the workflow details.

??? note "`python_package` — str. Python import package name"
    - default: `{{ project_slug | replace('-', '_') }}`; when: `{{ python_source }}`
    - validator: Must be a valid Python identifier — start with a letter or underscore, then
      only letters, digits, or underscores (no dashes, dots, or spaces) — and must not be a
      Python reserved keyword (e.g. `class`, `import`). An empty value is also rejected. This
      isn't just cosmetic: the value is spliced unquoted into `import <pkg>` (e.g. the
      `publish.yml` smoke job), so an invalid identifier is a guaranteed `SyntaxError` on
      every run.
    - Help: Python import package name
    - Drives: The `src/<python_package>/` directory name and the importable package name
      referenced in `pyproject.toml` `[tool.setuptools.packages]` or equivalent metadata.
      Defaults to `project_slug` with dashes replaced by underscores, following the Python
      convention (PEP 8 — package names use underscores, not dashes).

??? note "`python_version` — str. Minimum Python version (e.g. 3.14)"
    - default: `3.14`; when: `{{ has_python }}`
    - validator: Must be MAJOR.MINOR only (e.g. `3.14`). A patch component (`3.14.2`) or a
      comparator (`>=3.14`) will fail validation and render an invalid ruff target-version
      string.
    - Help: Minimum Python version (e.g. 3.14)
    - Drives: The `requires-python = ">=X.Y"` constraint in `pyproject.toml` and the
      `target-version = "pyXY"` setting in the ruff config. MAJOR.MINOR only — a patch
      component or comparator would produce an invalid `target-version` value in ruff's
      configuration.

## Ansible shape

Four levers configure the Ansible scaffold, fully orthogonal to Python — both can be true
simultaneously. `contains_ansible` is the user-facing entry point. The hidden computed flag
`has_ansible` is the single gate every Ansible template checks. From there: `ansible_kind`
selects the scaffold shape; the hidden computed flag `ansible_role_based` gates the
namespace/name and Galaxy publish path to the two role-based kinds (collection and role);
and `publish_to_galaxy` emits the publish workflow.

!!! note "Dependency chain"
    `contains_ansible` → `has_ansible` (computed, hidden) → `ansible_kind` →
    `ansible_role_based` (computed, hidden) → `ansible_namespace` / `ansible_name` →
    `publish_to_galaxy`

| Question | Type | Default | When shown |
| --- | --- | --- | --- |
| `contains_ansible` | bool | `false` | Always |
| `has_ansible` | bool | `{{ contains_ansible }}` | Never — hidden/computed (`when: false`) |
| `ansible_kind` | str | `collection` | `when: {{ has_ansible }}` |
| `ansible_role_based` | bool | `{{ has_ansible and ansible_kind in ['collection', 'role'] }}` | Never — hidden/computed (`when: false`) |
| `ansible_namespace` | str | `{{ repo_owner \| lower \| replace('-', '_') }}` | `when: {{ ansible_role_based }}` |
| `ansible_name` | str | `{{ project_slug \| replace('-', '_') }}` | `when: {{ ansible_role_based }}` |
| `publish_to_galaxy` | bool | `{{ ansible_role_based }}` | `when: {{ ansible_role_based }}` |

<a id="contains_ansible"></a>
??? note "`contains_ansible` — bool. Does this project contain Ansible content (playbooks, a role, or a collection)?"
    - default: `false`
    - Help: Does this project contain Ansible content (playbooks, a role, or a collection)?
    - Drives: The sole input to the `has_ansible` computed flag; the user-facing entry point
      to the entire Ansible cascade. Orthogonal to Python — a project can be both a Python
      package and an Ansible collection simultaneously. Defaults to `false` because most
      projects do not need Ansible scaffolding.

??? note "`has_ansible` — bool. Hidden/computed — never shown to the user (`when: false`)"
    - when: `false`
    - default: `{{ contains_ansible }}`
    - Drives: The single internal gate that every Ansible-specific template checks: the
      scaffold structure, Galaxy metadata, Molecule, and the CI lint gate. A skipped question
      (`when: false`) still resolves its `default` expression, so this value is always
      available to downstream questions and templates.

    !!! note "Why a separate computed flag?"
        Mirrors `has_python`: gating all Ansible templates on one computed value keeps the
        OR/AND logic in one place and lets every downstream question — `ansible_kind`,
        `ansible_role_based`, etc. — depend on it cleanly without repeating the condition.

??? note "`ansible_kind` — str. Ansible content shape — collection, role, or playbooks"
    - default: `collection`; when: `{{ has_ansible }}`
    - choices: `collection` (Galaxy-publishable; scaffolds `galaxy.yml`, `roles/`,
      `plugins/`), `role` (standalone role; scaffolds `tasks/`, `defaults/`, `handlers/`,
      `meta/`), `playbooks` (operational project; scaffolds `ansible.cfg`, `inventory/`,
      `playbooks/`; not published to Galaxy)
    - Help: Ansible content shape — drives the scaffold, testing, and publish path
    - Drives: The directory scaffold shape and the downstream cascade. `collection` and
      `role` activate `ansible_role_based`, enabling the namespace/name questions, a Molecule
      scenario, and the Galaxy publish workflow. `playbooks` is an operational project — no
      Galaxy namespace, no publish workflow. Only shown when `has_ansible` is `true`.

??? note "`ansible_role_based` — bool. Hidden/computed — never shown to the user (`when: false`)"
    - when: `false`
    - default: `{{ has_ansible and ansible_kind in ['collection', 'role'] }}`
    - Drives: The gate for the profile shared by `collection` and `role`: a Galaxy
      namespace/name, a Molecule scenario, and a Galaxy publish path. Every downstream
      question that belongs to that profile reads this single flag instead of repeating the
      kind check — the same pattern as `has_python`. Resolves to `false` when Ansible is
      absent or when `ansible_kind` is `playbooks`.

    !!! note "Why a separate computed flag?"
        `collection` and `role` share a Galaxy namespace/name, a Molecule scenario, and a
        publish path; `playbooks` does not. A single computed flag keeps that distinction in
        one place rather than repeating `ansible_kind in ['collection', 'role']` in every
        downstream question and template.

??? note "`ansible_namespace` — str. Ansible Galaxy namespace"
    - default: `{{ repo_owner | lower | replace('-', '_') }}`; when: `{{ ansible_role_based }}`
    - validator: Must be lowercase, start with a letter, and use underscores instead of
      dashes or spaces.
    - Help: Ansible Galaxy namespace (lowercase; underscores, not dashes)
    - Drives: The namespace portion of the fully-qualified collection or role name
      (`<namespace>.<name>`). Used in `galaxy.yml`, `meta/main.yml`, and the Galaxy publish
      workflow. Defaults to `repo_owner` lowercased with dashes converted to underscores,
      following Galaxy's naming rules (lowercase, start with a letter, underscores only).
      Only shown when `ansible_role_based` is `true`.

??? note "`ansible_name` — str. Ansible collection/role name"
    - default: `{{ project_slug | replace('-', '_') }}`; when: `{{ ansible_role_based }}`
    - validator: Must be lowercase, start with a letter, and use underscores instead of
      dashes or spaces.
    - Help: Ansible collection/role name (lowercase; underscores, not dashes)
    - Drives: The name portion of the fully-qualified collection or role name
      (`<namespace>.<name>`). Used in `galaxy.yml`, `meta/main.yml`, the FQCN throughout
      templates, and the Galaxy publish workflow. Defaults to `project_slug` with dashes
      converted to underscores. Only shown when `ansible_role_based` is `true`.

??? note "`publish_to_galaxy` — bool. Emit a Galaxy publish workflow?"
    - default: `{{ ansible_role_based }}`; when: `{{ ansible_role_based }}`
    - Help: Emit a Galaxy publish workflow (fires on each GitHub Release; needs an
      ANSIBLE_GALAXY_API_KEY secret)?
    - Drives: Adds `.github/workflows/publish-galaxy.yml` — a GitHub Actions workflow that
      publishes the collection or role to Ansible Galaxy on each GitHub Release. Answer
      `false` for collections or roles that are not published to the public Galaxy. Only
      shown when `ansible_role_based` is `true`.

    !!! note "No OIDC — an API key is required"
        Unlike `publish_to_pypi`, which uses OIDC Trusted Publishing (no long-lived tokens),
        Ansible Galaxy does not support OIDC. The generated workflow reads an
        `ANSIBLE_GALAXY_API_KEY` secret that you must provision in your repository settings.

## Includable modules

Each module is a boolean toggle. Most default to `false` (opt-in); `include_docs_site` is the
one exception, defaulting `true` (opt-out) — see its entry below. Modules are fully
orthogonal — you can enable any combination without affecting the quality baseline or any
other module. The SQL module unlocks two follow-up questions (`sql_dialect` and
`sql_use_dbt`) that are hidden when SQL is off. For the complete list of scaffolded files and
CI integration per module, see [Modules & levers](modules.md).

| Question | Type | Default | When shown |
| --- | --- | --- | --- |
| `include_terraform` | bool | `false` | Always |
| `include_docker` | bool | `false` | Always |
| `include_helm` | bool | `false` | Always |
| `include_sql` | bool | `false` | Always |
| `sql_dialect` | str | `sqlite` | `when: {{ include_sql }}` |
| `sql_use_dbt` | bool | `false` | `when: {{ include_sql }}` |
| `include_devcontainer` | bool | `false` | Always |
| `include_docs_site` | bool | `true` | Always |

<a id="include_terraform"></a>
??? note "`include_terraform` — bool. Terraform scaffolding (versions - variables - outputs)"
    - default: `false`
    - Help: Terraform scaffolding (versions - variables - outputs)
    - Drives: Scaffolds a `terraform/` directory with `versions.tf`, `variables.tf`, and
      `outputs.tf` stubs. See [Modules & levers](modules.md) for the complete file list and CI
      integration.

<a id="include_docker"></a>
??? note "`include_docker` — bool. Docker scaffolding (Dockerfile + compose)"
    - default: `false`
    - Help: Docker scaffolding (Dockerfile + compose)
    - Drives: Adds a `Dockerfile`, `.dockerignore`, and a `compose.yaml` to the project. See
      [Modules & levers](modules.md).

<a id="include_helm"></a>
??? note "`include_helm` — bool. Helm chart scaffolding"
    - default: `false`
    - Help: Helm chart scaffolding
    - Drives: Scaffolds a `helm/<project_slug>/` directory with a minimal Helm chart —
      `Chart.yaml`, `values.yaml`, `.helmignore`, and a `templates/` directory stub. See
      [Modules & levers](modules.md).

<a id="include_sql"></a>
??? note "`include_sql` — bool. SQL scaffolding (sqlfluff lint/fix + a dialect-aware .sqlfluff)"
    - default: `false`
    - Help: SQL scaffolding (sqlfluff lint/fix + a dialect-aware .sqlfluff)
    - Drives: Adds a dialect-aware `.sqlfluff` configuration file and wires sqlfluff into the
      prek hook set. Enabling SQL unlocks the two follow-up questions below: `sql_dialect`
      and `sql_use_dbt`. See [Modules & levers](modules.md) for the complete integration.

??? note "`sql_dialect` — str. SQL dialect for sqlfluff (28 choices)"
    - default: `sqlite`; when: `{{ include_sql }}`
    - choices: `ansi`, `athena`, `bigquery`, `clickhouse`, `databricks`, `db2`, `doris`,
      `duckdb`, `exasol`, `flink`, `greenplum`, `hive`, `impala`, `mariadb`, `materialize`,
      `mysql`, `oracle`, `postgres`, `redshift`, `snowflake`, `soql`, `sparksql`, `sqlite`,
      `starrocks`, `teradata`, `trino`, `tsql`, `vertica` — 28 dialects total
    - Help: SQL dialect — drives .sqlfluff (sqlfluff lints/fixes against it)
    - Drives: Sets `dialect = <value>` under `[sqlfluff]` in the generated `.sqlfluff` file.
      Only shown when `include_sql` is `true`. The dialect controls how sqlfluff parses and
      lints your SQL — choose the one that matches your database engine.

??? note "`sql_use_dbt` — bool. dbt-templated SQL?"
    - default: `false`; when: `{{ include_sql }}`
    - Help: dbt-templated SQL? Yes -> templater=dbt + the templater dep; bring your dbt
      project & models
    - Drives: When `true`, sets `templater = dbt` in `.sqlfluff` and adds the dbt sqlfluff
      templater as a dev dependency so sqlfluff can parse dbt Jinja macros and `ref()` calls.
      You supply your own dbt project and models. Only shown when `include_sql` is `true`.

<a id="include_devcontainer"></a>
??? note "`include_devcontainer` — bool. Dev Container scaffolding (.devcontainer/devcontainer.json)"
    - default: `false`
    - Help: Dev Container scaffolding (.devcontainer/devcontainer.json for Codespaces / VS
      Code)
    - Drives: Adds a `.devcontainer/devcontainer.json` with a baseline configuration for
      GitHub Codespaces and the VS Code Dev Containers extension. See
      [Modules & levers](modules.md).

<a id="include_docs_site"></a>
??? note "`include_docs_site` — bool. MkDocs Material docs site (mkdocs.yml + a placeholder page + the Pages build workflow)"
    - default: `true`
    - Help: MkDocs Material docs site (mkdocs.yml + a placeholder page + the Pages build
      workflow)
    - Drives: Adds `mkdocs.yml`, `overrides/404.html`, a placeholder `docs/index.md`, a
      shared `docs/assets/favicon.svg`, and a thin `.github/workflows/docs.yml` caller that
      delegates the actual build-and-deploy to `nivintw/repo-management`'s reusable
      workflow. Unlike every other module above, this one defaults **on** — every fleet repo
      is meant to carry it eventually, so set it to `false` to opt out. See
      [Modules & levers](modules.md).

## Copier meta-settings

These are not interactive questions — they are `copier.yml` directives that control template
mechanics. Documented here for completeness; none of them appear at the Copier prompt.

### `_tasks` — post-copy automation

Lists the commands Copier runs after rendering the project. They execute **only** when you
pass `--trust` to `copier copy`; without it, Copier skips them and `_message_after_copy`
prints the equivalent manual steps. All tasks are gated to the initial copy
(`_copier_operation == 'copy'`); `copier update` runs none of them.

| Task | Gate | Notes |
| --- | --- | --- |
| `git init -q` | `copy` + `initialize_repository` | Creates the `.git` directory. Skipped when adopting into an existing repo. |
| `uv sync` | `copy` + `has_python` | Creates the virtual environment and installs all dev dependencies. Only runs when the project includes Python. |
| `git add -A` | `copy` + `initialize_repository` | Stages all rendered files before the scaffold commit. Skipped when adopting. |
| `git commit -m "chore: scaffold <slug>"` | `copy` + `initialize_repository` | Makes the first commit using `author_name`/`author_email` as the git author identity so the commit is correct even without a global git config. Runs *before* `prek install` so the no-commit-to-branch hook cannot block the first commit to main. Guarded by `git diff --cached --quiet ||` to be idempotent on re-runs. |
| `uvx prek@0.4.8 install` | `copy` only | Installs the pre-commit hooks. Gracefully no-ops (prints a message) when there is no `.git` directory — i.e. when `initialize_repository: false` is used into a directory that has not yet been initialised as a git repo. |

### `_exclude` — drop the unchosen license text and one-time seeds

In addition to Copier's built-in defaults (`.git`, `*.pyc`, `~*`, etc.), `_exclude` uses
Jinja conditionals to drop the license text that was not chosen:

```jinja
{% if license != 'MIT' %}LICENSES/MIT.txt{% endif %}
{% if license != 'Apache-2.0' %}LICENSES/Apache-2.0.txt{% endif %}
```

Both texts stay in the template source (the `LICENSE.jinja` includes the Apache text via
`{% include %}`); they are simply not copied to the output so `reuse lint` does not flag an
unused license file.

`_exclude` also gates three **one-time SEED files** on `_copier_operation`, which *is* in scope
when Copier renders `_exclude`:

```jinja
{% if _copier_operation == 'update' %}CHANGELOG.md{% endif %}
{% if _copier_operation == 'update' %}tests/test_smoke.py{% endif %}
{% if _copier_operation == 'update' %}tests/smoke.bats{% endif %}
```

`CHANGELOG.md`, `tests/test_smoke.py`, and `tests/smoke.bats` render on the first `copy`, but
are excluded on `update` — so Copier's 3-way merge never re-patches a seed the user has since
grown, replaced, or deleted. Without this, a routine `copier update` would resurrect a deleted
sample test, clobber the release-please-owned `CHANGELOG.md`, and litter `.rej` files.

### `_skip_if_exists` — protect the seeds on adoption

The complementary lever for the adopt-into-existing-repo copy path. `_skip_if_exists` lists the
same three seeds so a `copier copy` into a repo that already has a `CHANGELOG.md` or a sample
test never overwrites one that exists:

```yaml
_skip_if_exists:
  - "CHANGELOG.md"
  - "tests/test_smoke.py"
  - "tests/smoke.bats"
```

On a fresh greenfield copy the files don't exist yet, so they still render. The two lists —
the `update`-gated `_exclude` entries above and this `_skip_if_exists` — are kept in sync so a
seed a user owns after the first copy is never re-patched by `update` nor clobbered on adoption.

### `_message_after_copy` — post-copy guidance

After a successful `copier copy`, Copier prints a message with project-specific setup steps.
Because `_copier_operation` is not available in the message context, the message branches on
`initialize_repository` instead:

- **Greenfield (`initialize_repository: true`):** If `--trust` was not passed, prints the
  manual steps in order — `git init`, optionally `uv sync`, then
  `git add -A && git commit`, then `uvx prek@0.4.8 install` — with a note that the commit must
  happen before hooks are installed (the no-commit-to-branch hook would otherwise block the
  first commit to main).
- **Adoption (`initialize_repository: false`):** Notes that git init and the scaffold commit
  were skipped, directs the user to reconcile the scaffold against their existing files and
  commit on their own branch, and links to the adoption documentation. See
  [Usage & adoption](usage.md#adopting-into-an-existing-repo).
