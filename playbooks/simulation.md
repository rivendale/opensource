# Simulation playbook

City building, tycoon, transport, colony and life sims. The full list of 177 projects is in
[../catalog/simulation.md](../catalog/simulation.md); OpenRCT2 and OpenTTD are cataloged under
[strategy](../catalog/strategy.md). Every project named here was checked against its repository
on 2026-09-23; reuse classes are quoted as the catalog states them (`copy`, `library use`,
`study only`, `check first`). This playbook centers on management sims; vehicle sims and
falling-sand toys share the fixed-timestep core but little else (see the racing and sandbox
playbooks).

## 1. What defines the genre

**Core loop:** build or change something, let the simulation run, read the indicators, find the
bottleneck, adjust. The pleasure is watching a system you built work, and working out why it
does not.

**Player verbs:** zone, place, connect (roads, rails, pipes, power), set prices, budgets and
policies, hire and assign, schedule, inspect, and control time (pause, speed up).

**Win and lose:** often open-ended. OpenRCT2's README describes both modes: scenarios require an
objective within a time limit, while sandbox play can drop restrictions and finance entirely. You
lose through bankruptcy, population leaving, or a colony that can no longer sustain itself. City
builders usually add ratings (Julius keeps them in `src/city/ratings.c`, next to `victory.c`).

