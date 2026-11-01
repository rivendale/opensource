# Repository hygiene checks

One check shared by the rivendale open-source repos: [`repo_hygiene.py`](repo_hygiene.py) (standard library only)
and the reusable workflow [`.github/workflows/hygiene.yml`](../../.github/workflows/hygiene.yml).

| Check | Fails when |
|---|---|
| `modes` | a tracked file with a shebang went from 100755 to 100644 since the base commit (a push through the GitHub API resets modes). A rename git does not pair because the file was also rewritten counts too: a deleted 100755 file and an added 100644 file with a shebang in the same directory, or with the same name |
| `invisible` | a tracked text file or path holds a raw character a reader cannot see: any format (Cf) or control (Cc) character except tab, newline, carriage return, form feed and vertical tab (the `strip_hidden()` set in [`tools/build_catalog.py`](../build_catalog.py), without the other controls `isspace()` lets through), the U+E0000 tag block, the Hangul fillers U+115F, U+1160, U+3164 and U+FFA0, the braille blank U+2800 and the combining grapheme joiner U+034F. A variation selector (U+FE00 to U+FE0F, U+E0100 to U+E01EF) fails unless it directly follows a symbol or emoji, a keycap base, or a CJK or other variant-bearing character. A byte order mark at the very start of a file is allowed. A file that is not valid UTF-8 fails, and is still scanned. Binary files are skipped the way git decides: a NUL byte in the first 8000 bytes, or `-text` or `binary` in `.gitattributes`. Path names are always checked, even on the allow-list |
| `claims` | a number written in a file disagrees with a count taken from the repo |
| `stale` | a dated marker such as "checked 2026-09-24" is older than `max_age_days`. Fenced code blocks are skipped. A warning unless `stale_fails` is true |
| `instructions` | an agent instruction file is over its byte limit, or its sentinel line is missing or not the last line |
| root safety (workflow job, [`root_safety.sh`](root_safety.sh)) | a `root_safety` command fails; or, while it runs as root, deletes or changes the mode, owner, type or symlink target of anything under `/bin`, `/sbin`, `/usr/bin`, `/usr/sbin`, `/usr/local/bin`, `/usr/lib`, `/usr/libexec`, `/usr/local/lib`, `/usr/share`, `/opt`, `/etc`, `/root` or `/home`, or changes the content of a file in `/usr/bin`, `/usr/local/bin` or `/bin` (a write through a symlink). A snapshot that cannot be taken or compared fails too. New files are fine |

```
python3 tools/hygiene/repo_hygiene.py --base origin/main     # every check; exit 1 on a failure, 2 on a bad config
python3 tools/hygiene/repo_hygiene.py --selftest             # plants each defect in a temp git repo, no network
python3 tools/hygiene/repo_hygiene.py --print-root-safety    # the config's root_safety commands
python3 tests/tools/test_repo_hygiene.py                     # command-line and root_safety.sh tests (this repo)
```

Write an invisible character as an escape (a `\u` escape in code and JSON, an HTML entity in markdown). A file that holds
one on purpose, such as a test fixture, goes on `invisible_allow` with the reason.

## Adopting it in another repo

1. Pick a commit of this repo's `main` that has the version you want, and use its full 40-character SHA twice: in
   `uses:` and as `hygiene_ref`. A workflow called from another repo cannot tell which commit it was called at, so the
   tool checkout needs the SHA passed in; a tag or branch is refused.
2. Add `.github/workflows/hygiene.yml` to your repo:

   ```yaml
   name: hygiene
   on:
     pull_request:
     push:
       branches: [main]
   permissions:
     contents: read
   jobs:
     hygiene:
       uses: rivendale/opensource/.github/workflows/hygiene.yml@<sha>
       with:
         hygiene_ref: <sha>
   ```

3. Add `.hygiene.json` at the repo root (schema below), run the tool locally against a checkout of this repo,
   and fix or allow-list what it finds:

   ```
   python3 /path/to/opensource/tools/hygiene/repo_hygiene.py --root . --base origin/main
   ```

4. To move to a newer version, change both SHAs in one commit.
5. Put `.hygiene.json` under CODEOWNERS, so a change that widens an allow-list or turns a check off needs a
   maintainer's review. On a pull request the tool also prints a notice (not a failure) for each way the change
   loosens the config compared with the base: a check turned off, an allow-list or exclusion added, a claim,
   instruction check or root_safety command dropped, a longer `max_age_days`, a changed `stale_pattern`.

