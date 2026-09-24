# Building a game with AI coding tools

How to go from a genre playbook to a playable game with three AI coding tools, while keeping every
borrowed line legal to ship. The chassis is engine-neutral: the tools write code for whatever
engine and language your game picked.

Commands here were checked on 2026-09-23 against Claude Code 2.1.281, Codex CLI 0.156.1 and Grok
CLI 1.0.41. Flags change between releases, so run `claude --help`, `codex --help` or `grok --help`
and check your version before you script anything.

## The tools, and what each is for

| tool | CLI | models (2026-09-23) | where we use it |
|---|---|---|---|
| Claude | `claude` (Claude Code) | Claude Opus 5.5, Fable 5.1 (`--model opus`, `--model fable`) | planning, architecture, design review, long-context review of a whole repo |
| Codex | `codex` (OpenAI Codex CLI) | GPT-6 Sol, GPT-6 Luna (`-m gpt-6-sol`, `-m gpt-6-luna`) | one scoped implementation task at a time, with tests run in its sandbox |
| Grok | `grok` (xAI Grok CLI) | grok 4.7 (`-m grok-4.7`) | an independent second opinion and blind reviewer |

- Opus 5.5 is the everyday planner and reviewer; keep Fable 5.1 for the hardest design calls. The
  `--model` aliases pick the latest model of that name; confirm which one you got in the session.
- Codex's own catalog (`codex debug models`) calls Sol the "workhorse model for coding and everyday
  work" and Luna the "fast and affordable model for easier tasks".
- Grok CLI 1.0.41 defaulted to an older model: pass `-m grok-4.7`, and see `grok models`.

These are defaults, not rules. What matters is that the model reviewing a change did not write it.

## Set up the game repository once

1. Clone this chassis next to your game so prompts can cite `../opensource/playbooks/<genre>.md`.
   - Claude Code: `claude --add-dir ../opensource`.
   - Codex: no flag. Its sandbox limits writes, not reads: under `-s read-only` and
     `-s workspace-write` it reads `../opensource` and cannot write there. Its `--add-dir` makes a
     directory *writable*, which a reference copy does not need. See it yourself with
     `codex sandbox -c 'sandbox_mode="read-only"' -- cat ../opensource/README.md`.
   - Grok: no flag. Its sandbox is off by default, and a default session read a file in a sibling
     directory. Its built-in docs say the `workspace` and `read-only` sandbox profiles also read
     everywhere, while `strict` reads only the working directory and system paths, so do not use
     `strict` with the chassis beside the repo.
2. Copy [`templates/AGENTS.md`](../templates/AGENTS.md) and
   [`templates/THIRD_PARTY.md`](../templates/THIRD_PARTY.md) into the game repo and fill them in.
3. Keep exactly one instruction file. All three CLIs read `AGENTS.md`: `codex debug prompt-input`
   shows its text in Codex's model input, and `grok inspect` lists it under Project Instructions
   once you trust the project. Claude Code reads it too. Keep no `CLAUDE.md` in or above the repo
   beside it: which file wins depends on the version, and two instruction files drift apart. The
   test in step 4 shows which one loaded.
4. Test from the consuming end: ask each tool to quote the first rule in `AGENTS.md`. If it
   cannot, the file is not loaded, whatever the configuration says.

## Which tool for which stage

| stage | lead | reviewer | artifact | done when |
|---|---|---|---|---|
| 1. Pick a genre and references | Claude | Grok | `docs/choice.md` | three references with their reuse class, at least one `copy` |
| 2. One-page design | Claude | Grok, blind | `docs/design.md` | one page, with a cut list |
| 3. Failure list | Claude | Codex | `docs/failure-modes.md` | every item names the playtest step that catches it |
| 4. Vertical slice | Codex | Claude | code, `playtest/` | the full loop plays once, start to game over, and the script passes |
| 5. Playtest | a person, plus the script | | `playtest/notes/<date>.md` | someone who did not build it has played it |
| 6. Iterate | Codex (tasks), Claude (plan) | Grok | small commits | each change has a playtest step that fails without it |
| 7. Harden | Claude | Grok and Codex | `docs/review-<date>.md` | every finding reproduced or dismissed with a reason |

