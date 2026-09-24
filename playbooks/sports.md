# Sports playbook

Team and individual sports, arcade and simulation, plus pinball, billiards and management games.
The catalog lists 11 sports projects, 2 of them `copy` class; the full table is in
[../catalog/sports.md](../catalog/sports.md). Many good sports projects are filed under
[arcade](../catalog/arcade.md), [simulation](../catalog/simulation.md) and
[strategy](../catalog/strategy.md), so the references below cross genres. Every project was checked
against its repository on 2026-09-23; reuse classes are quoted exactly as the catalog states them.

## 1. What defines the genre

**Core loop:** possession or turn → an attempt (shot, pass, serve, putt, delivery, flick) → physics
resolves it → score, save or foul → restart from a set piece → period ends → result → the next match
in a league, tournament or career.

**Player verbs:** move, pass, shoot, tackle or steal, switch the controlled player; for individual
sports, aim plus power plus timing (golf, tennis, badminton, cricket); for pinball, flip and nudge.

**Win and lose:** more points when time or periods run out, first to a target score, or fewest
strokes. Around the match sits a meta layer: league tables, promotion, a career ladder.

**What makes it hard to build:** players already know the rules, so every rule is either correct or
a visible, deliberate simplification. The ball is the star and its flight must be readable at a
glance. Team AI has to position well without the ball, which is most of the time.

