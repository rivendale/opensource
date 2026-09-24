# RPG playbook

Role-playing games: turn-based and action, from monster collectors and console-style RPGs to party
CRPGs, open worlds and tactics. The catalog lists 234 RPG projects, 37 of them `copy` class; the
full table is in [../catalog/rpg.md](../catalog/rpg.md). Some rows are misfiled neighbors (a few
card and board games), so read before you rely on a row. Every project named below was checked
against its repository on 2026-09-23.

## 1. What defines the genre

**Core loop:** explore, meet a challenge (a fight, a conversation, a locked door), earn a reward
(experience, items, money, a story flag), grow the character, then take on harder content. What
makes it an RPG rather than an action or adventure game is that **character power grows
separately from player skill**: a fight you lost at level 3 is winnable at level 6.

**Player verbs:** move and explore; talk and choose a reply; fight (attack, use a skill, use an
item, defend, flee); manage (equip, sort inventory, spend skill points, arrange the party); trade;
rest and save; accept and turn in quests.

**Win:** finish the main quest line, usually a final boss or story ending; many games keep going
afterward. **Lose:** the party is defeated, which sends the player back to the last save. Losing is
a setback, not the end of the game, so save placement is part of the difficulty design.

**Pick the subgenre before anything else**, because each one needs a different combat system:

| subgenre | combat | study in the catalog |
|---|---|---|
| monster collector | turn-based, one-on-one or small teams | Tuxemon |
| console-style (RPG Maker style) | turn-based menus, side or front view | EasyRPG Player |
| party CRPG | real-time with pause, isometric | GemRB |
| open-world first person | real-time | OpenMW, Daggerfall Unity |
| action RPG, Zelda-like | real-time, top-down | TetraForce, Veloren |
| tactics | turn-based on a grid | RPG Tactical Fantasy Game |

## 2. The systems to build, in build order

### First playable vertical slice: one town, one dungeon, one boss

