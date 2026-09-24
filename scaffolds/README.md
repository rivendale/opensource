# Scaffolds: start from a project that already runs

A scaffold is a small, working project that already has the parts every game needs and few people
budget time for: a main menu, an options screen that remembers its settings, pause, scene loading,
input that works on a gamepad, and a build that runs on someone else's machine. Starting from one
puts your first week into the game instead of the plumbing, and it gives an AI coding tool real,
running code and conventions to extend instead of an empty folder to fill.

This folder lists starter templates, AI bridges and art-tool add-ons found on GitHub and checked
there. The shortlist below was read repository by repository on 2026-09-23; stars and dates are a
snapshot from that day.

| file | what it lists |
|---|---|
| [`scaffolds.md`](scaffolds.md) | starter templates per engine: Godot, Unity, Bevy, Phaser, raylib, LÖVE, MonoGame, Excalibur, three.js |
| [`mcps.md`](mcps.md) | MCP servers that let an AI tool operate Blender, GIMP, Krita, Godot, Unity and Unreal Engine. Each one runs code on your machine, and some listen on every network interface by default: read its risk row in [`../ai/graphics.md`](../ai/graphics.md#maintained-servers-per-tool) and apply the [safe setup checklist](../ai/graphics.md#safe-setup-checklist) before installing one. |
| [`../data/scaffolds.json`](../data/scaffolds.json) | the same 153 repositories as data |

Art-tool add-ons are not generated: search found too few, some off-topic. The hand-checked add-on
tables are in [`../art/blender.md`](../art/blender.md) and [`../art/2d.md`](../art/2d.md).

## How to choose

1. **License class first.** Only a `copy` template (MIT, BSD, Apache-2.0, zlib, CC0, Unlicense...)
   can become your game's code. A `study only` template (GPL, AGPL) is for reading; copy nothing
   from it. Keep the template's `LICENSE` and add it to your `THIRD_PARTY.md` on day one.
2. **Then the assets.** A code license says nothing about a template's art, audio and fonts:
   - Maaack's Godot template ships its own plugin logo under **CC BY-NC-ND 4.0, which forbids
     commercial use and modified versions**: delete every `plugin_logo/logo.png` (six copies across
     `assets/`, `examples/` and its addons) before you ship. The Godot logo (CC BY 4.0) and the Git
     logo (CC BY 3.0) each need a credit.
   - The three.js template's two character models are CC-BY-4.0: credit the author or replace them.
   - Kenney's 3D platformer kit marks its models, sprites and sounds CC0, but its font, Lilita One,
     is SIL OFL 1.1: ship `fonts/license.txt` with the game.
   - bevy_new_2d says all of its assets are third party and credits them in `src/menus/credits.rs`.
3. **Maintenance.** Look at the last push, the engine version it targets, open issues, and whether
   it is archived (`scaffolds.md` marks archived rows). A template for Godot 4.7 may not open in an
   older editor. Stars measure attention, not quality or safety.
4. **What it includes.** Tick what your game needs before you compare templates:

   | need | why it is expensive to add late |
   |---|---|
   | main, pause and options menus | every screen needs focus, back navigation and gamepad support |
   | settings that persist | volume, resolution and language have to load before the first frame |
   | save and load | save data shapes how you structure game state |
   | input remapping | touches every place input is read |
   | scene transitions and loading | async loading and web exports behave differently |
   | localization | strings buried in code are hard to extract later |
   | CI builds | "works on my machine" hides missing files and export settings |
   | tests | a test harness is easiest to add while the project is small |

5. **Read the build scripts.** Templates run code when you install and build them. Phaser's
   official Vite templates call `gryzor.co`, a Phaser Studio domain, from `log.js` in the default
   `dev` and `build` scripts, sending the build type, the Phaser version and the `name` field of
   your `package.json` (the template's name until you rename your project); its README documents
   `npm run dev-nolog` and `npm run build-nolog`. Deploy workflows need secrets (bitbrain's itch.io
   workflow needs a `BUTLER_API_KEY`): give a workflow only the secrets it uses.
6. **Pick the smallest template that covers your list.** Every system you inherit is code you have
   to understand, and an AI tool will copy whatever patterns it finds.

## Shortlist by engine

Each row was checked by reading the repository's README and, where noted, its docs or file tree.
All are reuse class `copy` unless stated.

### Godot (engine license: MIT)

| template | license, stars | what it includes |
|---|---|---|
| [Maaack/Godot-Game-Template](https://github.com/Maaack/Godot-Game-Template) | MIT code (its plugin logo is CC BY-NC-ND 4.0: see step 2 above), 1,658 | main, options, pause and credits menus; loading screen; persistent settings; input remapping; keyboard, mouse and gamepad; basic save and load; level loader and win and lose screens; an itch.io upload script and a CI/CD guide. Godot 4.7, compatible with 4.4 and later. Also installs as a plugin into an existing project; a smaller [Minimal](https://github.com/Maaack/Godot-Minimal-Game-Template) variant exists. |
| [crystal-bit/godot-game-template](https://github.com/crystal-bit/godot-game-template) | MIT, 980 | scene transitions with a progress bar and parameters; multithreaded loading with a web fallback; settings for audio buses, language, resolution scale, FPS limit and vsync saved with `ConfigFile`; gettext localization (English, Italian); keyboard, gamepad and touch; debug shortcuts removed from release builds; GitHub Actions builds and GitHub Pages deploy. |
| [bitbrain/godot-gamejam](https://github.com/bitbrain/godot-gamejam) | MIT, 811 | main, settings and pause menus; audio volume and language settings; boot splash; saves the nodes in a `Persist` group when the player quits from the pause menu; CSV translations; itch.io deploy for macOS, Windows, Linux and web. Its README warns that not every game jam allows templates. |
| [chickensoft-games/GodotGame](https://github.com/chickensoft-games/GodotGame) | MIT, 420 | C# only: a `dotnet new` template with tests that run inside the game locally and in CI (Mesa software rendering), code coverage, Renovate dependency updates, spell check and VS Code debug profiles. No menus: pair it with a menu template. |

Also worth knowing: the official [godotengine/godot-demo-projects](https://github.com/godotengine/godot-demo-projects)
(MIT, 9,559) for learning one feature at a time; [KenneyNL/Starter-Kit-3D-Platformer](https://github.com/KenneyNL/Starter-Kit-3D-Platformer)
(MIT code; CC0 models, sprites and sounds; an OFL 1.1 font; 1,235) with a double-jump controller, coins, falling platforms, camera and
gamepad support; and [abarichello/godot-ci](https://github.com/abarichello/godot-ci) (MIT, 1,128), a
Docker image with GitHub Actions and GitLab CI examples that export and deploy to GitHub Pages,
GitLab Pages and itch.io.

### Unity (engine: proprietary, not open source)

Unity's C# source is published for reference only; its license does not permit modifying or
redistributing it. On 2026-09-23 Unity's plan page said Unity Personal is for individuals and small
organizations with less than $200K USD of revenue and funds raised in the last 12 months; read the
current terms before you commit. Unity Hub offers its own Core, Sample and Learning templates; they
are not open-source repositories and are not rated here.

- [SamuelAsherRivello/unity-project-template](https://github.com/SamuelAsherRivello/unity-project-template)
  (MIT, 143, last push 2025-09-28): folder structure and C# coding standards, assembly definitions,
  URP with post-processing, Cinemachine, ProBuilder, TextMeshPro, and the Unity Test Framework with
  code coverage. Sibling repositories add UI Toolkit, AR, VR, multiplayer, WebGPU or DOTS. Its feature
  list has no menus or save system.
- [game-ci/unity-builder](https://github.com/game-ci/unity-builder) (MIT, 1,095): a GitHub Action that
  builds Unity projects for several platforms. Not affiliated with Unity Technologies; docs at
  [game.ci](https://game.ci/docs).

Judging by their descriptions, none of the ten Unity rows in `scaffolds.md` is a menus, settings and
saving template like the Godot ones above; expect to build those parts.

### Bevy (engine license: MIT or Apache-2.0)

- [TheBevyFlock/bevy_new_2d](https://github.com/TheBevyFlock/bevy_new_2d) (CC0-1.0, MIT or
  Apache-2.0 at your option; GitHub reads MIT; 484): create it with `bevy new my_game --template 2d`
  from the Bevy CLI. Splash, title and loading screens; main, pause and settings menus; asset
  tracking; audio; dev tools; reusable UI widgets; CI/CD that deploys to itch.io.
- [NiklasEi/bevy_game_template](https://github.com/NiklasEi/bevy_game_template) (CC0-1.0, 1,148):
  a release workflow for Windows, Linux, macOS and web on a version tag, mobile builds, CI on every
  push, GitHub Pages deploy, and a `credits` directory shipped in every build.
- [bevyengine/bevy_github_ci_template](https://github.com/bevyengine/bevy_github_ci_template)
  (Apache-2.0, MIT or CC0-1.0; GitHub reads Apache-2.0; 264): CI running `cargo test`, `clippy` and
  `fmt`, and tagged release builds for Linux, Windows, macOS and wasm. Add it to either template.

### Web: Phaser (MIT), Excalibur (BSD-2-Clause), three.js (MIT)

- [phaserjs/template-vite-ts](https://github.com/phaserjs/template-vite-ts) (MIT, 195): official
  Phaser 4, Vite and TypeScript template with hot reload and a production build. The official
  `npm create @phaserjs/game` CLI offers it among other templates; its repository has no license
  file GitHub can identify (its npm metadata says MIT), and its README runs it at `@latest`. Clone
  the template repository at a release or commit instead, or pin the CLI
  (`npm create @phaserjs/game@1.3.2`, the latest on 2026-09-23) and read it first. Mind `log.js`
  (above).
- [excaliburjs/template-ts-vite](https://github.com/excaliburjs/template-ts-vite) (BSD-2-Clause, 39):
  the official Excalibur TypeScript and Vite template, also created by `npm create excalibur`,
  which fetches the latest `create-excalibur`: pin it (`npm create excalibur@2.0.0` on 2026-09-23).
- [SahilK-027/threejs-gamedev-template](https://github.com/SahilK-027/threejs-gamedev-template)
  (Apache-2.0, 49): entity-component structure, spatial audio, Draco and KTX2 loading with
  progress, GLSL hot reload, debug GUI and performance monitor, and an audio settings UI.

### Native: raylib (zlib), LÖVE (zlib), MonoGame (Ms-PL)

- [raysan5/raylib-game-template](https://github.com/raysan5/raylib-game-template) (Zlib, 705): official,
  in C. Screen files for logo, title, options, gameplay and ending; Visual Studio 2022, CMake and
  Makefile builds; GitHub Actions for Windows, Linux, macOS and WebAssembly.
- [karl-zylinski/odin-raylib-hot-reload-game-template](https://github.com/karl-zylinski/odin-raylib-hot-reload-game-template)
  (Zlib, 622): Odin; reloads gameplay code while the game runs; release, debug and web build scripts.
- [SasLuca/raylib-cmake-template](https://github.com/SasLuca/raylib-cmake-template) (Zlib, 218):
  minimal CMake that fetches raylib's source with `FetchContent`.
- [camchenry/Love2D-Template](https://github.com/camchenry/Love2D-Template) (MIT, 88, last push
  2023-12-25): bundles HUMP (gamestate, camera, timer, signal, class, vector), Lume, inspect.lua and
  HSLuv. Its author says it is primarily for personal use. HUMP's own repository has no license
  GitHub can identify, but the HUMP files in the template carry an MIT-style notice: keep them.
- MonoGame's official templates install with `dotnet new install MonoGame.Templates.CSharp::3.8.5.1`
  (pinned to the latest version on NuGet on 2026-09-23); then `dotnet new mgdesktopgl` creates a
  desktop project.

## Using a scaffold with AI tools

1. **Fork it, or press "Use this template".** Record the upstream URL and commit in
   [`THIRD_PARTY.md`](../templates/THIRD_PARTY.md), keep its `LICENSE` and attribution files, and add
   [`templates/AGENTS.md`](../templates/AGENTS.md).
2. **Run it unchanged first.** Build, export and play the example on the target platform. That
   proves the baseline and catches an engine-version mismatch before any AI edit hides it.
3. **Strip it,** in a session of its own:

   ```text
   Read the whole repository. We are building <one-sentence game> in <genre>.
   List every example scene, script, asset and workflow we do not need for the vertical slice,
   and every feature we keep (menus, settings, save, input remapping, CI). Do not delete yet.
   For each removal, name what references it. Keep LICENSE, attribution and credits files.
   ```

   Review the list, then let it remove files in one commit and confirm the project still builds.
4. **Point Claude or Codex at the playbook.** With this chassis cloned beside your game (see
   [`../ai/README.md`](../ai/README.md)):

   ```text
   Read ../opensource/playbooks/<genre>.md and this repository. Using the template's existing
   patterns (its scene loader, settings store and input actions), write docs/design.md for
   <game>, then list the systems in build order. Reuse the template's systems; do not add a
   second menu, save or settings system.
   ```

5. **Keep the upstream remote** so you can read later fixes, and review each upstream diff before
   merging it; a template update is code you did not write.

## How these lists are made

[`tools/find_scaffolds.py`](../tools/find_scaffolds.py) runs a set of GitHub searches per engine and
art tool, reads every result from GitHub's API, and keeps a repository only if it has code, a
license GitHub can identify, 25 or more stars and a push in the last three years. It also applies
the main catalog's lure filter, drops off-topic matches by name, and drops an MCP server whose repo or
owner account is under 60 days old. Those filters catch obvious lures, not malicious code: nothing
here is security-reviewed. It writes `data/scaffolds.json` and the two lists here.

```sh
python3 tools/find_scaffolds.py --out .     # needs the GitHub CLI, logged in
```

The lists are generated: change the queries in the script and rebuild rather than editing them by
hand. Search is keyword and star based, and a row's engine group comes from the query that found
it, so a row can sit under the wrong heading: the "Any engine" group holds one Godot and one Unity
template. The shortlist above is chosen by hand and should be rechecked when the lists change.

Most Blender add-ons, including those in [`../art/blender.md`](../art/blender.md), are GPL. Blender's license page says published
scripts and add-ons must use a GPL-compliant license, so treat Blender add-on code as `study only`
unless its repository says otherwise. The same page says what you create with Blender is your sole
property; [`../ai/graphics.md`](../ai/graphics.md) quotes what each art tool's own documentation says
about your output.

This is practical guidance, not legal advice.
