# Arcade playbook

Shoot 'em ups, single-screen classics, breakout- and asteroids-likes, maze chasers, snake, and
one-button games. The catalog lists 314 arcade projects, 65 of them `copy` class; the full table
is in [../catalog/arcade.md](../catalog/arcade.md). Some rows are neighbors (racers, pinball,
party games), so read a row before you rely on it. Every project named below was checked against
its repository on 2026-09-23.

## 1. What defines the genre

**Core loop:** start a run with a few lives, face a pattern of threats that escalates, score by
destroying, collecting or surviving, lose a life on a hit, and restart the moment the run ends.
A run lasts minutes. Progress is the player's own skill, not a character's stats: the same run
that killed you at minute two is survivable once you have learned its patterns.

**Player verbs:** move (four- or eight-way, rotate and thrust, or one axis like a paddle); fire,
sometimes with a charge or a rate limit; a scarce panic button (bomb, shield, slow motion);
collect (dots, power-ups, coins); dodge. One-button games cut this to a single input, which is
the whole design exercise in the 111 one-button games listed below.

**Win:** clear the last stage or boss, or loop the game; many arcade games have no ending and the
goal is the high score. **Lose:** lives or time run out. **Restart:** one input, instantly.

**What makes it hard to build:** feel. Input read on the frame it happens, a hitbox the player
trusts, bullets you can read against the background, a difficulty curve that is fair, and a
simulation deterministic enough to replay a run input for input.

## 2. The systems to build, in build order

### First playable vertical slice: one screen, one enemy, one minute

- [ ] Fixed-timestep simulation (60 ticks per second) separated from rendering
- [ ] Input from keyboard and gamepad, sampled once per tick
- [ ] Player movement and screen bounds, tuned until it feels right with no enemies
- [ ] One weapon, with bullets drawn from a preallocated pool
- [ ] One enemy type with one movement pattern, spawned on a timer
- [ ] Collision: circles or boxes, with the player's hitbox smaller than its sprite
- [ ] Score, lives, game over, and restart in one input
- [ ] A seeded random number generator, so a run can be reproduced

### v1

- [ ] Waves and stages as data or as scripts, not as code in the update loop
- [ ] A difficulty table: speed, spawn count, fire rate and time per level
- [ ] Three to five enemy types and one boss with phases
- [ ] Power-ups and a panic button with a visible stock
- [ ] Local high score table that survives a restart and a crash
- [ ] Title screen, pause, settings (key remapping, volume, fullscreen)
- [ ] Replays: record the seed and the input for every tick, then play them back
- [ ] Local two-player, if the design calls for it

### Polish

- [ ] Hit feedback: flash, a few frames of hit stop, screen shake, particles, one sound per event
- [ ] Readability pass: enemy bullets contrast with every background
- [ ] Difficulty modes, and a practice mode that starts at any stage
- [ ] Online leaderboard that accepts a score only with a replay that reproduces it
- [ ] Accessibility: remapping, a palette safe for color blindness, an option to reduce flashing
- [ ] Touch controls, if you ship on phones
- [ ] Credits screen generated from `THIRD_PARTY.md`

## 3. Reference projects to study

