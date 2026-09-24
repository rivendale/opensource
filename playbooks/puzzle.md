# Puzzle playbook

Logic, grid, physics and match-three puzzles, from Sokoban-style designed levels to generated boards
like sudoku and minesweeper. The full list of 241 projects, with license and activity, is in
[../catalog/puzzle.md](../catalog/puzzle.md). Every project named here was checked against its
repository on 2026-09-23; reuse classes are quoted as the catalog states them (`copy`, `library
use`, `study only`, `check first`).

## 1. What defines the genre

**Core loop:** look at the board, form a hypothesis, act, watch the rules respond, then undo or
retry. The reward is the moment the player understands something new about the rules, so each
level exists to teach one idea or to test one the player already has.

**Player verbs:** move, push, swap, rotate, place, drop, flag, assign a skill (in Lemmings-likes),
and always undo and restart.

**Win and lose:** reach a goal state: every crate on a target, every mine flagged, a target score.
Losing means running out of moves, time or units (OceanPop wants a target score before the moves run
out; a Pingus level sets how many of its pingus must be saved), or there is no losing at all when
undo is unlimited. Endless variants (2048, falling blocks) end when the board fills.

Two families build differently. **Designed levels** (Sokoban, Baba Is You, Lemmings) live or die on
hand-made content, a solution for every level and a solid undo. **Generated boards** (sudoku,
minesweeper, match-three, 2048) live or die on the generator and its fairness check: exactly one
solution, no dead board, no forced guess.

## 2. The systems to build, in build order

### First playable vertical slice

- [ ] Board state as plain data: a grid of cells and entities with positions, no engine types.
- [ ] Rules as a pure function, `step(state, input) -> state`. The renderer only reads state.
- [ ] Input: keyboard plus mouse or touch, one action per input, queued while an animation plays.
- [ ] Undo as a stack of state snapshots (or the input log replayed from the start), and restart.
- [ ] A win check after every step, and a level-complete screen.
- [ ] Three hand-made levels loaded from a text or JSON file, never hard-coded.
- [ ] A seeded RNG owned by the state if anything is random, so undo and replays reproduce it.

### v1

- [ ] A level format with metadata: title, author, license, par moves or time. Enigma and Pingus both
      put the author and license inside each level file.
- [ ] A solution file per level and a headless checker that replays it (BAB BE U keeps a `.replay`
      file beside most of its levels). Run the checker on every commit.
- [ ] For generated boards, a generator plus a validator: Nudoku rejects any removed clue that would
      allow a second solution.
- [ ] A level editor, in game or through a general tool such as Tiled or LDtk.
- [ ] Level select, progress and best scores saved locally.
- [ ] Hints: show the next move from the stored solution, or a written clue.
- [ ] A difficulty curve: order levels by solution length and playtest times, not by feel alone.

### Polish

- [ ] Animation that never blocks the next input: tween from the old state to the new one.
- [ ] A sound for every action, a satisfying clear, a win that feels earned.
- [ ] Accessibility: shapes as well as colors, remappable keys, a reduced-motion mode (PROXX ships a
      renderer without motion).
- [ ] Localized level names and hints.
- [ ] Performance on low-end devices (PROXX was built to run on feature phones).
- [ ] Sharing: a level code or URL per level, and daily seeds for generated boards.

## 3. Reference projects to study

The best-maintained and most instructive puzzle projects in the catalog. `study only` projects are
read for design; copy nothing from them ([../ai/README.md](../ai/README.md), "License hygiene").

