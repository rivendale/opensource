# Adventure playbook

Story-led games of exploration and puzzles: point-and-click graphic adventures, parser text
adventures, choice-based interactive fiction and visual novels. Zelda-style action adventures sit
in the [RPG playbook](rpg.md) (see TetraForce there). The catalog lists 76 adventure projects, 18
of them `copy` class; the full table is in [../catalog/adventure.md](../catalog/adventure.md). Some
rows are neighbors (engine ports, board games). Every project named below was checked against its
repository on 2026-09-23.

## 1. What defines the genre

**Core loop:** enter a scene, look around, pick things up, talk to people, then combine what you
carry and what you learned to get past an obstacle, which opens the next scene or story beat. The
player's progress is **knowledge and inventory, not reflexes or stats**: an adventure is a story
told through puzzles the player solves by thinking.

**Player verbs:** walk to, look at, pick up, use (an item on a thing, or two items together),
talk to (a dialogue tree), give, open. Parser games type these as commands (`take lamp`,
`go north`); choice games reduce them to picking a link; visual novels to picking a reply.

**Win:** reach an ending; many games have several. **Lose:** older designs killed the player or
left them stuck with no way forward; modern designs avoid both, so "losing" is being stuck on a
puzzle. Visual novels lose by reaching a bad ending, as in Ren'Py's own example game, whose test
file plays to a `good_end` and a `bad_end`.

| form | input | study in the catalog |
|---|---|---|
| point-and-click | mouse or touch on hotspots, inventory bar | Bladecoder Adventure Engine, ScummVM, JSGAM |
| parser text adventure | typed commands | Colossal Cave Adventure |
| choice-based fiction | clicked links | Twine, Squiffy |
| visual novel | text advance and menu choices | Ren'Py |

## 2. The systems to build, in build order

### First playable vertical slice: two rooms, one puzzle, one conversation

- [ ] A scene: background, a walkable area, a character who walks there by pathfinding
- [ ] Hotspots that show a name on hover, with look, use and talk responses
- [ ] Inventory: pick up, show, use an item on a hotspot, combine two items
- [ ] One dialogue tree whose choices set a flag
- [ ] One puzzle that needs the item and the flag; solving it opens the door to the second room
- [ ] A default response for every verb on every hotspot ("That doesn't work")
- [ ] All text read by string id from a data file
- [ ] Save and load: scene, positions, inventory, flags

**Done when** a stranger solves the puzzle without a hint, and reloading a save mid-puzzle keeps
their progress.

### v1

- [ ] A scene graph with transitions and entry points
- [ ] Scripts or action lists per verb per object, in data the writer edits, not engine code
- [ ] Dialogue in a narrative language (ink or Yarn Spinner) instead of hand-built trees
- [ ] Cutscenes as sequenced actions that can be skipped without losing their state changes
- [ ] A puzzle dependency chart kept beside the game and checked against it
- [ ] A hint system for players who are stuck
- [ ] Multiple save slots with thumbnails; autosave at scene changes
- [ ] Automated playthroughs, one per ending, run on every build
- [ ] Localization of all text; subtitles for any voice

### Polish

- [ ] A key that highlights every hotspot; no pixel hunting
- [ ] Character scaling with depth, walk-behind layers, parallax
- [ ] Ambient animation and music that changes with the scene
- [ ] Skip a dialogue line, text speed, font size
- [ ] Touch controls: tap to walk, long press to look
- [ ] Rewind to the previous choice (visual novels)
- [ ] A credits screen generated from `THIRD_PARTY.md`

**Parser variant:** replace hotspots with a room graph, an object model and a parser (verb,
object, preposition, object) with synonyms and a helpful "I don't understand" for everything else.

## 3. Reference projects to study

