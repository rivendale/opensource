# wp-incident-check failure list first

Failure contract recorded before implementation; synthetic CLI controls now accompany it.

1. Reading the site, export or launching a scanner before explicit owner authorization.
2. Claiming read-only while the wrapper, scanner, WordPress hooks or database can modify evidence.
3. Executing PHP, WordPress, uploaded code, SQL from an export, or an incident rule as instructions.
4. A symlink, traversal path, special file or concurrent replacement escapes the supplied snapshot.
5. A scanner's crash, timeout, missing license/signatures, skipped or unreadable file becomes a clean result.
6. Missing export, cron, install/update history or SSH baseline is hidden instead of reported as not checked.
7. A synthetic clean site is flagged; a planted public indicator is missed; an unexamined partial site is called clean.
8. Prefix-only account text is called a confirmed administrator without role evidence.
9. File timestamps substitute for authenticated installation history; timezone/window boundaries are wrong.
10. Known options, account prefixes, cron markers or domains appear in comments/backups and are called active compromise.
11. SSH keys are called unexpected without the owner's baseline, or full key material is printed.
12. Database passwords, raw export contents, client data or matched secret-bearing lines enter argv, logs or the report.
13. A scanner's default recursive mode follows symlinks outside the site.
14. Compiled/untrusted rules, arbitrary commands or attacker-supplied remediations are executed.
15. Cleanup runs automatically, alters the database, rotates keys or disables an account.
16. A clean indicator result is described as proof of safety or as a substitute for broader incident response.
17. No source URL/date is recorded, or an incident rule silently changes its source or meaning.
18. A catalog entry or install guide claims a runnable tool exists while scanner selection is still a proposal.

Before implementation, independent synthetic fixtures must cover one clean snapshot, every
indicator individually, combined indicators and partial inputs. Record file content hashes,
metadata and database-export bytes before/after every run. Add an owner-flag refusal that
proves the scanner was not launched and no evidence was read or written.

Review regression contract, 2026-10-20, before fixes:

19. Compressed, UTF-16 or NUL-bearing exports are called checked/clean without decoding.
20. Site file/byte/time budgets prevent database or cron inspection, or blame an export for a site cap.
21. Large plain exports or a literal split across read chunks evade matching.
22. Domain case changes evade matching; published indicators outside this bounded rule set are not named.
23. Installation instructions select stale code, imply unsupported platforms or conceal what PARTIAL requires next.
