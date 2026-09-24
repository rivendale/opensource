# Rhythm playbook

Games where the player acts in time with music: scrolling-note games (keyboard, dance pad, plastic
guitar), circle-clicking games, singing games. The full list of 102 projects, with license and
activity, is in [../catalog/rhythm.md](../catalog/rhythm.md). Every project named here was checked
against its repository on 2026-09-23; reuse classes are quoted as the catalog states them (`copy`,
`library use`, `study only`, `check first`).

## 1. What defines the genre

**Core loop:** see and hear the next notes approach, act on the beat, get a judgment for every note,
keep the combo and the life gauge up, finish the song, read the grade, retry to do better. The skill
is timing measured in milliseconds; the content is charts synchronized to songs.

**Player verbs:** tap, hold, release, slide, strum, hit a drum pad, sing a pitch, aim at a target.

**Win and lose:** clear the song with the gauge above its threshold, then earn a grade (Bemuse awards
an S for a score over 500000). Lose when the gauge or health empties. Many games add a no-fail
option, which turns losing into a lower grade.

Everything rests on one number: the difference between when the player acted and when the note was
due. If the game measures that badly, no amount of polish saves it.

## 2. The systems to build, in build order

### First playable vertical slice

- [ ] Song time read from the audio clock, never summed from frame deltas:
      `song_time = playback_position + time_since_last_mix - output_latency`. Every engine and
      audio library exposes these three numbers under its own names; section 5 shows one engine's.
- [ ] One chart format: song file, offset, BPM, notes as times or beats per lane.
- [ ] Note scroll computed from time: `y = (note_time - song_time) * speed`.
- [ ] Input events with their own timestamps, judged against the nearest unjudged note in the lane.
- [ ] Judgment windows in milliseconds as data, plus score, combo and gauge rules.
- [ ] A results screen and one-key retry.
- [ ] A global offset setting, applied to judgment and drawing.

### v1

- [ ] A chart editor, in game (Quaver has one) or standalone (NoteEditor, UltraStar Play's song
      editor).
- [ ] BPM changes, stops, hold notes, and several difficulties per song.
- [ ] Replays saved as input timestamps plus a chart hash, and a verifier that recomputes the score
      from them (YARG.Core lists replay verification among its jobs).
- [ ] Practice mode: loop a section and slow the song (beatoraja has practice mode and play-speed
      control from 0.25x to 4.0x in autoplay and replay).
- [ ] Scroll speed separate from song speed (Bemuse: lowering speed makes notes denser on screen
      without changing the song).
- [ ] Song select with audio preview and a difficulty number from a calculator (Etterna's
      `src/Etterna/MinaCalc/`, the difficulty code in Quaver.API).
- [ ] A calibration screen: tap along to a click track, measure the average error, store it.

### Polish

- [ ] Hit sounds or full keysounds (Bemuse: "each note has its own sound").
- [ ] Feedback on every hit: judgment text, an early or late indicator, a timing histogram on the
      results screen (beatoraja shows fast and slow, or the error in milliseconds).
- [ ] Skins and note skins as data (Etterna ships `NoteSkins/` and Lua themes).
- [ ] Controllers beyond the keyboard: MIDI, dance pads, plastic instruments (YARG supports
      five-fret guitar, drums and vocals).
- [ ] Leaderboards that accept only replays your verifier reproduces.
- [ ] Accessibility: lane colors that survive color blindness, reduced flashing, no-fail mode.

## 3. Reference projects to study

`study only` projects are read for design; copy nothing from them
([../ai/README.md](../ai/README.md), "License hygiene").

