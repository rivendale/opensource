# Personal finance

Budgeting, plain-text accounting, invoicing and investment tracking. 23 projects; 9 with a permissive code license. Sorted by reuse, then stars. Part of the [software list](../README.md), which explains the reuse classes.

| project | reuse | license | language | stars | last push | why |
|---|---|---|---|---|---|---|
| [OpenBB-finance/OpenBB](https://github.com/OpenBB-finance/OpenBB) | copy (see note) | Apache-2.0 (per license file) | Python | 73697 | 2026-09-30 | Open data platform that pulls market, economic and company data from many providers into Python, a CLI and AI agents; providers see what you query. **the data providers you configure see which symbols you query** |
| [actualbudget/actual](https://github.com/actualbudget/actual) | copy | MIT | TypeScript | 29231 | 2026-09-29 | Local-first envelope budgeting with optional sync server. |
| [ledger/ledger](https://github.com/ledger/ledger) | copy | BSD-3-Clause (per license file) | C++ | 6045 | 2026-09-22 | The original plain-text double-entry accounting CLI. |
| [mayswind/ezbookkeeping](https://github.com/mayswind/ezbookkeeping) | copy | MIT | Go | 5688 | 2026-09-30 | Lightweight self-hosted personal bookkeeping app. |
| [IRS-Public/direct-file](https://github.com/IRS-Public/direct-file) | copy (see note) | CC0-1.0 (per license file) | JavaScript | 4584 | 2026-06-11 | The IRS's free filing app, released into the public domain; archived and unmaintained, but its Fact Graph shows how to reason over a partial return. **its README says it is archived, no longer maintained and not for production; read it for the Fact Graph design** |
| [beancount/fava](https://github.com/beancount/fava) | copy | MIT | Python | 2582 | 2026-09-30 | Web interface for Beancount ledgers. |
| [beancount/smart_importer](https://github.com/beancount/smart_importer) | copy | MIT | Python | 308 | 2026-07-26 | Adds machine learning to Beancount importers: it predicts the missing account of each imported transaction from your existing entries. |
| [csingley/ibflex](https://github.com/csingley/ibflex) | copy | MIT | Python | 119 | 2026-09-08 | Python parser for Interactive Brokers Flex XML statements that turns trades, cash and positions into typed Python objects. |
| [mmacpherson/tenforty](https://github.com/mmacpherson/tenforty) | copy (see note) | MIT | C++ | 84 | 2026-09-28 | Python library that computes US federal and some state income tax for 2018 to 2025 on OpenTaxSolver, for what-if scenarios and cross-checks. **its README says Medicare and Net Investment Income Tax are not computed on capital gains (so tax can be understated), only California is tested against professionally prepared returns, and Windows is unsupported (WSL works); use it as a cross-check, not the return** |
| [portfolio-performance/portfolio](https://github.com/portfolio-performance/portfolio) | library use | EPL-1.0 | Java | 4081 | 2026-09-30 | Desktop investment tracker that computes time-weighted and money-weighted returns across accounts and imports broker statements. |
| [firefly-iii/firefly-iii](https://github.com/firefly-iii/firefly-iii) | study only | AGPL-3.0 | PHP | 24784 | 2026-09-30 | Self-hosted personal finance manager with rules and reports. |
| [we-promise/sure](https://github.com/we-promise/sure) | study only | AGPL-3.0 | Ruby | 10347 | 2026-09-30 | Community-maintained continuation of the archived Maybe personal finance app. |
| [ghostfolio/ghostfolio](https://github.com/ghostfolio/ghostfolio) | study only | AGPL-3.0 | TypeScript | 9388 | 2026-09-30 | Self-hosted portfolio and net-worth tracker. |
| [wealthfolio/wealthfolio](https://github.com/wealthfolio/wealthfolio) | study only | AGPL-3.0 | Rust | 9086 | 2026-09-30 | Local desktop investment tracker. |
| [beancount/beancount](https://github.com/beancount/beancount) | study only | GPL-2.0 | Python | 6039 | 2026-08-23 | Plain-text double-entry accounting in Python. |
| [hledgerorg/hledger](https://github.com/hledgerorg/hledger) | study only | GPL-3.0 | Haskell | 4737 | 2026-09-30 | Plain-text accounting tool, fast and robust. |
| [Gnucash/gnucash](https://github.com/Gnucash/gnucash) | study only | GPL-2.0-or-later (per license file) | C | 4364 | 2026-09-29 | Desktop double-entry accounting for households and small businesses. |
| [rotki/rotki](https://github.com/rotki/rotki) | study only | AGPL-3.0 | Python | 4039 | 2026-09-30 | Portfolio tracker and accounting app that keeps its database local and encrypted; it still queries chain and exchange APIs with your addresses and keys. |
| [firefly-iii/data-importer](https://github.com/firefly-iii/data-importer) | study only | AGPL-3.0 | PHP | 839 | 2026-09-30 | Imports CSV, CAMT.052 and CAMT.053 bank statements into Firefly III, with saved mapping rules for each bank's file layout. |
| [csingley/ofxtools](https://github.com/csingley/ofxtools) | study only | GPL-3.0-or-later (per license file) | Python | 345 | 2026-08-01 | Python library for OFX, the format banks and brokers use for statement downloads: parses files into objects and builds OFX requests. |
| [beancount/beangulp](https://github.com/beancount/beangulp) | study only | GPL-2.0 | Python | 145 | 2026-05-30 | Beancount's framework for importers that turn bank and card statement files into ledger entries, which balance assertions can then check. |
| [invoiceninja/invoiceninja](https://github.com/invoiceninja/invoiceninja) | check first | Elastic-2.0 (per license file) | PHP | 10174 | 2026-09-29 | Invoicing, quotes and payments platform. |
| [akaunting/akaunting](https://github.com/akaunting/akaunting) | check first | BUSL-1.1 (per license file) | PHP | 10153 | 2026-09-29 | Online accounting for small businesses. |

A license marked *per license file* was read from the repository's own license files, because GitHub's detector could not classify it or reported only part of it; the file and the reason are recorded in [tools/overrides.json](../../tools/overrides.json).
