# Strategy playbook

Real-time strategy (RTS), turn-based tactics, 4X, tower defense and wargames. The full list of 420
projects, with license and activity, is in [../catalog/strategy.md](../catalog/strategy.md). Every
project named here was checked against its repository on 2026-09-23; reuse classes are quoted as the
catalog states them (`copy`, `library use`, `study only`, `check first`).

## 1. What defines the genre

**Core loop:** read the situation, decide, commit orders, let the rules resolve them, read the
outcome, adjust. In a turn-based game the loop is one turn; in an RTS it runs continuously and the
player's attention is the scarce resource. Outcomes follow from readable rules, not reflexes: if a
player cannot explain why they lost, the design has failed even when the code works.

**Player verbs:** scout, gather, produce, build, research, move, attack, defend, expand, and in 4X
games negotiate and trade. The interesting decisions are trade-offs between them: an army now or
an economy later, attack here or defend there.

**Win and lose:** eliminate the opponents, hold objectives for a number of turns (Zone of Control,
below, wins by holding control zones), reach one of several victory types (Unciv keeps them in
`VictoryTypes.json`), or survive every wave in tower defense. You lose when your base, leader or
last unit falls, or when enemies leak through in tower defense.

## 2. The systems to build, in build order

Pick real-time or turn-based before you write code; it changes the simulation core and the netcode.

### First playable vertical slice

- [ ] Map as data: square or hex grid, terrain type per cell, movement cost per terrain.
- [ ] Simulation core with no engine imports: state, a seeded RNG it owns, `tick` or `resolve_turn`.
- [ ] Orders as plain data (`Move`, `Attack`, `Build`), the only way to change state. Renderer reads only.
- [ ] Selection and order input: click to select, click to order, a visible order queue.
- [ ] Pathfinding: A* on the grid, costs from the terrain table.
- [ ] One resource, one production building, two unit types where each beats the other in some case.
- [ ] Combat resolution with the numbers shown to the player.
- [ ] Win and lose checks, and a restart that clears all match state.
- [ ] A simple AI opponent that issues orders through the same queue as the human.
- [ ] A full-state hash function, printed every N ticks or every turn.
- [ ] Headless mode: run AI against AI for a fixed number of ticks with no rendering.

### v1

- [ ] Fog of war and scouting; the AI sees only what its player sees.
- [ ] Rules in data files, validated at load with readable errors (OpenRA lints its rules in `Lint/`).
- [ ] Tech tree or upgrades loaded from the same data files.
- [ ] Save and load: serialize state plus RNG position. A replay is the start state plus the order log.
- [ ] AI split into modules (economy, build order, military, expansion), each testable alone.
- [ ] Maps: a map format, an editor or importer, and optionally procedural maps.
- [ ] Multiplayer: lockstep with state-hash checks (RTS), or a server that validates each move (turns).
- [ ] Balance tooling: batch AI-against-AI runs over many seeds, results to CSV.
- [ ] Scenario scripting for tutorials and campaigns.

### Polish

- [ ] RTS controls: control groups, hotkeys, shift-queued orders, rally points.
- [ ] Minimap, "under attack" alerts that jump to the location, tooltips with the real numbers.
- [ ] Readability: team colors that survive color blindness, health bars, clear selection.
- [ ] Difficulty levels and AI personalities (Unciv keeps them in `Personalities.json`).
- [ ] Replay viewer and observer mode.
- [ ] Automation for late-game busywork (Unciv ships city and unit automation).
- [ ] Pathfinding that scales: hierarchical search or flow fields for large armies.
- [ ] Localization from the start of v1, not bolted on.

## 3. Reference projects to study

The best-maintained strategy projects in the catalog, all pushed in September 2026. Most are
`study only`: read them for design, copy nothing ([../ai/README.md](../ai/README.md), "License hygiene with AI").