**The first design decision: agents or aggregates.** Agent sims move individuals (OpenRCT2's
guests, Julius's walkers). Aggregate sims keep numbers per tile or per link (micropolisJS's map
scans, OpenTTD's cargo flows). Most games mix both; decide which one each system uses before
building it.

## 2. The systems to build, in build order

### First playable vertical slice

- [ ] Fixed-timestep tick independent of frame rate; pause, 1x, 2x and 4x speeds.
- [ ] Tile map as data: terrain, what is built, which networks pass through each tile.
- [ ] Place and remove one building type, with a cost preview before the player commits.
- [ ] Every world change is a command; "what would it cost?" and "do it" share one code path.
- [ ] One network (road, pipe or power) and a connectivity pass: flood fill from the sources.
- [ ] One producer, one consumer, one good, one currency.
- [ ] Agents or aggregates for this slice: build one, not both.
- [ ] Two readouts: money over time and one satisfaction measure.
- [ ] One way to fail (bankruptcy) and one goal.
- [ ] Save and load.
- [ ] Headless mode: run many in-game years with scripted placements and write monthly stats to CSV.

### v1

- [ ] Demand: micropolisJS keeps residential, commercial and industrial "valves" (`valves.js`).
- [ ] Agent needs as bounded meters with warning thresholds (OpenRCT2's guests, 0 to 255 each).
- [ ] Service coverage: roaming walkers (Julius) or a radius. Show whichever you choose.
- [ ] Economy: prices, upkeep, loans, a monthly report.
- [ ] Time slicing: spread expensive passes across ticks (micropolisJS's 16-phase cycle, below).
- [ ] Heavy solvers off the main thread with a defined join point (OpenTTD's link graph, below).
- [ ] Data overlays (pollution, land value, coverage, traffic); the same data serves debugging.
- [ ] Events and disasters; scenario goals and scripting.
- [ ] Content in data files, and a mod loader.
- [ ] Versioned saves with migration, plus a fixture save from every release loaded in CI.

### Polish

- [ ] Every idle building and unhappy agent can report why, computed by the simulation.
- [ ] Notifications that jump to the location, and never repeat the same warning in a burst.
- [ ] Graphs over time and advisor messages.
- [ ] Undo for placement.
- [ ] Scale: profile at ten times your target entity count; simplify off-screen simulation.
- [ ] Ambient audio that follows the state of the city, park or colony.
- [ ] A scripting API with typings (OpenRCT2 ships `openrct2.d.ts` for its JavaScript plugins).
- [ ] Color-blind-safe overlays and a scalable UI.

## 3. Reference projects to study

The best-maintained management sims in the catalog. Four of eight are `study only`: read them for
design, copy nothing ([../ai/README.md](../ai/README.md), "License hygiene with AI").

**[OpenRCT2](https://github.com/OpenRCT2/OpenRCT2)**: `study only`, GPL-3.0, C++ (cataloged under
strategy). A RollerCoaster Tycoon 2 reimplementation with cooperative multiplayer. Learn from:
- Guests as agents with needs: `src/openrct2/entity/Guest.h` defines the meters and thresholds;
  `peep/PeepThoughts.cpp` lists 174 thought types (can't afford, sick...) that report them.
- `peep/GuestPathfinding.cpp`: guest pathfinding across the park's footpaths.
- JavaScript plugins run on QuickJS-NG with TypeScript definitions (`distribution/scripting/`).
- It needs the original RCT2 files to play.

**[OpenTTD](https://github.com/OpenTTD/OpenTTD)**: `study only`, GPL-2.0, C++ (cataloged under
strategy). A transport sim based on Transport Tycoon Deluxe. Learn from:
- Cargo distribution as a multi-commodity flow over a link graph (`src/linkgraph/`), run in a
  separate thread because, as `docs/linkgraph.md` explains, the solver is CPU-hungry.
- AI companies and game scripts in Squirrel (`src/ai/`, `src/game/`, goal and story APIs).
- Its README promises every revision loads savegames from every older revision.
- Swappable base sets: free OpenGFX, OpenSFX and OpenMSX replace the original data files.

**[Julius](https://github.com/bvschaik/julius)**: `study only`, AGPL-3.0, C. A Caesar III
reimplementation that keeps the original logic, bugs included, so saves stay compatible. Learn from:
- Walker-based services: `src/figuretype/service.c` sends figures roaming up to a maximum roam
  length, and `src/figure/service.c` gives coverage to the houses they pass.
- City subsystems as separate files in `src/city/`: labor, migration, sentiment, health, trade,
  finance, ratings. The Augustus fork (`study only`, AGPL-3.0) changes gameplay; Julius does not.
- It needs the original Caesar III files.

**[micropolisJS](https://github.com/graememcc/micropolisJS)**: `study only`, GPL-3.0, JavaScript.
A port of the Micropolis city simulation to JavaScript and HTML5. Learn from:
- `src/simulation.js`: a 16-phase cycle scans the map in eighths over eight phases; power,
  pollution and land value passes run on their own intervals.
- One file per system: `census.js`, `evaluation.js`, `powerManager.js`, `traffic.js`,
  `residential.js`, `commercial.js`, `industrial.js`, `budget.js`, `disasterManager.js`.
- Its README warns of additional GPL terms and a separate Micropolis Public Name License.

**[OpenLoco](https://github.com/OpenLoco/OpenLoco)**: `copy`, MIT, C++. A reimplementation of
Locomotion, the spiritual successor to Transport Tycoon; its README says the C++ rewrite was
complete as of December 2025. Learn from:
- `src/OpenLoco/src/GameCommands/`: every world change (track, road, towns, industries,
  vehicles, company AI) goes through a command with flags such as `apply` and `ghost`.
- `GameSaveCompare.cpp`: logs byte-level divergences between two saves, a desync debugging tool.
- It needs the original Locomotion assets; the code is MIT, the art is not.

**[Outpost HD](https://github.com/OutpostUniverse/OPHD)**: `copy`, BSD-3-Clause, C++ with SDL2.
A colony builder that its README calls a redesign of Sierra's 1994 OUTPOST, "not a clone". Learn from:
- `GraphWalker.cpp`: connectivity by flood fill through connector structures.
- Colony resources as pools (`ProductPool.cpp`, `RobotPool.cpp`) and morale.
- It bundles MicroPather, a small A* library under a zlib notice (`appOPHD/MicroPather/`).

**[Space Station 14](https://github.com/space-wizards/space-station-14)**: `copy`, MIT, C# on the
Robust Toolbox engine. A multiplayer station sim. Learn from:
- Atmospherics: `Content.Server/Atmos/EntitySystems/` splits a tile gas simulation into files such
  as `AtmosphereSystem.LINDA.cs`, `AtmosphereSystem.Monstermos.cs` and `AtmosphereSystem.ExcitedGroup.cs`.
- Debug and measurement beside the simulation: `AtmosDebugOverlaySystem.cs`,
  `AtmosphereSystem.BenchmarkHelpers.cs`.
- A per-asset `meta.json` recording each asset's license and copyright.

**[sandspiel](https://github.com/MaxBittker/sandspiel)**: `copy`, MIT, Rust compiled to WebAssembly,
with WebGL and JavaScript. A falling-sand game. Learn from:
- Cellular automaton rules per species (`crate/src/species.rs`: sand, water, gas, wood, plant...).
- The browser split: simulation in Rust and wasm, rendering in WebGL.
- Its README credits fluid code adopted from WebGL-Fluid-Simulation (MIT on GitHub).

## 4. Reusable permissive code

| catalog project | reuse class, license | language | use it for |
|---|---|---|---|
| [OpenLoco](https://github.com/OpenLoco/OpenLoco) | `copy`, MIT | C++ | a command layer for world changes; save comparison for desync hunts |
| [Outpost HD](https://github.com/OutpostUniverse/OPHD) | `copy`, BSD-3-Clause | C++ | colony structures and connectivity; MicroPather A*, whose zlib notice lives only in its header (upstream has no license file GitHub detects), so keep the header |
| [Space Station 14](https://github.com/space-wizards/space-station-14) | `copy`, MIT | C# | tile gas simulation as a worked example (engine and assets carry other licenses, section 8) |
| [sandspiel](https://github.com/MaxBittker/sandspiel) | `copy`, MIT | Rust, JS | cellular automata in the browser |
| [Box2D](https://github.com/erincatto/box2d), [Matter.js](https://github.com/liabru/matter-js) | `copy`, MIT | C, JS | 2D rigid-body physics for contraption and vehicle sims (cataloged under engines) |
| [Dear ImGui](https://github.com/ocornut/imgui) | `copy`, MIT | C++ | debug panels; `PlotLines` and `PlotHistogram` for simulation variables |
| [Luanti](https://github.com/luanti-org/luanti) | `library use`, LGPL-2.1 (per list) | C++ | a voxel game engine with Lua modding; use unmodified |

Not in the catalog; license read from each repository's LICENSE file on 2026-09-23 (all would class
as `copy`):

| library | license | use it for |
|---|---|---|
| [EnTT](https://github.com/skypjack/entt), [flecs](https://github.com/SanderMertens/flecs) | MIT, MIT | entity component systems for large agent counts (flecs shows NOASSERTION on GitHub because its MIT file adds a Meta portions notice) |
| [Recast & Detour](https://github.com/recastnavigation/recastnavigation) | Zlib | navmeshes; `DetourCrowd` for crowd movement and collision avoidance |
| [FastNoiseLite](https://github.com/Auburn/FastNoiseLite) | MIT | terrain generation, ports in many languages |
| [WaveFunctionCollapse](https://github.com/mxgmn/WaveFunctionCollapse) | MIT | town and tile layouts generated from an example (GitHub shows NOASSERTION because its MIT file adds that the sample images and tiles are not part of the software) |

## 5. Engine options (engine-neutral)

| engine | license (catalog class) | fits | trade-off |
|---|---|---|---|
| [Godot](https://github.com/godotengine/godot) | MIT (`copy`) | 2D or 3D, editor, tilemaps | move hot simulation loops out of scripts when entity counts climb |
| [Bevy](https://github.com/bevyengine/bevy) | MIT or Apache-2.0 (not in catalog) | Rust ECS; many agents and systems | README: breaking API changes about every three months |
| [raylib](https://github.com/raysan5/raylib) with Dear ImGui | Zlib, MIT (`copy`) | C or C++ where you own the loop; add EnTT or flecs | no editor; you build every tool and menu |
| [PixiJS](https://github.com/pixijs/pixijs) | MIT (`copy`) | 2D in the browser; sandspiel shows the wasm route for heavy simulation | you supply game structure, UI and saves |
| [MonoGame](https://github.com/MonoGame/MonoGame) | MS-PL and MIT per list (`check first`) | C#, code-first 2D | confirm its `LICENSE.txt` (MS-PL) first; tooling is yours to build |

## 6. Assets

Code licenses say nothing about art, audio, maps or data. Check every asset separately and give it
a row in `THIRD_PARTY.md` ([template](../templates/THIRD_PARTY.md)).

- **[Kenney](https://kenney.nl/assets)**: CC0, commercial use allowed, no attribution required.
  Kits that fit: City Kit (Suburban, Commercial, Industrial, Roads), Factory Kit, Tiny Farm, Tiny
  Factory, UI Pack, Interface Sounds.
- **[game-icons.net](https://game-icons.net)**: over 4,000 icons for goods, services and alerts,
  under CC BY 3.0. Attribution is required.
- **[OpenGameArt.org](https://opengameart.org)**: licenses vary per submission (CC0, CC BY,
  CC BY-SA, GPL); some list several. Record the one you chose.
- **[Poly Haven](https://polyhaven.com)** and **[ambientCG](https://ambientcg.com)**: CC0
  textures, HDRIs and models for 3D cities and terrain.
- **[Freesound](https://freesound.org)**: per-sound CC0, CC BY or CC BY-NC (plus the retired
  Sampling+). Ambient loops are a sim's soundtrack; check each one.

Cautions from the reference projects:
- Space Station 14's README: most assets are CC-BY-SA 3.0, and some are non-commercial
  (CC-BY-NC-SA 3.0) and must be removed for commercial use.
- OpenTTD's free graphics base set, OpenGFX, is GPL-2.0: replacement art can be copyleft too.
- OpenRCT2, OpenLoco and Julius run only with the original commercial game files. They teach
  systems; your game needs its own art, data and name.

## 7. Building it with AI tools

Follow the stage table in [../ai/README.md](../ai/README.md): Claude plans and reviews, Codex implements
one scoped task at a time, Grok reviews blind, a person playtests. What changes for simulation:

| stage | lead | simulation-specific artifact |
|---|---|---|
| design | Claude (plan mode) | `docs/model.md`: every stock, flow and meter, agents or aggregates per system |
| failure list | Claude, attacked by Codex | runaway loops, frame-rate dependence, save migration, each with a playtest step |
| slice | Codex | headless simulation core, then placement tools and rendering |
| long runs | Codex runs, Claude reads | CSV of monthly stats over many in-game years and seeds |
| a number that goes wrong | Grok and Codex, blind | the CSV, the save file and the code, never your theory |

Prompts, in build order (fill the angle brackets; one task per Codex run):

```text
1. Model spec (Claude, plan mode): Read ../opensource/playbooks/simulation.md and
docs/design.md. Write docs/model.md: every stock (money, population, goods), every flow
between them, every agent meter with its range, and which systems use agents or
aggregates. For each feedback loop, say whether it grows or damps, and what caps it.

2. Simulation core (Codex): Implement src/sim/ in <language> with no engine imports:
a fixed-timestep tick, a seeded RNG owned by the state, and commands with query() and
apply() sharing one validation path. Add sim --seed N --years Y --script FILE that writes
one CSV row per in-game month. Run 50 years twice with the same seed; diff the CSVs.

3. Why answers (Codex): For every building and agent, compute a list of reasons it is
not working (no road, no workers, no input goods, unhappy because ...). The UI only
displays this list. Add a playtest that removes a road and asserts the reason appears.

4. Save migration (Codex): Add a version number to saves and a migration per version.
Keep saves/fixtures/<version>.sav; a test loads every fixture and runs 12 months.
```

To borrow a design from a `study only` project such as micropolisJS's phase cycle, write your own
notes and give a fresh session only the notes (the clean-room prompt in ../ai/README.md). Sending
fixes upstream? Space Station 14's README does not accept AI-generated code or assets.

### Simulation playtest checklist (add to the general one in ../ai/README.md)

- [ ] A 50-year headless run ends with no NaN, no negative stocks, and no unearned boom or collapse.
- [ ] Paused means paused: the state hash does not change while paused.
- [ ] The same in-game month gives the same state at 1x and 4x.
- [ ] Every idle building answers "why" in two clicks, and the answer is true.
- [ ] A bankruptcy spiral shows a warning early enough to act, and a way out exists.
- [ ] Every fixture save from earlier versions loads and runs.
- [ ] Tick time at ten times the target entity count is measured and written down.
- [ ] A new player, unhelped: note the first moment they do not know what to do next.

## 8. Genre-specific pitfalls

- **Opaque causality.** If the player cannot see why a number moved, they stop playing. Build the
  "why" into the simulation data, not the UI. OpenRCT2's guest thoughts show one way to surface it.
- **Runaway feedback loops.** Growth that feeds growth ends in infinite money or total collapse.
  Name every loop in the model spec, add damping, and catch it with long headless runs.
- **Simulation tied to frame rate.** Speed-up buttons then change outcomes. Fixed timestep first.
- **Too many agents.** Simulating every citizen as an agent stops scaling. Aggregate what the player
  cannot see, and move heavy solvers off the main thread with a defined join (OpenTTD's link graph).
- **Broken saves.** A format change that strands old cities throws away players' work. OpenTTD's
  promise to load every older save is the standard; fixture saves in CI are how you keep it.
- **Mixed licenses inside one repository.** Robust Toolbox, Space Station 14's engine, puts code
  contributed before 13 March 2019 under GPL-3.0 and later code under MIT (its `legal.md`), with
  images under CC-BY-SA 3.0. micropolisJS adds terms and a name license to the GPL. Read the legal
  files, not only the LICENSE badge.
- **Download lures.** Read the safety note in [../catalog/README.md](../catalog/README.md): never
  download a release, zip or installer from a catalog repository; build from source.
- **A sandbox with no goals.** Open-ended play leaves some players with nothing to aim at. OpenRCT2
  offers scenarios alongside sandbox play; ship at least one scenario.
