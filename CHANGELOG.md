# Changelog

## [1.9.0](https://github.com/nivintw/copier-everything/compare/v1.8.3...v1.9.0) (2026-07-05)


### Features

* Add include_docs_site template feature (MkDocs Material scaffold) ([cf86eb4](https://github.com/nivintw/copier-everything/commit/cf86eb4de5c679e87daf86d3200bea1ff0ac3a0a)), closes [#156](https://github.com/nivintw/copier-everything/issues/156)

## [1.8.3](https://github.com/nivintw/copier-everything/compare/v1.8.2...v1.8.3) (2026-07-05)


### Bug Fixes

* License .gitignore via REUSE.toml instead of a hawkeye negation ([c933e90](https://github.com/nivintw/copier-everything/commit/c933e90540624f433337edf9c75279ae4540e828)), closes [#145](https://github.com/nivintw/copier-everything/issues/145)

## [1.8.2](https://github.com/nivintw/copier-everything/compare/v1.8.1...v1.8.2) (2026-07-04)


### Bug Fixes

* Correct Ansible/Python/Helm template content and gating ([2b78454](https://github.com/nivintw/copier-everything/commit/2b78454921746c824ff9d2d5dd7892b10156b9b5)), closes [#139](https://github.com/nivintw/copier-everything/issues/139) [#140](https://github.com/nivintw/copier-everything/issues/140) [#141](https://github.com/nivintw/copier-everything/issues/141) [#143](https://github.com/nivintw/copier-everything/issues/143) [#137](https://github.com/nivintw/copier-everything/issues/137) [#138](https://github.com/nivintw/copier-everything/issues/138) [#142](https://github.com/nivintw/copier-everything/issues/142) [#132](https://github.com/nivintw/copier-everything/issues/132) [#134](https://github.com/nivintw/copier-everything/issues/134) [#133](https://github.com/nivintw/copier-everything/issues/133)
* Gate .envrc entry in licenserc SCRIPT_STYLE mapping on has_python ([1386a25](https://github.com/nivintw/copier-everything/commit/1386a25fadbac2e5c9a6095353f091c64e352779))

## [1.8.1](https://github.com/nivintw/copier-everything/compare/v1.8.0...v1.8.1) (2026-07-04)


### Bug Fixes

* Explicitly check the shebang in the checksum-script sync test ([e8d110b](https://github.com/nivintw/copier-everything/commit/e8d110be7df7b59f26fb93a80bd2a29e1fc4624b))

## [1.8.0](https://github.com/nivintw/copier-everything/compare/v1.7.0...v1.8.0) (2026-07-04)


### Features

* Back-port proven TestPyPI→PyPI Trusted Publishing flow to publish.yml ([1b754be](https://github.com/nivintw/copier-everything/commit/1b754be40f7ee7d184179ad5ba8579114e87b9b9)), closes [#109](https://github.com/nivintw/copier-everything/issues/109)


### Bug Fixes

* Reject Python reserved keywords in python_package validator ([300a6d3](https://github.com/nivintw/copier-everything/commit/300a6d361aa3656d802dc0179ce4b9218ee1b4f2))
* Validate python_package as a Python identifier, clarify tag-trust boundary ([f4f7c75](https://github.com/nivintw/copier-everything/commit/f4f7c7578770f190d71d666f69dc85c24799f264))

## [1.7.0](https://github.com/nivintw/copier-everything/compare/v1.6.0...v1.7.0) (2026-07-03)


### Features

* Add approve-bot-prs workflow (root + template) ([74c42d7](https://github.com/nivintw/copier-everything/commit/74c42d7e3b64325249403db854bb18ea87112ca2)), closes [#108](https://github.com/nivintw/copier-everything/issues/108)

## [1.6.0](https://github.com/nivintw/copier-everything/compare/v1.5.0...v1.6.0) (2026-06-29)


### Features

* Add first-class Ansible support (collection / role / playbooks) ([5bffa72](https://github.com/nivintw/copier-everything/commit/5bffa72b2ed3b462af683d3ef8b09f0066db8bdc)), closes [#99](https://github.com/nivintw/copier-everything/issues/99)

## [1.5.0](https://github.com/nivintw/copier-everything/compare/v1.4.0...v1.5.0) (2026-06-29)


### Features

* Source lychee excludes from .config + sync-test infra ([b198ccd](https://github.com/nivintw/copier-everything/commit/b198ccdb61b319a6a79df0ebce6840906bc90c41))

## [1.4.0](https://github.com/nivintw/copier-everything/compare/v1.3.2...v1.4.0) (2026-06-29)


### Features

* **template:** Strip status:* labels when an issue closes ([4f6071d](https://github.com/nivintw/copier-everything/commit/4f6071d8aec4458f261024d3df1b47572796dc92)), closes [#77](https://github.com/nivintw/copier-everything/issues/77)


### Bug Fixes

* **ci:** Retry checksum-refresh binary downloads ([1ac54cf](https://github.com/nivintw/copier-everything/commit/1ac54cfdd0ccc8536bb43b77e05a78538d892fa7)), closes [#76](https://github.com/nivintw/copier-everything/issues/76)
* **ci:** Retry pinned-binary downloads on transient errors ([a2948c3](https://github.com/nivintw/copier-everything/commit/a2948c3bd5f76a92e5d3e8a8641c78d871d92918)), closes [#76](https://github.com/nivintw/copier-everything/issues/76)

## [1.3.2](https://github.com/nivintw/copier-everything/compare/v1.3.1...v1.3.2) (2026-06-28)


### Bug Fixes

* Raise template ruff floor to &gt;=0.12 for py314 target-version ([fd6074c](https://github.com/nivintw/copier-everything/commit/fd6074c46a2ede8a69798f0a21883ef6ca41f466)), closes [#73](https://github.com/nivintw/copier-everything/issues/73)

## [1.3.1](https://github.com/nivintw/copier-everything/compare/v1.3.0...v1.3.1) (2026-06-28)


### Bug Fixes

* Exclude own /compare/ URLs from lychee link-check ([f69f992](https://github.com/nivintw/copier-everything/commit/f69f992adaf95f4313b80f1be3111a28e752176f))

## [1.3.0](https://github.com/nivintw/copier-everything/compare/v1.2.0...v1.3.0) (2026-06-28)


### Features

* Checksum-verify CI release binaries ([#58](https://github.com/nivintw/copier-everything/issues/58)) ([2f020e1](https://github.com/nivintw/copier-everything/commit/2f020e17cf240baf999d0f4215c7a6ffc1bce742))


### Bug Fixes

* Address Copilot review (hex case, App preflight, comment) ([3d6fb03](https://github.com/nivintw/copier-everything/commit/3d6fb037439fd09eebb3601380868e8c2123f6e8))
* Harden checksum-refresh automation + docs review fixes ([2ac6fa9](https://github.com/nivintw/copier-everything/commit/2ac6fa909b37330b0be272b70a96511e1714935e))
* Harden templated CI workflows and quality-gate configs ([66e8b9c](https://github.com/nivintw/copier-everything/commit/66e8b9cc562fdcfb21e8451b4057fcfed9aa98b0)), closes [#64](https://github.com/nivintw/copier-everything/issues/64) [#57](https://github.com/nivintw/copier-everything/issues/57) [#63](https://github.com/nivintw/copier-everything/issues/63) [#65](https://github.com/nivintw/copier-everything/issues/65) [#62](https://github.com/nivintw/copier-everything/issues/62)
* Stop gitleaks flagging SHA256 pins + fix EOF blank line ([8ccf1e4](https://github.com/nivintw/copier-everything/commit/8ccf1e40db423f72af9053f7f2433fda414d0491))
* Use complete Markdown glob for link-check paths filter ([3f0fb97](https://github.com/nivintw/copier-everything/commit/3f0fb9776505f0def92c2fd5b7fc954350465655))

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
