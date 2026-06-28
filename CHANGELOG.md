# Changelog

## [1.2.0](https://github.com/nivintw/copier-everything/compare/v1.1.0...v1.2.0) (2026-06-28)


### Features

* Support fleet adoption (PyPI publish, repo_name, version, adoption mode, agent docs) ([798b156](https://github.com/nivintw/copier-everything/commit/798b156390d11fb82e522667b052896fa146a1a3)), closes [#56](https://github.com/nivintw/copier-everything/issues/56) [#60](https://github.com/nivintw/copier-everything/issues/60) [#59](https://github.com/nivintw/copier-everything/issues/59) [#61](https://github.com/nivintw/copier-everything/issues/61) [#49](https://github.com/nivintw/copier-everything/issues/49) [#50](https://github.com/nivintw/copier-everything/issues/50) [#47](https://github.com/nivintw/copier-everything/issues/47)


### Bug Fixes

* Escape author identity in scaffold-commit task for names with quotes ([a30f99c](https://github.com/nivintw/copier-everything/commit/a30f99ce897361ad68fcffa9770b8062de2d9968))

## [1.1.0](https://github.com/nivintw/copier-everything/compare/v1.0.4...v1.1.0) (2026-06-27)


### Features

* Expand lint/security tooling (yamllint, terraform/helm hooks, trivy, lychee, kubeconform) ([27dc217](https://github.com/nivintw/copier-everything/commit/27dc217d1c1c576f3a5008466b53e22c6a3d04e6))

## [1.0.4](https://github.com/nivintw/copier-everything/compare/v1.0.3...v1.0.4) (2026-06-27)


### Bug Fixes

* Make the generated release-please flow work end-to-end ([e9bb68b](https://github.com/nivintw/copier-everything/commit/e9bb68bc183a2da06fa26bdf6efa52562b1b0249)), closes [#34](https://github.com/nivintw/copier-everything/issues/34) [#30](https://github.com/nivintw/copier-everything/issues/30) [#35](https://github.com/nivintw/copier-everything/issues/35) [#36](https://github.com/nivintw/copier-everything/issues/36) [#37](https://github.com/nivintw/copier-everything/issues/37)

## [1.0.3](https://github.com/nivintw/copier-everything/compare/v1.0.2...v1.0.3) (2026-06-27)


### Bug Fixes

* Run the full zizmor audit online in generated CI ([f67502e](https://github.com/nivintw/copier-everything/commit/f67502e8a288864d3b6dcd4d0fa1244a8a1131be)), closes [#27](https://github.com/nivintw/copier-everything/issues/27)

## [1.0.2](https://github.com/nivintw/copier-everything/compare/v1.0.1...v1.0.2) (2026-06-27)


### Bug Fixes

* Omit dead markdown-header licenserc config under frontmatter ([c2bcdb8](https://github.com/nivintw/copier-everything/commit/c2bcdb804f323648262af013feb600d6836e3db2)), closes [#28](https://github.com/nivintw/copier-everything/issues/28)

## [1.0.1](https://github.com/nivintw/copier-everything/compare/v1.0.0...v1.0.1) (2026-06-27)


### Bug Fixes

* Mark render-matrix shapes done only at a known conclusion ([55109e0](https://github.com/nivintw/copier-everything/commit/55109e0a78f349d73e870c4d78437d7665828a6d))


### Performance Improvements

* Parallelize render-matrix shapes + cache prek envs in CI ([4d82ddf](https://github.com/nivintw/copier-everything/commit/4d82ddf24b0a4093102c345d83dab71b65b9cf77))

## 1.0.0 (2026-06-27)


### Features

* Adopt hawkeye + reuse licensing at the repo root ([ebb3acd](https://github.com/nivintw/copier-everything/commit/ebb3acd85941559102d687a07a7b1b899352f568))
* adopt release-please for releases (root + template) ([5fbd0e9](https://github.com/nivintw/copier-everything/commit/5fbd0e92506dfcd319a74913b3862de3bf4a2f51))
* adopt the template's prek hooks at the repo root ([9d2b337](https://github.com/nivintw/copier-everything/commit/9d2b337c44e6678b600397b897689e36e71101a7))
* Auto-merge the release-please Release PR for continuous releases ([cf6a6d3](https://github.com/nivintw/copier-everything/commit/cf6a6d337de1f3dfb9563a4ee9ebdf54eb129d07))


### Bug Fixes

* Set GH_REPO so the release auto-merge step works without a checkout ([4e4894f](https://github.com/nivintw/copier-everything/commit/4e4894f6829a37b8a76e19a1e1ca58935fa14ebe))

<!--
SPDX-FileCopyrightText: © 2026 Tyler Nivin
SPDX-License-Identifier: MIT
-->

## Changelog

<!-- release-please manages this file; the first release will populate it. -->
