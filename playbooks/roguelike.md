# Roguelike playbook

Traditional roguelikes (turn-based, grid, permadeath) and roguelites (runs with unlocks between
them, often real-time or card-based). The catalog lists 69 roguelike projects, 11 of them `copy`
class; the full table is in [../catalog/roguelike.md](../catalog/roguelike.md). Every project named
below was checked against its repository on 2026-09-23.

## 1. What defines the genre

**Core loop:** enter a procedurally generated level, explore it under fog of war, fight or avoid
what you find, collect items whose use you often have to discover, go down the stairs. When you
die, the run is over: start again on a new seed. The genre's pull comes from **permadeath plus
procedural generation**: every decision matters because it cannot be undone, and every run is new.

**Player verbs:** move (usually eight directions), attack by moving into a monster, pick up, use
(drink, read, zap, throw), equip, rest, search, descend. One key press is one turn; monsters act
after the player, so the game waits while the player thinks.

**Win:** reach a goal and survive. Brogue CE's README states it plainly: retrieve the Amulet of Yendor
from the 26th level. **Lose:** death ends the run and the save goes with it.

**Roguelites** keep permadeath and procedural runs but add something that carries over (unlocked
cards, characters, upgrades), and many drop the grid for real-time or card combat. end_of_eden's
design document defines its roguelite as permadeath plus procedural event order, drops and enemy
spawns, with health not restored between fights.

## 2. The systems to build, in build order

### First playable vertical slice: three levels and a win screen

- [ ] Grid map on screen, player glyph or tile, eight-way movement
- [ ] Turn loop: the player acts, then every monster acts
- [ ] One seeded RNG passed to everything that needs randomness; the seed shown on the death screen
- [ ] Level generator: rooms and corridors, guaranteed connectivity, stairs down
- [ ] Field of view (shadowcasting) plus memory of explored tiles
- [ ] Three monster types: bump attack, chase the player with pathfinding
- [ ] HP, a death screen, restart on a new seed
- [ ] Two items: one potion, one weapon; pick up, use, equip
- [ ] A message log
- [ ] Win on reaching level 3

**Done when** a new player dies, understands why, and presses "new game" without being asked.

### v1

- [ ] A speed or energy scheduler, so fast and slow monsters act at different rates
- [ ] Monsters, items and level parameters in data files, loaded and validated at start
- [ ] Unidentified items: appearances shuffled per seed ("a murky potion")
- [ ] Several level generators (caves, rooms, mazes), chosen by depth or theme
- [ ] Hand-made set pieces ("vaults") placed inside generated levels
- [ ] Monster AI states: wandering, hunting, fleeing; noise, light or scent that lets monsters find
      the player
- [ ] Ranged attacks, spells, throwing, and a keyboard targeting mode
- [ ] Status effects with durations; terrain that interacts (fire spreads through grass)
- [ ] Save on quit, one slot, deleted on death
- [ ] A run summary at death: cause, depth, turns, seed
- [ ] A regression test that generates a fixed list of seeds and compares the result to a stored
      catalog of what each seed produced

### Polish

- [ ] Auto-explore and travel-to-stairs commands; mouse support alongside keys
- [ ] ASCII and tile modes behind one toggle
- [ ] Lighting and color that carry information (danger, magic, darkness)
- [ ] Recordings: store the seed plus the input list and replay a whole run
- [ ] A daily seed shared by every player
- [ ] Tutorial and in-game help for every command
- [ ] Meta-progression, roguelites only
- [ ] Browser or remote play

## 3. Reference projects to study

