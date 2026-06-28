<!--
SPDX-FileCopyrightText: © 2026 Tyler Nivin
SPDX-License-Identifier: MIT
-->

# Agent instructions — copier-everything

This is a [Copier](https://copier.readthedocs.io) **project template**, not an application.
Almost everything here is *template source* that renders into a generated project. Read this
before editing.

## The one rule that matters most

**Edit the `.jinja` source under `template/`, never rendered output.** Files in `template/`
end in `.jinja` and contain Jinja2 placeholders (`{{ project_slug }}`) and logic
(`{% if has_python %}`). A generated project is the *output* of rendering them — changing a
rendered file fixes nothing here. If you catch yourself editing a file with no `.jinja`
suffix inside a generated tree, stop: the fix belongs in the corresponding `template/…​.jinja`.

## Layout

- **`copier.yml`** — the questions (the template's whole interface) plus `_tasks` (post-copy
  setup) and `_exclude`. Add a question here before consuming its answer in `template/`.
- **`template/`** — the rendered tree. `_subdirectory: template`, `.jinja` suffix stripped on
  render.
- **`tests/`** — `render-matrix.sh` (the test suite) and `answers/*.yml` (one answer set per
  shape).
- **`.config/`** — this repo's own tool configs (the template emits the generated project's
  configs into `template/.config/`).

### Conditional-path filename convention

A path segment can itself be a Jinja conditional, so a whole file/dir renders only when an
answer is set. The empty-string result drops it:

```text
template/{% if include_docker %}Dockerfile{% endif %}.jinja      # only when include_docker
template/{% if has_python %}.python-version{% endif %}.jinja     # only for Python projects
```

When the condition is false the name collapses to empty and Copier emits nothing. Use this
(not in-file `{% if %}` around the whole body) to gate an entire file's existence.

### The Python shape levers

Three decoupled answers, not one: `has_python` (hidden, computed — Python present for any
reason) → `python_source` (is there a `src/<pkg>`) → `is_package` (built as an installable
dist). Gate Python config on `has_python`; gate source/`__init__.py` on `python_source`;
gate build-system/dist metadata and publish on `is_package`. Don't conflate them.

## Render & test

`tests/render-matrix.sh` renders **every** `tests/answers/*.yml` shape and runs the full
quality gate (reuse, hawkeye, taplo, prek/ruff/ty/pytest, bats, helm…) on each, derived from
what the render produced. It must stay green across all shapes.

```console
tests/render-matrix.sh                                   # the whole matrix (what CI runs)
copier copy --defaults --data-file tests/answers/pkg.yml --skip-tasks . /tmp/out   # one shape, by hand
```

Adding a new shape = a new `tests/answers/<name>.yml`. Changing template behavior in a way
that needs coverage = add or adjust an answer set so a shape exercises it.

## Licensing — REUSE / SPDX (the gate enforces this)

Every file needs license info or `reuse lint` fails.

- **This repo's own files** get SPDX headers maintained by **hawkeye** (`hawkeye format` /
  `check`, config in `.config/licenserc.toml`). Markdown carries an HTML-comment header
  (`<!-- SPDX-… -->`); shell/`#`-comment files carry `#` headers.
- **`template/**`** is covered by `REUSE.toml`'s `precedence = "override"` — its `.jinja`
  headers hold `{{ license }}` placeholders that only resolve at render time, so reuse must
  not parse them. The *rendered* headers are verified per-shape by `render-matrix.sh`.
- Files with no comment syntax (JSON, `.vscode/*`, `.python-version`, `uv.lock`) are listed
  in `REUSE.toml` annotations instead of carrying a header.

When you add a new file, make sure it's covered one of these ways.

## Release flow

`release-please` (manifest mode, in `.github/workflows/main.yml`) maintains a Release PR off
Conventional Commits, bumps the version + `CHANGELOG.md`, and cuts the tag/Release. Use
**Conventional Commit** messages (`feat:`, `fix:`, `chore:`…) — they drive versioning. The
generated project gets its own equivalent flow under `template/.github/workflows/`.

## Before you call it done

Run `tests/render-matrix.sh` (or at least the shapes your change touches) and confirm it's
green. A change that renders a broken project is not done, even if this repo's own files look
fine.
