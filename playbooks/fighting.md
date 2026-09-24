# Fighting playbook

One-on-one fighters, platform fighters and beat 'em ups. The full list, with license and activity
for every project, is in [../catalog/fighting.md](../catalog/fighting.md). Every project below was
checked against its repository on 2026-09-23; reuse classes are quoted exactly as the catalog
states them.

## 1. What defines the genre

**Core loop:** neutral (spacing, footsies) → a hit or a block → hit confirm into a combo or a
blockstring → knockdown → wake-up pressure → back to neutral. Rounds make a match, usually best of
three.

**Player verbs:** walk, dash, jump, crouch; light, medium and heavy attacks; special moves entered as
motion inputs (quarter circle, charge, double tap); block high or low; throw and throw escape.
Platform fighters add shield, roll, air dodge, grab and ledge recovery. Beat 'em ups swap the single
opponent for waves of enemies.

**Win and lose:** deplete the opponent's health (platform fighters: ring them out until their stocks
run out); at time-out, more health wins. A beat 'em up is won by clearing stages, lost with the last life.

**What makes it hard to build:** everything runs on a fixed tick, usually 60 per second, and players
feel single-frame differences, so the simulation must be deterministic from the first commit.

| subgenre | defining extra | catalog example |
|---|---|---|
| traditional 2D | motion inputs, frame data, meter | [Sakuga-Engine](https://github.com/NoisyChain/Sakuga-Engine) |
| 3D | sidestep axis, orbiting camera | [3D-Fighting-Camera](https://github.com/GatitoMimoso00/3D-Fighting-Camera) |
| platform fighter | percent damage, ring-outs, stages with ledges | [Super_Bash_Folds](https://github.com/blancmathis/Super_Bash_Folds) |
| beat 'em up | scrolling stages, enemy waves, co-op | [OpenBOR](https://github.com/DCurrent/openbor) |

## 2. The systems to build, in build order

### First playable vertical slice

- [ ] Fixed-timestep simulation at 60 ticks per second, fully separate from rendering.
- [ ] `step(state, input_p1, input_p2) -> state`: the whole game advances through one function.
- [ ] Input sampled once per tick into a ring buffer of the last 30 or so ticks per player.
- [ ] Two characters (the same one twice is fine): walk, jump, crouch, one attack.
- [ ] Per-move frame data as data, not code: startup, active and recovery frames, with hitboxes and
      hurtboxes per frame.
- [ ] Hit and block resolution: damage, hitstun, blockstun, pushback, hitstop.
- [ ] Health bars, round timer, KO, round reset, match end.
- [ ] Debug overlay: boxes, current frame of the move, frame advantage after each hit or block.
- [ ] Local two-player on one keyboard or two gamepads.

Done when two people play a full match and neither can point at a hit that "should not have happened".

### v1

- [ ] Game state is one plain, serializable value; save and load are each a single call. This is the
      prerequisite for rollback, replays and training mode, so do it before adding content.
- [ ] Determinism: integer or fixed-point math for gameplay, the random seed stored inside the
      state, no wall-clock reads, no iteration over unordered containers.
- [ ] Rollback netcode through a library from section 4, with a local input-delay setting and a
      state hash exchanged to detect desyncs.
- [ ] Motion-input parser with leniency windows; a priority rule for overlapping inputs.
- [ ] Throws and throw escapes, juggle limits and damage scaling (to stop infinite combos).
- [ ] Two or three characters with distinct archetypes (rushdown, zoner, grappler).
- [ ] Character select, stage select, rematch.
- [ ] Training mode: input display, frame data readout, dummy record and playback.
- [ ] Replays stored as initial state plus the input log.
- [ ] Gamepad support, remapping, and a stated rule for opposite directions held together (SOCD).
- [ ] CPU opponent with difficulty levels.

### Polish

- [ ] Hit sparks, screen shake and sound on the exact tick of the hit, rollback-safe (see pitfalls).
- [ ] Camera: 2D push and zoom, or a 3D orbit that survives cross-ups.
- [ ] Lobby, matchmaking or room codes; spectators.
- [ ] Accessibility: a simplified input mode, audio cues for key states, full remapping.
- [ ] Balance pass driven by recorded matches, not impressions.

## 3. Reference projects to study

1. **[OpenOMF](https://github.com/omf2097/openomf)**: `copy`, MIT, C. A remake of One Must Fall 2097.
   - `NETWORKING.md` explains a custom GGPO-style rollback: each side sends its unconfirmed inputs
     with their tick numbers, rewinds and replays when late inputs arrive, and exchanges state
     hashes; a hash mismatch ends the match.
   - The same document describes rollback-safe audio: after a replay, sounds that should no longer
     play are faded out and new ones faded in, to avoid pops.
   - `src/controller/` puts keyboard, joystick, AI, network and recorded input behind one
     controller interface, so a replay and a remote player look the same to the game.
   - `rectests/*.REC` are recorded matches used as regression tests, run by `run_rectests.sh`.
   - It loads the original game's data files, downloaded separately (BUILD.md calls the original
     freeware); that data is not MIT.
2. **[Ikemen GO](https://github.com/ikemen-engine/Ikemen-GO)**: `check first`, Go. The catalog shows
   "MIT (list; GitHub could not read it)". Its `LICENCE.txt` reads as MIT, but GitHub's detector
   returns no assertion, so read the whole file before copying anything.
   - Learn data-driven characters: it runs M.U.G.E.N 1.1-compatible characters, stages and
     screenpacks, which means every move, state and hitbox lives in content files, not engine code.
   - Its README notes the bundled screenpack is CC-BY 3.0, not MIT, and that it dynamically links
     FFmpeg (LGPL-2.1). One repository, three licenses.
3. **[Sakuga-Engine](https://github.com/NoisyChain/Sakuga-Engine)**: `copy`, MIT, C# on Godot 4
   (.NET build). A 1v1 2D fighter framework with rollback netcode built in, a state system, stances,
   projectiles, a pseudorandom number generator, game modes and an experimental AI. Study how it
   lets designers build a character without code.
4. **[Super_Bash_Folds](https://github.com/blancmathis/Super_Bash_Folds)**: `copy`, MIT, TypeScript,
   runs in the browser. A platform fighter with shields, rolls, air dodges, grabs, ledges, items and
   stock matches.
   - Learn the content contract: each fighter is one folder (`fighters/<id>/fighter.json` and
     `render.json`) validated against `fighters/fighter.schema.json`, and joins the game without an
     engine edit.
   - The pack format has license and attribution fields, and `render.json` maps art onto 50
     animation roles per fighter: a useful measure of how much art one character needs.
5. **[OpenBOR](https://github.com/DCurrent/openbor)**: `copy`, BSD-3-Clause, C. A royalty-free,
   sprite-based side-scrolling engine built for beat 'em ups, with a built-in script engine and games
   distributed as separate modules. Study the split between engine and module, and how scripting
   removed hard-coded behavior.
6. **[FightEngine](https://github.com/Fxll3n/FightEngine)**: `copy`, MIT, GDScript (Godot 4.5+
   plugin). `HitBox2D` and `HurtBox2D` nodes that only collide with each other, and attacks authored
   as `AnimationPlayer` tracks that move boxes and set active frames. If you adopt this, the
   animation time must be part of your saved state or rollback breaks.
7. **[TF.EX](https://github.com/Fcornaire/TF.EX)**: `study only`, GPL-2.0, C#. A mod that adds
   rollback netplay to TowerFall. It ships as separate pieces (state save and restore, replays, an
   input display, netplay), and its README calls the state library the base the others are built on.
   Read it for the order of work when retrofitting rollback; copy nothing. (A README badge says MIT;
   the LICENSE file is GPL-2.0.)

Look at, copy nothing: [Darklings](https://github.com/kidagine/Darklings-FightingGame) (`check first`, no license) lists deterministic physics and rollback in Unity.

## 4. Reusable permissive code

**Rollback netcode.** All are GGPO-style (input prediction, rewind, resimulate). Pick by language.

| library | class | license | language | notes from its README |
|---|---|---|---|---|
| [GekkoNet](https://github.com/HeatXD/GekkoNet) | `copy` | BSD-2-Clause | C/C++ | local, online, spectator and replay sessions; a stress session that keeps rolling back to expose desyncs; network stats |
| [Backdash](https://github.com/Delta3-Studio/Backdash) | `copy` | MIT | C# (.NET, NuGet) | MonoGame samples in `samples/`, and its README links a Godot sample; up to 4 players, replay save and load |
| [netplayjs](https://github.com/rameshvarun/netplayjs) | `copy` | ISC | TypeScript | WebRTC peer-to-peer in the browser; `RollbackWrapper`, or `LockstepWrapper` for state that cannot be rewound; public matchmaking server or self-host `netplayjs-server` |
| [backroll-rs](https://github.com/HouraiTeahouse/backroll-rs) | `copy` | ISC | Rust | pure Rust GGPO port, "early beta"; last push 2023-03 |
| [PleaseResync](https://github.com/HeatXD/PleaseResync) | `copy` | MIT | C# | "still under development" |
| [BestoNet](https://github.com/BestoGames/BestoNet) | `copy` | MIT | C# (Unity) | built for a shipped fighting game on Steamworks; its README says it will not work out of the box |
| [Rollback-Core](https://github.com/gregorik/Rollback-Core) | `copy` | MIT | C++ (Unreal Engine 5 plugin) | Win64; rollback state marked with `UPROPERTY(SaveGame)` |

- Upstream, not in the catalog (licenses read from GitHub on 2026-09-23): the original
  [GGPO](https://github.com/pond3r/ggpo) is MIT; [GGRS](https://github.com/gschup/ggrs), its Rust
  reimplementation, is MIT or Apache-2.0 at your option.
- [extreme_bevy](https://github.com/johanhelsing/extreme_bevy) (`copy`, CC0-1.0, Rust) is a worked
  example of Bevy + GGRS + Matchbox for browser peer-to-peer rollback. Its README warns the sprites
  are copied from the original Extreme Violence and not cleared as CC0, and that the history is
  force-pushed; pin a commit.

**State, camera and tools.**
- [massive-ecs](https://github.com/nilpunch/massive-ecs) (`copy`, MIT, C#): an ECS designed for
  deterministic prediction-rollback, with minimal storage for fast saves; Unity package or plain C#.
- [3D-Fighting-Camera](https://github.com/GatitoMimoso00/3D-Fighting-Camera) (`copy`, MIT, GDScript):
  a sidestep camera whose README explains why the naive approach flips sides on cross-ups.
- [unity-pattern-combo](https://github.com/homemech/unity-pattern-combo) (`copy`, MIT, C#): combos on the command pattern.
- [Dear ImGui](https://github.com/ocornut/imgui) (`copy`, MIT, C++): in-game frame-data and hitbox editors.

You rarely need a general physics engine such as [Box2D](https://github.com/erincatto/box2d)
(`copy`, MIT): axis-aligned boxes and your own pushback rules are easier to keep deterministic.

## 5. Engine options (engine-neutral)

| engine | catalog class, license | fits when | tradeoff |
|---|---|---|---|
| [Godot 4](https://github.com/godotengine/godot) | `copy`, MIT | you want an editor, 2D and 3D, and fighting-specific add-ons (Sakuga-Engine, FightEngine, Backdash's Godot sample) | keep gameplay out of the built-in physics and animation systems, or carry their state in your save |
| [raylib](https://github.com/raysan5/raylib) | `copy`, Zlib | you want to own the loop in C or C++, paired with GekkoNet | no editor; you build frame-data tools yourself |
| [MonoGame](https://github.com/MonoGame/MonoGame) | `check first`, MS-PL + MIT (list; GitHub could not read it) | C# without an editor; Backdash's SpaceWar samples use it | framework, not engine: scenes, UI and tools are yours; confirm its LICENSE file before you build on it |
| [Bevy](https://github.com/bevyengine/bevy) | not in the catalog; MIT or Apache-2.0 per its README | Rust, ECS, browser builds; extreme_bevy shows the GGRS path | still pre-1.0, so APIs change between releases |
| [Phaser](https://github.com/phaserjs/phaser) or [PixiJS](https://github.com/pixijs/pixijs) | `copy`, MIT | browser 2D, paired with netplayjs | JavaScript numbers are floats: keep gameplay in integers |

Proprietary engines appear in reference projects too (Darklings and BestoNet use Unity,
Rollback-Core targets Unreal); their own license terms apply on top of anything you copy.

## 6. Assets

A 2D fighter is an art-heavy game: Super_Bash_Folds maps 50 animation roles for every fighter.
Decide the art pipeline (hand-drawn sprites, 3D models rendered to sprites, or real-time 3D) before
you commit to a roster size.

- [Kenney](https://kenney.nl/assets): CC0 packs, including [Impact Sounds](https://kenney.nl/assets/impact-sounds)
  and 3D [Mini Characters](https://kenney.nl/assets/mini-characters).
- [Quaternius](https://quaternius.com/license.html): 3D models, not CC0 any more. The Quaternius Asset
  License v1.0 (2026-08-28) allows commercial games with no credit, but not redistributing the assets
  as assets, including in a template or asset pack, so keep them out of a public starter repo.
- [OpenGameArt](https://opengameart.org/): every asset has its own license (CC0, CC-BY, CC-BY-SA,
  GPL and others). This chassis treats CC-BY-SA as `study only`; filter for CC0 or CC-BY.
- [Freesound](https://freesound.org/): licensed per sound, and some are CC-BY-NC (non-commercial).

**A code license says nothing about the art.** The references above show every variant: OpenOMF's
engine is MIT but runs on the original game's data files; Ikemen GO's screenpack is CC-BY 3.0;
extreme_bevy is CC0 but its sprites are not cleared; OpenBOR's README records that the original
Beats of Rage used assets from SNK Playmore's King of Fighters series. Community character packs
for such engines often reuse commercial characters: trace every file before shipping one, and
record every asset in `THIRD_PARTY.md` ([template](../templates/THIRD_PARTY.md)).

## 7. Building it with AI tools

Follow the stage table in [../ai/README.md](../ai/README.md): Claude plans and reviews, Codex takes
one scoped task at a time, Grok reviews blind. For a fighting game that looks like this.

**Design (Claude).** Before any code:

```text
Read ../opensource/playbooks/fighting.md. Design GameState for a 1v1 fighter as one plain
serializable value (players, current move and frame, hitstun, fixed-point positions, RNG seed,
round timer) and a move data format (startup, active, recovery, per-frame boxes, advantage).
Write docs/state.md and docs/move-format.md. List every piece of state an engine would hide
from us (animation time, particles, audio, timers) and how each is saved or excluded.
```

**Slice (Codex, one task each).** Fixed-timestep loop and input ring buffer; hit resolution from the
move format; the debug overlay. Each task names its files and ends with a scripted playtest:

```text
Implement step(state, in1, in2) per docs/state.md. Add playtest/scripts/jab-trade.txt:
both players press light attack on frame 10; assert both take damage on the same frame and
frame advantage reads 0. Add jab-block.txt: P2 holds back; assert blockstun equals the value
in data/moves/jab.json. Run both and show the output.
```

**Rollback (Codex, then a blind review).** Integrate the library from section 4 behind
`save_state`, `load_state` and `advance`. Then add a stress mode that rolls back several frames every
tick and compares state hashes (GekkoNet ships one; build the same for other libraries). Hand the
reviewer the symptom and the files, not your theory:

```text
Two clients desync; state hashes diverge on frame <F>. Files: <src/sim/...>. List every
source of non-determinism you find (floats, unordered iteration, time, unseeded randomness,
state outside GameState), ranked by likelihood, with the line that shows it.
```

**Never paste `study only` code into a prompt**, including TF.EX or any GPL fighter. Describe the
mechanic in your own words and start a fresh session, as `ai/README.md` explains.

### Playtest checklist for this genre

- [ ] Two people who did not build it play ten matches; check every "I pressed it" against the input log.
- [ ] Frame data shown in training mode matches frames counted in a recorded replay.
- [ ] A saved replay of a full match ends on the same state hash every time it is played back.
- [ ] The rollback stress mode runs a full match with no hash mismatch.
- [ ] Online under added latency and packet loss, both players see the same KO on the same frame.
- [ ] Keyboard and gamepad both work; left and right held together obey your SOCD rule.
- [ ] No infinite combo survives: juggle limits and scaling hold in the corner.
- [ ] A new player can do a special move within a minute of being told the input.

## 8. Genre-specific pitfalls

- **Floats and engine physics in rolled-back gameplay.** Results can differ between machines and
  builds; use integers or fixed point for anything that decides a hit.
- **State outside the saved value.** Animation players, particle systems, coroutines, timers and
  audio keep running during a rollback unless you save them or make them pure functions of state.
- **Audio and effects after a rollback.** A hit spark or sound can appear, then be undone by a
  correction. OpenOMF fades sounds out and in to hide it; decide your rule early.
- **Input read per rendered frame.** On a 144 Hz display presses get dropped or doubled against a
  60 Hz simulation; sample input once per simulation tick.
- **Desync detection that cannot fire.** GekkoNet's README notes desync detection works only when
  limited saving is disabled. Prove your hash check fails when you break determinism on purpose.
- **Motion inputs that are too strict or too loose.** Record real attempts and tune the leniency
  window from the log, not by feel.
- **SOCD.** Opposite directions pressed together (common on all-button controllers, see
  [SOCD-Cleaner](https://github.com/ccelik97/SOCD-Cleaner), `copy`, MIT) need a defined outcome.
- **Content scope.** Each character is a full art and balance job; finish two before starting a third.
- **Download lures.** Never download a release, zip or installer from a catalog repository; build
  from source, as the [catalog's safety note](../catalog/README.md) explains.
