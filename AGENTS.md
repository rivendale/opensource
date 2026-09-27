# AGENTS.md

For any AI coding tool (Claude Code, Codex, Grok, others) working in this repository or in a
game or project started from it.

## What this repository is

A reference chassis, not an application, in two domains.

**Games**, at the top level: `catalog/` (open-source games by genre, license and activity
read from GitHub), `playbooks/` (how to build each genre), `ai/` (how to build with AI tools),
`lessons/` (what went wrong and right in small games we built), `templates/` (start files for a new
game repo), `art/` (Blender and 2D tools for game assets), `engines/` (Godot, Unity and others),
`scaffolds/` (starter templates and MCP servers, with a hand-checked shortlist).

**Software**, under `software/`: hand-picked open-source applications, tools, libraries and
curated lists beyond games, by category, with the same reuse classes.

`data/catalog.json`, `data/scaffolds.json` and `data/software.json` are the machine-readable lists;
`tools/` rebuilds them.

## Rules when you use it to build a game

1. **Copy code only from projects whose reuse class is `copy`.** Keep their copyright notice and
   add the file and its license to the game's `THIRD_PARTY.md` in the same change.
2. **`study only` means study only.** Read GPL or AGPL code to understand a mechanic, then write
   it from your own description of the mechanic. Never paste such code into a prompt and ask for
   a version of it.
3. **`check first` means no known license.** Treat it as all rights reserved.
4. **Code licenses do not cover assets.** Art, audio, maps and data need their own license check.
5. **Verify a claim against the repository before relying on it.** Catalog rows are a snapshot;
   licenses change. Re-read the LICENSE file of anything you copy from.
6. **The same rules hold for `software/`.** Running a GPL or AGPL program unmodified is ordinary
   use; the reuse class limits copying its code. A source-available license stays `check first`.

## Rules when you change this repository

- The catalog and scaffold lists are generated. Change `tools/build_catalog.py` or
  `tools/find_scaffolds.py` and rebuild; do not hand-edit `catalog/*.md`, `scaffolds/scaffolds.md`,
  `scaffolds/mcps.md` or `data/*.json`.
- The software list is generated too: add or change a seed in `tools/domains/software.json` and run
  `python3 tools/build_catalog.py --domain software --src sources --out .`; do not hand-edit
  `software/README.md` or `software/catalog/*.md`. A license correction goes in `tools/overrides.json`
  with the license file it was read from.
- Anything that runs code on a reader's machine (an MCP server, an add-on, an install command) gets
  its risk stated next to it and a pinned version, and links the checklist in `ai/graphics.md`.
- Public repository: no personal names, hosts, keys or private project details in any file.
- American English, plain words, no em dashes.
- Run `python3 tools/check_links.py` before opening a pull request; it checks every relative
  link and `#anchor` in the markdown, and `--selftest` checks the checker.
- After changing `tools/build_catalog.py` or `tools/fetch_sources.sh`, run `python3 tools/check_build.py`.
  It runs both against a fake `gh`, with no network, and checks what happens when GitHub fails.