## Prompt templates

Fill in the angle brackets. Each prompt names files to read, so the model works from real code.

### 1. Pick a genre playbook and references (Claude, plan mode)

Start with `claude --model opus --permission-mode plan` so nothing is written until you agree.

```text
Read ../opensource/playbooks/<genre>.md and ../opensource/catalog/<genre>.md.
I want to build: <two sentences about the game>. Platform: <browser/desktop/mobile>.
Engine preference: <engine, or "none yet">.
1. Say whether <genre> is the right playbook or a neighboring genre fits better, and why.
2. Pick three reference projects from the catalog, at least one with reuse class `copy`.
   For each: name, repo URL, reuse class exactly as the catalog states it, and the one
   thing we would learn or reuse from it.
3. For each `copy` project, read its file tree and name the files worth reusing. No guessing.
4. For each project, say what its code license does NOT cover (art, audio, levels, data).
Write docs/choice.md. Do not write code.
```

### 2. One-page design (Claude)

```text
Using docs/choice.md and ../opensource/playbooks/<genre>.md, write docs/design.md.
One page, these headings only:
- Pitch: one sentence, what the player does and why it is fun.
- Core loop: the three to five steps the player repeats.
- Win, lose, restart.
- Controls, for every input device we support.
- The one mechanic that makes this game different from the references.
- Vertical slice: the smallest build that plays the full loop once.
- Cut list: what we are deliberately not building in the slice.
- Assets: each one we need, where it comes from, and its license.
Mark every assumption with (assumed) so I can overturn it.
```

### 3. Failure list (Claude writes, Codex attacks)

```text
Read docs/design.md. Before any code exists, list the ways the vertical slice can fail.
Cover at least: frame-rate dependence; input that is dropped, repeated, or lost on
window focus change; state that survives a restart when it should not; save and load;
unseeded randomness; map and screen edges; softlocks; <network desync, if multiplayer>.
For each: the failure, how a player would notice, and the scripted playtest step that
would catch it. Write docs/failure-modes.md.
```

Then ask a different model what the list misses: `codex exec -s read-only -m gpt-6-sol "Read
docs/design.md and docs/failure-modes.md. List failures the list misses; do not repeat any."`

### 4. Vertical slice (Codex, one scoped task at a time)

Fetch the reference code yourself, pinned to a commit, with its license beside it. Ask GitHub for
the license path rather than trusting a README: GoRogue's README points at `LICENSE.md`, but the
file in the repository is `LICENSE`.

```sh
OWNER=Chris3606 REPO=GoRogue
SHA=$(gh api repos/$OWNER/$REPO/commits/HEAD --jq .sha)
LIC=$(gh api repos/$OWNER/$REPO/license --jq .path)
mkdir -p reference/$REPO
curl -fsSL "https://raw.githubusercontent.com/$OWNER/$REPO/$SHA/$LIC" -o reference/$REPO/LICENSE
curl -fsSL "https://raw.githubusercontent.com/$OWNER/$REPO/$SHA/GoRogue/FOV/RecursiveShadowcastingFOV.cs" \
  -o reference/$REPO/RecursiveShadowcastingFOV.cs
```

Write the task to a file, then run `codex exec -s workspace-write -m gpt-6-sol - < tasks/fov.md`
(a `-` prompt tells `codex exec` to read the instructions from stdin).

