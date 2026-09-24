# Sandbox playbook

Open-ended building and simulation games: voxel worlds where players dig, craft and build, and
simulation toys such as falling-sand games where players pour, burn and wire things to see what
happens. The full list of 34 projects, with license and activity, is in
[../catalog/sandbox.md](../catalog/sandbox.md). That list is small and mixed (it also caught SDKs
and tools that matched the keyword), and the catalog's genre mapping put most of the strongest
sandbox games under [../catalog/simulation.md](../catalog/simulation.md), so this playbook draws on
both. Every project named here was checked against its repository on 2026-09-23; reuse classes are
quoted as the catalog states them (`copy`, `library use`, `study only`, `check first`).

## 1. What defines the genre

**Core loop:** explore, gather, change the world, watch the systems react, then pick your own next
goal. The world and its rules are the content; the player writes the story.

**Player verbs:** dig, place, craft, combine, pour, ignite, wire, paint, explore, save and share.

**Win and lose:** usually neither. Survival modes add health, hunger and death; creative modes remove
every limit. Structure comes from player goals, progression unlocks and shared creations.

Two families share one architecture (a world of cells, rules applied to cells, persistence):
- **Voxel builders** (Craft, Luanti, Terasology, Cubyz): chunked 3D worlds, generation from noise,
  meshing, and usually multiplayer and mods.
- **Simulation toys** (sandspiel, The Powder Toy): a 2D grid where every cell follows its element's
  rules each tick, and sharing creations is half the game.

## 2. The systems to build, in build order

### First playable vertical slice

- [ ] World as a grid of cell types split into chunks (Craft uses 32 by 32 columns); cell types as a
      data table (solid, transparent, texture, behavior).
- [ ] Seeded, deterministic generation: the same seed and position always give the same cells.
- [ ] Pick and edit: a ray from the camera to the first solid cell, place and remove.
- [ ] Rendering that draws only exposed faces and rebuilds a chunk's mesh when it changes.
- [ ] Save only what the player changed on top of the generated world (Craft stores changed blocks in
      SQLite), and load it back.
- [ ] Player movement and collision, or for a 2D toy a brush, element picker and pause.
- [ ] A fixed simulation step, independent of frame rate.

### v1

- [ ] Inventory and crafting recipes as data files.
- [ ] A scripting or modding API, documented from the start (Luanti documents its Lua API in
      `doc/lua_api.md`; The Powder Toy exposes a Lua API).
- [ ] Lighting and a day and night cycle.
- [ ] Multiplayer: the server owns the world; clients request chunks and receive block updates.
- [ ] Survival and creative modes as rule sets over the same world.
- [ ] A versioned save format with migration, tested on saves from older builds.
- [ ] Sharing: export and import of a world region, or an in-game browser for uploaded creations.

### Polish

- [ ] Frustum culling, ambient occlusion (Craft), level of detail for far view (Cubyz).
- [ ] Meshing and saving off the main thread (Craft writes to SQLite on a background thread).
- [ ] Undo and blueprints in creative mode (Cubyz has `src/blueprint.zig`).
- [ ] Permissions, moderation and rollback for multiplayer and shared content.
- [ ] First-session guidance: a few suggested goals, so an empty world does not feel like no game.

## 3. Reference projects to study

`study only` projects are read for design; copy nothing from them
([../ai/README.md](../ai/README.md), "License hygiene").

