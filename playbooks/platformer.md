# Platformer playbook

2D and 3D platformers: jump-and-run, precision platformers, momentum platformers in the 16-bit
style, and puzzle platformers. The catalog lists 104 platformer projects, 16 of them `copy` class;
the full table is in [../catalog/platformer.md](../catalog/platformer.md). Many rows are ports that
need a commercial game's data, and a few neighbors (a beat 'em up, a typing game) landed here, so
read a row before you rely on it. Every project named below was checked against its repository on
2026-09-23.

## 1. What defines the genre

**Core loop:** run, jump, avoid hazards and enemies, reach the end of the level; die, respawn a
few seconds back, and try again with what you learned. The game is the player's mastery of one
movement model, and each level teaches a mechanic, tests it, then twists it.

**Player verbs:** run; jump, with height controlled by how long the button is held; fall; wall
jump or wall slide; dash; climb; crouch; stomp or attack; carry and throw; swim. Some games replace
the jump entirely: in VVVVVV the one movement verb is flipping gravity.

**Win:** reach the exit, flag or door; beat the final boss; optionally collect everything.
**Lose:** a pit, a hazard, or health running out; lives are optional and many modern platformers
drop them. **Restart:** at the last checkpoint, in about a second.

**What makes it hard to build:** controller feel (acceleration, air control, gravity, jump
buffering, coyote time), collision against tiles, slopes, one-way and moving platforms, a camera
that shows where you are about to land, and levels that teach without text.

## 2. The systems to build, in build order

### First playable vertical slice: one level, sixty seconds

- [ ] Fixed-timestep simulation; jump height must not depend on frame rate
- [ ] A tile map made in a level editor (Tiled or LDtk) and loaded at startup
- [ ] Character controller: run with acceleration and friction, gravity with a maximum fall speed
- [ ] Variable jump height: releasing the button early cuts the jump
- [ ] Coyote time and a jump buffer (SuperTux uses 0.1 s and 0.25 s)
- [ ] Tile collision resolved one axis at a time, so seams between tiles never snag
- [ ] One hazard, one enemy that walks and turns at ledges, a stomp that defeats it
- [ ] A checkpoint, respawn, and a level exit
- [ ] Camera that follows with a dead zone and stays inside the level's bounds

### v1

- [ ] Slopes, one-way platforms, and moving platforms that carry the player
- [ ] One signature mechanic (wall jump, dash, gravity flip, grapple) that levels are built around
- [ ] Three or four enemy types and one boss
- [ ] Collectibles, a level select or world map, and saved progress
- [ ] Camera look-ahead in the running direction and a locked vertical position on the ground
- [ ] Pause, settings, gamepad support, and key remapping
- [ ] Reload a level from the editor without restarting the game
- [ ] Recorded input replays that run in CI as regression tests

### Polish

- [ ] Landing dust, squash and stretch, and a distinct sound for jump, land, hurt and collect
- [ ] Assist options: slower game speed, extra jumps, invincibility
- [ ] A speedrun timer, and physics that stay stable once levels ship
- [ ] Secrets that reward exploring off the main path
- [ ] Controller dead zones, and rumble on hits
- [ ] Translation, if you have text

## 3. Reference projects to study

