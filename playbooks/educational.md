# Educational playbook

Games whose purpose is that the player learns something: early-learning suites for children, math
and reading drills, programming games, memory and focus trainers, games that teach a subject such as
physics. The catalog's own list, [../catalog/educational.md](../catalog/educational.md), is thin: 9
projects, none with a permissive code license, two active. The strongest references were placed in
neighboring genres (puzzle, simulation, other), so this playbook draws on those. Every project named
here was checked against its repository on 2026-09-23; reuse classes are quoted as the catalog
states them (`copy`, `library use`, `study only`, `check first`).

## 1. What defines the genre

**Core loop:** meet a challenge tied to one learning goal, attempt it, get immediate feedback that
explains, practice until it is mastered, unlock the next step. The genre works when the fun action
and the thing being learned are the same action: in WarriorJS the code you write is the strategy; in
Tux of Math Command solving the equation is what destroys the comet.

**Player verbs:** answer, type, write code, drag and match, sort, build, experiment, predict.

**Win and lose:** win by mastering a level, lesson or skill. Failure should be cheap and informative:
retry at once, with the mistake explained. There are usually two users: the learner, and a teacher
or parent who chooses content and reads progress (GCompris ships a separate teachers app; Tux of
Math Command lessons can save a summary).

Know the audience before anything else. A pre-reader (GCompris covers ages 2 to 10) needs spoken
instructions and big touch targets; a programmer learning a language needs an editor and a fast run
loop; an adult trainer needs short sessions and visible progress.

## 2. The systems to build, in build order

### First playable vertical slice

- [ ] One learning goal and its prerequisite, written down. GCompris activities declare `goal` and
      `prerequisite` in their `ActivityInfo.qml`.
- [ ] Content as data: an item generator driven by parameters (Tux of Math Command lesson files set
      the allowed operations and operand ranges).
- [ ] Challenge, attempt, immediate feedback that says why an answer is wrong, not only that it is.
- [ ] Levels as separate data sets (GCompris: `resource/<level>/Data.qml` per activity).
- [ ] Missed items come back (Tux lesson settings `repeat_wrongs` and `copies_repeated_wrongs`).
- [ ] Progress saved on the device, with no account required.
- [ ] Input suited to the audience: touch for young children, keyboard for typing and code.

### v1

- [ ] Difficulty that adapts to recent accuracy, bounded so a learner is never stuck on a wall.
- [ ] Hints in steps: a tip first, a more direct clue on request (WarriorJS levels carry both).
- [ ] For programming games, player code runs in a sandbox with a time limit (Elevator Saga's
      fitness suite evaluates submitted code inside a web worker).