- [ ] Tile map loaded from an editor file (Tiled or the engine's own), with a collision layer
- [ ] Player movement, camera follow, and a door that loads the next map
- [ ] Interact: talk to one NPC, open one chest
- [ ] Dialogue box with one branching choice, text read from a data file, never from code
- [ ] A global flag store (`town.elder.met = true`) that dialogue and events read and write
- [ ] One combat encounter: turn order, attack, one skill, one item, an enemy that picks an action,
      victory and defeat screens (or, for action RPGs: hitboxes, knockback, invulnerability frames)
- [ ] Stats: HP, one resource (MP or stamina), attack, defense; the damage formula in one function
- [ ] Experience and one level-up
- [ ] Inventory with three kinds of item: consumable, equipment, key item
- [ ] Save and load: flags, party, inventory, map and position
- [ ] Defeat returns the player to the last save

**Done when** a stranger plays from the title screen to the boss without being told what to do.

### v1

- [ ] Content database: monsters, items, skills, NPCs, encounters and quests as JSON, YAML or RON
      files, validated at load (missing id, dangling reference, duplicate id, wrong type)
- [ ] Map events as conditions plus actions in data, so writers add content without programmers
- [ ] Quest log with states: not started, active, complete, failed
- [ ] Party with equipment slots and formation; status effects with durations
- [ ] Shops and an economy with money sinks, so gold keeps meaning something
- [ ] Encounter tables per zone, or placed enemies with respawn rules
- [ ] Menus: status, equipment, items, skills, save, options, input rebinding
- [ ] Strings by id, ready for translation
- [ ] A headless battle simulator that runs thousands of fights and reports win rates
- [ ] A save format version number and a migration step per version

### Polish

- [ ] Screen transitions, hit feedback, damage numbers, camera shake in action combat
- [ ] Music per area and for battles, UI sounds
- [ ] Gamepad support, text speed, font size, readable contrast
- [ ] Autosave on map change, several slots
- [ ] Bestiary, achievements, difficulty options, new game plus
- [ ] A developer console for teleporting, setting flags and spawning items
- [ ] Optional mod support: content folders loaded in a declared priority order

## 3. Reference projects to study

**Tuxemon** ([repo](https://github.com/Tuxemon/Tuxemon)): `study only` (GPL-3.0), Python on pygame.
Monster-fighting RPG. All game data is JSON under `mods/tuxemon/db/` (monster, technique, item,
npc, encounter, mission, economy and more). Maps come from Tiled, and each map has a YAML file of
events written as `conditions` and `actions` (for example: if a variable is not set, lock
controls, show two translated dialog lines, set the variable). Each action is one small module in
`tuxemon/event/actions/`. Combat lives in `tuxemon/combat/` as an action queue plus a state
machine. It also has a CLI for live debugging. Learn the event model: it is the cleanest way to
let non-programmers write story.

**EasyRPG Player** ([repo](https://github.com/EasyRPG/Player)): `study only` (GPL-3.0), C++.
An interpreter for RPG Maker 2000 and 2003 games. The event interpreter is split into map, battle
and shared parts (`src/game_interpreter*.cpp`); switches and variables form the global flag store
(`game_switches.cpp`, `game_variables.cpp`); two battle styles sit side by side
(`scene_battle_rpg2k.cpp`, `scene_battle_rpg2k3.cpp`). Learn how far a small event command set
(show message, set switch, branch on condition, move an event) carries a full game.

**GemRB** ([repo](https://github.com/gemrb/gemrb)): `study only` (GPL-2.0), C++ engine with Python
UI. A reimplementation of the engine behind the Baldur's Gate games; it ships a tiny demo that runs
without the original data. The rules engine is C++, while every window and menu is a Python script
in `gemrb/GUIScripts/`, and creature AI and cutscenes are trigger and action scripts
(`gemrb/core/GameScript/`). Learn to keep UI out of the rules engine.

**Daggerfall Unity** ([repo](https://github.com/Interkarma/daggerfall-unity)): `copy` (MIT), C# on
Unity. Needs the original game data to run; its README points to a free copy on Steam. Quests are
text scripts in `Assets/StreamingAssets/Quests/`, parsed (`Questing/Parser.cs`) into resources
(Person, Place, Item, Foe, Clock) and tasks run by `Questing/QuestMachine.cs`. Game formulas live
in one file, `Formulas/FormulaHelper.cs`, whose `RegisterOverride` lets a mod replace a single
formula. The code may be copied, but it is written against the Unity editor, which has its own
license terms.

**OpenMW** ([repo](https://github.com/OpenMW/openmw)): `study only` (GPL-3.0), C++. An open-world
engine that plays Morrowind with the player's own copy. Data directories and content files load in
order, and later ones take priority (`--data`, `--content`); Lua scripts attach to contexts such
as `MENU`, `PLAYER` and `GLOBAL` through `files/data/builtin.omwscripts`; the editor is a separate
app (`apps/opencs`). Learn content layering: it is what makes a world moddable without patching
the base game.

**Veloren** ([repo](https://github.com/veloren/veloren)): `study only` (GPL-3.0), Rust. A
multiplayer voxel action RPG. The workspace splits `client`, `server`, `common`, `world` and
`rtsim` crates; `common` uses the specs ECS; items, loot tables, skill trees, recipes and abilities
are RON files under `assets/common/`; `rtsim` runs a low-resolution simulation of the whole world,
including NPCs and factions outside loaded chunks. Learn the crate split and the data layout; it is
far too large to start from.

**TetraForce** ([repo](https://github.com/loudsmilestudios/TetraForce)): `copy` (MIT), GDScript on
Godot. A small Zelda-style action RPG with online co-op. `engine/network.gd` records which player
hosts each map (`map_hosts`) and ticks every 0.05 seconds; NPC and sign text is JSON under
`dialogue/`; maps come in through a Tiled importer addon; the player and every enemy extend one
`Entity` class (`entities/entity.gd`). The project file is Godot 3 format, so expect porting work
on Godot 4.

**RPG Tactical Fantasy Game** ([repo](https://github.com/Grimmys/rpg_tactical_fantasy_game)):
`study only` (GPL-3.0), Python on pygame. Grid tactics with inventory and classes. Balance values
live in `data/` (`foes.xml`, `items.xml`, `skills.xml`, `classes.json`), and its README asks
contributors to balance by editing those files. Learn to keep every number outside the code.

## 4. Reusable permissive code

Catalog projects keep the catalog's class. Libraries marked "not in the catalog" had their license
read from GitHub on 2026-09-23; re-read the LICENSE file before you copy anything.

| need | project | class | license |
|---|---|---|---|
| grid pathfinding, field of view, dice parser, timed effects | [GoRogue](https://github.com/Chris3606/GoRogue) (C#) | `copy` | MIT |
| branching dialogue | [ink](https://github.com/inkle/ink) (C#) and [inkjs](https://github.com/y-lohse/inkjs) | not in the catalog | MIT |
| dialogue with engine integrations | [Yarn Spinner](https://github.com/YarnSpinnerTool/YarnSpinner) | not in the catalog | MIT |
| dialogue in Godot | [Dialogic](https://github.com/dialogic-godot/dialogic), [Godot Dialogue Manager](https://github.com/nathanhoad/godot_dialogue_manager) | not in the catalog | MIT |
| ECS | [EnTT](https://github.com/skypjack/entt) (C++), [flecs](https://github.com/SanderMertens/flecs) (C, C++) | not in the catalog | MIT (GitHub reads flecs as unknown; its LICENSE file is MIT) |
| 2D physics for action combat | [Box2D](https://github.com/erincatto/box2d), [Chipmunk Physics](https://github.com/slembcke/Chipmunk2D) | `copy` | MIT |
| 3D navigation meshes | [Recast Navigation](https://github.com/recastnavigation/recastnavigation) | not in the catalog | Zlib |
| overworld noise | [FastNoiseLite](https://github.com/Auburn/FastNoiseLite) | not in the catalog | MIT |
| online rooms and state sync | [Colyseus](https://github.com/colyseus/colyseus) (Node.js) | not in the catalog | MIT |
| a whole MMORPG platform to read and borrow from | [Reldens](https://github.com/damian-pastorini/reldens) (built with Colyseus and Phaser) | `copy` | MIT |
| debug and editor UI | [Dear ImGui](https://github.com/ocornut/imgui) | `copy` | MIT |
| map loading in Python | [PyTMX](https://github.com/bitcraft/pytmx) | `library use` | LGPL-3.0 |

**Tiled** ([repo](https://github.com/mapeditor/tiled)) is `check first` in the catalog because
GitHub cannot name one license. Its COPYING file splits it: the editor is GPL, while `libtiled` and
the TMX viewers are BSD-2-Clause. Authoring maps with the editor copies none of its code; if you
need its loader code, take it from `libtiled`.

Whole games with `copy` code: Daggerfall Unity (MIT) and TetraForce (MIT), above.

## 5. Engine options (engine-neutral)

- **[Godot](https://github.com/godotengine/godot)** (`copy`, MIT). Tilemaps, 2D and 3D, an editor,
  MIT dialogue addons. Tradeoff: GDScript works only in Godot, and major versions break projects
  (TetraForce is still on Godot 3).
- **[LibGDX](https://github.com/libgdx/libgdx)** (`copy`, Apache-2.0). Java for desktop, Android,
  iOS and HTML5. Tradeoff: a framework without an editor, so you build or adopt every tool.
- **[Phaser](https://github.com/phaserjs/phaser)** (`copy`, MIT). Browser games; Reldens and the
  WTFPL-licensed PokeMMO project in the catalog (`copy`) build online RPGs on it. Tradeoff: you
  write your own save system, menus and content tools.
- **[MonoGame](https://github.com/MonoGame/MonoGame)** (`check first`: GitHub could not read its
  license, and its source list says MS-PL + MIT, so confirm the LICENSE file before you build on
  it). C# framework; UI libraries such as GeonBit.UI and Apos.Gui are `copy` (MIT). Tradeoff: no
  scene editor.
- **[pygame](https://github.com/pygame/pygame)** (`library use`, LGPL-2.1). Tuxemon and RPG
  Tactical Fantasy Game both use it. Tradeoff: easy to change, harder to package and to keep fast.

## 6. Assets

RPGs need a lot of art: tilesets, character sprites in four or eight directions, portraits, item and
skill icons, and music for every area.

- **[Kenney](https://kenney.nl/support):** "all game assets on the asset pages are public domain
  licensed (CC0)", including for commercial use.
- **[OpenGameArt](https://opengameart.org/content/faq):** each asset carries its own license: CC0,
  CC-BY 3.0 or 4.0, CC-BY-SA 3.0 or 4.0, OGA-BY 3.0 or 4.0, or GPL 2.0 or 3.0. Filter by license.
- **[Liberated Pixel Cup](https://lpc.opengameart.org/):** a shared style of RPG characters and
  tiles, dual licensed CC BY-SA 3.0 and GPLv3. Share-alike, and every contributor must be credited.
- **[game-icons.net](https://game-icons.net/about.html):** skill and item icons under CC BY 3.0;
  credit the author.
- **[Freesound](https://freesound.org/help/faq/):** each sound is CC0, CC BY or CC BY-NC (no
  commercial use); older sounds may still carry the retired Sampling+ license.

**A code license says nothing about the art.** Kaetram's code is MPL-2.0 (`library use`), and its
README says its assets are CC-BY-SA 3.0. Tuxemon's `ATTRIBUTIONS.md` gives a license per asset,
from CC0 through CC BY-SA to some CC BY-NC-SA 3.0, which forbids commercial use of those files.
Daggerfall Unity, OpenMW, GemRB and EasyRPG Player run on commercial game data that none of them
include; their code license gives you no right to that data. Record every asset in the game's
`THIRD_PARTY.md` (see [../templates/THIRD_PARTY.md](../templates/THIRD_PARTY.md)).

## 7. Building it with AI tools

Follow the stage table in [../ai/README.md](../ai/README.md). For an RPG the work splits like this:

- **Claude** plans and reviews: the design page, content schemas, the quest and flag map, the
  failure list, and later whole-repo reviews for flags nothing sets and quests nobody can finish.
- **Codex** takes one scoped task at a time: the content loader, the battle core, the event
  runner, save migration, each with a playtest step that fails without it.
- **Grok** is the blind second opinion: simulator output and balance tables, and bugs given as a
  symptom plus the files, never your theory.

Describe a `study only` mechanic in your own words; never paste GPL code into a prompt.

**Prompts by stage:**

1. *Design (Claude):* "Write docs/design.md for a [subgenre] RPG: the core loop in one sentence,
   the player verbs, win and lose, and a slice of one town, one dungeon and one boss. Add a cut list."
2. *Data (Claude, then Codex):* "Define schemas for monster, item, skill, npc, encounter and quest,
   all referenced by string id. List every way a content file can be wrong, then write a loader
   that rejects each one with the file name and field."
3. *Combat (Codex):* "Implement turn-based combat as a pure function from state and action to new
   state, with a seeded RNG passed in and no rendering. Add a headless script that runs 1,000
   fights of this party against this encounter and prints win rate and average turns."
4. *Events (Codex):* "Run map events as a list of conditions and a list of actions read from YAML:
   show dialog, set flag, give item, start battle, move NPC, lock and unlock controls."
5. *Save (Codex):* "Serialize flags, party, inventory, map and position with a version number, a
   migration per version bump, and a playtest step that loads a save from the previous build."

**Playtest checklist**, on top of the general one in the AI guide:

- [ ] A scripted playthrough completes every quest from a fresh save
- [ ] Save on every map, reload: flags, inventory and position are identical
- [ ] A save from the previous build still loads
- [ ] Simulated win rates per encounter sit where the design says they should
- [ ] No softlock: a consumed key item, a required purchase with no money, a one-way door
- [ ] Every menu works with keyboard only and with gamepad only
- [ ] The longest line in every language fits its text box

## 8. Genre-specific pitfalls

- **RPGs run out of content before they run out of code.** Time how long one map, one quest and
  one NPC take in the vertical slice, then multiply before you promise a world.
- **Content in code.** A monster written as a class is a monster only a programmer can change.
  Tuxemon, Veloren and RPG Tactical Fantasy Game all keep content in data files.
- **A flag swamp.** Hundreds of booleans with names like `flag_217` become unfixable. Namespace
  them (`town.elder.met`), keep a list, and give the developer console a flag viewer.
- **Saves that break on update.** Adding one field breaks old saves unless the format has had a
  version number since the first build.
- **Balancing by feel.** Level curves and stat growth compound; simulate fights instead of guessing.
- **Grinding as padding.** If the player must repeat fights to pass a wall, the curve is wrong.
- **Branch explosion.** Every dialogue branch multiplies writing and testing. Let choices set
  flags that matter later, and bring branches back together.
- **Starting with an MMO.** Online RPGs need an authoritative server, accounts, persistence and
  moderation. Ship the single-player loop first; Reldens and Colyseus are there when you need them.
- **Reimplementation code is not a content license.** Copying code from a `copy` reimplementation
  that runs on commercial data is fine; shipping any of that data is not. A decompiled commercial
  game is different: the catalog marks it `check first`, and it is never a source to copy.
