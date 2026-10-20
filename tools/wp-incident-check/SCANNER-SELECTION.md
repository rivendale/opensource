# WordPress incident checker: scanner selection

Decision, 2026-10-20: Wordfence CLI is unsuitable as the default for a new site owner.
Use YARA for local indicator matching. The wrapper implements the conservative scope below;
its results are indicators, not a complete malware scan or proof of compromise.

## Wordfence prerequisite result

The [source license](https://github.com/wordfence/wordfence-cli/blob/main/LICENSE) is GPLv3.
Its [service terms, section 3](https://www.wordfence.com/wordfence-cli-license-terms-and-conditions/)
distinguish the CLI code license from access to the hosted API. An open code license does
not by itself supply access to that service.

The [official repository notice](https://github.com/wordfence/wordfence-cli#wordfence-cli)
says no new Free or Premium licenses are available. Free licenses expired October 14, 2026;
existing Premium access ends with the current term and will not renew. The older product
page still describes Free/Commercial options, so it is not a sufficient current install path.
The suitability problem is service availability for new users, not a prohibition on using GPL code.
No license was obtained, terms accepted, API called or scanner installed in this investigation.

## Proposed alternative: wrap YARA locally

Use the existing [YARA engine](https://github.com/VirusTotal/yara), which has a
[BSD three-clause license](https://github.com/VirusTotal/yara/blob/master/COPYING).
It matches rules against local files without requiring Wordfence's service. Keep it an
external dependency; do not copy scanner code or invent a malware-detection engine.
The Python binding is [Apache-2.0 licensed](https://github.com/VirusTotal/yara-python/blob/master/LICENSE);
its wheel includes the YARA engine. No third-party scanner source is copied into this repository.

Keep the originally requested JSON incident files, with source URLs and a checked date.
Translate their bounded literal/prefix indicators into trusted YARA source rules, never
third-party compiled rules or arbitrary executable rule commands. Use local source rules,
no string dumps, an explicit time bound and no-follow-symlink mode. The
[official CLI documentation](https://yara.readthedocs.io/en/stable/commandline.html)
describes source rules, recursion, symlink controls and timeouts. The binding is pinned to 4.5.4; tests exercise in-memory source rules against the real engine.

The first version accepts an offline site snapshot and a plain database export only.
Do not execute WordPress, PHP, SQL or an installer from the supplied material. It
requires an explicit owner-authorization flag before reading inputs or starting the engine.
Reports go to stdout; no repair, quarantine, in-place update or database connection occurs.
Run against a read-only snapshot/mount to enforce the no-evidence-write boundary.

YARA is a pattern engine, not WordPress account or SQL semantics. A raw export match is a
potential indicator, not proof of an active option or administrator. Correlation with user
roles and active rows would remain explicitly unverified unless a bounded export parser is
independently tested. Missing exports, scanner failures, skipped paths and unavailable server
state must produce a partial/error report, never a clean result.

## Incident scope to carry into implementation

Use only the [vendor's published incident advisory](https://rankmath.com/kb/pro-3-0-123-security-incident/).
The initial rule covers the stated download/update window and public option names,
account prefix, cron marker and callback-domain indicators from canonical T47. Match local
references only; never contact the callback domain. Installation history requires owner
records; filesystem timestamps alone do not prove install time. Unexpected SSH keys require
a trusted baseline and separately supplied server evidence. Site files alone cannot establish
the host's keys, crontabs or running-process state.

A future report must say what was checked, what matched and what was unavailable, without
printing export rows, credentials or key contents. It must link the vendor's ordered recovery
steps and distinguish advice from actions performed. A clean result does not prove a site clean.
Broader incident response, restoring a known-good backup and replacing exposed secrets remain
site-owner work. The wrapper never performs remediation.

## Before any runnable release

Use [FAILURES.md](FAILURES.md) as the contract. Build synthetic clean, individually planted,
combined and partial cases first. Assert authorization refusal, unchanged snapshot/export
bytes and metadata, no network, no execution and partial-result handling. Test against the
real selected scanner as well as failure stubs. Provide a novice README for exporting a
database through common hosts and reading the report; add the catalog entry only when the
tool actually runs. The synthetic tests exercise the real pinned YARA binding, per-indicator matches, partial
inputs, authorization refusal, no execution/network and unchanged input metadata.

The selected engine, wrapper and incident rules require independent review.