**SuperTux** ([repo](https://github.com/SuperTux/supertux)): `study only` (GPL-3.0), C++ on SDL2.
A jump-and-run with worlds, a world map, a built-in level editor (`src/editor/`) and Squirrel
scripting (`src/squirrel/`). In `src/object/player.cpp`, `JUMP_GRACE_TIME = 0.25f` accepts a jump
pressed shortly before landing and `COYOTE_TIME = 0.1f` allows one shortly after leaving a ledge.
The camera (`src/object/camera.hpp`) has normal, manual, free, autoscroll and scroll-to modes, with
look-ahead and peek. Learn the feel constants and the camera modes; the README says most of the
data is CC-BY-SA.

**AAAAXY** ([repo](https://github.com/divVerent/aaaaxy)): `copy` (Apache-2.0), Go on Ebitengine.
A nonlinear puzzle platformer in impossible spaces, shipped on desktop, Android, iOS and the web.
Levels come from Tiled (`assets/maps/level.tmx`). CI replays recorded demos
(`assets/demos/_100percent_*.dem`) through `scripts/regression-test-demo.sh` and checks the
completion time, so a physics change that breaks a route fails the build. Each third-party asset
has its own license and copyright file under `licenses/`. Learn replay-based regression testing and
asset bookkeeping you can copy.

**Open Surge** ([repo](https://github.com/alemart/opensurge)): `study only` (GPL-3.0), C on Allegro
with its own SurgeScript language. An engine for games in the style of 16-bit Sonic. The physics
actor (`src/physics/physicsactor.c`) switches between floor, right wall, ceiling and left wall
movement modes by angle, reads the ground through sensors, and applies slope factors for rolling
uphill and downhill. Learn momentum platforming on slopes and loops, which a plain box-and-tiles
controller does not handle.

**VVVVVV** ([repo](https://github.com/TerryCavanagh/VVVVVV)): `check first` (custom license). Its
source license forbids commercial use, and the repository "does not, however, contain any of the
icons, art, graphics or music". C++ on SDL2. Gravity flips only while standing on a floor or
ceiling (`game.gravitycontrol` in `desktop_version/src/Input.cpp`), which makes one verb carry the
whole game. `GlitchrunnerMode.h` restores the physics quirks of older versions on request, so
speedrun routes survive bug fixes. It also has an in-game editor. Learn single-verb design and how
to change physics without breaking a community.

**2D Platformer Hunter** ([repo](https://github.com/ta-david-yu/2D-Platformer-Hunter)): `copy`
(MIT), C# for Unity, last pushed 2024-04-03. A raycast-based controller split into Input,
Controller and Motor: the input can be a player or a waypoint AI, and motors can carry other
motors (moving platforms). Features jump buffering, coyote time, variable jump height, wall and air
jumps, ladders, ledge grabs and one-way platforms (`Runtime/Core/`). Learn the split, and copy the
controller if you use Unity.

**doukutsu-rs** ([repo](https://github.com/doukutsu-rs/doukutsu-rs)): `copy` (MIT), Rust, filed
under other in the catalog. A reimplementation of the Cave Story engine that runs the freeware,
Cave Story+ and Switch data, none of which the repository contains. Its platform layer
(`src/framework/`) sits behind backends for SDL2, glutin, the Switch and a null backend. Learn how
to keep the game independent of the platform, and why a headless backend makes automated tests
possible.

## 4. Reusable permissive code

Catalog projects keep the catalog's class. Libraries marked "not in the catalog" had their license
read from GitHub on 2026-09-23; re-read the LICENSE file at the commit you copy from.

| need | project | class | license |
|---|---|---|---|
| a complete 2D controller for Unity | [2D Platformer Hunter](https://github.com/ta-david-yu/2D-Platformer-Hunter) (C#) | `copy` | MIT |
| AABB collision that handles tunneling, in Lua | [bump.lua](https://github.com/kikito/bump.lua) | not in the catalog | MIT |
| level editor | [LDtk](https://github.com/deepnight/ldtk) | not in the catalog | MIT |
| level editor with a separately licensed loader | [Tiled](https://github.com/mapeditor/tiled): editor GPL, `src/libtiled` BSD-2-Clause per its `COPYING` | `check first` | GPL and BSD-2-Clause |
| replay regression tests and Tiled maps in Go | [AAAAXY](https://github.com/divVerent/aaaaxy) | `copy` | Apache-2.0 |
| platform backends behind one interface, in Rust | `src/framework/` in [doukutsu-rs](https://github.com/doukutsu-rs/doukutsu-rs) | `copy` | MIT |
| 2D physics for physics-driven platformers | [Box2D](https://github.com/erincatto/box2d), [Chipmunk2D](https://github.com/slembcke/Chipmunk2D) | `copy` | MIT |
| jump, coin and hurt sound effects | [rFXGen](https://github.com/raysan5/rfxgen), a tool that exports `.wav` | `copy` | Zlib |
| live tuning panel for jump constants | [Dear ImGui](https://github.com/ocornut/imgui) (C++) | `copy` | MIT |

Authoring maps in Tiled copies none of its code. If you need a loader, take one from `libtiled` or
write your own against the documented format.

## 5. Engine options (engine-neutral)

- **[Godot](https://github.com/godotengine/godot)** (`copy`, MIT). An editor with tilemaps and 2D
  physics (`tilemap` and `godot_physics_2d` modules). Tradeoff: the physics module will not tune
  feel for you; a tight controller is still your own movement code on a kinematic body.
- **[Phaser](https://github.com/phaserjs/phaser)** (`copy`, MIT). Browser 2D with Arcade and Matter
  physics (`src/physics/`). Tradeoff: no editor; pair it with Tiled or LDtk.
- **[HaxeFlixel](https://github.com/HaxeFlixel/flixel)** (`copy`, MIT). A 2D engine on Haxe and
  OpenFL that compiles to native targets. Tradeoff: you work in Haxe, and native builds go
  through the Haxe and OpenFL toolchains.
- **[Ebitengine](https://github.com/hajimehoshi/ebiten)** (not in the catalog; Apache-2.0). A 2D
  engine for Go on Windows, macOS, Linux, Android, iOS, WebAssembly and Switch; AAAAXY is built on
  it. Tradeoff: an API, not an editor; you bring the level tools.
- **[LÖVE](https://github.com/love2d/love)** (`check first` in the catalog; its `license.txt`
  says zlib). Lua 2D for Windows, macOS, Linux, Android and iOS; bump.lua fits it. Tradeoff: no
  browser target in that list.

## 6. Assets

A platformer needs a tileset that reads clearly (what is solid, what hurts, what is background), a
character with run, jump, fall, land and hurt animations, and short, loopable music.

- **[Kenney](https://kenney.nl/support):** "all game assets on the asset pages are public domain
  licensed (CC0)", including for commercial projects.
- **[OpenGameArt](https://opengameart.org/content/faq):** each asset has its own license (CC0,
  CC-BY, CC-BY-SA, OGA-BY, GPL). This chassis groups CC-BY-SA with `study only`, so filter for
  CC0 and CC-BY.
- **[Freesound](https://freesound.org/help/faq/):** licensed per sound; CC BY-NC forbids earning
  money with the result.
- **Copy AAAAXY's bookkeeping.** Every third-party asset has a `licenses/asset-<name>-LICENSE.txt`
  and a matching `COPYRIGHT` file; one sprite pack there is CC0. It is a working model for
  `THIRD_PARTY.md`.

**A code license says nothing about the art.** SuperTux's code is GPL-3.0 and most of its data is
CC-BY-SA. Open Surge's `licenses/` folder holds eleven license texts, from CC0 and CC-BY through
CC-BY-SA, GPL, OFL and the Giftware license. VVVVVV's art and music stay proprietary. doukutsu-rs
runs only on Cave Story data it does not include. 2D Platformer Hunter credits its sample character
sprites to a separate itch.io pack; check that pack's terms before you ship them. Record every
asset in `THIRD_PARTY.md` ([template](../templates/THIRD_PARTY.md)).

## 7. Building it with AI tools

Follow the stages in [../ai/README.md](../ai/README.md): Claude plans and reviews, Codex takes one
scoped task at a time, Grok reviews blind. A platformer lives or dies on numbers a person has to
feel, so the AI builds the tuning tools and a person turns the knobs.

1. *Design (Claude, plan mode):* "Using ../opensource/playbooks/platformer.md, write
   docs/design.md: the signature mechanic, the verbs, and a slice of one level that introduces the
   mechanic, tests it, then twists it. List every movement constant (run speed, acceleration,
   gravity, jump velocity, maximum fall speed, coyote time, jump buffer) in one table with a
   starting value."
2. *Failure list:* add platformer items to the template list: snagging on the seam between two
   floor tiles, jump height changing with frame rate, falling through a moving platform, a jump
   eaten when pressed a frame before landing, being crushed with no death, and the camera
   hiding the landing spot on a long fall.
3. *Controller (Codex):* "Implement a kinematic character controller with fixed-step movement
   and per-axis tile collision. Read every constant from data/movement.json and hot-reload it.
   Add coyote time and a jump buffer. Playtest scripts: run across a flat floor of 40 tiles and
   assert y never changes; press jump 3 ticks before landing and assert a jump starts."
4. *Levels:* ask for a loader for your editor's format that rejects unknown tile types and
   missing spawn points with the file and position, then a level-reload key.
5. *Replays in CI (Codex, then Claude reviews):* "Record input per tick and replay headless;
   assert the level is finished and the tick count matches. Add a CI job that runs every replay
   in playtest/replays/." AAAAXY's workflow is the model: a physics change that breaks a route
   fails the build.
6. *Blind review (Grok):* send the symptom and the files: "The player sometimes stops dead when
   running across flat ground. Reproduce with: <command>."

**Playtest checklist:**

- [ ] A new player clears the first screen without instructions
- [ ] Jump pressed just before landing, or just after leaving a ledge, still jumps
- [ ] Running across any flat floor never snags on a tile seam
- [ ] Jump height and run speed match at 30, 60 and 144 Hz render rates
- [ ] Moving platforms carry the player and never drop them through
- [ ] Death to control again takes about a second
- [ ] On every long fall, the landing spot is on screen before you reach it
- [ ] Every recorded replay still finishes its level on the current build

## 8. Genre-specific pitfalls

- **A general physics engine for the player.** Rigid bodies make controls floaty and catch on
  edges. Use a kinematic controller unless physics is the point of the game.
- **Tile seams.** Resolving both axes at once lets the corner between two floor tiles push the
  player sideways or stop it dead. Resolve one axis at a time.
- **"The game ate my jump."** Without a jump buffer and coyote time, correct inputs fail by a frame
  or two, and players blame the game.
- **Frame-rate-dependent jumps.** Integrating gravity per rendered frame changes jump height with
  the monitor. Step at a fixed rate.
- **A camera that hides the landing.** Look ahead in the direction of travel and down on falls.
- **Slow respawns.** Precision platformers ask for hundreds of deaths; every second of respawn is
  multiplied by all of them.
- **Changing physics after levels exist.** Every level and every speedrun route depends on the
  constants. Freeze them early, run replays in CI, and if you must change them, consider keeping
  the old behavior as an option, as VVVVVV does.
- **Share-alike and proprietary art.** SuperTux's data is mostly CC-BY-SA; VVVVVV's art is
  proprietary. Check the art, not just the code.
- **Ports that need data you do not have.** doukutsu-rs and many catalog rows run on commercial
  game files their code license does not cover.
