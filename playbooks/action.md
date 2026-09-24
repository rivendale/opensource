# Action playbook

Beat 'em ups, hack and slash, and third-person action, plus the top-down action games the catalog
files here (bomb arenas, open-city reimplementations). The catalog lists 137 action projects, only
22 of them `copy` class, and many rows are GPL releases of commercial engines or reimplementations
that need the original game's data. The full table is in
[../catalog/action.md](../catalog/action.md). Two strong references live in neighboring genres
(OpenBOR under fighting, Punchy under platformer), so read those tables too. Every project named
below was checked against its repository on 2026-09-23.

## 1. What defines the genre

**Core loop:** enter an area, enemies engage, read their wind-ups, answer with attacks, blocks and
dodges, clear the group, move on; a boss closes the stage. Health is the resource you spend on
mistakes. Unlike a shooter, the threats are close, and every hit has weight: the enemy flinches,
stumbles or flies.

**Player verbs:** move (with a depth lane in a 2.5D brawler, free in 3D); light and heavy attacks
that chain into combos; block or parry; dodge or roll with a moment of invulnerability; jump;
grab and throw; pick up weapons and items; a special move with a cost; lock on to a target (3D).

**Win:** clear the stage and its boss. **Lose:** health and lives run out; in co-op, a downed
partner can often be revived. **Restart:** from the last checkpoint, fast.

**What makes it hard to build:** hit feel (hit stop, knockback, hitstun), frame timing (startup,
active and recovery frames for every attack), enemies that telegraph before they strike, a group of
enemies that does not attack all at once, and in 3D, a camera that never loses the fight.

## 2. The systems to build, in build order

### First playable vertical slice: one room, one enemy type, one combo

- [ ] Fixed-timestep simulation, with input buffered for a few ticks so presses are not lost
- [ ] State machine: idle, move, attack (startup, active, recovery), hitstun, knockdown, dead
- [ ] Hitboxes and hurtboxes per animation frame, stored as data next to the animation
- [ ] One three-hit combo, and a block or dodge with invulnerability frames
- [ ] One enemy: approach, visible wind-up, attack, back off
- [ ] Damage, knockback, and a few frames of hit stop on every connecting hit
- [ ] Camera that follows the player inside the room's bounds
- [ ] Health, death, and restart from the room's start

### v1

- [ ] Attack tokens: a coordinator lets only one or two enemies attack at a time
- [ ] Three or four enemy archetypes (rusher, blocker, ranged, heavy) and one boss with phases
- [ ] Weapons and throwable objects, grabs and throws
- [ ] Stage flow: lock the screen or arena until the wave is cleared, then open the way forward
- [ ] Local co-op for two players, with a friendly-fire setting
- [ ] Health bars, an enemy health bar on hit, a combo counter
- [ ] Checkpoints and save
- [ ] Fighters, enemies and attacks as data files, so tuning needs no rebuild

### Polish

- [ ] Hit stop, shake and knockback scaled by attack weight; hit sparks and layered sounds
- [ ] Cancel windows (attack into dodge, attack into special) tuned in playtests
- [ ] 3D: lock-on, camera collision, and a camera that frames both player and target
- [ ] Death animations or ragdolls that do not block the next fight
- [ ] Difficulty settings; hold or toggle for block; full remapping
- [ ] Record where players die in playtests and retune those encounters

## 3. Reference projects to study

