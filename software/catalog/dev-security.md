# Developer tools and security

Package managers, linters, scanners, supply-chain checks and command-line tools. 24 projects; 21 with a permissive code license. Sorted by reuse, then stars. Part of the [software list](../README.md), which explains the reuse classes.

| project | reuse | license | language | stars | last push | why |
|---|---|---|---|---|---|---|
| [astral-sh/uv](https://github.com/astral-sh/uv) | copy | Apache-2.0 | Rust | 90200 | 2026-09-26 | Very fast Python package and project manager. |
| [nektos/act](https://github.com/nektos/act) | copy | MIT | Go | 72117 | 2026-08-09 | Run GitHub Actions workflows locally. |
| [BurntSushi/ripgrep](https://github.com/BurntSushi/ripgrep) | copy | Unlicense | Rust | 68630 | 2026-08-04 | Fast recursive search that respects ignore files. |
| [astral-sh/ruff](https://github.com/astral-sh/ruff) | copy | MIT | Rust | 49804 | 2026-09-26 | Very fast Python linter and formatter. |
| [mitmproxy/mitmproxy](https://github.com/mitmproxy/mitmproxy) | copy | MIT | Python | 45157 | 2026-09-10 | Intercepting proxy to see exactly what an app sends over the network. |
| [duckdb/duckdb](https://github.com/duckdb/duckdb) | copy | MIT | C++ | 41720 | 2026-09-25 | In-process analytical SQL that queries CSV, Parquet and JSON files in place; answers questions about a big export without loading a database. |
| [aquasecurity/trivy](https://github.com/aquasecurity/trivy) | copy | Apache-2.0 | Go | 38086 | 2026-09-25 | Scanner for vulnerabilities, misconfigurations and secrets in images, repos and IaC. |
| [jqlang/jq](https://github.com/jqlang/jq) | copy | MIT (per license file) | C | 35699 | 2026-09-25 | Command-line JSON processor. **docs/ is CC-BY-3.0; bundled dtoa, decNumber (ICU) and BSD-2-Clause files keep their own notices** |
| [projectdiscovery/nuclei](https://github.com/projectdiscovery/nuclei) | copy | MIT | Go | 31547 | 2026-09-26 | Template-driven vulnerability scanner for your own services. |
| [gitleaks/gitleaks](https://github.com/gitleaks/gitleaks) | copy | MIT | Go | 29498 | 2026-09-23 | Scans commits and git history for secrets; fast enough for a pre-commit hook and a CI gate. |
| [pre-commit/pre-commit](https://github.com/pre-commit/pre-commit) | copy | MIT | Python | 15595 | 2026-08-17 | Framework for managing git pre-commit hooks across languages. |
| [crowdsecurity/crowdsec](https://github.com/crowdsecurity/crowdsec) | copy | MIT | Go | 14977 | 2026-09-25 | Collaborative intrusion detection and IP blocking for exposed services. |
| [anchore/grype](https://github.com/anchore/grype) | copy | Apache-2.0 | Go | 12932 | 2026-09-25 | Vulnerability scanner that consumes SBOMs or images. |
| [google/osv-scanner](https://github.com/google/osv-scanner) | copy | Apache-2.0 | Go | 11092 | 2026-09-26 | Checks lockfiles against the OSV vulnerability database. |
| [anchore/syft](https://github.com/anchore/syft) | copy | Apache-2.0 | Go | 9613 | 2026-09-25 | Generates software bills of materials from images and filesystems. |
| [mvdan/sh](https://github.com/mvdan/sh) | copy | BSD-3-Clause | Go | 9089 | 2026-09-22 | Shell parser and formatter (shfmt). |
| [zizmorcore/zizmor](https://github.com/zizmorcore/zizmor) | copy | MIT | Rust | 6580 | 2026-09-26 | Static analysis for GitHub Actions workflow security bugs. |
| [sigstore/cosign](https://github.com/sigstore/cosign) | copy | Apache-2.0 | Go | 6330 | 2026-09-24 | Sign and verify container images and artifacts. |
| [bats-core/bats-core](https://github.com/bats-core/bats-core) | copy | MIT (per license file) | Shell | 6287 | 2026-09-26 | Test runner for Bash scripts, suited to end-to-end script checks. |
| [ossf/scorecard](https://github.com/ossf/scorecard) | copy | Apache-2.0 | Go | 5711 | 2026-09-25 | Scores a repository's supply-chain security practices; useful before adopting a dependency. |
| [rhysd/actionlint](https://github.com/rhysd/actionlint) | copy | MIT | Go | 4265 | 2026-07-16 | Linter for GitHub Actions workflow files. |
| [semgrep/semgrep](https://github.com/semgrep/semgrep) | library use | LGPL-2.1 | C | 16774 | 2026-09-25 | Fast pattern-based static analysis with community rules. |
| [koalaman/shellcheck](https://github.com/koalaman/shellcheck) | study only | GPL-3.0 | Haskell | 40090 | 2026-09-26 | Static analysis for shell scripts; catches quoting and pipefail mistakes. |
| [trufflesecurity/trufflehog](https://github.com/trufflesecurity/trufflehog) | study only | AGPL-3.0 | Go | 28076 | 2026-09-26 | Finds leaked credentials in git, buckets and chat exports and checks whether each key is still live, which sorts real leaks from noise. |

A license marked *per license file* was read from the repository's own license files, because GitHub's detector could not classify it or reported only part of it; the file and the reason are recorded in [tools/overrides.json](../../tools/overrides.json).