**[Craft](https://github.com/fogleman/Craft)**: `copy`, MIT, C (cataloged under puzzle). "A few
thousand lines of C using modern OpenGL", with multiplayer through a Python server. Last pushed in
2024. Its README has an "Implementation Details" section that is a voxel tutorial in itself. Learn
from:
- Chunks of 32 by 32 blocks, terrain from simplex noise seeded by position, and only exposed faces
  rendered; each chunk keeps a one-block overlap with its neighbors to know which edge faces show.
- Saves as deltas: a SQLite table `block` with columns `p, q, x, y, z, w`, applied over the generated
  world at load.
- A plain ASCII line protocol: the client asks for a chunk with a cache key, and the server sends
  only block changes made since that key.

**[Minecraft](https://github.com/fogleman/Minecraft)**: `copy`, MIT, Python with pyglet. The same
author's Python demo: one `main.py` of 902 lines. Learn from:
- The smallest readable voxel game, ideal for a first slice or a teaching fork. Its README states the
  goal of turning it into an educational tool.

**[Terasology](https://github.com/MovingBlocks/Terasology)**: `copy`, Apache-2.0, Java 17 (cataloged
under simulation). A voxel world engine built as "a stable platform for various types of gameplay".
Learn from:
- An engine plus gameplay modules kept in separate repositories under the Terasology organization;
  engine packages include `entitySystem`, `world`, `persistence`, `network` and `recording`.
- Split licensing stated plainly: Apache-2.0 for code, CC BY 4.0 for artwork.

**[sandspiel](https://github.com/MaxBittker/sandspiel)**: `copy`, MIT, Rust compiled to WebAssembly
plus JavaScript and WebGL (cataloged under simulation). A falling-sand game built for "sharing and
forking of fun creations". Learn from:
- One update function per element (`update_sand`, `update_water`, `update_fire` and more in
  `crate/src/species.rs`) that sees neighbors only through a small `SandApi`.
- A cell written during a tick is stamped with the next generation in its `clock` field
  (`crate/src/lib.rs`), so it is not processed twice in one pass.
- Wind from a WebGL fluid simulation adopted from another MIT project, and a Firebase backend for
  browsing shared creations.

**[Luanti](https://github.com/luanti-org/luanti)**: `library use`, LGPL-2.1 (per list), C++
(formerly Minetest, cataloged under simulation). "A free open-source voxel game engine with easy
modding and game creation." Learn from:
- Games and mods written entirely in Lua against a documented API (`doc/lua_api.md`), distributed
  through its ContentDB.
- Its `LICENSE.txt` puts the engine's textures and sounds under CC BY-SA 3.0 and 4.0, separately
  from the LGPL code.

**[Minetest Game](https://github.com/luanti-org/minetest_game)**: `library use`, LGPL-2.1 (per
list), Lua (cataloged under simulation). The base game for Luanti, now in maintenance-only mode.
Learn from:
- A whole game as 34 mods under `mods/` (`default`, `farming`, `doors`, `tnt` and others), each with
  its own `license.txt`: in `mods/default`, code is LGPL-2.1 and media CC BY-SA 3.0.

**[The Powder Toy](https://github.com/The-Powder-Toy/The-Powder-Toy)**: `study only`, GPL-3.0, C++
(cataloged under simulation). A physics sandbox simulating air pressure and velocity, heat, gravity
and material interactions. Learn from:
- One source file per element: 195 `.cpp` files in `src/simulation/elements/`.
- A Lua API for automation and plugins, and an online save browser with thousands of community saves.

**[Cubyz](https://github.com/PixelGuys/Cubyz)**: `study only`, GPL-3.0, Zig (cataloged under
simulation). A voxel sandbox pushed in September 2026. Learn from:
- Level of detail for far view distances and 3D chunks with no height or depth limit.
- Block behavior as small callbacks (`src/callbacks/block/server/decay.zig`, `vine_decay.zig`) and a
  written `docs/GAME_DESIGN_PRINCIPLES.md`.

## 4. Reusable permissive code

| catalog project | reuse class, license | language | use it for |
|---|---|---|---|
| [Craft](https://github.com/fogleman/Craft) | `copy`, MIT | C | chunking, face culling, delta saves, the chunk protocol, ambient occlusion |
| [sandspiel](https://github.com/MaxBittker/sandspiel) | `copy`, MIT | Rust, JavaScript | a cellular-automaton core in WebAssembly with per-element rules |
| [Terasology](https://github.com/MovingBlocks/Terasology) | `copy`, Apache-2.0 | Java | entity system, world storage and module loading patterns |
| [Box2D](https://github.com/erincatto/box2d), [Chipmunk2D](https://github.com/slembcke/Chipmunk2D) | `copy`, MIT | C | 2D rigid bodies for physics sandboxes (cataloged under engines) |
| [Three.js](https://github.com/mrdoob/three.js), [Babylon.js](https://github.com/BabylonJS/Babylon.js) | `copy`, MIT and Apache-2.0 | JavaScript, TypeScript | a browser voxel renderer (cataloged under engines) |
| [Luanti](https://github.com/luanti-org/luanti) | `library use`, LGPL-2.1 (per list) | C++ | the whole engine, unmodified, with your game in Lua on top |

Not in the catalog; license read from each repository's LICENSE file on 2026-09-23 (all would class
as `copy`):

| library | license | use it for |
|---|---|---|
| [FastNoiseLite](https://github.com/Auburn/FastNoiseLite) | MIT | terrain noise, with ports in C, C++, C#, Java, JavaScript, Rust, Go, GLSL, HLSL and more |
| [Jolt Physics](https://github.com/jrouwe/JoltPhysics) | MIT | multi-core 3D rigid bodies and collision |
| [EnTT](https://github.com/skypjack/entt), [flecs](https://github.com/SanderMertens/flecs) | MIT, MIT | entity component systems for many simulated objects (flecs' MIT file adds a Meta portions notice, so GitHub shows NOASSERTION) |

## 5. Engine options (engine-neutral)

| engine | license (catalog class) | fits | trade-off |
|---|---|---|---|
| [Godot](https://github.com/godotengine/godot) | MIT (`copy`) | 2D sandboxes, small voxel worlds, web export | large voxel worlds need your own chunk meshing, ideally in native code |
| [Luanti](https://github.com/luanti-org/luanti) | LGPL-2.1 (`library use`, per list) | a voxel game with multiplayer and mods on day one | you work inside its world model; its bundled media is CC BY-SA |
| [Bevy](https://github.com/bevyengine/bevy) | MIT or Apache-2.0 (not in catalog) | Rust ECS, many simulated entities | its README: breaking API changes about every three months |
| [raylib](https://github.com/raysan5/raylib) | Zlib (`copy`) | build a Craft-style engine yourself in C | you write chunking, meshing and UI from scratch |
| [Three.js](https://github.com/mrdoob/three.js) | MIT (`copy`) | browser voxel or physics toys | a renderer, not an engine: input, saving and networking are yours |

## 6. Assets

Code licenses say nothing about textures, models, sounds or worlds. Check every asset separately and
give it a row in `THIRD_PARTY.md` ([template](../templates/THIRD_PARTY.md)).

- **[Kenney](https://kenney.nl/assets)**: CC0, no attribution required. Packs that fit: Voxel Pack,
  Block Pack, Survival Kit, Foliage Pack, UI Pack, Impact Sounds.
- **[Poly Haven](https://polyhaven.com)** and **[ambientCG](https://ambientcg.com)**: CC0 textures,
  models and skies.
- **[OpenGameArt.org](https://opengameart.org)**: licenses vary per submission (CC0, CC BY,
  CC BY-SA, GPL). Record the one you chose.
- **[Freesound](https://freesound.org)**: each sound has its own license (CC0 through CC BY-NC).

Cautions from the reference projects:
- **ShareAlike media.** Luanti's bundled textures and sounds and Minetest Game's media are CC BY-SA.
  Shipping them is allowed, but your changes to them must be CC BY-SA too, and attribution is owed.
- sandspiel's `assets/` folder includes third-party font files; the MIT file covers its code, so
  check each font's own license before reuse.
- Terasology's artwork is CC BY 4.0: free to use with attribution, unlike its Apache-2.0 code.
- Worlds and saves players upload are their content. Say in your terms how shared creations may be
  used before you build a browser for them.

## 7. Building it with AI tools

Follow the stage table in [../ai/README.md](../ai/README.md): Claude plans and reviews, Codex
implements one scoped task at a time, Grok reviews blind, a person playtests. What changes for
sandboxes:

| stage | lead | sandbox-specific artifact |
|---|---|---|
| design | Claude (plan mode) | `docs/world.md`: cell types, chunk size, generation inputs, save format with a version number |
| failure list | Claude, attacked by Codex | chunk-edge bugs, generator drift, save corruption, update-order bias, runaway simulations |
| slice | Codex | world core and generator with no renderer, a region dump tool, then rendering |
| performance | Codex measures, Claude reads | frame and tick timings for a worst-case scene, before and after each change |
| "my world broke" | Grok and Codex, blind | the save file, the build versions and the loader code, never your theory |

Prompts, in build order (fill the angle brackets; one task per Codex run):

```text
1. World spec (Claude, plan mode): Read ../opensource/playbooks/sandbox.md and
docs/design.md. Write docs/world.md: cell types with properties, chunk dimensions,
generation (noise functions, seed handling), the edit operations, and a save format that
stores only player changes plus a format version. List what happens at chunk edges.

2. World core (Codex): Implement src/world/ in <language> with no engine imports:
generate(seed, chunk_x, chunk_z), get(x, y, z), set(x, y, z, type), and save/load of
changed cells only. Add a CLI, world --seed N --dump X Z, that prints a chunk as text.
Run it twice with the same seed and diff the output; then edit a block on a chunk edge,
save, reload and show the block is still there.

3. Simulation tick (Codex, simulation toys): Add step(grid) at a fixed rate. Each element
has one update rule reading neighbors through an API. A cell moved this tick is not
updated again. Alternate the horizontal scan direction each tick. Show a column of sand
settling the same way at 30 and 144 frames per second.

4. Multiplayer (Codex): The server owns the world. Clients request chunks with a cache
key and receive only changes since that key. Two scripted clients edit the same chunk;
show both end with identical dumps.
```

To borrow a design from a `study only` project such as The Powder Toy's elements, write your own
notes and give a fresh session only the notes (the clean-room prompt in ../ai/README.md).

### Sandbox playtest checklist (add to the general one in ../ai/README.md)

- [ ] The same seed generates the same world on two machines and two builds.
- [ ] A block placed on every kind of chunk edge and corner survives save and reload.
- [ ] A save from the previous release loads in the new one, or is refused with a clear message.
- [ ] Killing the game mid-save leaves the last good save loadable.
- [ ] The worst-case scene (a screen full of active sand, or maximum view distance) holds frame rate.
- [ ] Walking far from the origin shows no jitter in movement or rendering.
- [ ] Two players editing the same area see the same result after a minute.
- [ ] A new player, unhelped, finds something they want to build within five minutes.

## 8. Genre-specific pitfalls

- **Changing the generator changes old worlds.** When saves store only deltas, as Craft's do, the
  generated terrain comes from code. Changing noise parameters silently reshapes every existing
  world. Version the generator and keep old versions runnable, or save generated chunks once visited.
- **Chunk-edge bugs.** Faces, lighting and edits break at chunk borders first. Craft keeps a one-block
  overlap per neighbor for this reason; test edges explicitly.
- **Floating-point precision far from the origin.** Craft's README notes it as a problem at large X
  and Z. Use chunk-relative coordinates or recenter the world around the player.
- **Update-order bias in cellular automata.** Scanning the grid in one fixed direction makes liquids
  drift that way and lets a cell move twice. Stamp updated cells, as sandspiel does, and alternate
  the scan direction.
- **Runaway simulations.** Fire, explosions and liquid floods can grow without bound. Cap active cells
  per tick and keep ticking the rest next frame.
- **Save corruption.** Write to a new file and rename it into place, keep a backup, and version the
  format from the first save.
- **Scope.** Sandboxes invite endless features. Cubyz writes down its game design principles; do the
  same and cut against them.
- **Griefing.** Any shared world or creation browser needs permissions, reporting and rollback before
  it opens to strangers.