**[OpenRA](https://github.com/OpenRA/OpenRA)**: `study only`, GPL-3.0, C#. An RTS engine whose
bundled mods reimagine Red Alert, Tiberian Dawn and Dune 2000. Learn from:
- Lockstep networking: `OpenRA.Game/Network/OrderManager.cs` keeps a sync hash per frame and, on a
  mismatch, dumps a desync report (`SyncReport.cs`); `ReplayRecorder.cs` records matches.
- Rules as YAML composed from traits (`mods/ra/rules/*.yaml`), with generated trait documentation.
- A bot assembled from modules: `BaseBuilderBotModule`, `HarvesterBotModule`,
  `SquadManagerBotModule` and others in `OpenRA.Mods.Common/Traits/BotModules/`.
- `HierarchicalPathFinder.cs`, whose comments explain how an abstract graph gives A* a better
  heuristic around obstacles. A Lua API drives scripted missions.

**[The Battle for Wesnoth](https://github.com/wesnoth/wesnoth)**: `study only`, GPL-2.0, C++ with
WML data and Lua. Turn-based hex tactics with campaigns, hotseat and online play. Learn from:
- Movetypes: each unit family has a `movement_costs` and a `defense` table per terrain
  (`data/core/units.cfg`), so terrain matters without special cases in code.
- AI in Lua, including small reusable "micro AIs" (`data/ai/micro_ais/`).
- `copyrights.csv`: one row per asset file with license, author and MD5. Copy the practice.

**[Unciv](https://github.com/yairm210/Unciv)**: `library use`, MPL-2.0, Kotlin on LibGDX. A
moddable Civilization V remake for Android and desktop. Learn from:
- A whole 4X ruleset in JSON, one folder per ruleset (`android/assets/jsons/Civ V - Gods & Kings/`:
  `Techs.json`, `Units.json`, `Policies.json`, `VictoryTypes.json`, `Personalities.json`).
- AI split by scope in `core/src/com/unciv/logic/automation/`: `city/ConstructionAutomation.kt`,
  `civilization/DiplomacyAutomation.kt`, `DeclareWarPlanEvaluator.kt`, and unit automation.
- Scope discipline: its README says features from Civ V go in, everything else goes to mods.

**[Beyond All Reason](https://github.com/beyond-all-reason/Beyond-All-Reason)**: `study only`,
GPL-2.0, Lua on the Recoil RTS engine. Learn from:
- The split between a generic RTS engine and game logic written entirely in Lua.
- Headless integration tests: `tools/headless_testing/` runs the engine's headless build in Docker
  from a start script and writes results to a test log.
- Per-category asset licenses (`license_music.txt`, `license_sounds.txt`, `license_icons.txt`).

**[Mindustry](https://github.com/Anuken/Mindustry)**: `study only`, GPL-3.0, Java. "The automation
tower defense RTS": factory logistics feeding tower defense. Learn from:
- Generated code: entity classes are generated from component classes, and network packets from
  methods marked `@Remote` (explained in its README).
- A dedicated server build from the same codebase (`gradlew server:dist`).

**[FreeOrion](https://github.com/freeorion/freeorion)**: `study only`, GPL-2.0, C++ with Python.
A turn-based space 4X, inspired by Master of Orion but (its README says) not a clone. Learn from:
- AI in Python, one file per concern (`default/python/AI/`: `ColonisationAI.py`, `MilitaryAI.py`,
  `ProductionAI.py`, `ResearchAI.py`, `PriorityAI.py`).
- Content in scripts, not code (`default/scripting/`: buildings, species, ship hulls and parts,
  policies).

**[OpenCiv3](https://github.com/C7-Game/OpenCiv3)**: `copy`, MIT, C# on Godot. A pre-alpha,
mod-oriented Civilization III remake. Learn from:
- Engine and presentation kept apart: `C7Engine` holds the mechanics and AI, `C7` is the Godot
  front end, and `EngineTests` tests the mechanics without a renderer.
- Caution: its README says `ConvertCiv3Media` reads images and animations from Civilization III.
  The code is MIT; that art is not yours to ship.

## 4. Reusable permissive code

| catalog project | reuse class, license | language | use it for |
|---|---|---|---|
| [boardgame.io](https://github.com/boardgameio/boardgame.io) | `copy`, MIT | TypeScript | turn-based state, multiplayer sync, lobby, phases, generated bots, logs with time travel; install from npm |
| [GDHexGrid](https://github.com/romlok/godot-gdhexgrid) (cataloged under action) | `copy`, MIT | GDScript | hex coordinate conversion and A* for Godot |
| [OpenRTS](https://github.com/methusalah/OpenRTS) | `copy`, MIT | Java | a 3D RTS engine and editor on jMonkeyEngine 3 (cataloged under engines) |
| [War1](https://github.com/acoto87/war1) | `copy`, Zlib | C | classic RTS pathfinding, collision, gathering, fog of war; plays only with the original `DATA.WAR`, so no art comes with it |
| [Zone of Control](https://github.com/ozkriff/zoc) | `copy`, Apache-2.0 | Rust | hex wargame rules: fog of war, reaction fire, morale and suppression (discontinued) |
| [FreeHeroes](https://github.com/mapron/FreeHeroes) | `copy`, MIT | C++ | a Heroes III style engine with a battle emulator and replay files |
| [Unciv](https://github.com/yairm210/Unciv) | `library use`, MPL-2.0 | Kotlin | MPL-2.0 is per file: use files unmodified; changes to them stay MPL |

The catalog also lists a Codeberg repository named OpenRTS: a different Python project that shares
the name (`study only`, GPL-2.0 per list). Do not confuse the two; re-read the GitHub project's
LICENSE at the commit you copy.

Not in the catalog; license read from each repository's LICENSE file on 2026-09-23 (all would
class as `copy`):

| library | license | use it for |
|---|---|---|
| [Recast & Detour](https://github.com/recastnavigation/recastnavigation) | Zlib | navmesh pathfinding for 3D maps; `DetourCrowd` for crowd movement and avoidance |
| [EnTT](https://github.com/skypjack/entt), [flecs](https://github.com/SanderMertens/flecs) | MIT, MIT | entity component systems (C++; C and C++) for large unit counts. GitHub's API shows flecs as NOASSERTION because its MIT file adds a Meta portions notice |
| [BehaviorTree.CPP](https://github.com/BehaviorTree/BehaviorTree.CPP) | MIT | behavior trees for unit and commander AI |
| [honeycomb](https://github.com/flauwekeul/honeycomb) | MIT | hex grids in TypeScript, node or browser |
| [Yuka](https://github.com/Mugen87/yuka) | MIT | JavaScript game AI: goal-driven agents, steering, navmesh, fuzzy logic |
| [FastNoiseLite](https://github.com/Auburn/FastNoiseLite), [WaveFunctionCollapse](https://github.com/mxgmn/WaveFunctionCollapse) | MIT, MIT | procedural maps: noise in many languages; tilemaps generated from an example. GitHub shows WaveFunctionCollapse as NOASSERTION because its MIT file adds that the sample images and tiles are not part of the software |

**Netcode:** no permissive lockstep RTS library turned up in the catalog. Lockstep is little code
once the simulation is deterministic: study OpenRA's design, then write your own.

## 5. Engine options (engine-neutral)

| engine | license (catalog class) | fits | trade-off |
|---|---|---|---|
| [Godot](https://github.com/godotengine/godot) | MIT (`copy`) | 2D or 3D, any subgenre; OpenCiv3 and GDHexGrid show it | keep the simulation in plain code rather than engine nodes if you need lockstep |
| [Bevy](https://github.com/bevyengine/bevy) | MIT or Apache-2.0 (not in catalog) | Rust ECS, large unit counts | README: a release with breaking API changes about every three months |
| [LibGDX](https://github.com/libgdx/libgdx) | Apache-2.0 (`copy`) | Java, desktop, Android, HTML5, iOS; Unciv is built on it | code first, no scene editor |
| [Phaser](https://github.com/phaserjs/phaser) with boardgame.io | MIT (`copy`) | turn-based games in the browser | browser performance limits a large real-time battle |
| [MonoGame](https://github.com/MonoGame/MonoGame) | MS-PL and MIT per list (`check first`) | C#, code-first 2D | confirm its `LICENSE.txt` (MS-PL) first; you build the editor and UI tooling yourself |

The long-running open RTS engines are copyleft: Spring, Stratagus (`study only`, GPL-2.0) and OpenRA
(`study only`, GPL-3.0). Building on one makes your game GPL, outside this chassis's copy rule.

## 6. Assets

Code licenses say nothing about art, audio, maps or unit data. Check every asset separately and
give it a row in `THIRD_PARTY.md` ([template](../templates/THIRD_PARTY.md)).

- **[Kenney](https://kenney.nl/assets)**: CC0, commercial use allowed, no attribution required. Kits
  that fit: Tower Defense Kit, Hexagon Kit, Medieval RTS, Castle Kit, UI Pack, Interface Sounds.
- **[game-icons.net](https://game-icons.net)**: over 4,000 icons (its home page count) for
  abilities, techs and resources, under CC BY 3.0. Attribution is required; put it in the credits.
- **[OpenGameArt.org](https://opengameart.org)**: licenses vary per submission (CC0, CC BY,
  CC BY-SA, GPL); some list several. Filter by license and record the one you chose.
- **[Poly Haven](https://polyhaven.com)** and **[ambientCG](https://ambientcg.com)**: CC0 textures
  and models for 3D terrain.
- **[Freesound](https://freesound.org)**: each sound has its own license (CC0, CC BY or CC BY-NC,
  plus the retired Sampling+). Non-commercial sounds are unusable in a game you sell.

Cautions from the reference projects:
- BAR's code is GPL-2.0, but `license_music.txt` puts its original soundtrack under CC BY-NC-ND 4.0.
- Wesnoth's `copyrights.csv` shows art and music under GPL or CC BY-SA, file by file.
- Many high-star catalog entries (VCMI, Free Heroes 2, OpenDUNE, Wargus) are labeled
  "original required": they run on a commercial game's files.

## 7. Building it with AI tools

Follow the stage table in [../ai/README.md](../ai/README.md): Claude plans and reviews, Codex implements
one scoped task at a time, Grok reviews blind, a person playtests. What changes for strategy:

| stage | lead | strategy-specific artifact |
|---|---|---|
| design | Claude (plan mode) | `docs/rules.md`: every unit stat, cost and formula as a named constant |
| failure list | Claude, attacked by Codex | determinism hazards and AI information leaks, each with its playtest step |
| slice | Codex | headless simulation core, then the renderer on top |
| balance | Codex runs, Claude reads | CSV of AI-against-AI results over many seeds |
| desync or AI bug | Grok and Codex, blind | two state dumps plus the code, never your theory |

Prompts, in build order (fill the angle brackets; one task per Codex run):

```text
1. Rules spec (Claude, plan mode): Read ../opensource/playbooks/strategy.md and
docs/design.md. Write docs/rules.md: map, units with every stat, costs, turn or tick
structure, combat formula, victory and defeat. Every number is a named constant.

2. Simulation core (Codex): Implement src/sim/ in <language> with no engine imports:
State, an RNG owned by State and seeded at match start, orders as plain data,
apply(state, order) and tick(state). Integer or fixed-point math for anything that
affects outcomes; no iteration over unordered hash maps. Add hash(state) and a CLI,
sim --seed N --orders FILE, that prints the hash every 100 ticks. Run it twice with the
same input and show both outputs.

3. AI opponent (Codex): Add src/ai/ that reads only cells visible to its player and
emits orders through the same queue as a human. Add sim --bots 2 --seeds 1..200
--csv out.csv with columns seed, winner, ticks, final_hash. Show the first ten rows.

4. Lockstep (Codex): Clients send orders tagged with the tick they execute on and
exchange hash(state) every 30 ticks. On mismatch, each writes desync/<tick>-<player>.json
and stops. Add a test mode that injects one extra RNG call on one client; show the
mismatch detected and dumped.
```

To borrow a design from a `study only` project such as OpenRA's bot modules, write your own notes
and give a fresh session only the notes (the clean-room prompt in ../ai/README.md). Sending fixes
upstream? BAR's `AI_POLICY.md` requires disclosing AI-assisted code in the pull request.

### Strategy playtest checklist (add to the general one in ../ai/README.md)

- [ ] Same seed and same order log give the same final hash on two machines and two operating systems.
- [ ] A saved and reloaded match reaches the same hash as an uninterrupted one.
- [ ] A recorded replay ends in the same state as the live match.
- [ ] The AI's log shows it never acted on a cell its player could not see.
- [ ] Every unit counters something and is countered by something; the table is in `docs/rules.md`.
- [ ] Across the batch runs, no single opening wins beyond the band you set before looking.
- [ ] Fifty units ordered through a one-cell choke all arrive; none jitter forever.
- [ ] Turn processing or tick time at the largest map and unit cap stays under your budget.
- [ ] A new player, unhelped, can say after one match why they won or lost.

## 8. Genre-specific pitfalls

- **Nondeterminism breaks lockstep and replays.** Floating point across compilers and platforms,
  unordered map iteration, a shared RNG also used by visual effects, and logic tied to frame time
  all cause desyncs. Hash state from the first slice; OpenRA's per-frame sync hash is the pattern.
- **An AI that cheats or is helpless.** Route AI orders through the human's order path and test
  AI against AI headless; BAR's headless tests and OpenRA's bot modules show both halves.
- **Pathfinding cost grows with army size.** Plain A* per unit per tick stalls large battles.
  Cache paths, use hierarchical search (OpenRA) or flow fields, and test chokepoints early.
- **Balance by spreadsheet alone.** Batch runs find outliers; only people find what is dull.
- **Late-game tedium in 4X.** Turn time and micromanagement grow with empire size; offer automation.
- **Hidden numbers.** If combat uses terrain defense, show it on hover. Wesnoth keeps defense per
  terrain in data tables, which makes the number easy to surface wherever the player needs it.
- **Scope.** A strategy game can grow forever. Unciv's rule (the Civ V feature set in the base
  game, everything else as mods) is one way to say no.
- **Licenses GitHub could not read.** Athena Crisis and CorsixTH show MIT per their list but are
  `check first` because GitHub's API could not confirm it. Read the LICENSE file yourself.