**Bladecoder Adventure Engine** ([repo](https://github.com/bladecoder/bladecoder-adventure-engine)):
`copy` (Apache-2.0), Java on libGDX. A point-and-click engine with a graphical editor
(`adventure-editor`) and a runtime (`blade-engine`) for Android, iOS and desktop. Its model classes
map straight onto the genre: `Scene`, `InteractiveActor`, `CharacterActor`, `Inventory`, `Verb`,
`VerbManager`, `VerbRunner`, `WalkZoneActor`, `ObstacleActor`, `Dialog`. Verb responses are chains
of small action classes in `engine/actions/`, and dialogue can run in ink (`InkRunAction`,
`IfInkVariableAction`). Its README admits the documentation is thin and points to its test game
project instead. Learn the verb and action model; the code may be reused with its notice.

**Ren'Py** ([repo](https://github.com/renpy/renpy)): `library use` (the catalog records
"LGPL-2.1 (most code under MIT)"; the full terms are on Ren'Py's license page), Python. The
standard visual novel engine. The repository carries two example games (`tutorial/`,
`the_question/`); `renpy/rollback.py` gives players rewind, `renpy/loadsave.py` handles saves,
`renpy/lint.py` checks a script for errors, and `the_question/game/testcases.rpy` scripts
playthroughs (click "start", advance until the choice screen, pick an answer, advance until the
main menu). Learn rollback and scripted playthroughs.

**Twine** ([repo](https://github.com/klembot/twinejs)): `study only` (GPL-3.0), TypeScript. The
editor for choice-based stories, drawn as a map of linked passages. Its README notes the story
formats it bundles live in separate repositories; published stories embed one of them, and they
carry their own licenses (SugarCube is BSD-2-Clause and Snowman is MIT, both read from GitHub).
Learn the passage map as an authoring view: the writer sees every branch at once.

**Squiffy** ([repo](https://github.com/textadventures/squiffy)): `copy` (MIT), TypeScript. Writes
stories in a plain text format and compiles them to HTML with a CLI
(`npx @textadventures/squiffy-cli story.squiffy`). It separates *sections* (moving to one disables
every earlier link) from *passages* (links stay live), which is a clean answer to "can the player
go back?". Version 6 is a beta rewrite, per its README.

**ScummVM** ([repo](https://github.com/scummvm/scummvm)): `study only` (GPL-3.0), C++. Runs
classic adventure games through a large set of engine reimplementations under `engines/`. In the
SCUMM engine, `boxes.cpp` defines walk boxes with flags, a scale per box (characters shrink as
they walk away) and a box matrix for pathfinding; `verbs.cpp` drives the verb interface; one
`script_v*.cpp` file per script version shows how the bytecode changed from game to game. Learn
walk boxes and per-box scaling; they solve 2D adventure movement cheaply.

**JavaScript Graphic Adventure Maker (JSGAM)** ([repo](https://github.com/kreezii/jsgam)):
`copy` (MIT), JavaScript. A browser point-and-click engine built on PixiJS, Howler, DragonBones,
LocalForage, PolyK and Walkable, with a template project and a tutorial. Before shipping, check
its dependencies: its `package.json` requires `gsap`, which is published under GSAP's own
"Standard 'no charge' license", not an open source license.

**Colossal Cave Adventure** ([repo](https://github.com/troglobit/adventure)): `copy` (Unlicense),
C. The original parser adventure. Long and short room descriptions, object text and messages are
numbered entries in `src/advent1.txt` through `advent4.txt`; the vocabulary is a word table in
`advword.h`; `english.c` reads and analyzes the player's words; verbs such as take, drop and open
are functions in `verb.c` and `itverb.c`; each turn runs through `turn()` in `turn.c`. Learn how
little code a parser game needs, and how much of it is data. Last push 2024-02-09.

## 4. Reusable permissive code

Catalog projects keep the catalog's class. Libraries marked "not in the catalog" had their license
read from GitHub on 2026-09-23; re-read the LICENSE file before you copy anything.

| need | project | class | license |
|---|---|---|---|
| point-and-click engine and editor (Java) | [Bladecoder Adventure Engine](https://github.com/bladecoder/bladecoder-adventure-engine) | `copy` | Apache-2.0 |
| point-and-click framework for Godot | [Escoria core](https://github.com/godot-escoria/escoria-core) and its [demo game](https://github.com/godot-escoria/escoria-demo-game) | not in the catalog | MIT |
| branching dialogue | [ink](https://github.com/inkle/ink) (C#) and [inkjs](https://github.com/y-lohse/inkjs) (JavaScript) | not in the catalog | MIT |
| dialogue with Unity and Godot integrations | [Yarn Spinner](https://github.com/YarnSpinnerTool/YarnSpinner) | not in the catalog | MIT |
| dialogue and visual novel scenes in Godot | [Dialogic](https://github.com/dialogic-godot/dialogic), [Godot Dialogue Manager](https://github.com/nathanhoad/godot_dialogue_manager) | not in the catalog | MIT |
| choice-based stories compiled to HTML | [Squiffy](https://github.com/textadventures/squiffy) | `copy` | MIT |
| hypertext fiction in the browser (last push 2018) | [Undum](https://github.com/idmillington/undum) | `copy` | MIT |
| browser point-and-click engine | [JSGAM](https://github.com/kreezii/jsgam) (check its `gsap` dependency) | `copy` | MIT |
| a parser game to read end to end | [Colossal Cave Adventure](https://github.com/troglobit/adventure) | `copy` | Unlicense |
| 2D rendering for a custom web engine | [pixi.js](https://github.com/pixijs/pixijs) | `copy` | MIT |

Ren'Py is `library use` in the catalog: build on it as an engine and keep its notices; do not lift
its files into another codebase.

## 5. Engine options (engine-neutral)

- **[Godot](https://github.com/godotengine/godot)** (`copy`, MIT) with Escoria or Dialogic (MIT).
  A full 2D editor for scenes, walkable areas and animation. Tradeoff: frameworks track Godot's
  minor versions; the Escoria demo game's README describes a script tweak needed between Godot
  4.6 and 4.7.
- **[Ren'Py](https://github.com/renpy/renpy)** (`library use`). Visual novels and choice-heavy
  games in a Python-based script, with rollback, saves and testcases built in. Tradeoff:
  point-and-click is possible but not what it is built around.
- **[Bladecoder Adventure Engine](https://github.com/bladecoder/bladecoder-adventure-engine)**
  (`copy`, Apache-2.0) on [LibGDX](https://github.com/libgdx/libgdx) (`copy`, Apache-2.0).
  Purpose-built for point-and-click, with an editor and mobile targets. Tradeoff: thin
  documentation, and a smaller community than a general engine.
- **[Phaser](https://github.com/phaserjs/phaser)** or **[pixi.js](https://github.com/pixijs/pixijs)**
  (both `copy`, MIT), optionally with JSGAM. Plays in any browser with no install. Tradeoff: you
  build the verb system, save system and tools yourself.
- **Text only:** ink with inkjs, or Squiffy (all MIT). Tradeoff: no graphics system; the fastest
  way to test whether the story and puzzles work before any art exists.

## 6. Assets

Adventures spend most of their budget on backgrounds, character animation and writing. Art style
must stay consistent from scene to scene, which makes mixing packs harder than in other genres.

- **[Kenney](https://kenney.nl/support):** "all game assets on the asset pages are public domain
  licensed (CC0)", including for commercial use; useful for items and UI.
- **[OpenGameArt](https://opengameart.org/content/faq):** per-asset licenses: CC0, CC-BY 3.0 or 4.0,
  CC-BY-SA 3.0 or 4.0, OGA-BY 3.0 or 4.0, GPL 2.0 or 3.0. Escoria's demo game credits a CC0
  adventure character sprite sheet from OpenGameArt and CC0 item packs from Kenney.
- **[game-icons.net](https://game-icons.net/about.html):** inventory icons under CC BY 3.0; credit
  the author.
- **[Freesound](https://freesound.org/help/faq/):** CC0, CC BY or CC BY-NC per sound; NC forbids
  commercial use.

**A code license says nothing about the art, the writing or the voices.** Reimplementations are
the sharpest case: engge (`copy`, MIT, archived) says in its README that you must buy Thimbleweed
Park and copy its data files to play, and ScummVM runs each game from that game's own data files,
which its code license does not cover. The catalog lists the visual novel Digital: A Love Story as
`check first`, with a CC-BY-NC-SA-3.0 note from its source list: non-commercial terms. Record every
image, sound, font and voice line in `THIRD_PARTY.md` (see
[../templates/THIRD_PARTY.md](../templates/THIRD_PARTY.md)), with the voice actor's contract terms.

## 7. Building it with AI tools

Follow the stage table in [../ai/README.md](../ai/README.md). For an adventure the work splits
like this:

- **Claude** plans and reviews: the design page, the puzzle dependency chart, the failure list
  (dead ends, missing responses), and reviews of the whole script for unreachable content.
- **Codex** takes one scoped task at a time: walkable areas and pathfinding, the verb and action
  runner, inventory, save and load, the playthrough runner, each with a playtest step.
- **Grok** is the blind second opinion: hand it the dependency chart alone and ask where a player
  gets stuck; hand it a bug as a symptom plus the files, never your theory.

Describe a `study only` mechanic in your own words; never paste GPL code into a prompt.

**Prompts by stage:**

1. *Puzzles (Claude):* "Write a puzzle dependency chart for this story: every puzzle, the items
   and facts it needs, what it unlocks. Then list every state where the player can no longer
   finish the game, and every puzzle whose solution a player could not infer from in-game clues."
2. *Scene data (Claude, then Codex):* "Define a data format for scenes, hotspots, items and
   verb responses, all by string id. Write a validator that reports every hotspot and verb pair
   with no response and every item that is never obtainable."
3. *Movement (Codex):* "Implement a walkable area as polygons with holes and find a path inside it.
   Add a playtest step that clicks outside the area and expects the character to stop at the edge."
4. *Playthroughs (Codex):* "Write a runner that plays a script of verb commands against the game
   headless and asserts the scene and flags at each step. Add one script per ending."
5. *Writing (Claude):* "Write look-at text for these hotspots in this voice guide, one to two
   sentences each, each hinting at its use without naming the solution."

**Playtest checklist**, on top of the general one in the AI guide:

- [ ] In every scene, a new player can say what they are trying to do next
- [ ] Every ending is reached by an automated playthrough on the current build
- [ ] No dead end: no item can be lost, no door closes behind a missing item
- [ ] Every verb on every hotspot answers with something, even a default line
- [ ] Saving during a cutscene or dialogue and reloading keeps the story consistent
- [ ] Hotspot highlighting shows every interactive thing; nothing requires pixel hunting
- [ ] Text fits its boxes in every language, and no text is baked into images

## 8. Genre-specific pitfalls

- **Moon logic.** A solution the designer finds obvious and nobody else can guess. Every puzzle
  needs a clue the player can find in the game; watch testers, do not ask them.
- **Dead ends.** The player drops, uses up or misses an item and can no longer finish, often
  without knowing it. The dependency chart and an automated check catch these; memory does not.
- **One bottleneck.** When a single puzzle blocks all progress, one stuck player is a quit.
  Keep two or three puzzle threads open at a time.
- **Pixel hunting.** Hotspots the size of a few pixels test eyesight, not thinking.
- **"Use everything on everything."** When players cannot reason, they brute force. Specific wrong
  responses that hint are cheaper than a hint system, and more fun.
- **Parser frustration.** Missing synonyms make the right idea fail. Log every command players type
  and add the words they used.
- **Writing volume.** Every hotspot, verb and branch is text to write, translate and maybe voice.
  Count lines in the vertical slice and multiply before you plan the rest.
- **Save state in the middle of a script.** Saves taken during cutscenes or dialogue must restore
  to a consistent point; test it on purpose.
- **Borrowed data.** Engine reimplementations with `copy` code still run on data you do not own;
  never ship another game's art, music or text.
