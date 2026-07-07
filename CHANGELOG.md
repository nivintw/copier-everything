# Changelog

## [1.12.0](https://github.com/nivintw/copier-everything/compare/v1.11.2...v1.12.0) (2026-07-07)


### Features

* **hooks:** ship a guard-hooks + twin-sync enforcement toolkit ([71187d6](https://github.com/nivintw/copier-everything/commit/71187d6f65f906ca2da8f94979ab3ada5fe43adf))
* **template:** PyPI upload guard, multi-package release model, generic link excludes ([2768242](https://github.com/nivintw/copier-everything/commit/27682428a33e9d42f3112204d460cdf1d8f36195))


### Bug Fixes

* **ci:** make the generated check_copier_src_path.py lint/format-clean ([7766d6b](https://github.com/nivintw/copier-everything/commit/7766d6b029780cf448d8a7efdf29971a90723586))
* **ci:** unbreak the render-matrix gate for the new src-path hook + taplo formatting ([6eddbbd](https://github.com/nivintw/copier-everything/commit/6eddbbd5a295abe4bae51254e587caf95aed34f2))
* **hooks:** fail the harness on a crashed hook; clarify the 3.9 union-annotation note (Copilot) ([1b556ba](https://github.com/nivintw/copier-everything/commit/1b556baa890494736c0ddabfd424669e9fd2f9c4))
* **hooks:** keep the guard except-clauses parenthesized (portable) + share a dispatch helper ([18858d9](https://github.com/nivintw/copier-everything/commit/18858d90fd2c429afac6c7adcce5157c8ee06f85))
* **lychee:** require a subdomain on the pages.github.io exclude (Copilot review) ([a85d945](https://github.com/nivintw/copier-everything/commit/a85d945f3c9c7e8174d2ee3f2b3c51ef3443777c))
* **main:** split the stranded-Release-PR query and close the jq authorship gaps ([b4168db](https://github.com/nivintw/copier-everything/commit/b4168dbfadf1a3e3186e4859ea4c9c50c740d861))
* **refresh-checksums:** harden the tamper gate, port to bash 3.2, add a commit-pin class ([cfcee2d](https://github.com/nivintw/copier-everything/commit/cfcee2d54b2a820a46db48e7dea9a89d789e86af))
* **review:** close a tamper-gate bypass, a multi-package guard gap, and a close data-loss path ([cad4794](https://github.com/nivintw/copier-everything/commit/cad47949ef2e5e3355716f57b064726619f6c430))
* **template:** six generated-project correctness fixes (docs, forms, CI, updates) ([d16870b](https://github.com/nivintw/copier-everything/commit/d16870b0c6d95a040b756bfb8a8c31e4b237657e))

## [1.11.2](https://github.com/nivintw/copier-everything/compare/v1.11.1...v1.11.2) (2026-07-06)


### Bug Fixes

* **release:** join stranded Release PR numbers correctly for 3+ packages ([f25105d](https://github.com/nivintw/copier-everything/commit/f25105dd78966d647c5924d064204d71f9b47c93))
* **release:** make release-please auto-merge N-package-generic unconditionally ([69aec39](https://github.com/nivintw/copier-everything/commit/69aec39ebcad8a9289ed47fc55bd4f851920e7a2)), closes [#198](https://github.com/nivintw/copier-everything/issues/198)
* **release:** name the stranded Release PR(s) in the auto-merge-disabled warning ([4156cc0](https://github.com/nivintw/copier-everything/commit/4156cc0de7f93df137ef04cc8116cabf4c505030))

## [1.11.1](https://github.com/nivintw/copier-everything/compare/v1.11.0...v1.11.1) (2026-07-06)


### Bug Fixes

* address ruff findings CI caught that local prek didn't run ([2c8e4ca](https://github.com/nivintw/copier-everything/commit/2c8e4cadc21d966781b5afbc1e6455514793eb42))
* docs-site push trigger doesn't watch overrides/** ([1e6a73f](https://github.com/nivintw/copier-everything/commit/1e6a73fb1b92aa909d8b36f092bde7dbaf04698f)), closes [#192](https://github.com/nivintw/copier-everything/issues/192)
* harden pinned_value_at_base() against masked cat-file/show failures ([1106631](https://github.com/nivintw/copier-everything/commit/11066311338f79351e7711b7da8226888d59e67e)), closes [#193](https://github.com/nivintw/copier-everything/issues/193) [#191](https://github.com/nivintw/copier-everything/issues/191)
* non-bot-commit guard silently passed for unlinked-email commits ([a8da203](https://github.com/nivintw/copier-everything/commit/a8da203864cc8cec4b828275ff447282d84eac30))
* pinned_value_at_base regressed the exact case it was meant to protect ([0ba0129](https://github.com/nivintw/copier-everything/commit/0ba01299a8297e513b515ba8bb9564f599696868))
* restore asciinema-player mkdocs wiring dropped by the v1.10.0 baseline ([a071341](https://github.com/nivintw/copier-everything/commit/a071341e5b6d9dea8c32f19e3dd49f7a453908c8)), closes [#196](https://github.com/nivintw/copier-everything/issues/196)
* silence a shellcheck SC2094 false positive from the simplify refactor ([fbd5589](https://github.com/nivintw/copier-everything/commit/fbd558912241bc49ae0ba7e4ceeed7a5271933be))
* stranded-Release-PR closer can destroy human edits; label-hygiene TOCTOU gap ([02465aa](https://github.com/nivintw/copier-everything/commit/02465aacaef179d5de2550515d1f91917cbf6669)), closes [#195](https://github.com/nivintw/copier-everything/issues/195)
* widen rumdl per-file-ignores glob to cover nested docs subdirectories ([3804ba7](https://github.com/nivintw/copier-everything/commit/3804ba7b705dd22082b7134f7d51d9658b4c92fe)), closes [#194](https://github.com/nivintw/copier-everything/issues/194)

## [1.11.0](https://github.com/nivintw/copier-everything/compare/v1.10.1...v1.11.0) (2026-07-06)


### Features

* **template:** wire fleet docs-site features into include_docs_site ([dd3a33f](https://github.com/nivintw/copier-everything/commit/dd3a33fbbcc7883a082f23e2bae07d858f8a298c)), closes [#184](https://github.com/nivintw/copier-everything/issues/184)


### Bug Fixes

* bump the stale repo-management docs.yml pin, fix snippet MD041 ([884253b](https://github.com/nivintw/copier-everything/commit/884253b7dae6e7ea82cf41f879b665ba90bd37b0))
* stop hardcoding the template author's identity as the default answer ([327bc06](https://github.com/nivintw/copier-everything/commit/327bc0649542e3a640b9807a45b0ad8ca4fea2fc))
* **template:** stop docs-site tables mangling long identifiers ([f445a7f](https://github.com/nivintw/copier-everything/commit/f445a7fdcef1ff2bc914edddb0eb1999d2588b01))
* **test:** compare mkdocs.yml plugins by value, not just by name ([a95466a](https://github.com/nivintw/copier-everything/commit/a95466a775ca46388a5f75e131a9c5e14b54d9f3))
* **test:** pin year in the sync fixture, not just author identity ([7b7ef85](https://github.com/nivintw/copier-everything/commit/7b7ef85eeba7ec4e27cc76fb326e7ef709bac945))

## [1.10.1](https://github.com/nivintw/copier-everything/compare/v1.10.0...v1.10.1) (2026-07-06)


### Bug Fixes

* Four small template correctness/consistency fixes ([eeb074e](https://github.com/nivintw/copier-everything/commit/eeb074ebd12062a0ba4c9a2d521c0f9fa8c1eb80)), closes [#161](https://github.com/nivintw/copier-everything/issues/161) [#166](https://github.com/nivintw/copier-everything/issues/166) [#170](https://github.com/nivintw/copier-everything/issues/170) [#175](https://github.com/nivintw/copier-everything/issues/175)

## [1.10.0](https://github.com/nivintw/copier-everything/compare/v1.9.3...v1.10.0) (2026-07-06)


### Features

* **template:** fold fleet-general MkDocs Material improvements into docs-site baseline ([08c6b8c](https://github.com/nivintw/copier-everything/commit/08c6b8c38922e92e40da30cace82954ad70ca7d8))


### Bug Fixes

* Address review findings on the MkDocs Material migration ([a453b6f](https://github.com/nivintw/copier-everything/commit/a453b6f9ff466e459dd717a464f0be0e5300beb5))

## [1.9.3](https://github.com/nivintw/copier-everything/compare/v1.9.2...v1.9.3) (2026-07-06)


### Bug Fixes

* Close stranded Release PRs so release-please regenerates them ([219e6bf](https://github.com/nivintw/copier-everything/commit/219e6bfd286fdcd47528bbcc3fc9bf9c24718845)), closes [#183](https://github.com/nivintw/copier-everything/issues/183)

## [1.9.2](https://github.com/nivintw/copier-everything/compare/v1.9.1...v1.9.2) (2026-07-06)


### Bug Fixes

* Exclude CHANGELOG.md from typos, unblocking release-please auto-merge ([9d3ca09](https://github.com/nivintw/copier-everything/commit/9d3ca0912582de23e773720fa2fd02f93c09d2a7)), closes [#181](https://github.com/nivintw/copier-everything/issues/181)
* Fail loudly on a bad path in pinned_value() instead of masking it ([95e64e8](https://github.com/nivintw/copier-everything/commit/95e64e8c5c6a975f70e319d75268dbb2f9612982)), closes [#169](https://github.com/nivintw/copier-everything/issues/169)
* Gate rumdl's MD033 disable on include_docs_site ([1c1382d](https://github.com/nivintw/copier-everything/commit/1c1382d46846251b7ed2a8e28e148bf030401e51)), closes [#163](https://github.com/nivintw/copier-everything/issues/163)
* Harden the checksum tamper gate against silent degrade paths ([eef6ffe](https://github.com/nivintw/copier-everything/commit/eef6ffe1bf55ea57bb7540ecf63c8a43069ec877))
* Re-check issue state before stripping labels in label-hygiene ([3a31ee0](https://github.com/nivintw/copier-everything/commit/3a31ee0633c1df70549f8a3d9571f8bcfdabf929)), closes [#171](https://github.com/nivintw/copier-everything/issues/171)
* Set BASE_REF on checksum-refresh postUpgradeTask so the tamper gate is active ([65e5817](https://github.com/nivintw/copier-everything/commit/65e581797614422837c8233cc39eb5c48dec20ae)), closes [#165](https://github.com/nivintw/copier-everything/issues/165)
* Stop 404ing on unvendored asciinema assets, exclude dev-only docs/superpowers/** ([1ef6ec7](https://github.com/nivintw/copier-everything/commit/1ef6ec7d16f2748a2c55f6153b124ca97b74fb27)), closes [#172](https://github.com/nivintw/copier-everything/issues/172) [#162](https://github.com/nivintw/copier-everything/issues/162)
* Sync root's label-hygiene.yml with the [#171](https://github.com/nivintw/copier-everything/issues/171) reopen-race fix ([21caf01](https://github.com/nivintw/copier-everything/commit/21caf01b4a8acbccc7948ff2674828791b20cea1))
* Trigger approve-bot-prs on pull_request_target, not pull_request ([4a87894](https://github.com/nivintw/copier-everything/commit/4a878947986c5f10a60c4638dc0bd6cc182ee369)), closes [#174](https://github.com/nivintw/copier-everything/issues/174)

## [1.9.1](https://github.com/nivintw/copier-everything/compare/v1.9.0...v1.9.1) (2026-07-05)


### Bug Fixes

* Handle both on:/True key representations in docs.yml test ([4e00a76](https://github.com/nivintw/copier-everything/commit/4e00a76cacc1ed65101768a069d38042ada098a7))
* Parse rendered docs.yml as YAML instead of substring-matching triggers ([63adc39](https://github.com/nivintw/copier-everything/commit/63adc392ec01a2066b38687864686bcb088d73d9))
* Re-add push trigger to docs.yml caller now that repo-management[#86](https://github.com/nivintw/copier-everything/issues/86) shipped ([c7ab066](https://github.com/nivintw/copier-everything/commit/c7ab066154bb5dbbb5a3f736e19661c48ff34958)), closes [#160](https://github.com/nivintw/copier-everything/issues/160)

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
