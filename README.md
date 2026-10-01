# opensource

Open-source projects to build on instead of starting from scratch, each with its license read from
GitHub and a plain rule for what you may reuse. Two domains so far: games, and software beyond games.

## Domains

| domain | what it holds | start here |
|---|---|---|
| Games | a genre catalog of 2,718 open-source games and engines, a build playbook per genre, and guides to game art, engines and building with AI tools | [Start a new game](#start-a-new-game), [genres](#genres) |
| Software | 366 hand-picked open-source applications, tools and libraries beyond games, in 19 categories from self-hosting, local AI and agent memory to documents, media, learning and personal finance, and curated lists that go wider | [`software/`](software/README.md) |

Both follow the same [license rule](#the-license-rule). The games material sits at the top level of
this repository; everything else lives under [`software/`](software/).

## Games

A chassis for building new games **from open source instead of from scratch**: a genre catalog of
2,718 open-source games and engines with each project's license and activity read from GitHub,
a build playbook per genre, a guide to building with AI coding tools (Claude, Codex, Grok), and
engineering lessons from small games we built.

## Start a new game

1. **Pick a genre** and read its playbook in [`playbooks/`](playbooks/): the core loop, the systems in
   build order, the reference projects worth studying, and the pitfalls.
2. **Choose what to learn from and what to reuse.** Every project in [`catalog/`](catalog/) carries a
   reuse class (below). Reuse code only from `copy` projects, with attribution.
3. **Pick an engine.** The chassis is engine-neutral; each playbook lists engines that fit the genre.
   For a browser game, choose by game type: [three.js and React Three Fiber](engines/threejs-r3f.md) for
   3D you build in-house, [Phaser](engines/phaser.md) for 2D, sprite and isometric games, and
   [Godot 4](engines/godot.md#godot-on-the-web-when-to-choose-it) for a bigger 3D game still shipped to
   the browser.
4. **Build with AI tools** following [`ai/README.md`](ai/README.md): which tool for which stage,
   prompt templates, and how to use a second model as a reviewer. See also [AI game agents](ai/game-agents.md)
   and [code-only animation](ai/animation.md).
5. **Start the game repo from [`templates/`](templates/)**: an `AGENTS.md` every AI tool reads, and a
   `THIRD_PARTY.md` recording every file you borrowed and its license.

## Graphics, engines and starting projects

- [`art/blender.md`](art/blender.md): 3D game art with Blender, from modeling to engine export,
  3D-to-2D sprite rendering, Python automation, and letting AI tools drive Blender.
- [`art/2d.md`](art/2d.md): 2D art with GIMP, Krita, Inkscape and pixel-art tools, tile maps,
  texture atlases and batch automation.
- [`art/audio.md`](art/audio.md): sound effects, music and loudness with jsfxr, Audacity, LMMS,
  local music generation and a rerunnable FFmpeg export script.
- [`engines/`](engines/): [Godot](engines/godot.md) (with [Godot on the web](engines/godot.md#godot-on-the-web-when-to-choose-it)),
  [three.js and React Three Fiber](engines/threejs-r3f.md) for browser 3D, [Phaser](engines/phaser.md)
  for 2D, sprite and isometric games, [Unreal](engines/unreal.md) (source-available
  under Epic's EULA), [Unity](engines/unity.md) (not open source; its terms are summarized), and
  [others](engines/others.md): Bevy, LOVE, raylib, MonoGame, Defold, Babylon.js, PlayCanvas, Kaplay and
  other web libraries. See the [Rust, WebAssembly and WebGPU guide](engines/rust-wasm-webgpu.md) for
  browser games.
- [`scaffolds/`](scaffolds/README.md): the best-maintained open-source starter templates per engine,
  plus [MCP servers](scaffolds/mcps.md) that let AI tools operate art tools and engines. Rebuilt by
  `tools/find_scaffolds.py`.
- [`ai/graphics.md`](ai/graphics.md): AI and game graphics, safely.
- [`ai/media-studio.md`](ai/media-studio.md): trailers and devlogs: video from code, capture,
  assembly by script and hand editing, with which tools an agent can drive.

**MCP servers and add-ons run code on your machine.** Read the code, pin a version, keep them
local, and give them the least access that works.

## The license rule

| reuse class | licenses | what you may do |
|---|---|---|
| `copy` | MIT, BSD, Apache-2.0, zlib, ISC, CC0, Unlicense... | reuse the code, keep the copyright notice, list it in THIRD_PARTY.md |
| `library use` | LGPL, MPL, EPL | use it unmodified as a library; do not copy it into your code |
| `study only` | GPL, AGPL, CC-BY-SA | read it for design and mechanics; copy nothing |
| `check first` | no license; a license only a list states; one GitHub could not identify; a decompiled commercial game | all rights reserved until you confirm otherwise |

**A code license says nothing about art, audio, maps or data**, which frequently carry their own
licenses (often non-commercial). Check assets separately. This is practical guidance, not legal advice.

## Genres

598 of 2,718 projects have a permissive code license verified on GitHub. Built 2026-09-23.

| genre | projects | copy | active in the last 2 years | playbook |
|---|---|---|---|---|
| [Strategy](catalog/strategy.md) | 420 | 39 | 139 | [playbook](playbooks/strategy.md) |
| [Simulation](catalog/simulation.md) | 177 | 29 | 74 | [playbook](playbooks/simulation.md) |
| [Arcade](catalog/arcade.md) | 314 | 65 | 69 | [playbook](playbooks/arcade.md) |
| [Action](catalog/action.md) | 137 | 22 | 27 | [playbook](playbooks/action.md) |
| [Platformer](catalog/platformer.md) | 104 | 16 | 37 | [playbook](playbooks/platformer.md) |
| [RPG](catalog/rpg.md) | 234 | 37 | 76 | [playbook](playbooks/rpg.md) |
| [Roguelike](catalog/roguelike.md) | 69 | 11 | 23 | [playbook](playbooks/roguelike.md) |
| [Fighting](catalog/fighting.md) | 76 | 40 | 40 | [playbook](playbooks/fighting.md) |
| [Shooter](catalog/shooter.md) | 202 | 22 | 75 | [playbook](playbooks/shooter.md) |
| [Puzzle](catalog/puzzle.md) | 241 | 54 | 61 | [playbook](playbooks/puzzle.md) |
| [Racing](catalog/racing.md) | 66 | 16 | 25 | [playbook](playbooks/racing.md) |
| [Sports](catalog/sports.md) | 11 | 2 | 1 | [playbook](playbooks/sports.md) |
| [Adventure](catalog/adventure.md) | 76 | 18 | 23 | [playbook](playbooks/adventure.md) |
| [Sandbox](catalog/sandbox.md) | 34 | 15 | 16 | [playbook](playbooks/sandbox.md) |
| [Board and card](catalog/board-card.md) | 34 | 12 | 17 | [playbook](playbooks/board-card.md) |
| [Rhythm](catalog/rhythm.md) | 102 | 36 | 69 | [playbook](playbooks/rhythm.md) |
| [Educational](catalog/educational.md) | 9 | 0 | 2 | [playbook](playbooks/educational.md) |
| [Engines and frameworks](catalog/engines.md) | 257 | 105 | 141 |  |
| [Other](catalog/other.md) | 155 | 59 | 48 |  |

## How the catalog is built

`tools/fetch_sources.sh` downloads three public lists and a few GitHub topic searches;
`tools/build_catalog.py` merges them, then asks GitHub's API for every repository's license,
language, stars and last push. **A list's claim about a license is never used when GitHub can be
asked**, and a list's license never makes a project `copy`: projects hosted elsewhere show their list's
license marked "per list, unverified" and read `check first`. Rebuild:

```sh
tools/fetch_sources.sh && python3 tools/build_catalog.py --src sources --out .
```

Both need the GitHub CLI, `gh`, installed and signed in; the build says so in one line when it is
not. `fetch_sources.sh` replaces the lists in `sources/` only when every download and search
succeeded. A GitHub lookup that fails is retried with growing waits; one that still fails stops the
build before anything is written, and the lookups that succeeded stay cached in `sources/`, so a
rerun picks up where it stopped. `python3 tools/check_build.py` checks those failure paths with a
fake `gh` and no network.

**Safety:** topic searches pull in malware lures named after commercial games, so 444 projects found
only by a topic search with under 10 stars or no code, named like a download lure, or removed on review, are left out (counts in
[`catalog/README.md`](catalog/README.md)). **Never download a release, zip or installer from a catalog
repository; read and build from source.** Report a lure you still find as an issue.

Genres come from the lists' own headings and keywords, mapped to one taxonomy; expect some
projects in a neighboring genre. Corrections are welcome as pull requests to the mapping in
`tools/build_catalog.py`.

The software list is built differently, from curated seeds rather than parsed lists, with the same
GitHub lookup and license rule; see [how it is built](software/README.md#how-this-list-is-built).

## Sources and credit

- [bobeff/open-source-games](https://github.com/bobeff/open-source-games) (CC0)
- [michelpereira/awesome-open-source-games](https://github.com/michelpereira/awesome-open-source-games) (CC0)
- [Trilarion/opensourcegames](https://github.com/Trilarion/opensourcegames) ([site](https://trilarion.github.io/opensourcegames/)) (CC0)
- GitHub topic [`open-source-game`](https://github.com/topics/open-source-game), plus fighting-game,
  beat-em-up, rollback-netcode, racing-game, sports-game, rhythm-game and sandbox-game

Thank you to the maintainers of those lists. Every listed project keeps its own license.

## License

This repository's tools and documents are MIT licensed (see [LICENSE](LICENSE)). The games catalog
data derives from CC0 lists and GitHub metadata; the software list from its own curated seeds and
GitHub metadata.