**Brogue: Community Edition** ([repo](https://github.com/tmewett/BrogueCE)): `study only`
(AGPL-3.0), C. The model of a small, readable traditional roguelike. Level generation is
`src/brogue/Architect.c`; `Dijkstra.c` computes the distance maps that movement and AI read;
`Light.c` does lighting; `Recordings.c` saves replays. The part to copy as a practice (not as
code) is the test suite: `test/seed_catalogs/` stores what each seed generates, and a CI step
named "Check that seed catalogs are unchanged" runs `test/compare_seed_catalog.py` against it.
Graphical tiles ship alongside ASCII, toggled with one key. The tiles are licensed separately
from the code (CC BY-SA 4.0, in `bin/assets/LICENSE.txt`).

**Shattered Pixel Dungeon** ([repo](https://github.com/00-Evan/shattered-pixel-dungeon)):
`study only` (GPL-3.0), Java on libGDX. The most-starred roguelike in the catalog after
Cataclysm, built for Android, iOS and desktop from one codebase. Levels are assembled in two
stages: a builder arranges rooms into a shape (`levels/builders/`: loop, figure eight, branches,
line, grid), then a painter dresses them per region (`levels/painters/`: caves, city, halls and
others), drawing on a large library of room types in `levels/rooms/`. Learn the builder and
painter split: shape and theme vary independently.

**Dungeon Crawl Stone Soup** ([repo](https://github.com/crawl/crawl)): `study only` (GPL-2.0),
C++ with Lua. Hand-made map pieces are `.des` files under `crawl-ref/source/dat/des/`, sorted into
arrival vaults, branch ends, portals and floating minivaults, with a written guide
(`dat/des/guide.txt`). The same game runs in a terminal, as a tiles build, and in the browser
through its own web server (`crawl-ref/source/webserver`). Learn how authored vaults give
generated levels landmarks and set pieces.

**Angband** ([repo](https://github.com/angband/angband)): `study only` (GPL-2.0), C. Nearly all game
content is plain text under `lib/gamedata/`: `monster.txt`, `object.txt`, `class.txt`,
`vault.txt`, `room_template.txt`, and `dungeon_profile.txt`, which sets how each kind of level is
built (block size, room count, rarity). Learn how far a text data format can carry a game, and how
level profiles make generation tunable without code.

**Cataclysm: Dark Days Ahead** ([repo](https://github.com/CleverRaven/Cataclysm-DDA)):
`study only` (CC-BY-SA-3.0, a share-alike license applied to the code itself), C++. A survival
roguelike with a very large content set in `data/json/`, a documented load order
(`data/json/LOADING_ORDER.md`), map generation templates and reusable palettes (`mapgen`,
`mapgen_palettes`), and `effects_on_condition`, which let data files pair dialog-style conditions
with effects outside of dialog. Learn how JSON content scales to a very large item set and how
palettes keep map templates short.

**GoRogue** ([repo](https://github.com/Chris3606/GoRogue)): `copy` (MIT), C#. A library, not a
game: A* and goal maps (Dijkstra maps), recursive shadowcasting, sense maps for sound and light,
spatial maps, a step-based map generation framework, a dice notation parser, a turn-based effects
system and a message bus. Learn the API shapes, then use it directly if you are in .NET.

**LambdaHack** ([repo](https://github.com/LambdaHack/LambdaHack)): `copy` (BSD-3-Clause), Haskell.
An engine plus a sample game, with an SDL2 desktop frontend and a WebAssembly browser frontend. Its
README describes the design goal: a strict, type-enforced separation of engine code from read-only
content, and of clients (human or AI) from the server. Learn that separation even if you never
write Haskell.

**end_of_eden** ([repo](https://github.com/BigJk/end_of_eden)): `copy` (MIT), Go. A deck-building
roguelite that runs in a terminal or a window. The rules core is Go (`game/`), while enemies,
equipment and events are Lua (`assets/scripts/`) against a documented API
(`docs/LUA_API_DOCS.md`), with a written design document (`docs/GAME_DESIGN.md`) and an SSH entry
point (`cmd/game_ssh`). Its last push was 2024-09-02, so read it as a finished design rather than
a live dependency.

## 4. Reusable permissive code

Catalog projects keep the catalog's class. Libraries marked "not in the catalog" had their license
read from GitHub on 2026-09-23; re-read the LICENSE file before you copy anything.

| need | project | class | license |
|---|---|---|---|
| FOV, pathfinding, map generation, dice, effects (C#) | [GoRogue](https://github.com/Chris3606/GoRogue) | `copy` | MIT |
| map generation, pathfinding, FOV (C#, older) | [RogueSharp](https://github.com/FaronBracy/RogueSharp), last push 2024-08-03 | `copy` | MIT |
| console, FOV, pathfinding (C and C++) | [libtcod](https://github.com/libtcod/libtcod) | not in the catalog | BSD-3-Clause |
| the same for Python | [python-tcod](https://github.com/libtcod/python-tcod) | not in the catalog | BSD-2-Clause |
| display, FOV, map generators, pathfinding, scheduler, noise, RNG (TypeScript) | [rot.js](https://github.com/ondras/rot.js) | not in the catalog | BSD-3-Clause |
| terminal, A* and Dijkstra maps, dice RNG, noise (Rust) | [bracket-lib](https://github.com/amethyst/bracket-lib) | not in the catalog | MIT |
| a whole engine with content separation (Haskell) | [LambdaHack](https://github.com/LambdaHack/LambdaHack) | `copy` | BSD-3-Clause |
| tile and bitmap generation from an example | [WaveFunctionCollapse](https://github.com/mxgmn/WaveFunctionCollapse) (C#) | not in the catalog | MIT (GitHub reads it as unknown; the LICENSE file is MIT) |
| cave and overworld noise | [FastNoiseLite](https://github.com/Auburn/FastNoiseLite) | not in the catalog | MIT |
| a browser roguelike to read end to end | [Rot Magus](https://github.com/kosinaz/Rot-Magus) (rot.js and Phaser) | `copy` | Apache-2.0 |

rot.js alone covers most of a traditional roguelike's plumbing: its `src/map/` has rogue,
digger, uniform, cellular, arena and maze generators; `src/fov/` has discrete, precise and
recursive shadowcasting; `src/scheduler/` has simple, speed and action schedulers.

## 5. Engine options (engine-neutral)

- **A roguelike library instead of an engine:** libtcod or python-tcod (BSD), rot.js (BSD-3-Clause),
  bracket-lib (MIT). Tradeoff: ideal for ASCII or simple tiles and fast to start; you add
  animation, audio and menus yourself.
- **[Godot](https://github.com/godotengine/godot)** (`copy`, MIT). Tiles, animation, particles and
  an editor, good for a roguelite with juice. Tradeoff: the grid, turn loop and FOV are yours to
  write; physics nodes fight a turn-based model, so keep game state in plain data.
- **[LibGDX](https://github.com/libgdx/libgdx)** (`copy`, Apache-2.0). Shattered Pixel Dungeon
  proves one Java codebase can ship on desktop, Android and iOS. Tradeoff: no editor.
- **[Phaser](https://github.com/phaserjs/phaser)** (`copy`, MIT) with rot.js, or
  **[excalibur](https://github.com/excaliburjs/Excalibur)** (`copy`, BSD-2-Clause). Browser play
  with no install; Rot Magus shows the Phaser pairing. Tradeoff: saves live in browser storage.
- **[MonoGame](https://github.com/MonoGame/MonoGame)** (`check first`: GitHub could not read its
  license, and its source list says MS-PL + MIT) with GoRogue. Tradeoff: no scene editor, and you
  confirm its LICENSE file before you build on it.

## 6. Assets

ASCII roguelikes need no art at all, only a font (check it is under the SIL Open Font License or
similar). Tiles are the usual first upgrade.

- **[Kenney](https://kenney.nl/support):** "all game assets on the asset pages are public domain
  licensed (CC0)", including for commercial use.
- **[OpenGameArt](https://opengameart.org/content/faq):** per-asset licenses: CC0, CC-BY 3.0 or 4.0,
  CC-BY-SA 3.0 or 4.0, OGA-BY 3.0 or 4.0, GPL 2.0 or 3.0. Search it for roguelike tilesets and
  filter by license.
- **[game-icons.net](https://game-icons.net/about.html):** item and spell icons under CC BY 3.0;
  credit the author.
- **[Freesound](https://freesound.org/help/faq/):** CC0, CC BY or CC BY-NC per sound; NC forbids
  commercial use.

**A code license says nothing about the art.** Brogue CE's code is AGPL-3.0 but its tiles are
CC BY-SA 4.0, under a separate license file. Keep one row per asset in the game's `THIRD_PARTY.md`
(see [../templates/THIRD_PARTY.md](../templates/THIRD_PARTY.md)).

## 7. Building it with AI tools

Follow the stage table in [../ai/README.md](../ai/README.md). For a roguelike the work splits
like this:

- **Claude** plans and reviews: the design page, the list of ways a generated level can be broken,
  the data schemas, and whole-repo reviews for randomness that bypasses the seeded RNG.
- **Codex** takes one scoped task at a time: the turn loop, each generator, the level checker, the
  seed catalog test, a port of a `copy` algorithm (the AI guide walks through porting GoRogue's
  field of view with its MIT notice and a `THIRD_PARTY.md` row).
- **Grok** is the blind second opinion: hand it a failing seed and the files, never your theory.

Describe a `study only` mechanic in your own words; never paste GPL or AGPL code into a prompt.

**Prompts by stage:**

1. *Turn loop (Codex):* "Write a turn-based grid core with no rendering: a map, a player, monsters
   and a scheduler where each actor has a speed. All randomness comes from one seeded RNG passed
   in. Expose `step(state, action) -> state`."
2. *Generator (Claude lists, Codex builds):* "Write a rooms-and-corridors generator that takes a
   seed. First list the ways a level can be broken: unreachable stairs, a player spawned in a wall,
   items in walls, overlapping rooms. Write a checker for each and run it over 10,000 seeds."
3. *Determinism (Codex):* "Store what seeds 1 to 100 generate (layout hash, items, monsters). Add
   a test that fails when any seed changes, and a command that updates the catalog on purpose."
4. *Content (Codex):* "Move monsters and items into data files. Write a validator that rejects
   unknown fields, missing ids and references to ids that do not exist."
5. *AI (Codex, reviewed by Claude):* "Give monsters three states (wander, hunt, flee) driven by a
   distance map toward the player and one away from danger. Log each state change."

**Playtest checklist**, on top of the general one in the AI guide:

- [ ] A reported seed reproduces the same first level on another machine
- [ ] The level checker passes on thousands of seeds, after every change
- [ ] Every death was visible in advance: the player could have seen the threat coming
- [ ] A first-time player understands each item after using it once
- [ ] Quitting and reloading mid-level restores the exact state; dying deletes the save
- [ ] Every action works from the keyboard alone, and the common ones from the mouse
- [ ] Runs end at a variety of depths, not always at the same wall

## 8. Genre-specific pitfalls

- **Hidden nondeterminism.** A UI animation that draws from the gameplay RNG changes the dungeon.
  Keep separate RNG streams for generation, combat and cosmetics, and test seeds the way Brogue CE
  does.
- **Unfair deaths.** Instant kills from off screen make permadeath feel like theft. Telegraph
  danger and let the player see it.
- **Broken levels.** Players generate far more levels than you will ever test, so a rare
  unreachable staircase still reaches them. Validate every generated level before it is shown.
- **Identification tedium.** Unknown items are a puzzle only if testing them is interesting.
  Give the player safe ways to learn.
- **Save scumming.** If the save file can be copied back, permadeath is optional. Decide whether
  you care, and say so.
- **Interaction explosions.** Fire, gas, water and doors multiply into cases nobody tested. Keep a
  table of which systems touch which, and write a test for each pair.
- **Key overload.** Classic command lists run to dozens of keys. Add context actions, a command
  menu and mouse support early.
- **Meta-progression hiding a weak loop.** If a roguelite is only fun after twenty unlocks, the
  first run is the problem.
- **The famous ones are not permissive.** Of the projects above, Brogue CE, Shattered Pixel
  Dungeon, Dungeon Crawl Stone Soup, Angband and Cataclysm are `study only`, and the catalog marks
  NetHack `check first` under its own license. Study their mechanics; take code only from the
  permissive libraries in section 4.