```text
Task: add field of view to the dungeon map.
Reference: reference/GoRogue/RecursiveShadowcastingFOV.cs, from GoRogue (MIT, catalog
reuse class `copy`) at commit <SHA>. Port its recursive shadowcasting to <language>.
It uses grid types from SadRogue.Primitives; replace those with our own grid types.
Rules:
- Head the ported file with GoRogue's copyright line and MIT notice from
  reference/GoRogue/LICENSE (the source file has none of its own), marked as modified.
- Add a THIRD_PARTY.md row: our path, source URL at <SHA>, MIT, holder, what changed.
- Touch only src/fov/ and the map renderer. No refactors elsewhere.
- Add a playtest step: player at a known seeded position; tiles behind a wall are hidden.
- Run <test command> and the playtest and show the output. Stop if either fails twice.
```

Other `copy` starting points, each checked against its repository on 2026-09-23:

| need | project (catalog reuse class) | where to look |
|---|---|---|
| rollback netcode for a browser fighting game | [netplayjs](https://github.com/rameshvarun/netplayjs) (ISC, `copy`) | `netplayjs-client/src/netcode/rollback.ts`; `lockstep.ts` for state that cannot be rewound |
| turn-based rules, multiplayer sync, bots | [boardgame.io](https://github.com/boardgameio/boardgame.io) (MIT, `copy`) | use the npm package as a dependency rather than copying files |
| grid merge puzzle logic | [2048](https://github.com/gabrielecirulli/2048) (MIT, `copy`) | `js/game_manager.js`, `js/grid.js` |
| pseudo-3D road with curves and hills | [JavaScript Racer](https://github.com/jakesgordon/javascript-racer) (MIT, `copy`) | `v2.curves.html`, `v3.hills.html`; its music and sprites are not MIT (see below) |
| roguelike pathfinding | [GoRogue](https://github.com/Chris3606/GoRogue) (MIT, `copy`) | `GoRogue/Pathing/AStar.cs`, `GoRogue/Pathing/GoalMap.cs` |

### 5. Playtest harness (Codex builds, a person plays)

```text
Build a headless playtest runner: playtest/run --seed N --script FILE.
- Fixed timestep, seeded RNG, no wall-clock reads inside the simulation.
- A script is lines of "<frame> <input>"; the runner feeds them and advances frames.
- Assertions are on what a player could observe: position, score, lives, current screen.
- Print one line per assertion, PASS or FAIL with the observed value; write the final
  state to playtest/out/<script>.json; exit non-zero on any FAIL or logged error.
Write playtest/scripts/first-minute.txt covering docs/failure-modes.md items <numbers>.
```

Then prove the runner can fail (see Verification habits) before you trust a PASS from it.

### 6. Iterate on a bug (Codex, or Claude for anything spanning many files)

```text
Symptom: <what the player saw>. Expected: <what should happen>.
Repro: playtest/run --seed <N> --script <file> fails at frame <F> with: <output line>.
Find the cause before changing code, and show the evidence. Then fix it with the smallest
change, add a playtest step that fails on the old code and passes on the new, and show both
runs.
```

### 7. Harden (Claude, report only)

```text
Review the whole repository against docs/design.md and docs/failure-modes.md.
Do not edit code; the only file you write is docs/review-<date>.md. For each finding:
file and line, what goes wrong, and the input or sequence that triggers it. Rank by what
a player would hit first. Then list every file or asset we did not write that is missing
from THIRD_PARTY.md, and every asset whose license is unknown.
```

## Blind review with a second model

If you send your diagnosis, you get your diagnosis back. A reviewer handed your theory tends to
confirm it, and a reviewer reading your summary inherits whatever your summary left out. Give it the
symptom and the real files, assembled fresh from the repository, and ask for its own explanation.

```text
A game written in <language>. Observed: <symptom>. Expected: <behavior>.
Reproduce with: <command>.
The relevant files follow. Give the most likely cause, the evidence in the code for it,
and one alternative cause you considered and rejected. If these files are not enough to
decide, name the file you would need.
```

```sh
mkdir -p .review    # and add .review/ to .gitignore
{ cat .review/brief.md
  for f in src/netcode.ts src/game.ts; do printf '\n--- %s ---\n' "$f"; cat "$f"; done
} > .review/prompt.md
grok -m grok-4.7 --prompt-file .review/prompt.md > .review/grok.md
codex exec -s read-only -m gpt-6-sol -o .review/codex.md - < .review/prompt.md
codex review --uncommitted    # Codex's built-in review of working-tree changes
```

- Leave out your theory, the commit message and the chat where you debugged it.
- The code is inside the prompt, so reviewers need no write access. Use read-only modes:
  `-s read-only` in Codex, `--permission-mode plan` in Claude Code and Grok.
- Treat each verdict as a candidate, not a finding. Reproduce it with a playtest step before you
  change code; reviewers are confidently wrong too.
- When two reviewers agree, check that they did not both read the same incomplete input. Agreement
  over one missing file is one measurement, not two.

## Verification habits

1. **Write the ways it can fail before you build it.** `docs/failure-modes.md` comes before code,
   and every task names the items it addresses.
2. **Prefer end-to-end playtest scripts over unit tests written by the same model.** A unit test
   written by the model that wrote the code encodes the same misunderstanding and grades its own
   homework. Ground truth has to come from outside the model: a scripted playthrough that asserts
   what a player would see, or a person playing.
3. **Prove a check can fail.** Break the game on purpose and confirm the script goes red. Vary the
   break: delete a line, skip a call, load a stale build, remove an asset. A check that has only
   ever printed PASS is not evidence yet.
4. **Test the build the player gets.** "It compiles" and "the tests pass" are not "the player can
   do it". Run the exported or deployed build, not only the dev server.
5. **Reconcile counts, and say what you did not verify.** If the loader read 12 levels, the menu
   shows 12. An honest "not tested on touch" beats a silent gap.

### Playtest checklist

- [ ] A new player understands the goal without reading anything, and you watched without helping.
- [ ] Inputs register on the frame they are pressed; nothing sticks after a window focus change.
- [ ] Speed, physics and timers behave the same at 30, 60 and 144 frames per second.
- [ ] Losing is clear; restart is one action, works from every screen and clears all run state.
- [ ] Save, quit and reload restores the same state. No state is a softlock.
- [ ] Mute works and volume persists. Resize, fullscreen and the smallest screen stay playable.
- [ ] Every supported input device works: keyboard, gamepad, touch.
- [ ] Multiplayer: two clients under added latency agree; one dropping mid-match crashes neither.
- [ ] The worst-case scene holds the target frame rate on the lowest target hardware.
- [ ] `THIRD_PARTY.md` matches the files in the repo, and the credits screen lists every asset.

A game can pass every review and still be dull. Only a person playing it finds that.

## License hygiene with AI

The rule: copy code only from `copy`-class projects. `study only` projects (`study` in
`data/catalog.json`) are read for design and mechanics, never copied. `check first` means no known
license, which is all rights reserved.

- **Never paste GPL, AGPL or unlicensed code and ask for a copy, a port or "a version in
  TypeScript".** A translation of copyleft code is still derived from it.
- **Ask for the mechanic in your own words.** Read the `study only` project yourself, write a plain
  description of the behavior (inputs, rules, edge cases), then start a fresh session with only
  that description. Example: Brogue: Community Edition (AGPL-3.0, `study only`) builds its levels
  in `src/brogue/Architect.c` and `src/brogue/Dijkstra.c`. Study how its levels feel to play; do
  not feed those files to a model.
- **Check whether a `copy` implementation of the same idea exists.** Often it does: distance-map
  pathfinding is in GoRogue's `GoalMap.cs` (MIT, `copy`).
- **A clean-room prompt says so:**

  ```text
  Implement the mechanic described below in <language> for our game. The description is
  our own. Do not reproduce code from any existing project. If you recognize this as a
  known game's implementation, say which one instead of writing it from memory.
  <your description>
  ```

- **Models can reproduce code they have seen.** If a generated file looks suspiciously complete,
  search GitHub for a distinctive line before you commit it.
- **Keep `THIRD_PARTY.md` current in the same commit** that brings a file in: path, source URL at a
  commit, license, copyright holder, what you changed. Before a release, ask a model to diff the
  repo against `THIRD_PARTY.md` and list anything unaccounted for.
- **Re-read the LICENSE at the commit you copy from.** The catalog is a snapshot from 2026-09-23;
  licenses change.

**Code licenses say nothing about art, audio, levels or data.** Three catalog projects show why:

- [Overgrowth](https://github.com/WolfireGames/overgrowth) (Apache-2.0, `copy` in its GitHub row):
  the README says only the code is in the repository, and the art and levels can only be legally
  obtained by buying the game.
- [JavaScript Racer](https://github.com/jakesgordon/javascript-racer) (MIT, `copy`): the README
  says its music is licensed only for that project, and its sprites are placeholders borrowed from
  the Sega Genesis version of Out Run.
- [Brogue: Community Edition](https://github.com/tmewett/BrogueCE) (AGPL-3.0, `study only`): its
  tile art carries a separate CC-BY-SA-4.0 license in `bin/assets/LICENSE.txt`.

Record asset licenses in `THIRD_PARTY.md` separately from code. This is practical guidance, not
legal advice.

## Cost and context

- **Keep `AGENTS.md` short.** Every tool loads it into every session, so each line is paid for on
  every request. Put the rules there and link to longer documents.
- **Point at paths; do not paste the repo.** Paste code only for a blind reviewer.
- **Compact before you walk away, not after you come back.** Prompt caches expire; compacting a
  cold session reprocesses the whole window at the uncached price. All three can compact on
  demand: Claude Code has `/compact` and the `--autocompact` flag; Codex CLI 0.156.1 has `/compact`
  in its interactive session and a `model_auto_compact_token_limit` setting; Grok CLI 1.0.41 has
  no compact flag, but its built-in docs list `/compact [context]` and an automatic compact at
  `session.auto_compact_threshold_percent`. Coming back cold, start a new session pointed at a
  short `docs/handoff.md` (done, next, broken) instead of resuming.
- **Do the arithmetic, not a remembered price.** An uncached request costs roughly the window's
  tokens times the input price; cached input is billed at a fraction of that. Check your provider's
  current pricing page: a rule built on last month's price goes stale silently.
- **Match the model to the task, and cap scripted runs.** Luna for mechanical edits, Sol for
  implementation, Opus for plans and reviews, Fable for the hardest calls.
  `claude -p --max-budget-usd <dollars> "..."` stops a non-interactive Claude run at a limit.
- **Keep secrets and player data out of prompts.** Load keys from the environment.

## Commands checked for this guide

| purpose | command | checked with |
|---|---|---|
| Claude planning session | `claude --model opus --permission-mode plan` | Claude Code 2.1.281 |
| Claude one-shot, capped | `claude -p --max-budget-usd <dollars> "<prompt>"` | Claude Code 2.1.281 |
| Codex scoped task from a file | `codex exec -s workspace-write -m gpt-6-sol - < task.md` | Codex CLI 0.156.1 |
| Codex review of changes | `codex review --uncommitted` or `codex review --base main` | Codex CLI 0.156.1 |
| Codex model catalog | `codex debug models` | Codex CLI 0.156.1 |
| Codex: is AGENTS.md loaded? | `codex debug prompt-input \| grep AGENTS.md` | Codex CLI 0.156.1 |
| Codex: can it read the chassis? | `codex sandbox -c 'sandbox_mode="read-only"' -- cat ../opensource/README.md` | Codex CLI 0.156.1 |
| Grok single turn from a file | `grok -m grok-4.7 --prompt-file prompt.md` | Grok CLI 1.0.41 |
| Grok: is AGENTS.md loaded? | `grok inspect` | Grok CLI 1.0.41 |