The workflow has two jobs. `static` checks out your repo with full history (the mode check needs the base commit),
then the tool at `hygiene_ref`, runs the selftest and then the checks. The base is the pull request's base commit, a
merge group's base, or the commit before a push; when that is missing or all zeros (a new branch) it falls back to the
default branch. `root-safety` runs each `root_safety` command as root in a throwaway `python:3.12` container with no
network (loopback works, so local stub servers are fine), on a copy of your repo. The image is pinned by digest
(the 2026-10-28 `python:3.12` index; mirror.gcr.io and public.ecr.aws/docker/library gave the same digest, Docker Hub
itself was rate-limited when checked). A run without `hygiene_ref` outside this repo fails. Both jobs have `contents: read` and
check out with `persist-credentials: false`; no token reaches the container.

## `.hygiene.json`

Every key is optional. A key starting with `_` is a comment, at any level. An unknown key is an error, so a typo
does not turn a check off.

| Key | Type | Default | Meaning |
|---|---|---|---|
| `modes` | bool | `true` | run the executable-bit check |
| `invisible` | bool | `true` | run the invisible-character check |
| `invisible_allow` | list of globs | `[]` | paths whose content the invisible check skips (their names are still checked); a glob of only `*` and `/` is refused |
| `claims` | list of claims | `[]` | numbers to check, see below |
| `stale` | bool | `true` | run the stale-marker check |
| `stale_pattern` | regex | `\b(?:checked\|verified\|as of)[:\s]+(\d{4}-\d{2}-\d{2})\b` | case-insensitive; group 1 captures the date |
| `stale_globs` | list of globs | `["**/*.md"]` | files the stale check reads; keep it to docs |
| `stale_exclude` | list of globs | `[]` | files the stale check skips (generated pages, fixtures, dated logs); a glob of only `*` and `/` is refused |
| `max_age_days` | int | `45` | a marker older than this is stale |
| `stale_fails` | bool | `false` | a stale marker fails instead of warning |
| `instructions` | list | `[]` | `{"file": "AGENTS.md", "max_bytes": 32768, "sentinel": "..."}`; `max_bytes` defaults to 32768, `sentinel` is optional and must be the last non-blank line |
| `root_safety` | list of strings | `[]` | one-line shell commands the workflow runs as root in a container, from the repo root, stdin closed |

A glob entry is either a string or `{"glob": "...", "why": "..."}`. Globs match tracked paths from the repo root:
`*` and `?` stay inside one directory, `**/` matches any number of directories, `dir/**` matches everything under `dir`,
`[abc]` and `[!abc]` match one character other than `/`. Refused, with exit 2: `**` inside a segment (`docs**.md`),
POSIX classes (`[[:alpha:]]`), `/` or `[` inside a class, and invalid ranges (`[z-a]`).

A claim is `{"file": ..., "pattern": ..., <one count>}`. `pattern` is a regex whose group 1 captures the number
(commas allowed); every match in `file` must equal the count. A pattern that is not found fails, and so does a match
whose group 1 is empty or not a number. The count is one of (nested keys are checked too; a typo exits 2):

- `"count_glob": "skills/*/SKILL.md"`: the number of tracked files that match;
- `"count_json": {"file": "data/x.json", "key": "entries"}`: the length of the value at a dotted key (empty key: the top level);
- `"count_lines": {"file": "LIST.md", "pattern": "^- "}`: the number of lines that match.

Example:

```json
{
  "_comment": "why each allow-list entry exists goes in its why",
  "invisible_allow": [{"glob": "tests/fixtures/**", "why": "planted bidi and zero-width characters"}],
  "claims": [{"file": "README.md", "pattern": "(\\d+) skills", "count_glob": "skills/*/SKILL.md"}],
  "stale_globs": ["README.md", "docs/**/*.md"],
  "instructions": [{"file": "AGENTS.md", "max_bytes": 32768,
                    "sentinel": "Sentinel: if you can read this line, the whole file loaded."}],
  "root_safety": ["python3 evals/run.py --selftest"]
}
```

## Limits

- The invisible set follows the Unicode tables of the Python that runs it (3.12 on the runner), so a character
  assigned in a later Unicode version may not be caught.
- A file marked `-text` or `binary` in `.gitattributes` is skipped, so that file is a place to review too.
- Which characters may carry a variation selector is a rule of thumb (symbols, keycap bases, CJK and a few scripts),
  not the full Unicode variation-sequence tables.
- The root-safety job only sees what the commands do inside the container, to the paths above. It compares file
  contents only in the bin directories.