- [ ] An educator view: choose lessons, see sessions, errors and time on task (Tux's `save_summary`,
      GCompris's teachers app).
- [ ] Localization of text and of spoken instructions (GCompris asks contributors to record voices
      per language).
- [ ] Accessibility: readable fonts, keyboard or switch access, captions, time pressure optional.
- [ ] Classroom use: works offline; optional local multiplayer (Tux of Math Command has a LAN mode).

### Polish

- [ ] Rewards that carry the subject: each Particle Clicker research item links to a page about a
      real discovery (`"info": "html/CPV.html"` in `json/research.json`).
- [ ] A character and celebrations that younger learners respond to.
- [ ] Content packs teachers or the community can add (WarriorJS towers are installable packages).
- [ ] Onboarding that needs no reading for pre-readers: demonstration, then audio.
- [ ] A short check before and after a lesson, so you can see whether anyone learned anything.

## 3. Reference projects to study

`study only` projects are read for design; copy nothing from them
([../ai/README.md](../ai/README.md), "License hygiene").

**[GCompris](https://invent.kde.org/education/gcompris)**: `study only`, GPL-3.0 (per list), C++ and
QML on Qt Quick. A KDE suite of more than 100 activities for children aged 2 to 10 (its README), read
through its [GitHub mirror](https://github.com/KDE/gcompris). Learn from:
- Activity metadata: `src/activities/algebra_plus/ActivityInfo.qml` declares title, goal,
  prerequisite, manual, difficulty, section tags and levels; each level's data lives in
  `resource/<n>/Data.qml`.
- A separate teachers application, per-file license metadata (`REUSE.toml`), voice recordings per
  language.
- Its README says the whole suite is now AGPL-3.0 because of one AGPL library, and that it does not
  accept AI-generated code.

**[Tux of Math Command](https://github.com/tux4kids/tuxmath)**: `study only`, GPL-3.0 (per list;
GitHub could not read it), C. Arcade math drill: comets carry equations, solving one destroys it.
Learn from:
- Lessons as plain text in `data/missions/lessons/`: `addition_allowed`, `max_minuend`,
  `repeat_wrongs = 1`, `copies_repeated_wrongs = 2`, `save_summary = 1`.
- LAN play for classrooms (`src/server.c`, `src/menu_lan.c`) and a second mode, Factoroids,
  described in `doc/README`.

**[WarriorJS](https://github.com/olistic/warriorjs)**: `copy`, MIT, TypeScript (cataloged under
puzzle). "Learn JavaScript and TypeScript by writing code that fights." Learn from:
- Level definitions (`towers/the-narrow-path/src/index.ts`) that carry a description, a `tip`, an
  optional `clue`, a time bonus, an ace score, and the abilities the warrior gains at that level.
- The engine split into packages (`libs/core`, `libs/abilities`, `libs/units`, `libs/scoring`) and
  towers other people can publish, with a maker guide in `docs/maker/`.

**[Elevator Saga](https://github.com/magwo/elevatorsaga)**: `copy`, MIT, JavaScript (cataloged under
simulation). A programming game: write the elevator controller. Its README says it is not actively
maintained. Learn from:
- Challenges as small objects with a description and an `evaluate(world)` that returns true, false,
  or null while undecided (`challenges.js`).
- Player code run through a fitness suite in a web worker (`fitnessworker.js`), an API reference
  page (`documentation.html`) and unit tests in `test/`.

**[Particle Clicker](https://github.com/particle-clicker/particle-clicker)**: `copy`, MIT,
JavaScript (cataloged under simulation). An incremental game "that teaches players the history of
high energy particle physics", made in a weekend at the 2014 CERN Webfest. Learn from:
- Progression as data (`json/research.json`, `upgrades.json`, `workers.json`, `achievements.json`)
  and one explanatory page per discovery in `html/`: the reward and the lesson are one object.

**[Braincup](https://github.com/SimonSchubert/Braincup)**: `copy`, Apache-2.0, Kotlin (cataloged under
other). A math, memory and focus trainer, pushed in September 2026. Learn from:
- 45 activities (40 scored mini-games and 5 extras, per its README) in one Kotlin Multiplatform
  codebase with Compose Multiplatform, built for Android, iOS, desktop and web, with screenshot tests
  in `screenshotTests/`.

**[Untrusted](https://github.com/AlexNisnevich/untrusted)**: `check first` (no license GitHub could
read), JavaScript (cataloged under puzzle). A game played by editing the JavaScript that generates
each level. Learn from:
- Level files where `#BEGIN_EDITABLE#` and `#END_EDITABLE#` mark the lines the player may change
  (`#{#` and `#}#` mark parts of lines), and a `commandsIntroduced` list per level that introduces
  the API a few commands at a time.
- Caution: its README puts the game and soundtrack under CC BY-NC-SA 3.0, non-commercial. Study the
  design; copy nothing.

**[Brain Workshop](https://github.com/brain-workshop/brainworkshop)**: `study only`, GPL-2.0, Python
with pyglet (cataloged under puzzle). A dual n-back trainer. Learn from:
- Trial-by-trial session data recorded to disk, and scores that weigh the percentage correct as well
  as the n-back level.
- Its README says all music and some media were removed for copyright reasons and replaced.

## 4. Reusable permissive code

| catalog project | reuse class, license | language | use it for |
|---|---|---|---|
| [WarriorJS](https://github.com/olistic/warriorjs) | `copy`, MIT | TypeScript | a code-writing game engine: abilities, units, scoring, level packs |
| [Elevator Saga](https://github.com/magwo/elevatorsaga) | `copy`, MIT | JavaScript | challenge objects with `evaluate`, running player code in a worker |
| [Particle Clicker](https://github.com/particle-clicker/particle-clicker) | `copy`, MIT | JavaScript | a data-driven incremental game that pairs each unlock with content |
| [Braincup](https://github.com/SimonSchubert/Braincup) | `copy`, Apache-2.0 | Kotlin | cross-platform mini-game structure; keep its Apache-2.0 license text and notices |
| [Ruby Warrior](https://github.com/ryanb/ruby-warrior) | `copy`, MIT | Ruby | "Game written in Ruby for learning Ruby" (cataloged under roguelike) |
| [Minecraft](https://github.com/fogleman/Minecraft) | `copy`, MIT | Python | a 902-line voxel demo whose README wants it to become an educational tool (cataloged under sandbox) |

Not in the catalog; license read from each repository on 2026-09-23 (all would class as `copy`):

| library | license | use it for |
|---|---|---|
| [Blockly](https://github.com/RaspberryPiFoundation/blockly) | Apache-2.0 | a visual block-code editor for web apps, for learners not ready to type code |
| [JS-Interpreter](https://github.com/NeilFraser/JS-Interpreter) | Apache-2.0 | "a sandboxed JavaScript interpreter in JavaScript": step through player code safely |
| [i18next](https://github.com/i18next/i18next) | MIT | translation of UI text, with plurals and interpolation |
| [Fluent](https://github.com/projectfluent/fluent.js) | Apache-2.0 | localization where grammar varies by language |

## 5. Engine options (engine-neutral)

| engine | license (catalog class) | fits | trade-off |
|---|---|---|---|
| [Godot](https://github.com/godotengine/godot) | MIT (`copy`) | desktop, mobile and web activities with rich UI | measure web export size and load time on the school devices you target |
| [Phaser](https://github.com/phaserjs/phaser) | MIT (`copy`) | browser activities that open from a link on school machines | you build progress, reporting and editors yourself |
| [ct.js](https://github.com/ct-js/ct-js) | MIT (`copy`) | a 2D engine and editor that "aims to be powerful and flexible while still being easy to use and learn", built on pixi.js, with a visual scripting language (cataloged under engines) | smaller community than Godot or Phaser |
| [Ren'Py](https://github.com/renpy/renpy) | LGPL-2.1, most code MIT (`library use`, per list) | story- and dialogue-driven learning (cataloged under adventure) | built for visual novels; other game types fight the engine |

## 6. Assets

Code licenses say nothing about art, audio, voices or the subject content itself. Check every asset
separately and give it a row in `THIRD_PARTY.md` ([template](../templates/THIRD_PARTY.md)).

- **[Kenney](https://kenney.nl/assets)**: CC0, no attribution required. Packs that fit: Animal Pack,
  Shape Characters, UI Pack, Input Prompts, Interface Sounds, Music Jingles.
- **Fonts**: [Atkinson Hyperlegible](https://fonts.google.com/specimen/Atkinson+Hyperlegible) is under
  the SIL Open Font License 1.1, as are most Google Fonts. Check each font's license file.
- **Emoji and symbols** (not in the catalog; licenses read from each repository on 2026-09-23):
  [Twemoji](https://github.com/jdecked/twemoji) graphics are CC BY 4.0 per its `LICENSE-GRAPHICS`
  (attribution), while its code is MIT; [OpenMoji](https://github.com/hfg-gmuend/openmoji) is
  CC BY-SA 4.0 (attribution and ShareAlike).
- **Voices**: record your own, with written permission from every speaker, and a parent's for a
  child's voice.
- **[OpenGameArt.org](https://opengameart.org)** and **[Freesound](https://freesound.org)**: licenses
  vary per item (CC0 through CC BY-NC). Non-commercial items cannot go in a paid product, and many
  schools buy software.

Cautions from the reference projects:
- Untrusted's game and soundtrack are non-commercial. Brain Workshop removed its music for
  copyright reasons. GCompris tracks licenses per file with `REUSE.toml`: copy that practice.
- Subject content (questions, explanations, facts) is an asset too. Record its source, and have
  someone who knows the subject review it.

## 7. Building it with AI tools

Follow the stage table in [../ai/README.md](../ai/README.md): Claude plans and reviews, Codex
implements one scoped task at a time, Grok reviews blind, a person playtests. What changes for
educational games:

| stage | lead | educational artifact |
|---|---|---|
| design | Claude (plan mode) | `docs/learning-goals.md`: audience, goals, prerequisites, how mastery is measured |
| failure list | Claude, attacked by Codex | wrong answers accepted, content errors, frustration loops, unsafe player code, data collection |
| content | Codex generates, an independent checker verifies, a subject expert reviews | item bank with answers, sources and a review mark per item |
| slice | Codex | one activity end to end, with feedback and saved progress |
| "this answer is wrong" reports | Grok and Codex, blind | the item, the generator and the checker code, never your theory |

Prompts, in build order (fill the angle brackets; one task per Codex run):

```text
1. Learning goals (Claude, plan mode): Read ../opensource/playbooks/educational.md and
docs/design.md. Write docs/learning-goals.md: audience and reading level, each goal with
its prerequisite, the item types that practice it, what counts as mastery, and the common
mistakes for each goal with the feedback each mistake should get.

2. Item generator and checker (Codex): Implement src/items/ in <language>: generate(goal,
level, seed) -> item with prompt, answer and distractors. Write a separate check(item)
that computes the answer independently. Generate 10,000 items per goal and level; print
counts, duplicates and any item where check disagrees. Exit non-zero on a disagreement.

3. Activity loop (Codex): One activity from docs/learning-goals.md: show an item, accept
an answer, give the mistake-specific feedback, requeue missed items twice, save progress
locally. Add a playtest script that answers wrong three times, then right, and asserts
the feedback text and the requeue.

4. Code sandbox (Codex, programming games only): Run player code in <worker, interpreter
or process> with a time and memory limit and access only to the game API. Show that an
infinite loop, a network call and access to the page are each stopped with a readable
message.
```

To borrow a design from a `study only` project such as GCompris, write your own notes and give a
fresh session only the notes (the clean-room prompt in ../ai/README.md). GCompris does not accept
AI-generated code, so keep AI-assisted work in your own repository.

### Educational playtest checklist (add to the general one in ../ai/README.md)

- [ ] A learner from the target audience plays unassisted, and you watched without helping.
- [ ] A short check before and after one session shows improvement for most testers.
- [ ] Every generated item passes the independent checker across 10,000 seeds per level.
- [ ] Each common wrong answer gets feedback that names the mistake.
- [ ] Guessing (clicking every option fast) does not advance the learner.
- [ ] No state leaves a learner stuck: a level can always be retried or skipped.
- [ ] Timed modes can be switched off, and the game is playable with keyboard only.
- [ ] The game works offline, and no personal data leaves the device by default.
- [ ] A subject expert signed off the content, and a teacher tried the educator view.

## 8. Genre-specific pitfalls

- **Learning and fun in separate boxes.** A quiz followed by a minigame as a reward teaches players
  to rush the quiz. Make the learned skill the game's main action (WarriorJS, Elevator Saga, Tux of
  Math Command).
- **Wrong content.** A wrong fact in a learning game is worse than a bug, and AI tools produce
  plausible wrong facts and answers. Check every item with independent code or a reviewer.
- **Rewarding guesses.** Multiple choice with no cost to wrong answers teaches clicking. Add a cost,
  a delay, or free-response items.
- **Punishing failure.** Lives and game-over screens drive young or anxious learners away. Make
  failure a quick retry with a better explanation.
- **One difficulty for everyone.** Adapt from recent accuracy and requeue misses, as Tux's lesson
  settings do.
- **Children's data.** Laws such as COPPA in the United States (children under 13) and the child
  consent rules in the GDPR constrain what you may collect. Collect nothing by default, need no
  account, and add no third-party analytics. This is not legal advice.
- **Ignoring the teacher.** If a teacher cannot choose content or see progress in a minute, the game
  will not be used in class.
- **Reading level.** Instructions written for adults lose children. Test with the real audience and
  add audio.
- **Copyleft and non-commercial foundations.** GCompris is AGPL-3.0 per its README; Untrusted is
  non-commercial. Study them; build on `copy` projects.
