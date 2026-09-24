# Racing playbook

Kart racers, arcade and simulation racers, top-down and pseudo-3D racers. The full list, with
license and activity for every project, is in [../catalog/racing.md](../catalog/racing.md); several
driving simulators are filed under [../catalog/simulation.md](../catalog/simulation.md). Every
project below was checked against its repository on 2026-09-23; reuse classes are quoted exactly as
the catalog states them.

## 1. What defines the genre

**Core loop:** grid start → drive the lap through ordered checkpoints → overtake, defend, recover
from mistakes → finish → position or time decides the reward → next track or retry for a cleaner
lap. Time trial replaces opponents with your own ghost.

**Player verbs:** accelerate, brake, steer, drift or handbrake, boost, use an item (kart racers), look
back, reset to the track.

**Win and lose:** finish first, finish above a qualifying position, or beat a target time. You lose
by finishing too low, by running out a checkpoint timer, or by elimination in battle modes.

**What makes it hard to build:** the car is the character and the track is the level, so handling
feel decides everything; speed exposes every frame-rate dependency, and the AI must lose convincingly.

| subgenre | defining extra | catalog example |
|---|---|---|
| kart / arcade | items, drift boost, forgiving physics | [SuperTuxKart](https://github.com/supertuxkart/stk-code), [kart-royale](https://github.com/ryancampbell/kart-royale) |
| simulation | tire model, drivetrain, setup screens | [VDrift](https://github.com/VDrift/vdrift) |
| top-down 2D | tile tracks, many cars on screen | [Dust Racing 2D](https://github.com/juzzlin/DustRacing2D) |
| pseudo-3D | scaled sprites on a projected road | [JavaScript Racer](https://github.com/jakesgordon/javascript-racer) |
| futuristic / hover | no wheels, energy or shield systems | [PolyRace](https://github.com/vthem/PolyRace) |

## 2. The systems to build, in build order

### First playable vertical slice

- [ ] Fixed physics timestep, with rendering interpolated between steps.
- [ ] One vehicle with arcade handling: throttle, brake, steering that tightens as speed drops, grip
      that gives way to a slide past a threshold.
- [ ] One closed track built around a centerline spline (or node graph) that everything else keys off.
- [ ] Ordered checkpoints; lap counted from progress along the centerline, not from one finish trigger.
- [ ] Race timer, lap times, a finish screen.
- [ ] Chase camera with smoothing.
- [ ] Reset to the last checkpoint.

Done when a lap can be driven and timed, and cutting across the infield does not count as a lap.

### v1

- [ ] Race position from laps completed plus progress along the centerline.
- [ ] AI drivers that follow a racing line with a target speed per segment; difficulty by target
      speed and line error, not by breaking physics.
- [ ] Vehicle tuning as data (mass, grip, top speed, acceleration), layered per class and difficulty.
- [ ] Three or more tracks from a track data format, ideally with an editor.
- [ ] Surfaces: grass, dirt and ice change grip and drag.
- [ ] Time trial with a ghost recorded per tick.
- [ ] Gamepad steering with a speed-sensitive limit; keyboard steering smoothed.
- [ ] HUD: speed, position, lap, lap times, minimap.
- [ ] Kart racers: item boxes, items, drift charged into boost.
- [ ] Split-screen or online multiplayer.

### Polish

- [ ] Engine audio driven by RPM, tire squeal on slip, impact sounds.
- [ ] Skid marks, dust and sparks; speed-dependent field of view; camera shake on impacts.
- [ ] Replays with free camera.
- [ ] Catch-up tuning measured and stated, not hidden.
- [ ] Draw distance, level of detail and a frame-time budget for the lowest target device.

## 3. Reference projects to study

1. **[SuperTuxKart](https://github.com/supertuxkart/stk-code)**: `study only`, GPL-3.0 (list; GitHub
   could not read it), C++. The most-starred racing project in the catalog, last pushed on the catalog's build date.
   - `src/tracks/drive_graph.*` and drive nodes give every kart a distance along the track;
     `check_lap.hpp` detects a new lap when that distance drops sharply, and `check_manager` and
     `check_line` enforce ordered checkpoints.
   - `data/kart_characteristics.xml` layers tuning: base values, then difficulty (easy to best), then
     kart class (light, medium, heavy), then handicap.
   - `src/karts/controller/skidding_ai.*` is the racing AI; `src/network/rewind_manager.*` handles
     online correction; `ghost_kart` replays; `src/physics/btKart.hpp` derives from Bullet's raycast vehicle.
   - Its art lives in a separate `stk-assets` repository, and `data/` folders carry their own
     license files (the icons file says "Various", including CC-BY-SA 3.0).
2. **[VDrift](https://github.com/VDrift/vdrift)** (catalog genre: simulation): `study only`, GPL-3.0,
   C++. A drift-focused driving simulator. `src/physics/` splits the car into engine, clutch,
   transmission, differential, driveshaft, brakes, suspension, aero devices and tires, with three
   tire models built on the Pacejka "magic formula". Read it to understand what an arcade model is
   approximating, then write your own simpler one.
3. **[Dust Racing 2D](https://github.com/juzzlin/DustRacing2D)**: `study only`, GPL-3.0, C++ with Qt
   and OpenGL. Tile-based tracks with a Qt level editor, 11 computer opponents, split-screen, race,
   time trial and duel modes, pit stops, and a separate physics engine (MiniCore). Study how the
   tile editor keeps track creation cheap.
4. **[kart-royale](https://github.com/ryancampbell/kart-royale)**: `copy`, MIT, TypeScript with
   Three.js.
   - Mini-turbo drifting in `src/kart/`, a banked spline circuit, a racing-line AI in
     `src/game/AI.ts`, and Web Audio synthesis in `src/audio/`; there are no image or audio files,
     everything is generated in code.
   - `tools/` holds the test rigs: `drift-bench.mjs` asks whether a drifting lap is actually faster
     than a clean one, `autoplay.mjs` plays full races and asserts on classification, items,
     deadlocks and NaN, `camera-probe.mjs` measures camera lag and swing.
   - Its README's "Things that went wrong" section is worth reading before you build anything.
5. **[JavaScript Racer](https://github.com/jakesgordon/javascript-racer)** (catalog genre: arcade):
   `copy`, MIT, JavaScript in HTML. An Out Run-style pseudo-3D racer built in four steps (straight
   road, curves, hills, final), each with a write-up. Its README ends with a list of what it would
   take to make it a real game: a ready-made backlog.
6. **[OpenNFS](https://github.com/OpenNFS/OpenNFS)**: `copy`, MIT, C++. Asset loaders for classic Need
   for Speed tracks and cars, Bullet physics for vehicle dynamics, and an engine designed to be
   configured per title. It is early in development and bundles no EA material: it needs the original
   games. Study how one engine is configured to reproduce different handling and graphics.
7. **[Racez.io](https://github.com/MankyDanky/web-racing)** (catalog name web-racing): `copy`, MIT,
   JavaScript. Three.js rendering with Ammo.js (a WebAssembly port of Bullet), WebRTC peer-to-peer
   races joined by party code, checkpoint gates, reset to last checkpoint, and a touch joystick.
8. **[PolyRace](https://github.com/vthem/PolyRace)**: `copy`, MIT, C# on Unity. Procedurally generated
   terrain built in chunks by Unity jobs (`Assets/Scripts/LevelGen/`), four hovercraft with their
   own properties, and input behind one `ICommand` interface with keyboard, touch and replay
   implementations, so ghosts drive through the same path as players. Its README lists third-party
   pieces under other licenses (LibNoise.Unity under LGPL, DOTween, Flaticon sprites).

## 4. Reusable permissive code

**Vehicle physics.** Licenses of the libraries not in the catalog were read from GitHub on
2026-09-23.

| library | class | license | language | why for racing |
|---|---|---|---|---|
| [Jolt Physics](https://github.com/jrouwe/JoltPhysics) | not in the catalog | MIT | C++ | wheeled and tracked vehicles; its README says the simulation runs deterministically, within documented limits |
| [Bullet](https://github.com/bulletphysics/bullet3) | not in the catalog | zlib per its LICENSE.txt, except `Extras` and `examples/ThirdPartyLibs` | C++ | the raycast vehicle that SuperTuxKart and OpenNFS build on |
| [ammo.js](https://github.com/kripken/ammo.js) | `check first` | GitHub reads no license; the LICENSE file reads as zlib, so confirm it before you copy | JavaScript/WASM | Bullet in the browser; used by Racez.io |
| [Rapier](https://github.com/dimforge/rapier) | not in the catalog | Apache-2.0 | Rust; browser bindings in its `typescript` directory (the old rapier.js repository is archived) | ships a vehicle controller example (`examples3d/vehicle_controller3.rs`) |
| [Avian](https://github.com/avianphysics/avian) | not in the catalog | MIT or Apache-2.0 | Rust (Bevy) | ECS-based physics built for Bevy |

Top-down racers need only 2D: [Box2D](https://github.com/erincatto/box2d), [Chipmunk Physics](https://github.com/slembcke/Chipmunk2D)
or [Matter.js](https://github.com/liabru/matter-js), all `copy`, MIT.

**Handling and input.**
[AC-Advanced-Gamepad-Assist](https://github.com/adam10603/AC-Advanced-Gamepad-Assist) (`copy`, MIT,
Lua; catalog genre: simulation) is an Assetto Corsa mod that limits steering to the front tires'
optimal slip angle and adds self-steer that mimics caster. Its README explains why raw stick input
feels twitchy in a driving game and what an assist does about it.

**Roads and tracks.** JavaScript Racer's `v2.curves.html` and `v3.hills.html` (`copy`, MIT) are a
complete pseudo-3D road renderer. kart-royale's spline circuit and bench tools (`copy`, MIT) are a
starting point for 3D.

**Netcode and tools.** With many cars, client-server with prediction is usually simpler than
peer-to-peer rollback. For Godot, [netfox](https://github.com/foxssake/netfox) (not in the catalog;
MIT on GitHub) provides client-side prediction and server reconciliation; for two-player browser
races, [netplayjs](https://github.com/rameshvarun/netplayjs) (`copy`, ISC) works if your state
serializes. [Dear ImGui](https://github.com/ocornut/imgui) (`copy`, MIT) suits live handling tweaks.

## 5. Engine options (engine-neutral)

| engine | catalog class, license | fits when | tradeoff |
|---|---|---|---|
| [Godot 4](https://github.com/godotengine/godot) | `copy`, MIT | editor-driven 3D or 2D; has a `VehicleBody3D` node and a bundled `jolt_physics` module | the stock vehicle node suits arcade handling; sim handling means writing your own tire model |
| [Three.js](https://github.com/mrdoob/three.js) | `copy`, MIT | browser racers (kart-royale, Racez.io) | renderer only: physics, audio and tooling are separate choices |
| [Babylon.js](https://github.com/BabylonJS/Babylon.js) | `copy`, Apache-2.0 | browser 3D from a project that calls itself a game and rendering engine, not only a renderer | no racing reference in this catalog builds on it |
| [Bevy](https://github.com/bevyengine/bevy) + Avian | not in the catalog; MIT or Apache-2.0 per their READMEs | Rust, ECS, procedural content | still pre-1.0, so APIs change between releases |
| [raylib](https://github.com/raysan5/raylib) or [LibGDX](https://github.com/libgdx/libgdx) | `copy`, Zlib / `copy`, Apache-2.0 | top-down or pseudo-3D in C or Java | you build the editor and tools yourself |

Proprietary engines appear in the references: PolyRace uses Unity, and
[UETrafficGame](https://github.com/ScrappyCocco/UETrafficGame) (`copy`, MIT) is an Unreal Engine 5
vehicle playground inspired by Epic's vehicle template; its README reserves that template's starting
content to Epic. The engine's own terms apply on top of any code license.

## 6. Assets

- [Kenney](https://kenney.nl/assets): CC0, including the [Racing Kit](https://kenney.nl/assets/racing-kit),
  [Car Kit](https://kenney.nl/assets/car-kit) and [Racing Pack](https://kenney.nl/assets/racing-pack).
- [Poly Haven](https://polyhaven.com/license) and [ambientCG](https://ambientcg.com/license): CC0
  textures and HDRI skies. [Quaternius](https://quaternius.com/): CC0 models.
- [Freesound](https://freesound.org/): engine and tire recordings, licensed per sound; some are
  CC-BY-NC (non-commercial). [OpenGameArt](https://opengameart.org/): licensed per asset.
- Or generate everything in code, as kart-royale does: no asset licenses to track.

**A code license says nothing about the art.** The racing catalog shows it plainly:

- [Trigger Rally](https://github.com/CodeArtemis/TriggerRally) (`study only`): the code is GPL-3.0,
  but its LICENSE.md forbids modifying or redistributing the content without a separate license.
- Dust Racing 2D's images are CC BY-SA 3.0 (which this chassis treats as `study only`), and
  SuperTuxKart's art sits in a separate repository with per-folder licenses.
- JavaScript Racer's README says its music is licensed only for that project and its sprites are
  placeholders borrowed from the Genesis version of Out Run.
- OpenNFS (`copy`, MIT) is its own engine, but it runs only on the original games' data files,
  which its license does not cover.
- Decompilations and disassemblies go further. dRally's source files are decompiler output named
  by binary address, and NFSIISE builds on a disassembly of the original game (its `src/Asm`
  submodule). The catalog marks [dRally](https://github.com/urxp/dRally) and
  [NFSIISE](https://github.com/zaps166/NFSIISE) `check first` although GitHub reports MIT: their
  legal status is unclear, and they are never a source to copy, whatever license the reconstruction
  claims.

Real car makes, models, logos and liveries are trademarks: design your own cars unless you hold a
license. Record every asset in `THIRD_PARTY.md` ([template](../templates/THIRD_PARTY.md)).

## 7. Building it with AI tools

Follow the stage table in [../ai/README.md](../ai/README.md): Claude plans and reviews, Codex takes
one scoped task at a time, Grok reviews blind. For a racer:

**Design (Claude).** Write the handling model and the track format before code:

```text
Read ../opensource/playbooks/racing.md. For an arcade <kart/rally/street> racer, write
docs/handling.md: every tuning parameter (mass, grip, slip threshold, steering limit by speed,
drift entry and exit, boost), its unit, a starting value, and what the player feels when it
changes. Then write docs/track-format.md: centerline, checkpoints, surfaces, spawn grid, AI
racing line. Mark every assumption (assumed).
```

**Slice (Codex, one task each).** Vehicle controller; checkpoint and lap system; chase camera. Each
task ends in a scripted run:

```text
Implement lap counting per docs/track-format.md. Add playtest/scripts/shortcut.txt: drive
from the grid straight across the infield to the finish line; assert the lap counter is still
0. Add wrong-way.txt: cross the line backwards then forwards; assert no lap is awarded.
Run both at 30, 60 and 144 FPS render rates and show that lap times match.
```

**AI and feel (Codex builds, you measure).** Copy kart-royale's idea of benches that answer a design
question with a number:

```text
Add tools/autoplay: 8 AI cars, 3 laps, seed <N>. Assert every car finishes, none is stuck
for more than 5 seconds, no position or speed is NaN, and final positions agree with
progress along the centerline. Add tools/drift-bench: the same AI lap with and without
drifting; print both lap times and the difference.
```

**Review (Grok, blind).** Give it the symptom ("cars clip through the barrier at turn 3 above
<speed>") and the physics files, not your theory. Never paste `study only` code such as
SuperTuxKart's AI into a prompt; describe the behavior in your own words (see `ai/README.md`).

kart-royale's README reports that its automated screenshot critics found none of the gameplay bugs;
inverted steering, missing mobile controls and a race-freezing pause menu all came from a human
playing. Budget for people.

### Playtest checklist for this genre

- [ ] Shortcuts, wrong-way driving and reversing over the line never award a lap.
- [ ] The same input script gives the same lap time at 30, 60 and 144 FPS.
- [ ] Gamepad steering at top speed is controllable; keyboard steering is not binary.
- [ ] Every AI car finishes every track, and recovers after being pushed off.
- [ ] A ghost replays the recorded lap exactly.
- [ ] Reset works everywhere, including wedged against a wall or upside down.
- [ ] Split-screen (if any) holds the target frame rate with all cars on screen.
- [ ] A new player finishes a lap first try, then asks to race again for a better time.

## 8. Genre-specific pitfalls

- **Physics tied to frame rate.** A variable timestep changes handling on every machine; step
  physics at a fixed rate and interpolate the render.
- **Tunneling.** At racing speeds a car can pass through a thin barrier in one step; use continuous
  collision detection or thicker colliders.
- **Finish-line-only lap counting.** It invites shortcuts and back-and-forth exploits. Count progress
  along the track, as SuperTuxKart's drive graph does.
- **Tracks that cross themselves.** Bridges and figure-eights break a nearest-point lookup on a flat
  centerline; SuperTuxKart has 3D drive nodes alongside 2D ones.
- **Realistic physics on a gamepad.** A sim tire model on a thumbstick feels twitchy; the gamepad
  assist mod above was written for exactly that complaint.
- **Catch-up that feels like cheating.** Players notice AI that speeds up behind them; tune it openly.
- **Camera sickness.** kart-royale's camera probe treats swing as "the nausea metric"; measure yours.
- **Floating-point precision.** Very large tracks jitter far from the origin; keep coordinates small.
- **Remakes that need the original game.** OpenNFS, dRally, NFSIISE and
  [Dethrace](https://github.com/dethrace-labs/dethrace) (`check first`, a reverse engineering of
  Carmageddon) all need commercial data files; they teach structure, not shippable content.