**Overgrowth** ([repo](https://github.com/WolfireGames/overgrowth)): `copy` (Apache-2.0), C++ with
AngelScript. 3D melee combat. Character behavior is scripted, and one file,
`Data/Scripts/aschar.as`, holds timed active blocks and dodges, parrying and catching thrown
weapons, knockback multipliers, and an active ragdoll that takes fall and injured poses and
recovers. The README says only the code is here: the art and levels "can only be legally obtained
by purchasing" the game, though "total conversions" with entirely new assets are allowed. Learn
physically reactive melee and timing-based defense.

**OpenBOR** ([repo](https://github.com/DCurrent/openbor)): `copy` (BSD-3-Clause), C. A "royalty
free sprite-based side scrolling gaming engine" optimized for beat 'em ups, cataloged under
fighting. Its script API (`engine/source/openborscript/`) exposes separate attack and body
collision boxes, command input for special moves, factions, and x, y, z axes with an x-z plane for
depth. Learn how a mature brawler engine models the genre; it is also an engine choice (section 5).

**Fish Folk: Punchy** ([repo](https://github.com/fishfolk/punchy)): `check first` in the catalog,
filed under platformer; its `LICENSE.md` says the code is MIT or Apache-2.0 at your option and the
media is CC BY-NC. Rust on Bevy, last pushed 2024-06-06. A 2.5D beat 'em up whose fighters are YAML
(`assets/fighters/*/*.fighter.yaml`): hurtbox, stats, animations by frame range, and attacks with
damage, startup, active and recovery frames, hitbox and hitstun. Learn the data format: the attack
in `fishy.fighter.yaml` is ten lines.

**SDLPoP** ([repo](https://github.com/NagyD/SDLPoP)): `check first` in the catalog; its code is
GPL-3.0, but it is a port of the DOS Prince of Persia built from its disassembly, and the catalog
marks decompiled commercial games as legally unclear. C on SDL2. Every move is a named entry in a
sequence table (`src/seqtbl.c`): strike, block, advance, retreat, blocked strike, block to strike,
run jump, hang. Sword fighting is transitions between those sequences. It also records replays.
Learn how to make combat readable by building it from short, committed animations.

**Mr.Boom** ([repo](https://github.com/Javanaise/mrboom-libretro)): `copy` (MIT), C converted from
DOS assembly, with bots in C++. A Bomberman clone for up to eight players, as a libretro core and
as a standalone SDL2 game, with netplay through RetroArch. The bots in `ai/` run a small behavior
tree (a C++98 port with `Selector` and `Sequence` nodes) over grid helpers in `GridFunctions.cpp`.
Learn a behavior tree small enough to read in one sitting, and eight-player local chaos.

**Carnage3D** ([repo](https://github.com/codenamecpp/carnage3d)): `copy` (MIT), C++. A
reimplementation of the first top-down Grand Theft Auto: walk, drive, shoot, up to four players in
split screen. Built on Box2D, with pedestrian AI (`AiPedestrianBehavior.cpp`), a console with
variables and Dear ImGui debug windows. Its README says "Original GTA1 game resources required".
Learn how a small team structures an open-city action game, and how much a debug console helps.

## 4. Reusable permissive code

Catalog projects keep the catalog's class. Libraries marked "not in the catalog" had their license
read from GitHub on 2026-09-23; re-read the LICENSE file at the commit you copy from.

| need | project | class | license |
|---|---|---|---|
| 2D physics and collision | [Box2D](https://github.com/erincatto/box2d) (C), [Chipmunk2D](https://github.com/slembcke/Chipmunk2D) (C) | `copy` | MIT |
| 3D physics, ragdolls | [Jolt Physics](https://github.com/jrouwe/JoltPhysics) (C++); Godot ships a `jolt_physics` module | not in the catalog | MIT |
| 3D enemy navigation | [Recast Navigation](https://github.com/recastnavigation/recastnavigation) (C++) | not in the catalog | Zlib |
| small behavior tree | `ai/bt/` in [Mr.Boom](https://github.com/Javanaise/mrboom-libretro) (C++98) | `copy` | MIT |
| entity-component-system | [EnTT](https://github.com/skypjack/entt) (C++), [flecs](https://github.com/SanderMertens/flecs) (C, C++) | not in the catalog | MIT (GitHub reads flecs as unknown; its LICENSE file is MIT) |
| online co-op or versus with rollback | [GekkoNet](https://github.com/HeatXD/GekkoNet) (C, C++), [Backdash](https://github.com/Delta3-Studio/Backdash) (C#), [netplayjs](https://github.com/rameshvarun/netplayjs) (TypeScript) | `copy` | BSD-2-Clause, MIT, ISC |
| a sprite brawler engine to build on or read | [OpenBOR](https://github.com/DCurrent/openbor) (C) | `copy` | BSD-3-Clause |
| fighter and attack data format | `*.fighter.yaml` in [Punchy](https://github.com/fishfolk/punchy) | `check first` | MIT or Apache-2.0 per its `LICENSE.md` |
| hitbox viewer and tuning panels | [Dear ImGui](https://github.com/ocornut/imgui) (C++) | `copy` | MIT |

Rollback matters only if you ship online play; local co-op needs none of it. If you do, read the
[fighting playbook](fighting.md), which covers rollback in depth.

## 5. Engine options (engine-neutral)

- **[Godot](https://github.com/godotengine/godot)** (`copy`, MIT). An editor, 2D and 3D, with
  `jolt_physics`, `navigation_2d`, `navigation_3d` and `multiplayer` modules in the engine
  source. Tradeoff: frame-exact combat means driving animation from your own fixed tick rather
  than letting the animation system own timing.
- **[MonoGame](https://github.com/MonoGame/MonoGame)** (`check first` in the catalog: its list says
  MS-PL and MIT, and GitHub could not read the license; `LICENSE.txt` is MS-PL). A C#
  reimplementation of XNA; its README lists Streets of Rage 4 among the games made with it, and
  console support for registered developers. Tradeoff: code first; you build or adopt the editor.
  MS-PL is weak copyleft: modified MonoGame source you distribute stays MS-PL; your game code does
  not.
- **[Bevy](https://github.com/bevyengine/bevy)** (not in the catalog; `LICENSE-MIT` and
  `LICENSE-APACHE`). Rust with an ECS at the core; Punchy is built on it. Tradeoff: its README
  says it is "still in the early stages" and ships breaking releases about every three months.
- **[OpenBOR](https://github.com/DCurrent/openbor)** (`copy`, BSD-3-Clause). If the game is a 2D
  sprite brawler, the engine already exists, on Android, Linux, macOS and Windows. Tradeoff: its
  own module format and script language, and a 2D sprite pipeline only.

## 6. Assets

Action games are animation-heavy: every attack needs readable startup, a clear hit frame and
recovery, and every enemy needs hit, knockdown and getting-up animations.

- **[Kenney](https://kenney.nl/support):** "all game assets on the asset pages are public domain
  licensed (CC0)", including for commercial projects.
- **[Quaternius](https://quaternius.com/license.html):** not CC0 any more. The Quaternius Asset
  License v1.0 (2026-08-28) allows commercial games with no credit, but forbids redistributing the
  assets as assets, including in a template or asset pack, so keep them out of a public starter repo.
  Useful for 3D prototypes and third-person action.
- **[OpenGameArt](https://opengameart.org/content/faq):** each asset has its own license (CC0,
  CC-BY, CC-BY-SA, OGA-BY, GPL). This chassis groups CC-BY-SA with `study only`, so filter for
  CC0 and CC-BY.
- **[Freesound](https://freesound.org/help/faq/):** licensed per sound; CC BY-NC forbids earning
  money with the result. Search for impact sounds first.

**A code license says nothing about the art.** Overgrowth is Apache-2.0 code with commercial assets
you may not redistribute. Punchy's code is MIT or Apache-2.0 while its media is CC BY-NC. Carnage3D
needs the original game's resources. SDLPoP's repository ships the game's `.DAT` data files in
`data/`, which its GPL code license does not make reusable. OpenBOR's README records that the
original Beats of Rage used assets from SNK's King of Fighters, and community modules for brawler
engines often reuse commercial characters: trace every file before you ship it. Record every asset
in `THIRD_PARTY.md` ([template](../templates/THIRD_PARTY.md)).

## 7. Building it with AI tools

Follow the stages in [../ai/README.md](../ai/README.md): Claude plans and reviews, Codex takes one
scoped task at a time, Grok reviews blind. Action combat is tuning more than code, so make every
number a data value a person can change during a playtest.

1. *Design (Claude, plan mode):* "Using ../opensource/playbooks/action.md, write docs/design.md for
   a <2.5D brawler, 3D hack and slash>: verbs, one combo, one enemy, one room. List every attack
   with damage, startup, active and recovery frames, and hitstun, as a table."
2. *Failure list:* add action items to the template list: a hit registered twice by one swing,
   an attack whose active frames skip past a fast enemy, invulnerability that outlasts the dodge,
   enemies stacking on one spot, hitstun that locks a player forever, and a camera that shows a
   wall instead of the fight.
3. *Combat core (Codex):* "Implement a character state machine driven by a fixed tick. Attacks
   come from data/fighters/*.yaml with startup, active and recovery frames and per-frame hitboxes.
   A hitbox can hit each hurtbox once per attack. Add a debug overlay that draws hitboxes and
   hurtboxes. Playtest script: a light attack at frame 10 hits a dummy placed in range exactly
   once; a dummy one pixel out of range takes no damage."
4. *Enemy AI:* describe behaviors in your own words ("waits at medium range, takes an attack token,
   winds up for 20 ticks, lunges, backs off") and ask for a behavior tree or state machine, plus
   an attack-token coordinator with a configurable limit. SDLPoP is `check first`: take its ideas,
   not its code.
5. *Feel pass (Claude reviews, a person decides):* ask for a list of every hit stop, knockback
   and shake value in the code, moved into one data file with comments, so tuning is one file.
6. *Blind review (Grok):* send the symptom and the files: "The third hit of the combo sometimes
   misses an enemy standing in range. Reproduce with: <command>."

**Playtest checklist:**

- [ ] A new player lands a combo and dodges an attack in the first minute without instructions
- [ ] Every enemy attack has a wind-up a watcher can name before it lands
- [ ] One swing never damages the same enemy twice
- [ ] A dodge started during an enemy's active frames avoids the hit
- [ ] Three or more enemies never attack in the same instant unless the design says so
- [ ] Combat behaves the same at 30, 60 and 144 Hz render rates
- [ ] Two local players can each tell which character is theirs in a crowded fight
- [ ] In 3D, the camera keeps the player and the current target on screen in every arena

## 8. Genre-specific pitfalls

- **Animation owns timing.** If hit frames depend on the animation player's clock, combat changes
  with frame rate and with every re-export of an animation. Drive gameplay from ticks and data.
- **No hit stop.** Hits without a few frames of freeze feel weightless no matter how good the art.
- **Enemies attack in a mob.** Without attack tokens a crowd lands every hit at once and the fight
  is unfair. Ration attacks.
- **Telegraphs too short or unreadable.** If a watcher cannot say what an enemy is about to do,
  players cannot learn the fight.
- **Hitboxes as sprite bounds.** A sword that hits behind the player feels broken. Define boxes per
  frame in data, as OpenBOR and Punchy do, and draw them in a debug view.
- **Stun locks.** Hitstun longer than the attacker's recovery, repeated, pins a player or a boss
  forever. Cap juggles or add escape options.
- **Camera last.** In 3D the camera decides whether combat is playable. Build it with the first
  enemy, not after the tenth.
- **Reimplementations are not asset licenses.** Carnage3D, SDLPoP and many action rows run on data
  their code license does not cover.
- **Content cost.** Each enemy needs a full animation set. Ship three finished enemies before you
  design a tenth.