**Taisei Project** ([repo](https://github.com/taisei-project/taisei)): `check first` in the catalog;
its `COPYING.txt` reads MIT for the code. C11 on SDL3 with an OpenGL renderer, and it runs in a
browser through WebGL. A vertical bullet hell. Stages are written as coroutines: in
`src/stages/stage1/timeline.c` each enemy is a `TASK` that moves, calls `WAIT(frames)`, then fires
a ring of projectiles, with `difficulty_value()` choosing a number per difficulty level. Replays in
`src/replay/` store press, release and axis events plus a desync-check event. Learn the coroutine
style for pattern scripting and the replay format for determinism.

**OpenTyrian** ([repo](https://github.com/opentyrian/opentyrian)): `study only` (GPL-2.0), C on
SDL2. A port of the DOS vertical shooter Tyrian with story, one- and two-player arcade modes and
networked play over UDP, with a lag-compensation delay set in frames (`--net-delay`) and hole
punching so players rarely open ports. Learn the weapon shop and upgrade economy between stages
(`doc/tools/weapon.py` decodes the weapon data) and how a two-player shooter shares one screen.

**Destination Sol** ([repo](https://github.com/MovingBlocks/DestinationSol)): `copy`
(Apache-2.0), Java on libGDX with Box2D. An arcade space shooter with Newtonian flight: "There are
no brakes! You have to turn and burn." Shields and armor are vulnerable to different weapons, and
abilities spend consumable charges. Ships, items, factions and sounds are JSON and assets under
`modules/core/assets/`. Learn how data-driven content lets a small team add ships without code.

**Open Hexagon** ([repo](https://github.com/vittorioromeo/SSVOpenHexagon)): `study only` in the
catalog (its source list says GPL-3.0); the repository's `LICENSE` file currently holds the
Academic Free License 3.0 text, so confirm before you treat it as anything but `study only`.
C++20 on SFML. "Four buttons, one goal: survive." Levels are packs of JSON plus Lua scripts
(`_RELEASE/Packs/*/Scripts/`), plus replays (`src/SSVOpenHexagon/Core/Replay.cpp`) and online
leaderboards. Learn how one tiny verb set carries a whole game when the patterns are scriptable.

**Curvytron** ([repo](https://github.com/Curvytron/curvytron)): `copy` (MIT), JavaScript. A
browser multiplayer Tron game with curves. Client and server share base models in `src/shared/`;
the server owns the simulation and indexes trail segments in a grid of `Island` cells for
collision (`src/server/core/Island.js`). Bonuses are split by target (`BonusSelf*`,
`BonusEnemy*`, `BonusGame*`), and rooms have a kick vote. Learn a small server-authoritative room
design you can copy.

**Pacman** ([repo](https://github.com/mumuy/pacman)): `copy` (MIT), JavaScript and canvas, 12
levels. `Map.prototype.finder` in `static/script/game.js` is a breadth-first search that wraps
through tunnels. A chasing ghost treats the other chasing ghosts as walls, so the pack spreads
out; a frightened ghost picks a random neighboring tile; an eaten ghost paths home. The README
asks for credit when you reuse it. Learn how little AI a maze chaser needs.

**Duck Hunt JS** ([repo](https://github.com/MattSurabian/DuckHunt-JS)): `copy` (MIT), JavaScript
with PixiJS, Howler and GreenSock. The whole difficulty curve is one table, `src/data/levels.json`
(waves, ducks, speed, bullets, hit radius, time per level), and audio ships as one audio sprite.
Learn to tune difficulty in data. Its dog and duck art recreates a commercial game's characters,
and the MIT license file says nothing about them.

**C-Dogs SDL** ([repo](https://github.com/cxong/cdogs-sdl)): `study only` (GPL-2.0, with
significant BSD-2-Clause portions), C on SDL2. An overhead run-and-gun for up to four players in
co-op and deathmatch, with a campaign editor (`src/cdogsed/`) and over 100 user campaigns. Its
data is CC0, CC-BY or CC-BY-SA per its README. Learn four-player local co-op and an editor that
turned players into level designers.

## 4. Reusable permissive code

Catalog projects keep the catalog's class. Libraries marked "not in the catalog" had their license
read from GitHub on 2026-09-23; re-read the LICENSE file at the commit you copy from.

| need | project | class | license |
|---|---|---|---|
| 2D physics for pinball, breakout variants, physics toys | [Box2D](https://github.com/erincatto/box2d) (C), [Chipmunk2D](https://github.com/slembcke/Chipmunk2D) (C) | `copy` | MIT |
| 2D physics in the browser | [matter-js](https://github.com/liabru/matter-js); Phaser bundles it under `src/physics/matter-js` | `copy` | MIT |
| maze chaser pathfinding with wraparound | `Map.prototype.finder` in [Pacman](https://github.com/mumuy/pacman) | `copy` | MIT |
| server-authoritative rooms in JavaScript | [Curvytron](https://github.com/Curvytron/curvytron) | `copy` | MIT |
| rooms and state sync as a framework | [Colyseus](https://github.com/colyseus/colyseus) (Node.js) | not in the catalog | MIT |
| peer-to-peer browser versus with rollback | [netplayjs](https://github.com/rameshvarun/netplayjs) (TypeScript) | `copy` | ISC |
| chiptune sound effects | [rFXGen](https://github.com/raysan5/rfxgen), a tool that exports `.wav` | `copy` | Zlib |
| tiny browser arcade framework | [crisp-game-lib](https://github.com/abagames/crisp-game-lib); [111 one-button games](https://github.com/abagames/111-one-button-games-in-2021) are built on it | not in the catalog; the games repo is `copy` | MIT |
| frame time overlay | [stats.js](https://github.com/mrdoob/stats.js) | `copy` | MIT |
| debug and tuning UI | [Dear ImGui](https://github.com/ocornut/imgui) (C++) | `copy` | MIT |

Taisei's coroutine scheduler (`src/coroutine/`) is a compact, readable pattern-scripting system,
and its `COPYING.txt` is MIT, but the catalog row is `check first`. Confirm the license at the
commit you would copy from and record it before you take a file.

## 5. Engine options (engine-neutral)

- **[Phaser](https://github.com/phaserjs/phaser)** (`copy`, MIT). Browser 2D with WebGL and Canvas
  rendering; ships Arcade and Matter physics (`src/physics/`). Tradeoff: no editor, and you build
  your own save, input remapping and replay layers.
- **[TIC-80](https://github.com/nesbox/TIC-80)** (`copy`, MIT). A fantasy computer: 240x136
  display, 16-color palette, built-in code, sprite, map, sound and music editors, games shipped as
  one cartridge, Lua and several other languages. Tradeoff: the limits are the point; outgrow them
  and you port.
- **[raylib](https://github.com/raysan5/raylib)** (`copy`, Zlib). A small C library for Windows,
  Linux, macOS, Raspberry Pi, Android and HTML5. Tradeoff: no scene system or editor; you own the
  architecture.
- **[LÖVE](https://github.com/love2d/love)** (`check first` in the catalog; its `license.txt` says
  zlib and bundles ENet under MIT). Lua 2D for Windows, macOS, Linux, Android and iOS. Tradeoff: a
  browser build is not in that list, so check web options before you commit.
- **[Godot](https://github.com/godotengine/godot)** (`copy`, MIT). An editor, 2D and 3D, tilemaps,
  and `enet` and `webrtc` modules for multiplayer. Tradeoff: more engine than a one-screen game
  needs, and major versions break projects.

## 6. Assets

Arcade games need little art but a lot of sound: every shot, hit, pickup and death wants its own
effect, and the music loops for minutes at a time.

- **[Kenney](https://kenney.nl/support):** "all game assets on the asset pages are public domain
  licensed (CC0)", including for commercial projects.
- **[OpenGameArt](https://opengameart.org/content/faq):** each asset has its own license (CC0,
  CC-BY, CC-BY-SA, OGA-BY, GPL). This chassis groups CC-BY-SA with `study only`, so filter for
  CC0 and CC-BY.
- **[Freesound](https://freesound.org/help/faq/):** licensed per sound; CC BY-NC forbids earning
  money with the result, and some older sounds still carry the retired Sampling+ license.
- **Make your own:** rFXGen (above) generates chiptune effects from presets such as coin, shoot,
  explosion and power-up.

**A code license says nothing about the art.** Destination Sol's code is Apache-2.0, but its
soundtrack is CC BY-NC 4.0, "free for our use with Destination Sol". Taisei's soundtrack and
character portraits are CC-BY 4.0, separate from its MIT code. Open Hexagon's sound effects may be
used only by Open Hexagon and never in commercial content. OpenTyrian's release builds include the
Tyrian 2.1 freeware data, released with one line of terms: "Feel free to play it all you want and
share it with friends." Nothing there grants reuse in a new game. SpaceCadetPinball is MIT on
GitHub but `check first` in the catalog, as a decompiled commercial game, and it plays only with
"original game resources (not included)". Record every asset in `THIRD_PARTY.md`
([template](../templates/THIRD_PARTY.md)).

## 7. Building it with AI tools

Follow the stages in [../ai/README.md](../ai/README.md): Claude plans and reviews, Codex takes one
scoped task at a time, Grok reviews blind. Arcade games are small enough that the risk is not scope
but feel, so every stage below ends in something you can play or replay.

1. *Design (Claude, plan mode):* "Using ../opensource/playbooks/arcade.md, write docs/design.md for
   a <subgenre> arcade game: the core loop, the verbs, how a run ends, the one mechanic that is
   new, and a slice of one screen, one enemy and one minute. Put the difficulty curve in a table:
   level, enemy speed, spawn interval, fire rate."
2. *Failure list (Claude writes, Codex attacks):* add arcade items to the template list: bullet
   speed that changes with frame rate, fast bullets passing through thin targets, an enemy
   spawning on the player, no invulnerability after respawn, a high score lost on quit, and input
   lost when three keys are held.
3. *Slice (Codex):* "Implement a fixed 60 Hz simulation step, a preallocated bullet pool of
   <N>, one enemy that moves in a sine wave and fires every <T> ticks, circle collision with a
   player hitbox of radius <r> pixels, lives, and restart. Seeded RNG only. Add a playtest script
   that survives 30 seconds by standing still in a known safe spot and asserts lives = 3."
4. *Patterns:* describe each wave in your own words ("five enemies enter from the top left,
   pause for one second, fire a ring of eight, exit right") and ask for a data format and a
   coroutine or timeline runner. Taisei is `check first` and Open Hexagon is `study only`: take
   the idea from them, not the code.
5. *Replays (Codex, then Claude reviews):* "Record the seed and each tick's input to a file;
   replay it headless and assert the final score and tick count match. Run the same replay at
   30, 60 and 144 Hz render rates." This doubles as the playtest harness in the AI guide.
6. *Blind review (Grok):* send the symptom and the files, not your theory: "Enemy bullets
   sometimes pass through the player at 144 Hz. Reproduce with: <command>."

**Playtest checklist:**

- [ ] A new player scores points in the first ten seconds without instructions
- [ ] Deaths feel fair to a watcher: the hit is visible and the hitbox matches expectation
- [ ] A recorded replay reproduces the same score at 30, 60 and 144 Hz
- [ ] Bullet speed and fire rate do not change with frame rate
- [ ] Restart from game over and from pause clears score, lives, bullets and timers
- [ ] The high score survives quitting and relaunching
- [ ] Every enemy bullet is readable on every background, including during screen shake
- [ ] The worst wave holds the target frame rate on the slowest target device

## 8. Genre-specific pitfalls

- **Frame-rate-dependent movement.** Speeds per rendered frame make the game harder on a fast
  monitor and break every replay. Step the simulation at a fixed rate.
- **Hitbox equals sprite.** Deaths from a pixel of overlap feel unfair. Keep the player's hitbox
  smaller than its art and consider showing it while focused or slowed.
- **Unreadable bullets.** Enemy shots must contrast with backgrounds, effects and each other.
  Test in grayscale.
- **Difficulty in code.** A curve spread across `if` statements cannot be tuned. Keep it in one
  table, as Duck Hunt JS does.
- **Nondeterminism.** Unseeded randomness, wall-clock reads, float drift and unordered hash map
  iteration all break replays and leaderboard validation. Taisei's replay format carries a
  desync-check event.
- **Trusting client scores.** An online leaderboard without replay validation fills with
  impossible scores. Accept a score only with a replay the server can re-run.
- **A clone's license is not the original's.** MIT on a remake covers its author's code, not the
  original game's name, characters, art or sound.
- **Ports run on data their code license does not cover.** SpaceCadetPinball needs the original
  game's resources, and OpenTyrian's Tyrian data is freeware to play and share, which is not a
  license to build a new game on.
- **Polishing forever.** Arcade games are small; the slice plus three enemy types and a boss is
  a finished game. Put it in front of players before adding a fourth enemy.