**[osu!](https://github.com/ppy/osu)**: `copy`, MIT, C#. The current osu! client ("lazer"), pushed
in September 2026. Learn from:
- Gameplay styles as rulesets: `osu.Game.Rulesets.Osu`, `.Taiko`, `.Catch` and `.Mania` are separate
  projects, each with its own test project, and `Templates/` starts a custom ruleset.
- Its README separates rights clearly: code MIT, the "osu!" and "ppy" names protected as trademarks,
  and game resources under a separate license (`ppy/osu-resources`, mostly CC BY-NC 4.0).
- Its README says contributions created or aided by AI are closed without discussion. Do not send
  AI-assisted pull requests upstream.

**[Etterna](https://github.com/etternagame/etterna)**: `copy`, MIT, C++ with Lua themes. A fork of
StepMania 5 focused on keyboard players. Learn from:
- `src/Etterna/MinaCalc/`: a chart difficulty calculator with separate key-mode files.
- Millisecond-based scoring with scalable judgment windows (`Themes/_fallback/Scripts/10
  WifeSundries.lua`) and per-skillset ratings.
- Caution: its README says the MAD and FFmpeg libraries it builds with are GPL, so a binary is not
  MIT-only even though the source is.

**[Quaver](https://github.com/Quaver/Quaver)**: `library use`, MPL-2.0, C#. A competitive
vertical-scrolling game with two modes, an in-game editor and multiplayer. Learn from:
- Submodules with their own licenses: `Quaver.API` (MPL-2.0) parses and writes maps and replays,
  converts maps from other games and calculates difficulty; `Wobble` (MIT) extends MonoGame.
- Its README says all game assets are under a separate license (`Quaver.Resources`).

**[YARG](https://github.com/YARC-Official/YARG)**: `library use`, LGPL-3.0, C# on Unity. A
plastic-instrument game for five-fret guitar, drums, vocals and pro guitar. Learn from:
- The backend kept in `YARG.Core` (LGPL-3.0): engine, chart parser, replay verification.
- An External Licenses table listing each bundled library and asset with its license. Two things in
  it are not free for commercial use: the BASS audio library and two CC BY-NC crowd sounds.

**[UltraStar Play](https://github.com/UltraStar-Deluxe/Play)**: `copy`, MIT, C# on Unity. A singing
game with a song editor. Learn from:
- Pitch detection (`Assets/Common/AiTools/PitchDetection/`) and a companion app that streams a
  phone's microphone to the game (`ClientSideMicDataSender.cs`).
- Its README points to a commercial continuation, which the MIT license allows.

**[Bemuse](https://github.com/bemusic/bemuse)**: `study only`, AGPL-3.0, TypeScript. A web rhythm game
for BMS charts, built with React, Redux and PixiJS. Learn from:
- Keysounded play, note speed separate from song speed, party mode that starts players at the same
  moment, and online rankings.
- Its README says the AGPL covers only the main project: the sub-packages are "mostly MIT", and the
  `bms` parser's `package.json` says MIT.

**[beatoraja](https://github.com/exch-bms2/beatoraja)**: `study only`, GPL-3.0, Java on LibGDX. A
BMS player. Learn from:
- Practice mode, eight groove gauges, eleven clear lamps, a fast or slow and millisecond readout, and
  command-line autoplay and replay modes.

**[StepMania](https://github.com/stepmania/stepmania)**: `check first` (MIT per list; GitHub could
not read the license), C++ with Lua. The dance game Etterna forked from. Its README: source MIT,
bundled songs under a non-commercial Creative Commons license, MAD and FFmpeg GPL when built. Read
the license files yourself before copying anything.

## 4. Reusable permissive code

| catalog project | reuse class, license | language | use it for |
|---|---|---|---|
| [osu-framework](https://github.com/ppy/osu-framework) | `copy`, MIT | C# | a game framework built for rhythm games (cataloged under engines); fluXis (`copy`) builds on a fork of it. Its BASS dependency needs a paid license for commercial distribution |
| [rhythm-game-utilities](https://github.com/rhythm-game-utilities/rhythm-game-utilities) | `copy`, MIT | C++ | `.chart` and `.midi` parsing, note positions, hit accuracy, beat detection, with bindings for several engines. Its README says early development, not for production |
| [NoteEditor](https://github.com/setchi/NoteEditor) | `copy`, MIT | C# | a Unity chart editor with long notes, undo and copy and paste; WAV only; last pushed in 2019 |
| [BeatLearning](https://github.com/sedthh/BeatLearning) | `copy`, Apache-2.0 | Python | experimental models that generate beatmaps from audio |
| [Quaver](https://github.com/Quaver/Quaver) | `library use`, MPL-2.0 | C# | `Quaver.API` for map and replay formats and difficulty; use its files unmodified, changes stay MPL |
| [YARG](https://github.com/YARC-Official/YARG) | `library use`, LGPL-3.0 | C# | `YARG.Core` for chart parsing and replay verification, as an unmodified library |

Not in the catalog; license read from each repository on 2026-09-23 (all would class as `copy`):

| library | license | use it for |
|---|---|---|
| [miniaudio](https://github.com/mackron/miniaudio) | public domain (Unlicense) or MIT-0, your choice | low-latency playback, mixing and decoding in C with no dependencies |
| [SoLoud](https://github.com/jarikomppa/soloud) | zlib (its bundled libraries vary, all permissive per its LICENSE) | a C++ audio engine for games |
| [Tone.js](https://github.com/Tonejs/Tone.js) | MIT | Web Audio scheduling, transport and synthesis in the browser |
| [howler.js](https://github.com/goldfire/howler.js) | MIT | simple cross-browser audio playback |

## 5. Engine options (engine-neutral)

| engine | license (catalog class) | fits | trade-off |
|---|---|---|---|
| [osu-framework](https://github.com/ppy/osu-framework) | MIT (`copy`) | C# desktop and mobile rhythm games; osu! and fluXis | BASS is commercial for commercial releases; the project refuses AI-assisted contributions |
| [Godot](https://github.com/godotengine/godot) | MIT (`copy`) | 2D or 3D, with an official guide to audio sync | chart tooling is yours to build |
| [Phaser](https://github.com/phaserjs/phaser) or [pixi.js](https://github.com/pixijs/pixijs) with Web Audio | MIT (`copy`) | browser games; Bemuse renders with PixiJS | output latency differs per device and browser; calibration is mandatory |
| [LibGDX](https://github.com/libgdx/libgdx) | Apache-2.0 (`copy`) | Java on desktop and Android; beatoraja is built on it | code first, no editor |
| [MonoGame](https://github.com/MonoGame/MonoGame) | MS-PL and MIT per list (`check first`; its `LICENSE.txt` is MS-PL with MIT-licensed portions) | C#; Quaver's Wobble framework extends it | you build UI and tooling |

Engine example for the song clock in section 2: Godot's docs page "Sync the gameplay with audio and
music" computes song time as `AudioStreamPlayer.get_playback_position()` plus
`AudioServer.get_time_since_last_mix()`, minus `AudioServer.get_output_latency()`. In another engine,
find the same three values before you write any judging code.

## 6. Assets

Music is the product. Code licenses say nothing about songs, charts, hit sounds or skins; check
every one and give it a row in `THIRD_PARTY.md` ([template](../templates/THIRD_PARTY.md)).

- **Commission or write original music**, with a written license that covers charting, bundling and
  commercial sale. It is the only source with no surprises.
- **[Incompetech](https://incompetech.com/music/royalty-free/licenses/)**: music under CC BY 4.0;
  attribution is required.
- **[OpenGameArt.org](https://opengameart.org)** music and sounds: licenses vary per submission.
  Avoid NoDerivatives (ND) terms: a chart synchronized to a track can count as an adaptation.
- **[Kenney](https://kenney.nl/assets)**: CC0 Music Jingles, Interface Sounds and Input Prompts for
  menus and controller glyphs.
- **[Freesound](https://freesound.org)**: hit sounds and claps, each with its own license (CC0
  through CC BY-NC).

Cautions from the reference projects:
- osu!'s resources are CC BY-NC 4.0; StepMania's bundled songs are non-commercial; YARG bundles two
  CC BY-NC sounds. MIT code next to non-commercial content is common in this genre.
- A chart made for a commercial song is still that song. beatoraja's README says "Don't use this
  application for playing copyrighted contents", and YARG's README takes a firm stance against
  piracy. Importers for other games' formats (Quaver.API, fluXis's `fluXis.Import.*` projects) are
  for charts and songs whose owners allow it.

## 7. Building it with AI tools

Follow the stage table in [../ai/README.md](../ai/README.md): Claude plans and reviews, Codex
implements one scoped task at a time, Grok reviews blind, a person playtests. What changes for
rhythm games:

| stage | lead | rhythm-specific artifact |
|---|---|---|
| design | Claude (plan mode) | `docs/timing.md`: clock source, chart format, judgment windows in ms, score and gauge formulas |
| failure list | Claude, attacked by Codex | clock drift, frame-rate-dependent judging, latency, pause and resume, encoder delay |
| slice | Codex | headless judge that scores a chart from timestamped inputs, then audio and rendering |
| feel | a person, with the timing log | error histograms from real play, before any window is changed |
| "my hits are late" reports | Grok and Codex, blind | the input log, the chart and the clock code, never your theory |

Prompts, in build order (fill the angle brackets; one task per Codex run):

```text
1. Timing spec (Claude, plan mode): Read ../opensource/playbooks/rhythm.md and
docs/design.md. Write docs/timing.md: where song time comes from in <engine>, the chart
format, every judgment window in milliseconds, score, combo and gauge formulas, how the
offset setting applies, and what happens on pause, resume and seek.

2. Headless judge (Codex): Implement src/judge/ in <language> with no audio or engine
imports: parse_chart(file) and judge(chart, events, offset_ms) -> list of judgments,
where events are (time_ms, lane, down/up). Add a CLI, judge --chart F --events E. Show
results for events exactly on every note, and for events at each window edge plus and
minus 1 ms.

3. Audio clock (Codex): Implement song_time() for <engine> from the audio position, per
docs/timing.md. Log song_time minus a frame-summed clock every second over a full song
at 30, 60 and 144 frames per second, and show the log.

4. Calibration and replays (Codex): A tap-along screen that stores the mean error as the
offset. Save each play as the chart hash plus its event list; replay --file R must
reproduce the score exactly. Show a replay's score matching the live score.
```

To borrow a design from a `study only` project such as Bemuse or beatoraja, write your own notes and
give a fresh session only the notes (the clean-room prompt in ../ai/README.md).

### Rhythm playtest checklist (add to the general one in ../ai/README.md)

- [ ] Autoplay (inputs exactly on each note) scores perfect at 30, 60 and 144 frames per second.
- [ ] Inputs 1 ms inside and outside each window edge get the judgments `docs/timing.md` specifies.
- [ ] The last note of the longest song is judged as accurately as the first: no drift.
- [ ] Pause, resume and seek keep notes and music together.
- [ ] Calibration recovers a known offset injected into the input path, within a few milliseconds.
- [ ] A saved replay reproduces its score on another machine.
- [ ] Tested with wireless headphones and a TV, and calibration fixes both.
- [ ] Every song and sound in the build has a license row, and none is non-commercial if you sell.

## 8. Genre-specific pitfalls

- **Frame time is not song time.** Summing frame deltas drifts, and judging on the frame an input was
  noticed ties accuracy to frame rate. Read the audio clock and judge input timestamps.
- **The latency stack.** Audio output buffers, wireless headphones, TV processing and input polling
  all add delay. Ship a calibration screen in the first public build, not at the end.
- **Encoded audio shifts sync.** MP3 encoders pad the start of a file, and decoders disagree on
  trimming it. Chart against the decoded audio your game plays, or use a format without padding.
- **Windows tuned by feel alone.** Record real error histograms from playtesters before changing a
  window; a player's "too strict" is often a latency problem.
- **Commercial audio middleware.** osu-framework and YARG depend on BASS, free only for
  non-commercial use. Budget for its license or pick miniaudio or SoLoud from the start.
- **Music you cannot ship.** The most common way a rhythm project dies. Settle rights for every song
  before charting it.
- **Flashing effects.** Beat-synced flashes can trigger photosensitive players. Offer a
  reduced-flashing option and keep it on in trailers.
- **Upstream AI policies.** osu!, osu-framework and others close AI-assisted pull requests. Keep
  AI-assisted work in your own game's repository.
