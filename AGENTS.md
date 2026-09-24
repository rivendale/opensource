# AGENTS.md

For any AI coding tool (Claude Code, Codex, Grok, others) working in this repository or in a
game started from it.

## What this repository is

A reference chassis, not a game: `catalog/` (open-source games by genre, license and activity
read from GitHub), `playbooks/` (how to build each genre), `ai/` (how to build with AI tools),
`lessons/` (what went wrong and right in small games we built), `templates/` (start files for a new
game repo), `art/` (Blender and 2D tools for game assets), `engines/` (Godot, Unity and others),
`scaffolds/` (starter templates and MCP servers, with a hand-checked shortlist). `data/catalog.json`
and `data/scaffolds.json` are the machine-readable lists; `tools/` rebuilds them.

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

## Rules when you change this repository

- The catalog and scaffold lists are generated. Change `tools/build_catalog.py` or
  `tools/find_scaffolds.py` and rebuild; do not hand-edit `catalog/*.md`, `scaffolds/scaffolds.md`,
  `scaffolds/mcps.md` or `data/*.json`.
- Anything that runs code on a reader's machine (an MCP server, an add-on, an install command) gets
  its risk stated next to it and a pinned version, and links the checklist in `ai/graphics.md`.
- Public repository: no personal names, hosts, keys or private project details in any file.
- American English, plain words, no em dashes.
- Run `python3 tools/check_links.py` before opening a pull request; it checks every relative
  link and `#anchor` in the markdown, and `--selftest` checks the checker.
