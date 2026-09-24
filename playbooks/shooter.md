# Shooter playbook

First-person and third-person shooters, plus the top-down multiplayer shooters the catalog files
here; scrolling shoot 'em ups are in the [arcade playbook](arcade.md). The catalog lists 202
shooter projects, 22 of them `copy` class; the full table is in
[../catalog/shooter.md](../catalog/shooter.md). Many of the best-maintained rows are GPL source
ports of id Software engines, which this chassis treats as `study only`, and many need commercial
game data. Every project named below was checked against its repository on 2026-09-23.

## 1. What defines the genre

**Core loop:** move through a space, spot a threat, aim, shoot, manage health, ammo and position,
and reach an objective: the exit of a level, a frag limit, a round win. Single-player shooters add
keys, secrets and encounters; multiplayer shooters repeat short matches on a few maps.

**Player verbs:** move (strafe, sprint, crouch, jump); look and aim with a mouse or a stick; shoot,
either hitscan (instant) or with projectiles; reload; switch weapons; use or interact; take cover
(common in third person); throw grenades. Arena shooters add movement tricks: Red Eclipse has wall
running, boosts and dashing.

**Win:** reach the exit or beat the boss; in multiplayer, reach the score or round limit or
complete the objective (Hypersomnia has bomb defusal and gun game). **Lose:** health runs out;
single-player restarts at a checkpoint, multiplayer respawns or waits for the next round.

**What makes it hard to build:** aim feel (raw input, no smoothing, sensitivity that does not
change with frame rate), hit registration that players trust, netcode (client prediction, server
reconciliation, interpolation, lag compensation), levels with readable sightlines and cover, and
enemies that feel smart without being perfect shots.

## 2. The systems to build, in build order

### First playable vertical slice: one room, one weapon, one enemy

- [ ] Fixed-step simulation with interpolated rendering
- [ ] First-person or over-the-shoulder camera; raw mouse input with a sensitivity setting;
      gamepad look with a dead zone
- [ ] Movement with acceleration, friction and air control; capsule collision against level geometry
- [ ] One hitscan weapon with fire rate, spread and a visible impact
- [ ] Health, damage, death and respawn
- [ ] One enemy that checks line of sight, closes distance and fires after a reaction delay
- [ ] Crosshair and a health and ammo display
- [ ] A level blocked out in plain boxes, before any art

### v1

- [ ] Three or four weapons with distinct roles (precise hitscan, splash projectile, close range)
- [ ] Ammo and reloads, pickups or loadouts
- [ ] Enemy navigation on a navigation mesh, with cover and flanking, and three archetypes
- [ ] Levels with keys, doors and secrets, or multiplayer maps with safe spawn points
- [ ] Multiplayer: authoritative server; the same movement code on client and server for prediction;
      interpolation of other players; lag-compensated hits
- [ ] Bots, so multiplayer can be tested and played with few people online
- [ ] Settings: field of view, sensitivity, invert, remapping, audio
- [ ] Join a game by address or code; a dedicated server that runs headless

### Polish

- [ ] Recoil, muzzle flash, hit markers, directional damage indicators, positional footsteps
- [ ] Weapon animations; camera bob with an off switch
- [ ] Aim assist for gamepads, tuned and optional
- [ ] Spectating and demo recording
- [ ] Server-side validation of every shot, move and pickup
- [ ] Accessibility: field-of-view slider, reduced motion, subtitles, team colors safe for color
      blindness

## 3. Reference projects to study

