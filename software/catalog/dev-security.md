# Developer tools and security

Package managers, linters, scanners, supply-chain checks and command-line tools. 27 projects; 22 with a permissive code license. Sorted by reuse, then stars. Part of the [software list](../README.md), which explains the reuse classes.

| project | reuse | license | language | stars | last push | why |
|---|---|---|---|---|---|---|
| [astral-sh/uv](https://github.com/astral-sh/uv) | copy | Apache-2.0 | Rust | 90292 | 2026-09-29 | Very fast Python package and project manager. |
| [nektos/act](https://github.com/nektos/act) | copy | MIT | Go | 72164 | 2026-08-09 | Run GitHub Actions workflows locally. |
| [BurntSushi/ripgrep](https://github.com/BurntSushi/ripgrep) | copy | Unlicense | Rust | 68707 | 2026-08-04 | Fast recursive search that respects ignore files. |
| [astral-sh/ruff](https://github.com/astral-sh/ruff) | copy | MIT | Rust | 49847 | 2026-09-29 | Very fast Python linter and formatter. |
| [mitmproxy/mitmproxy](https://github.com/mitmproxy/mitmproxy) | copy | MIT | Python | 45194 | 2026-09-27 | Intercepting proxy to see exactly what an app sends over the network. |
| [duckdb/duckdb](https://github.com/duckdb/duckdb) | copy | MIT | C++ | 41796 | 2026-09-29 | In-process analytical SQL that queries CSV, Parquet and JSON files in place; answers questions about a big export without loading a database. |
| [aquasecurity/trivy](https://github.com/aquasecurity/trivy) | copy | Apache-2.0 | Go | 38136 | 2026-09-29 | Scanner for vulnerabilities, misconfigurations and secrets in images, repos and IaC. |
| [jqlang/jq](https://github.com/jqlang/jq) | copy (see note) | MIT (per license file) | C | 35722 | 2026-09-27 | Command-line JSON processor. **docs/ is CC-BY-3.0; bundled dtoa, decNumber (ICU) and BSD-2-Clause files keep their own notices** |
| [projectdiscovery/nuclei](https://github.com/projectdiscovery/nuclei) | copy | MIT | Go | 31625 | 2026-09-29 | Template-driven vulnerability scanner for your own services. |
| [gitleaks/gitleaks](https://github.com/gitleaks/gitleaks) | copy | MIT | Go | 29557 | 2026-09-23 | Scans commits and git history for secrets; fast enough for a pre-commit hook and a CI gate. |
| [pre-commit/pre-commit](https://github.com/pre-commit/pre-commit) | copy | MIT | Python | 15603 | 2026-09-29 | Framework for managing git pre-commit hooks across languages. |
| [crowdsecurity/crowdsec](https://github.com/crowdsecurity/crowdsec) | copy | MIT | Go | 15004 | 2026-09-29 | Collaborative intrusion detection and IP blocking for exposed services. |
| [anchore/grype](https://github.com/anchore/grype) | copy | Apache-2.0 | Go | 12952 | 2026-09-29 | Vulnerability scanner that consumes SBOMs or images. |
| [google/osv-scanner](https://github.com/google/osv-scanner) | copy | Apache-2.0 | Go | 11119 | 2026-09-29 | Checks lockfiles against the OSV vulnerability database. |
| [anchore/syft](https://github.com/anchore/syft) | copy | Apache-2.0 | Go | 9626 | 2026-09-29 | Generates software bills of materials from images and filesystems. |
| [mvdan/sh](https://github.com/mvdan/sh) | copy | BSD-3-Clause | Go | 9097 | 2026-09-29 | Shell parser and formatter (shfmt). |
| [vercel-labs/deepsec](https://github.com/vercel-labs/deepsec) | copy | Apache-2.0 | TypeScript | 8056 | 2026-09-29 | Security scanner that points coding agents at a whole repository and revalidates each finding; it runs on your machines, but code goes to your model. |
| [zizmorcore/zizmor](https://github.com/zizmorcore/zizmor) | copy | MIT | Rust | 6604 | 2026-09-29 | Static analysis for GitHub Actions workflow security bugs. |
| [sigstore/cosign](https://github.com/sigstore/cosign) | copy | Apache-2.0 | Go | 6337 | 2026-09-29 | Sign and verify container images and artifacts. |
| [bats-core/bats-core](https://github.com/bats-core/bats-core) | copy | MIT (per license file) | Shell | 6290 | 2026-09-26 | Test runner for Bash scripts, suited to end-to-end script checks. |
| [ossf/scorecard](https://github.com/ossf/scorecard) | copy | Apache-2.0 | Go | 5723 | 2026-09-29 | Scores a repository's supply-chain security practices; useful before adopting a dependency. |
| [rhysd/actionlint](https://github.com/rhysd/actionlint) | copy | MIT | Go | 4278 | 2026-07-16 | Linter for GitHub Actions workflow files. |
| [semgrep/semgrep](https://github.com/semgrep/semgrep) | library use | LGPL-2.1 | C | 16793 | 2026-09-29 | Fast pattern-based static analysis with community rules. |
| [koalaman/shellcheck](https://github.com/koalaman/shellcheck) | study only | GPL-3.0 | Haskell | 40099 | 2026-09-26 | Static analysis for shell scripts; catches quoting and pipefail mistakes. |
| [trufflesecurity/trufflehog](https://github.com/trufflesecurity/trufflehog) | study only | AGPL-3.0 | Go | 28187 | 2026-09-29 | Finds leaked credentials in git, buckets and chat exports and checks whether each key is still live, which sorts real leaks from noise. |
| [wireshark/wireshark](https://github.com/wireshark/wireshark) | study only | GPL-2.0 | C | 9944 | 2026-09-29 | The standard network protocol analyzer: capture and inspect traffic to find bandwidth hogs, unknown devices and suspicious connections. |
| [nmap/nmap](https://github.com/nmap/nmap) | check first | Nmap Public Source License 0.95 (per license file) | C | 13689 | 2026-09-28 | Scans a network for devices, open ports and running services; the standard way to audit what is actually listening on a home or office network. **free to run as it ships; the NPSL adds terms beyond GPLv2, including limits on bundling Nmap into commercial products without a license from its authors** |

A license marked *per license file* was read from the repository's own license files, because GitHub's detector could not classify it or reported only part of it; the file and the reason are recorded in [tools/overrides.json](../../tools/overrides.json).