| subgenre | defining extra | catalog example |
|---|---|---|
| team arcade | AI teammates, formations, player switching | [Open Kick-Off](https://github.com/ssenegas/kickoff), [Freekick 3](https://github.com/anttisalonen/freekick3) |
| individual timing | aim, power and timing windows | [Free Tennis](https://codeberg.org/osgames/freetennis) (`study only`, GPL-2.0, one OCaml file) |
| physics sport | ball or table simulation is the game | [Open Golf](https://github.com/mgerdes/Open-Golf), [Vector Pinball](https://github.com/dozingcat/Vector-Pinball), [NOVA PINBALL](https://github.com/wesleywerner/nova-pinball) |
| management | tactics and squad; matches are simulated | [OpenWebSoccer-Sim](https://github.com/ihofmann/open-websoccer), [EliFUT](https://github.com/EliFUT/android) |

## 2. The systems to build, in build order

### First playable vertical slice

- [ ] Fixed-timestep simulation with a seeded random generator; rendering interpolates.
- [ ] Ball physics: gravity, drag, bounce and friction, tested with no players on the field.
- [ ] The playing area: bounds, goals, holes, net or pockets, and what counts as "in".
- [ ] One controllable athlete (or club, cue, flipper) with the sport's main action.
- [ ] Scoring and a restart after every point (kickoff, serve, next shot).
- [ ] One opponent: local second player or the simplest AI that plays by the rules.
- [ ] Clock or target score, and an end-of-match screen.

Done when a short match plays from start to result and every point was awarded by the rules, not by
a bug.

### v1

- [ ] The ruleset as its own module (a referee): fouls, out of bounds, serve rotation, offside, or a
      written list of what you simplified and why.
- [ ] Team AI with roles and formation anchors keyed to where the ball is, so players spread out
      instead of chasing it.
- [ ] Player switching and pass targeting with a visible indicator.
- [ ] Aim, power and timing feedback the player can read before and after the action.
- [ ] Difficulty that changes AI decisions and timing windows, not the physics.
- [ ] Teams and players as data, with invented names (see pitfalls).
- [ ] Modes: exhibition, tournament or league table, and a practice mode.
- [ ] Local multiplayer; online 1v1 if the sport allows it.
- [ ] A camera that frames the play, and goal or point replays.

### Polish

- [ ] Crowd and commentary that react to events (near miss, comeback, record).
- [ ] Tutorial that teaches the rules during play, not on a wall of text.
- [ ] Season or career progression and statistics.
- [ ] Touch controls, if you target phones.
- [ ] Accessibility: remapping, adjustable game speed or timing assist.

## 3. Reference projects to study

1. **[Open Golf](https://github.com/mgerdes/Open-Golf)**: `copy`, MIT, C with the sokol libraries.
   The most-starred project in the sports catalog; last pushed 2024-03, so not active.
   - Hand-written ball physics: `src/common/bvh.c` tests the ball against a bounding volume hierarchy
     of course triangles, and `golf_ball_contact` resolves each contact with restitution and friction,
     including water and out-of-bounds surfaces.
   - An in-game editor built with Dear ImGui edits a hole's terrain and plays it immediately; lightmaps
     are baked with Lightmapper and xatlas.
   - Its models include Kenney's Nature Kit, with the CC0 license file kept in `data/models/nature_kit/`.
2. **[Open Kick-Off](https://github.com/ssenegas/kickoff)** (catalog genre: arcade): `copy`, MIT, Java
   with libGDX. A rewrite of the 1990 football game Kick Off 2. `assets/tactics/*.xml` gives each
   shirt number a target position for each ball region, with `tactic-regions.png` as the region map:
   a classic formation system expressed as data. The pitch is a Tiled map.
3. **[Freekick 3](https://github.com/anttisalonen/freekick3)** (catalog genre: simulation):
   `study only`, GPL-3.0, C++. Player AI in `src/match/ai/` is split into states (defend, midfielder,
   offensive, goalkeeper, kick ball) driven by tactic parameters, and the referee is a match entity
   with its own actions (`Referee.cpp`, `RefereeActions.cpp`). Its artwork is CC-BY-SA 3.0.
4. **[Vector Pinball](https://github.com/dozingcat/Vector-Pinball)** (catalog genre: arcade):
   `study only`, GPL-3.0, Java. Pinball built on libGDX's Box2D wrapper, drawn only with lines and
   circles so the work goes into physics; a separate experimental table editor exists.
5. **[NOVA PINBALL](https://github.com/wesleywerner/nova-pinball)**: `study only`, GPL-3.0, Lua on
   LÖVE. One table on top of a separate pinball engine repository (same license) whose README says
   it leans on LÖVE's physics module and ships a table editor.
   - The table layout is a data file (`nova.pinball`), not code.
   - The goal is a chain of missions written out in `missions.md` (spell NOVA, shoot both ramps,
     hit the left targets and then the left ramp, and so on), with the next target hinted on the
     LED display and by flashing table lights.
   - Nudging is allowed until too much of it tilts the table, and a 30-second safe mode returns a
     drained ball: small rules that make a physics toy feel like a game.
   - Its README says the project now lives on Codeberg; the GitHub copy is no longer maintained.
6. **[OpenWebSoccer-Sim](https://github.com/ihofmann/open-websoccer)** (catalog genre: strategy):
   `library use`, LGPL-3.0, PHP. An online football manager (tactics, transfers, training, youth
   academy, stadium) whose matches are simulated automatically in real time with a live ticker.
   Run or extend it as its own component; do not copy its code into yours.
7. **[EliFUT](https://github.com/EliFUT/android)** (catalog genre: simulation): `copy`, Apache-2.0,
   Java and Kotlin for Android; last pushed 2020-10. A football manager whose matches are drawn, not
   played: `match/MatchResultGenerator.kt` sets home-win and draw odds from the two squads' rating
   difference, samples the total goals from a distribution and splits them between the clubs, and
   `LeagueRoundExecutor.java` applies a round's results to the table. The random generator is
   passed in, which is what lets `MatchResultGeneratorTest.java` pin results. Its player data is
   another matter (see section 6).

## 4. Reusable permissive code

**Ball and table physics.**
- Open Golf's `src/common/bvh.c` (`copy`, MIT): a compact ball-versus-mesh contact routine for golf,
  pool, bowling or any ball rolling on authored terrain.
- 2D: [Box2D](https://github.com/erincatto/box2d), [Chipmunk Physics](https://github.com/slembcke/Chipmunk2D)
  and [Matter.js](https://github.com/liabru/matter-js), all `copy`, MIT: pinball, air hockey,
  table and top-down sports.
- 3D, not in the catalog (licenses read from GitHub on 2026-09-23):
  [Jolt Physics](https://github.com/jrouwe/JoltPhysics) (MIT) and
  [Rapier](https://github.com/dimforge/rapier) (Apache-2.0; its `typescript` directory holds the
  browser bindings, and the old rapier.js repository is archived).
- Ball flight is usually simpler to own than to configure: gravity, drag and, for spin, a lift
  term, integrated on the fixed step, fit in a few dozen lines and keep replays exact.

**Rules, tactics and AI.**
- Keep the rules (a referee module), the match flow (a state machine) and the physics apart, so
  each can be tested alone.
- Open Kick-Off's tactic XML format (`copy`, MIT): one target position per player per ball region.
  Reuse the format and author your own positions for your own formations.
- EliFUT's `MatchResultGenerator.kt` (`copy`, Apache-2.0): a rating-weighted result generator with
  an injected random source, for the simulated matches of a management game.

**Netcode.** [netplayjs](https://github.com/rameshvarun/netplayjs) (`copy`, ISC) for browser 1v1
with rollback or lockstep; [netfox](https://github.com/foxssake/netfox) (not in the catalog; MIT on
GitHub) for Godot client-server with prediction. Or design turn-based, which sidesteps real-time
netcode entirely.

**Tools.** [Dear ImGui](https://github.com/ocornut/imgui) (`copy`, MIT), as Open Golf uses it, for
in-game course and tuning editors.

## 5. Engine options (engine-neutral)

| engine | catalog class, license | fits when | tradeoff |
|---|---|---|---|
| [Godot 4](https://github.com/godotengine/godot) | `copy`, MIT | 2D or 3D with an editor, desktop and mobile export | built-in physics is general-purpose; ball flight with spin is still yours to write |
| [Phaser](https://github.com/phaserjs/phaser) | `copy`, MIT | 2D browser sports; its README lists built-in Arcade and Matter.js physics | 2D only |
| [Three.js](https://github.com/mrdoob/three.js) | `copy`, MIT | 3D browser sports | renderer only: physics, audio and UI are separate choices |
| [LibGDX](https://github.com/libgdx/libgdx) | `copy`, Apache-2.0 | Java on desktop and Android; Open Kick-Off and Vector Pinball use it, with its Box2D wrapper | a framework, not an editor-driven engine |
| [raylib](https://github.com/raysan5/raylib) | `copy`, Zlib | C, small and self-contained, like Open Golf's sokol setup ([sokol](https://github.com/floooh/sokol) is zlib, not in the catalog) | you write the editor yourself, as Open Golf did |

NOVA PINBALL runs on [LÖVE](https://github.com/love2d/love) (`check first`: GitHub could not read its
license; its source list says Zlib), a small Lua framework with Box2D physics built in.

## 6. Assets

- [Kenney](https://kenney.nl/assets): CC0, including the [Sports Pack](https://kenney.nl/assets/sports-pack)
  and [Minigolf Kit](https://kenney.nl/assets/minigolf-kit); Open Golf ships Kenney's Nature Kit.
- [Poly Haven](https://polyhaven.com/license) and [ambientCG](https://ambientcg.com/license): CC0
  grass, court and wood textures. [Quaternius](https://quaternius.com/): CC0 models.
- [Freesound](https://freesound.org/): crowd, whistle and ball sounds, licensed per sound; some are
  CC-BY-NC (non-commercial). [OpenGameArt](https://opengameart.org/): licensed per asset.
- Or synthesize simple sounds (bounce, kick, whistle) in code, which leaves no audio license to
  track.

**A code license says nothing about the art, or the names.**
- Freekick 3's code is GPL-3.0 and its artwork CC-BY-SA 3.0 (this chassis treats both as
  `study only`). NOVA PINBALL's README credits its music and fonts to other authors, one font under
  CC BY-SA; the game's GPL does not cover them.
- **Decompiled or disassembled commercial games are `check first`.** Their legal status is unclear,
  and they are never a source to copy, whatever license the reconstruction claims.
  [SpaceCadetPinball](https://github.com/k4zmu2a/SpaceCadetPinball) (catalog genre: arcade,
  `check first`), a decompilation of the Windows pinball game, shows it: GitHub reports MIT, and it
  still needs the original game's resources, which it does not include.
- Real leagues, clubs, players, kits, logos and stadiums are licensed separately from any code.
  [EliFUT](https://github.com/EliFUT/android) (catalog genre: simulation, `copy`, Apache-2.0)
  describes itself as based on FIFA 15 Ultimate Team data, and Freekick 3 points to tools that fetch
  real team data from Wikipedia. Ship invented teams and names.

Record every asset and data source in `THIRD_PARTY.md` ([template](../templates/THIRD_PARTY.md)).

## 7. Building it with AI tools

Follow the stage table in [../ai/README.md](../ai/README.md): Claude plans and reviews, Codex takes
one scoped task at a time, Grok reviews blind. Sports games live or die on rules, so the rules come
first.

**Rules spec (Claude).**

```text
Read ../opensource/playbooks/sports.md. For an arcade <sport> game, write docs/rules.md:
every rule of the real sport we keep, every rule we simplify or drop (and why), how each is
detected in code (which event, which threshold), and what the player sees when it fires.
List edge cases: ball on the line, simultaneous touches, fouls during a set piece, time
expiring mid-play. Mark every assumption (assumed).
```

**Slice (Codex, one task each).** Ball physics; the referee module; one athlete's main action. Each
task ends with scripted cases taken from `docs/rules.md`:

```text
Implement the referee per docs/rules.md as a pure function of match state and events.
Add playtest/scripts/ for each edge case listed there, e.g. ball-on-line.txt: place the ball
with its center over the goal line but not fully across; assert no goal. Run all scripts
and show one PASS or FAIL line per case.
```

**Team AI (Codex, then you watch it).** Formation anchors by ball region first, then roles; judge
it by watching a full AI-versus-AI match at double speed, not from logs.

**Review (Grok, blind).** Give it `docs/rules.md` and the referee code, and ask which written rule
the code gets wrong and which situation the rules do not cover. Do not tell it where you think the
bug is. Never paste `study only` code (Freekick 3, Vector Pinball, NOVA PINBALL) into a prompt;
describe the behavior yourself, as `ai/README.md` explains.

### Playtest checklist for this genre

- [ ] Someone who plays the real sport watches a match and names every rule that looked wrong.
- [ ] Every edge case in `docs/rules.md` has a script, and each script fails when its rule is
      removed.
- [ ] The same shot input gives the same result at 30, 60 and 144 FPS.
- [ ] A fast ball never passes through posts, nets or walls.
- [ ] In an AI-versus-AI match, players hold positions instead of swarming the ball.
- [ ] Player switching picks the player the tester expected.
- [ ] Each difficulty level is beatable and none needs physics cheats.
- [ ] A new player scores (or wins a point) in their first match without reading instructions.

## 8. Genre-specific pitfalls

- **Half-implemented real rules.** Fans read a missing rule as a bug. Simplify on purpose and say
  so in the game.
- **Swarming AI.** Without formation anchors every AI player chases the ball; start from positions
  keyed to ball location, as Open Kick-Off's tactic files do.
- **Ball tunneling.** Shots are the fastest objects in the game; use continuous collision or
  sub-steps for the ball.
- **Frame-rate dependent power or spin.** Charge meters and ball flight must run on the fixed step.
- **Difficulty by cheating.** Buffing AI physics feels unfair; change decisions and timing windows.
- **Real-time netcode for physics-heavy play.** It is hard; a relay server that forwards inputs, or
  a turn-based design, is a simpler first step.
- **Real names and likenesses.** See section 6: use invented teams, players and kits.
- **Download lures.** Never download a release, zip or installer from a catalog repository; build
  from source, as the [catalog's safety note](../catalog/README.md) explains.