**[2048](https://github.com/gabrielecirulli/2048)**: `copy`, MIT, JavaScript. The original 2048,
last pushed in 2024. Learn from:
- The smallest complete split between rules, state, rendering, input and storage, in ten small
  files under `js/`: `game_manager.js`, `grid.js` and `tile.js` hold the game, `html_actuator.js`
  draws it, `keyboard_input_manager.js` handles keys and swipes, `local_storage_manager.js` keeps the
  best score and the game in progress.

**[PROXX](https://github.com/GoogleChromeLabs/proxx)**: `copy`, Apache-2.0, TypeScript. A
minesweeper-like game "for every device with a web browser (including feature phones)". Archived in
2026, so treat it as a read-only reference. Learn from:
- Pure game logic in a web worker (`src/worker/gamelogic/`), reached through Comlink, which keeps the
  main thread free for animation.
- Two renderers behind one interface: WebGL with motion, Canvas 2D without. Its README says sprites
  are generated at load time and cached in IndexedDB.

**[BAB BE U](https://github.com/lilybeevee/bab-be-u)**: `copy`, MIT, Lua on LÖVE. A fan game of
Baba Is You, where the rules are blocks on the board. Last pushed in 2023. Learn from:
- Rules read from the board every turn (`game/parser.lua`, `game/rules.lua`) and a separate undo
  module (`game/undo.lua`).
- Recorded solutions: `officialworlds/` holds 431 `.replay` files beside 507 `.bab` levels.
- Caution: it imitates a commercial game. Learn the systems; do not ship its content or look.

**[OceanPop](https://github.com/sharkwouter/oceanpop)**: `copy`, MIT, C++ with SDL2. A match-three
game with 35 levels and three modes, pushed in September 2026. Learn from:
- A level is only a size, a seed, a move budget and a target (`assets/levels/level010.json`), so each
  level's board is generated deterministically from its seed.
- Game modes as separate states (`src/states/GameState*.cpp`), plus credits files for PS2, PSP, Vita
  and Wii builds.
- Caution: its README credits the shell sprites to Freepik, backgrounds to Pexels and songs to
  Pixabay. None of that is MIT.

**[Pingus](https://github.com/Pingus/pingus)**: `study only`, GPL-3.0, C++. A Lemmings clone,
pushed in August 2026. Learn from:
- S-expression level files (523 `.pingus` files under `data/levels/`) whose header carries the
  license, the number of pingus, the number to save and a budget for each action.
- 159 `.pingus-demo` recordings, and an in-game level editor (`src/editor/`).

**[Enigma](https://github.com/Enigma-Game/Enigma)**: `study only`, GPL-2.0, C++. An Oxyd-style
marble game whose README counts more than 1000 levels. Learn from:
- XML level files (`data/levels/`) with metadata for author, license and par times per difficulty,
  and an embedded Lua block that maps two-character tile codes to objects.

**[Nudoku](https://github.com/jubalh/nudoku)**: `study only`, GPL-3.0, C with ncurses. Learn from:
- `src/sudoku.c`: fill a grid, punch holes, and reject any hole after which `count_solutions` finds
  more than one solution. Difficulty is the number of holes. Puzzles can be printed to PDF or PNG.

**[Lix](https://github.com/SimonN/LixD)**: `check first` (CC0 per list; GitHub could not read the
license), D with Allegro. Lemmings-like, over 700 puzzles, a level editor and 2 to 8 player
networked games. Its README says the code, graphics, levels and sound effects are CC0, while the
font and some music tracks are not. Read `doc/copying.txt` yourself before treating it as `copy`.

## 4. Reusable permissive code

| catalog project | reuse class, license | language | use it for |
|---|---|---|---|
| [PuzzleScript](https://github.com/increpare/PuzzleScript) | `copy`, MIT | JavaScript | grid puzzles as rewrite rules, such as `[ > Player \| Crate ] -> [ > Player \| > Crate ]`; undo and restart are built in (cataloged under engines) |
| [2048](https://github.com/gabrielecirulli/2048) | `copy`, MIT | JavaScript | grid slide-and-merge logic in `js/game_manager.js` and `js/grid.js` |
| [boardgame.io](https://github.com/boardgameio/boardgame.io) | `copy`, MIT | TypeScript | turn-based or competitive puzzles online (cataloged under strategy); Matchimals.fun (`copy`) is built on it |
| [Matter.js](https://github.com/liabru/matter-js), [Box2D](https://github.com/erincatto/box2d) | `copy`, MIT | JavaScript, C | 2D rigid-body physics for physics puzzles (cataloged under engines) |
| [Dear ImGui](https://github.com/ocornut/imgui) | `copy`, MIT | C++ | in-house level editors and debug views (cataloged under engines) |
| [rFXGen](https://github.com/raysan5/rfxgen) | `copy`, Zlib | C | generate your own sound effects for moves, clears and wins (cataloged under engines) |

Not in the catalog, license read from the repository on 2026-09-23:
[LDtk](https://github.com/deepnight/ldtk), a level editor, is MIT. The catalog has
[Tiled](https://github.com/mapeditor/tiled) as `check first`; its `COPYING` file says the editor is
GPL while `libtiled` and the TMX viewers are BSD 2-clause. Using an editor does not put its license
on the maps you make with it.

## 5. Engine options (engine-neutral)

| engine | license (catalog class) | fits | trade-off |
|---|---|---|---|
| [PuzzleScript](https://github.com/increpare/PuzzleScript) | MIT (`copy`) | turn-based grid puzzles, prototypes in hours | little beyond the grid; use it to find the idea, then rebuild |
| [Godot](https://github.com/godotengine/godot) | MIT (`copy`) | any puzzle, 2D or 3D, desktop, mobile and web export | keep the rules in plain scripts, not scene nodes, so a checker can run headless |
| [Phaser](https://github.com/phaserjs/phaser) | MIT (`copy`) | browser and mobile web puzzles | no bundled level editor or save system |
| [LÖVE](https://github.com/love2d/love) | zlib per its `license.txt` (`check first`: GitHub could not read it) | small 2D puzzles in Lua; BAB BE U uses it | no editor; its README documents desktop and mobile builds, not web |
| [raylib](https://github.com/raysan5/raylib) | Zlib (`copy`) | C or C bindings, small binaries | no scene system or editor |

## 6. Assets

Code licenses say nothing about art, audio or levels. Check every asset separately and give it a row
in `THIRD_PARTY.md` ([template](../templates/THIRD_PARTY.md)).

- **[Kenney](https://kenney.nl/assets)**: CC0, commercial use allowed, no attribution required. Packs
  that fit: Sokoban, Puzzle Pack 2, Physics Assets, UI Pack, Input Prompts, Interface Sounds, Music
  Jingles.
- **[game-icons.net](https://game-icons.net)**: icons under CC BY 3.0; attribution is required.
- **[OpenGameArt.org](https://opengameart.org)**: the license varies per submission (CC0, CC BY,
  CC BY-SA, GPL). Record the one you chose.
- **[Freesound](https://freesound.org)**: each sound has its own license, CC0 through CC BY-NC.
  Non-commercial sounds are unusable in a game you sell.
- **Generate your own**: rFXGen output is yours; so are levels you design.

Cautions from the reference projects:
- OceanPop's code is MIT, but its sprites, photos and music come from sites with their own terms.
- Pop Pop Win (`copy`, BSD-3-Clause, a Dart minesweeper) credits its art and sound effects to named
  people in its README without stating a license for them.
- **Levels are content with a license.** Each Pingus level declares `(license "GPLv3+")`. Importing a
  GPL game's level pack makes those levels GPL, whatever license your code has.

## 7. Building it with AI tools

Follow the stage table in [../ai/README.md](../ai/README.md): Claude plans and reviews, Codex
implements one scoped task at a time, Grok reviews blind, a person playtests. What changes for
puzzles:

| stage | lead | puzzle-specific artifact |
|---|---|---|
| design | Claude (plan mode) | `docs/rules.md`: every rule as one sentence, plus the order rules apply in |
| failure list | Claude, attacked by Codex | rule-order ambiguities, undo and RNG, unsolvable or trivially solvable levels |
| slice | Codex | pure `step()` core, headless replay checker, then the renderer |
| content | a person designs, Codex verifies | levels plus a solution file each; the checker must pass |
| "level is broken" reports | Grok and Codex, blind | the level file, the input log and the rules code, never your theory |

Prompts, in build order (fill the angle brackets; one task per Codex run):

```text
1. Rules spec (Claude, plan mode): Read ../opensource/playbooks/puzzle.md and
docs/design.md. Write docs/rules.md: board, entities, every rule as one sentence, the
order rules resolve in, what counts as a move, win and lose. List every pair of rules
that could conflict and say which wins.

2. Core and undo (Codex): Implement src/core/ in <language> with no engine imports:
State, step(state, input) -> State, is_won(state). Undo keeps prior States; restart
returns the level's initial State. Any randomness uses an RNG stored inside State.
Add a CLI, check --level FILE --solution FILE, that replays the solution and exits 0
only if the level is won exactly at the last input. Show it passing and failing.

3. Levels as data (Codex): Load levels from levels/*.<ext> with title, author,
license and par. Reject a malformed level with a message naming the file and line.
Run check on every level with its solution and print one line per level.

4. Generator (Codex, generated boards only): Generate boards from a seed. After each
removal or placement, count solutions up to 2 and undo the change if the count is not
exactly 1. Print seed, clue count and solve time for seeds 1..200.
```

To borrow a mechanic from a `study only` project such as Pingus or Enigma, write your own
description of it and give a fresh session only that description (the clean-room prompt in
../ai/README.md).

### Puzzle playtest checklist (add to the general one in ../ai/README.md)

- [ ] Every shipped level passes the replay checker; the checker fails on a level with one tile moved.
- [ ] A new player solves the first three levels unaided, and you learned nothing new from watching.
- [ ] Undo after every kind of move (including random ones) restores the exact previous board.
- [ ] Restart from every screen, mid-animation included, gives the level's initial state.
- [ ] No level has a shortcut far shorter than its intended solution (compare with par).
- [ ] No generated board needs a guess; each has exactly one solution, checked for 200 seeds.
- [ ] Rapid inputs during animations are neither lost nor applied twice.
- [ ] The game is fully playable in grayscale.

## 8. Genre-specific pitfalls

- **Unsolvable or trivially solvable levels.** A late rule change can break levels you finished
  weeks ago. Keep a solution for every level and replay them all on every commit, as BAB BE U's
  `.replay` files and Pingus's demo recordings allow.
- **Rule-order ambiguity.** When two rules apply at once, the order is part of the design. Write it
  down (PuzzleScript documents its execution order) and test the conflicting pairs.
- **Undo that forgets something.** Undo must restore the RNG position, counters and triggered events,
  not only positions. Snapshotting the whole state is simplest and cheap at puzzle sizes.
- **Unfair generators.** A sudoku with two solutions or a minesweeper board that needs a guess feels
  like cheating. Validate every board (Nudoku's `count_solutions`). PROXX places its mines only
  after the first reveal, away from that cell and its neighbors (`_placeMines` in
  `src/worker/gamelogic/index.ts`).
- **Difficulty spikes.** Order levels by measured solve times from playtests, not by the designer's
  sense of difficulty; the designer already knows the answers.
- **Animation locks.** Blocking input until an animation ends makes the game feel slow. Apply the
  move to the state at once and let the renderer catch up.
- **Color as the only signal.** Match-three and flood-fill games often encode everything in hue. Add
  shapes or symbols.
- **Borrowed content.** Clones and fan games (BAB BE U, Pingus, Lix all name their inspirations) show
  the systems well, but a well-known game's level designs and art belong to someone else. Design your
  own levels.
