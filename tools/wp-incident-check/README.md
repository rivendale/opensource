# Check an offline WordPress copy for published incident indicators

This tool checks files you supply for the published Rank Math PRO 3.0.123 indicators.
It uses the existing YARA engine. It does not repair a site, contact a website, execute PHP
or connect to a database. A clean result does not prove a site clean.

Use Linux or Ubuntu under WSL, Python 3.11 or newer, and a local copy owned by your user.
Run on an offline backup/snapshot, not a busy live site. Keep exports private: they may
contain passwords and personal information. Do not upload them to an agent or this repo.
Reading is restricted to regular files and directories; symlinks are skipped and reported.
Linux no-atime reads preserve the supplied evidence's access timestamps. Unsupported
systems, permissions or missing inputs produce a partial result, not a clean certificate.

## Install

Candidate code, awaiting independent review. Installing the binding runs third-party code;
use this exact version in its own environment. See the [safe setup checklist](../../ai/graphics.md#safe-setup-checklist).
The commands below pin the candidate implementation for review. Independent review is
still required before release; this is not a released security tool.

```bash
git clone --branch wp-incident-check https://github.com/rivendale/opensource.git wp-incident-review
cd wp-incident-review
git checkout --detach 8ac1cd6a96228d608518d986d4c3c5b43bb8df1c
python3 -m venv .wp-check-venv
.wp-check-venv/bin/python -m pip install --only-binary=:all: -r tools/wp-incident-check/requirements.txt
```

[Scanner selection and licenses](SCANNER-SELECTION.md) explains why Wordfence CLI is unsuitable
for new users and why the local YARA binding is used instead. No Wordfence account or API key
is needed. YARA matching is offline; installation downloads the pinned package from PyPI.

## Get a copy of your site and database

Download a backup of the site's files and database from your host. Extract the files into a
new local directory that you own, for example `/home/you/site-copy`. Keep the SQL export
outside that directory. The program reads plain, uncompressed SQL as text; it never imports it.

- **cPanel:** open Backup Wizard, choose Backup, then a database backup. Download the site's
  file backup too. See the [host control-panel guide](https://docs.cpanel.net/cpanel/files/backup-wizard/).
- **Hosts with phpMyAdmin:** select your site's database, choose Export, then Quick and SQL.
  Download the file. The [WordPress database backup guide](https://developer.wordpress.org/advanced-administration/security/backup/database/)
  explains this workflow. Table prefixes do not have to be `wp_` for these text checks.
- **Managed hosts:** use the dashboard's downloadable backup/export feature. If it only offers
  a restore button, ask support for an offline files backup and plain SQL export. Do not
  enter a database password on this tool's command line; it has no live-DB mode.

Decompress `.gz`/`.zip` backups locally first. Do not restore or execute them to scan them.
Files above 8 MiB, more than 10,000 files, 256 MiB total, excessive depth or a time limit
make coverage partial. Large database exports will need a different investigation path;
this small checker does not silently certify the unexamined remainder.

## Run the basic check

Replace both paths with your own local copies. The flag means you own the site or have its
owner's permission. Without it, the tool refuses before it reads inputs or loads the scanner.

```bash
.wp-check-venv/bin/python tools/wp-incident-check/wp-incident-check \
  --authorized-owner --site /home/you/site-copy \
  --database-export /home/you/site.sql
```

Expect a **PARTIAL** report from this basic command. It does not supply server crontabs,
SSH keys, a trusted key baseline or installation history. The report names those gaps.
A shared-hosting user may need the host's security team to investigate server-level evidence.
There is no requirement to give this tool live server access.

Optional owner-supplied evidence can be added with these path options:

- `--cron-export /path/to/crontab.txt`: a saved crontab, not a shell command to execute.
- `--ssh-keys /path/to/authorized_keys-copy --known-ssh-keys /path/to/trusted-public-keys`:
  compare the snapshot's public keys with a baseline you independently trust. No private keys.
- `--plugin-version 3.0.123 --installed-at 2026-10-16T01:00:00+00:00`: version and timestamp
  from your historical install/update record. A current version or file mtime does not prove
  which version was activated in the incident window. Always include the timezone.

## Read the report

`Checked` names examined inputs. `Potential indicator` means a published string or update
window matched; it is not a confirmed active administrator, database option or malicious intent.
Database exports can contain comments, old rows and backups. Confirm context before cleanup.
`Unexpected SSH keys` means only that keys differ from your supplied baseline; key contents
are never printed. `Not checked` and **PARTIAL** mean investigation is incomplete.

Exit codes: **0** no listed indicators in all supplied evidence categories; **1** indicators
found with those categories checked; **2** partial/error, whether or not indicators were found;
**64** missing explicit owner authorization. No automatic repair occurs at any exit code.
Output goes to your terminal. If you redirect it, choose a private file outside the site copy.

If something is found, preserve the evidence and follow the
[vendor's recovery steps](https://rankmath.com/kb/pro-3-0-123-security-incident/) in order with
your host/security professional. A pre-incident backup is the vendor's preferred recovery
route. Stop persistence before cleanup, replace exposed credentials and verify recovery.
This tool does none of those actions. Known indicator absence is not proof of a clean host.

## Validate this checkout

```bash
.wp-check-venv/bin/python -B tools/wp-incident-check/tests/test_check.py
```

The tests create synthetic sites and use the real pinned YARA binding. No real website,
export, credential or callback domain is contacted. [Failure list](FAILURES.md).