**ioquake3** ([repo](https://github.com/ioquake/ioq3)): `study only` (GPL-2.0), C on SDL2. The
community continuation of Quake III Arena. `code/game/bg_pmove.c` is "both games player movement
code": it takes a player state and a user command and returns a new player state, and runs on the
server and in the client. `code/cgame/cg_predict.c` uses it to predict the local player ahead of
the server's snapshots, `code/qcommon/msg.c` delta-encodes entity and player states, and
`code/botlib/` holds the bots. Learn the prediction model: one movement function, shared by server
and client.

**Chocolate Doom** ([repo](https://github.com/chocolate-doom/chocolate-doom)): `study only`
(GPL-2.0), C. A Doom source port that aims at "accurate reproduction of the original DOS versions
of the games, including bugs" and compatibility with DOS demo, configuration and save files. A Doom
demo is recorded per-tick input (`G_ReadDemoTiccmd` in `src/doom/g_game.c`) played back through the
simulation, so exact reproduction is testable. Learn why a deterministic simulation turns every
recorded match into a regression test.

**Red Eclipse** ([repo](https://github.com/redeclipse/base)): `check first` in the catalog; its
`doc/license.txt` puts the code under zlib, from the Tesseract and Cube 2 engines, with the bundled
ENet under an MIT-style license. C++ on SDL and OpenGL. An arena shooter with parkour (wall
running, boosts, dashing), game modes with mutators, and a built-in editor that edits maps
cooperatively online. Learn how movement tech changes arena design, and live cooperative editing.

**Hypersomnia** ([repo](https://github.com/TeamHypersomnia/Hypersomnia)): `study only`
(AGPL-3.0), C++ with no game engine. A top-down competitive shooter playable in the browser.
Its networking is built on "cross-platform simulation determinism": only inputs travel, and every
client, browser or native, simulates the same match, floats included. It ships an in-game map
editor and a headless server as a Docker image or AppImage. Learn what full determinism buys and
what it costs.

**TOSIOS** ([repo](https://github.com/halftheopposite/TOSIOS)): `copy` (MIT), TypeScript. An
open-source browser IO shooter: a PixiJS client, an authoritative Colyseus server on Node.js and
a `common` package of shared constants and logic. Maps come from Tiled with two reserved layers,
`collisions` and `spawners`; a `half` collision tile stops players but lets bullets through, a
`full` tile stops both. Learn a small authoritative multiplayer shooter you can fork.

**Third Person Shooter Demo** ([repo](https://github.com/godotengine/tps-demo)): `check first` in
the catalog; its `LICENSE.md` puts the code under MIT and the assets and music under CC-BY 3.0.
GDScript on Godot 4. `player/player_input.gd` is a `MultiplayerSynchronizer` that syncs aiming,
motion, shooting and the shoot target, clamps camera pitch, and treats a short press of the aim
button as a toggle and a hold longer than 0.4 seconds as hold-to-aim, for trackpads and
accessibility. Learn over-the-shoulder aiming and input synchronization in an engine you can use.

## 4. Reusable permissive code

Catalog projects keep the catalog's class. Libraries marked "not in the catalog" had their license
read from GitHub on 2026-09-23; re-read the LICENSE file at the commit you copy from.

| need | project | class | license |
|---|---|---|---|
| client and server netcode for a C++ shooter | [yojimbo](https://github.com/mas-bandwidth/yojimbo) | not in the catalog | BSD-3-Clause |
| UDP transport | [ENet](https://github.com/lsalzman/enet) (C); Red Eclipse and LÖVE bundle it, and Godot has an `enet` module | not in the catalog | MIT |
| authoritative rooms on Node.js | [Colyseus](https://github.com/colyseus/colyseus); TOSIOS is built on it | not in the catalog | MIT |
| unreliable, UDP-like messages to browsers | [geckos.io](https://github.com/geckosio/geckos.io) (WebRTC) | not in the catalog | BSD-3-Clause |
| a whole browser shooter to fork | [TOSIOS](https://github.com/halftheopposite/TOSIOS) | `copy` | MIT |
| 3D physics and character collision | [Jolt Physics](https://github.com/jrouwe/JoltPhysics) (C++) | not in the catalog | MIT |
| bot navigation meshes | [Recast Navigation](https://github.com/recastnavigation/recastnavigation) (C++) | not in the catalog | Zlib |
| browser 3D rendering | [three.js](https://github.com/mrdoob/three.js), [Babylon.js](https://github.com/BabylonJS/Babylon.js) | `copy` | MIT, Apache-2.0 |
| entity-component-system | [EnTT](https://github.com/skypjack/entt) (C++), [flecs](https://github.com/SanderMertens/flecs) (C, C++) | not in the catalog | MIT (GitHub reads flecs as unknown; its LICENSE file is MIT) |
| debug overlays and admin panels | [Dear ImGui](https://github.com/ocornut/imgui) (C++) | `copy` | MIT |

The prediction and delta-encoding ideas in ioquake3 are the reference design, but its code is
`study only`. Describe the model in your own words and build it on the libraries above.

## 5. Engine options (engine-neutral)

The GPL engines at the top of the catalog (ioquake3, GZDoom, Chocolate Doom and other id Tech
ports) are `study only` here, so they are not engine options for a game built on this chassis.

- **[Godot](https://github.com/godotengine/godot)** (`copy`, MIT). 3D with an editor, and
  `multiplayer`, `enet`, `webrtc`, `navigation_3d` and `jolt_physics` modules in the engine
  source; the TPS demo shows its multiplayer synchronizers. Tradeoff: major versions break
  projects; the TPS demo keeps a branch per older Godot version.
- **[Stride](https://github.com/stride3d/stride)** (not in the catalog; MIT). A C# 3D engine with
  the Game Studio editor and an `fps` project template (`stride new fps`). Tradeoff: building it
  from source needs specific MSVC toolsets, per its README.
- **[Babylon.js](https://github.com/BabylonJS/Babylon.js)** (`copy`, Apache-2.0) or
  **[three.js](https://github.com/mrdoob/three.js)** (`copy`, MIT). 3D in the browser, with
  nothing to install for players. Tradeoff: three.js is a rendering library, so physics, netcode
  and input are yours; both are bounded by browser performance and download size.
- **[jMonkeyEngine](https://github.com/jMonkeyEngine/jmonkeyengine)** (`copy`, BSD-3-Clause). A
  Java 3D engine with an SDK derived from NetBeans. Tradeoff: Java, with the SDK as a separate
  download.
- **Red Eclipse** (`check first`; code zlib per `doc/license.txt`). A complete arena shooter with
  a cooperative editor. Tradeoff: it is a specific game rather than a general engine, and its
  content defaults to CC-BY-SA.

## 6. Assets

Shooters need a lot of 3D: modular level pieces, weapons with first-person animations, characters,
and physically based textures, plus weapon and impact sounds that carry information.

- **[Freedoom](https://github.com/freedoom/freedoom)** (`check first` in the catalog; its
  `COPYING.adoc` is BSD-3-Clause): complete levels, art, sound and music for Doom engines.
- **[LibreQuake](https://github.com/lavenderdotpet/LibreQuake)** (`check first`; `docs/COPYING` is
  BSD-3-Clause): free content for Quake engines, which otherwise need "proprietary data files from
  id Software".
- **[Quaternius](https://quaternius.com/license.html):** not CC0 any more. The Quaternius Asset
  License v1.0 (2026-08-28) allows commercial games with no credit, but forbids redistributing the
  assets as assets, including in a template or asset pack, so keep them out of a public starter repo.
- **[Poly Haven](https://polyhaven.com/license):** "Our assets are all licensed as CC0".
- **[ambientCG](https://docs.ambientcg.com/license/):** all assets under CC0 1.0 Universal.
- **[Kenney](https://kenney.nl/support):** "all game assets on the asset pages are public domain
  licensed (CC0)".
- **[Freesound](https://freesound.org/help/faq/)** and
  **[OpenGameArt](https://opengameart.org/content/faq):** licensed per file; skip CC BY-NC, and
  this chassis groups CC-BY-SA with `study only`, so prefer CC0 and CC-BY.

**A code license says nothing about the art.** The TPS demo's code is MIT but its assets need
CC-BY 3.0 credit. Red Eclipse's code is zlib, while its content defaults to CC-BY-SA and accepts
nothing more restrictive than BY and SA. ioquake3 and the Doom ports ship engines, not the
commercial games' data; Freedoom and LibreQuake exist to fill that gap, and their BSD-3-Clause
terms still require the copyright notice. Record every asset in `THIRD_PARTY.md`
([template](../templates/THIRD_PARTY.md)).

## 7. Building it with AI tools

Follow the stages in [../ai/README.md](../ai/README.md): Claude plans and reviews, Codex takes one
scoped task at a time, Grok reviews blind. Netcode is where shooters fail, so it gets its own
failure list and a blind review, and it is tested under added latency from the first day.

1. *Design (Claude, plan mode):* "Using ../opensource/playbooks/shooter.md, write docs/design.md:
   first or third person, single-player or multiplayer, the weapon list with roles, and a slice of
   one room, one weapon, one enemy. If multiplayer, name the network model (server-authoritative
   with prediction, or deterministic lockstep) and why."
2. *Failure list:* add shooter items to the template list: sensitivity that changes with frame
   rate, shots traced from the camera hitting what the muzzle cannot see, a hit shown on the
   client that the server rejects, rubber-banding under packet loss, spawning in view of an enemy,
   and a bot stuck on a stair.
3. *Movement (Codex):* "Write the player movement as one pure function: (state, input, dt) ->
   state, with no rendering or engine calls, used by both client and server. Playtest: replay a
   recorded input file on client and server builds and assert identical final positions."
4. *Netcode (Codex, then a blind review):* "Add client-side prediction with reconciliation and
   interpolation of remote players at <N> ms behind. Add a latency and loss simulator (100 ms,
   2 percent loss). Playtest: two headless clients strafe and fire for 60 s; assert the server
   and both clients agree on every hit." ioquake3 is `study only`: describe its model in your own
   words, never paste it.
5. *Bots:* ask for navigation-mesh movement plus a reaction delay and an accuracy that falls
   off with distance and target speed, all in one data file.
6. *Blind review (Grok):* send the symptom and the files: "At 150 ms simulated latency, players
   see hit markers for shots the server does not count. Reproduce with: <command>."

**Playtest checklist:**

- [ ] A new player finds and fires the first weapon within 30 seconds
- [ ] Mouse turn distance per centimeter is the same at 30, 60 and 144 Hz
- [ ] Hits register as players expect at 0, 100 and 200 ms with 2 percent loss
- [ ] No rubber-banding in a 10-minute match at 100 ms
- [ ] A player who joins mid-match sees the same world as everyone else
- [ ] Bots reach every area of every map without getting stuck
- [ ] Field of view, sensitivity and camera bob settings persist and apply immediately
- [ ] Nobody in the playtest reports motion sickness with default settings

## 8. Genre-specific pitfalls

- **Aim tied to frame rate or smoothed.** Mouse look must use raw deltas with no acceleration or
  smoothing by default, and sensitivity must not change with frame rate.
- **Trusting the client.** The server decides hits, damage, pickups and position; the client only
  predicts and displays.
- **No prediction.** Without it every input waits a full round trip. With it but without shared
  movement code, the client mispredicts constantly; ioquake3 runs one movement file on both sides.
- **Camera and muzzle disagree.** Tracing from the camera can hit targets the gun cannot see, and
  tracing from the muzzle can miss what the crosshair covers. Decide which rules, especially in
  third person.
- **Art before blockout.** Sightlines, cover and scale are found in gray boxes; art built first
  gets thrown away.
- **Perfect bots.** Bots that never miss are not fun. Give them reaction time and error.
- **Motion sickness.** A narrow default field of view and forced camera bob make players ill. Ship
  a field-of-view slider and an off switch.
- **Building on a GPL engine.** id Tech ports are excellent to study, but this chassis copies code
  only from `copy` projects, and a game built on a GPL engine is derived from it.
- **Commercial data.** Classic source ports run on the original game's files unless you pair them
  with Freedoom or LibreQuake. Test with those, and make your own content to ship.
- **Starting with online multiplayer.** It adds a server, prediction and latency testing to every
  feature. Prove the combat against bots, then add the network.
