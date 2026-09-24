# Other engines and frameworks

Bevy, Phaser, LÖVE, raylib, MonoGame, Defold, and three.js, PixiJS and Excalibur for the web. For
Godot see [`godot.md`](godot.md); for Unity, which is not open source, see [`unity.md`](unity.md).

How this page was checked, on 2026-09-23:

- **Licenses** were read from each project's LICENSE file or README, not only from GitHub's license
  detector, which misreads several of these (noted where it does).
- **Starter templates** come from [`scaffolds/scaffolds.md`](../scaffolds/scaffolds.md) (a license
  GitHub identifies, 25+ stars, a push in the last three years), plus official templates added here
  with their license and activity checked on GitHub. Official templates below 25 stars are included
  and their star counts shown.
- **Catalog counts** are a keyword search of [`data/catalog.json`](../data/catalog.json); some rows
  match only by keyword, so confirm the engine in the repository. Reproduce with, for example:

```sh
jq -r --arg p '\bphaser\b' '.entries[] | select([.name, .description, (.labels // [] | join(" ")),
  (.deps // "" | tostring)] | map(. // "") | join(" ") | test($p; "i")) | [.reuse, .license, .repo] | @tsv' data/catalog.json
```

**About AI tooling here.** These are code-first frameworks: an AI coding tool edits the source
directly, so an MCP server matters less than it does for an editor like Unity or Godot. What helps
most is documentation written for language models (`llms.txt`), which three.js, PixiJS, Defold and
Phaser publish. Where an MCP server or remote-control protocol exists, it runs code on your machine
with your permissions: prefer a well-maintained project, read its code, pin a release or commit,
run it with least privilege and in development builds only, and **never expose it to the network**.
Keep every port bound to localhost. Each server below carries its own risk note; the
[safe setup checklist](../ai/graphics.md#safe-setup-checklist) applies to all of them. More in
[`ai/README.md`](../ai/README.md) and [`ai/graphics.md`](../ai/graphics.md), which also covers licensing
of AI-generated art. Record AI-generated and AI-assisted assets in the game repo's `THIRD_PARTY.md`, in
its section "AI-generated and AI-assisted assets" ([template](../templates/THIRD_PARTY.md#ai-generated-and-ai-assisted-assets)).

**Pinning starters.** The generators below (`npm create`, `npx`, `cargo install`, `dotnet new install`)
run code from a package registry. Name an exact version (the latest on 2026-09-23 is given), not
`@latest`, which runs whatever was published last. For npm, an exact version pins the generator, not
its dependencies, which npm resolves again on a cold cache; read the generated project and commit its
lockfile.

**Art tools.** [Blender](https://www.blender.org/about/license/) (GPL; "What you create with Blender
is your sole property"), GIMP (GPL v3 or later) and Krita (GPL-3.0) are open source. The
[Tiled](https://github.com/mapeditor/tiled) map editor is GPL, with its `libtiled` library under
BSD 2-clause. [Aseprite](https://github.com/aseprite/aseprite) is source-available under its own
EULA, not open source. See [`art/blender.md`](../art/blender.md) and [`art/2d.md`](../art/2d.md).

## Bevy (Rust)

- **License:** MIT or Apache-2.0, at your option, per the [README](https://github.com/bevyengine/bevy)
  ("except where noted"). GitHub's detector shows only Apache-2.0. Latest release v0.19.1
  (2026-08-13).
- **Suits:** Rust programmers building 2D or 3D games in a data-driven ECS, entirely in code. The
  README warns that Bevy "is still in the early stages of development" and ships a release with
  breaking API changes about every three months, so pin your Bevy version.
- **Starters:**
  - [TheBevyFlock/bevy_new_2d](https://github.com/TheBevyFlock/bevy_new_2d): CC0-1.0, MIT or
    Apache-2.0 at your option; 484 stars; pushed 2026-08-06; Bevy 0.19. Menus, screens, dev tools,
    a demo, and CI/CD that can deploy to itch.io. Create it with the Bevy CLI:
    `bevy new my_game --template 2d`. Its assets are third-party; see its credits menu.
    `bevy new` copies the template's current default branch, so record the commit you started from.
  - [TheBevyFlock/bevy_cli](https://github.com/TheBevyFlock/bevy_cli): MIT and Apache-2.0 license
    files; alpha (`cli-v0.1.0-alpha.2`). `bevy run` and `bevy run web` run native and web builds.
    Install it pinned, as its README shows:
    `cargo install --git https://github.com/TheBevyFlock/bevy_cli --tag cli-v0.1.0-alpha.2 --locked bevy_cli`.
  - [NiklasEi/bevy_game_template](https://github.com/NiklasEi/bevy_game_template): CC0-1.0 except
    some assets and the Bevy icons; 1,148 stars; pushed 2026-07-25; Bevy 0.19. CI/CD for web,
    Windows, Linux, macOS, iOS and Android.
  - [bevyengine/bevy_github_ci_template](https://github.com/bevyengine/bevy_github_ci_template):
    Apache-2.0, MIT or CC0-1.0 at your option, per its README and three license files (GitHub's
    detector reads only Apache-2.0); 264 stars; CI workflows only.
- **Art pipeline:** glTF is built in (the `bevy_gltf` crate); export `.glb` from Blender. 2D sprite
  sheets use `TextureAtlasLayout` (see the `sprite_sheet` and `texture_atlas` examples).
- **AI tooling:** the Bevy Remote Protocol (`bevy_remote`, JSON-RPC 2.0) lets a client inspect and
  change a running game's entities. It is opt-in: you add `RemotePlugin` plus `RemoteHttpPlugin`,
  which listens on 127.0.0.1 port 15702 by default. **BRP has no authentication:** any program on your
  machine that reaches the port can read and change the running game, so enable it only in development
  builds, keep the default address, and never set it to `0.0.0.0` or add a wildcard CORS header.
  [natepiano/bevy_brp](https://github.com/natepiano/bevy_brp) (70 stars, active) provides `bevy_brp_mcp`,
  an MCP server over that protocol, run over stdio; version 0.22.7 supports Bevy 0.19. It launches your
  apps with Cargo and can call any BRP method, including ones that change the world or shut the app
  down. Install it pinned, after the [safe setup checklist](../ai/graphics.md#safe-setup-checklist):
  `cargo install bevy_brp_mcp --version 0.22.7 --locked`. Its license files
  (MIT, Apache-2.0) sit in its `mcp/` folder and GitHub detects no root license, which is why the
  scaffolds list leaves it out: read those files first.
- **Catalog:** 6 rows mention Bevy, 2 `copy` (extreme_bevy, CC0; bevy_timewarp, MIT).

## Phaser (JavaScript and TypeScript)

- **License:** MIT. Latest release v4.2.1 (2026-07-09). Developed by Phaser Studio Inc with its
  community.
- **Suits:** 2D browser games with WebGL and Canvas rendering; the README also names YouTube
  Playables, Discord Activities, Reddit games and Twitch overlays, and native apps through
  third-party tools.
- **Starters:**
  - Official CLI: `npm create @phaserjs/game@1.3.2` ([phaserjs/create-game](https://github.com/phaserjs/create-game);
    its README says `@latest`).
    It offers Vue, React, Angular, Next.js, SolidJS, Svelte and Remix with Vite, Rollup, Parcel,
    Webpack, ESBuild, Import Map or Bun, plus three demo games. The CLI repository shows no license
    file; the templates it installs are MIT.
  - Official templates: [template-vite-ts](https://github.com/phaserjs/template-vite-ts) (MIT, 195
    stars, pushed 2026-04-21), [template-vite](https://github.com/phaserjs/template-vite) (MIT, 138)
    and [template-webpack](https://github.com/phaserjs/template-webpack) (MIT, 1,173). Their
    descriptions still say Phaser 3, but their `package.json` pins Phaser 4.0.0.
  - Community: [openforge/ionic-phaser-game-template](https://github.com/openforge/ionic-phaser-game-template)
    (MIT, 110, 2025-09-19) for mobile apps; [enable3d/enable3d-phaser-project-template](https://github.com/enable3d/enable3d-phaser-project-template)
    (MIT, 51, 2025-03-08) adds enable3d, a 3D extension for Phaser 3 with physics.
- **Art pipeline:** the loader reads sprite sheets, texture atlases (JSON and XML), multi-atlases,
  Aseprite JSON exports, Tiled JSON and CSV maps, bitmap fonts, SVG and compressed textures. For 3D
  models rendered to sprites, see [`art/blender.md`](../art/blender.md).
- **AI tooling:** [phaser.io/llms.txt](https://phaser.io/llms.txt) indexes the examples. Phaser
  Editor v5 is a paid, proprietary desktop app; its [MCP server](https://github.com/phaserjs/editor-mcp-server)
  works only with a running Phaser Editor and its repository shows no license file. Its README runs it
  unpinned (`npx @phaserjs/editor-mcp-server`) and does not say how it reaches the editor, so it is not
  recommended here; if you use it, pin `@1.0.6` and read that part of its code first. No community Phaser MCP server met this chassis's bar.
- **Catalog:** 16 rows mention Phaser, 7 `copy`.

## LÖVE (Lua)

- **License:** zlib for LÖVE itself, per its [`license.txt`](https://github.com/love2d/love/blob/main/license.txt),
  which also lists the bundled libraries under their own licenses (MIT, FreeType License, BSD and
  others). GitHub's detector cannot identify the license, so the catalog shows LÖVE as `check first`; the file
  says zlib. Latest release 11.5 (2023-12-03); the `main` branch is the next major version and
  "should not be considered stable".
- **Suits:** small 2D games, game jams and prototypes in Lua.
- **Starters:**
  - [Oval-Tutu/bootstrap-love2d-project](https://github.com/Oval-Tutu/bootstrap-love2d-project):
    MIT; 186 stars; pushed 2025-12-15. VS Code workspace with Lua language support and a debugger,
    GitHub Actions builds for Android, iOS, HTML5, Linux, macOS and Windows, and itch.io publishing.
    Supports LÖVE 11.5 only. Not in the scaffolds list; added here after checking it on GitHub.
  - [camchenry/Love2D-Template](https://github.com/camchenry/Love2D-Template): MIT; 88 stars; last
    push 2023-12-25.
  - [hazzard993/love-typescript-template](https://github.com/hazzard993/love-typescript-template):
    MIT; 38 stars; pushed 2026-05-05; write the game in TypeScript.
- **Art pipeline:** 2D. `love.graphics.newImage` loads images, `newQuad` cuts frames from a sprite
  sheet, `newSpriteBatch` draws many of them cheaply, and `newMesh` draws custom geometry. The
  graphics API has no model loader, so plan on 2D art from GIMP, Krita or a pixel editor.
- **AI tooling:** no LÖVE MCP server met the bar (the largest had 11 stars).
- **Catalog:** 19 rows mention LÖVE, 7 `copy`.

## raylib (C)

- **License:** Zlib. Latest release 6.0 (2026-04-23). Bindings exist for more than 70 languages.
- **Suits:** learning, and C or C++ programmers who want a small library instead of an editor, for
  2D or 3D.
- **Starters:**
  - [raysan5/raylib-game-template](https://github.com/raysan5/raylib-game-template): official;
    Zlib; 705 stars; pushed 2026-08-13. Plain C, with Visual Studio and Linux setup notes.
  - [raysan5/raylib-gamejam-template](https://github.com/raysan5/raylib-gamejam-template): official;
    Zlib; 99 stars.
  - [SasLuca/raylib-cmake-template](https://github.com/SasLuca/raylib-cmake-template) (Zlib, 218) for
    CMake; [educ8s/Raylib-CPP-Starter-Template-for-VSCODE](https://github.com/educ8s/Raylib-CPP-Starter-Template-for-VSCODE)
    (MIT, 795) for C++; [karl-zylinski/odin-raylib-hot-reload-game-template](https://github.com/karl-zylinski/odin-raylib-hot-reload-game-template)
    (Zlib, 622) for Odin with hot reload.
- **Art pipeline:** per the README, animated 3D models in IQM, M3D and glTF, PBR materials,
  compressed textures (DXT, ETC, ASTC), and TTF, OTF, FNT and BDF fonts. Export glTF from Blender.
- **AI tooling:** no raylib MCP server found; its 200+ examples are the best context to give a model.
- **Catalog:** 2 rows mention raylib, 1 `copy` (raylib itself).

## MonoGame (C#)

- **License:** Microsoft Public License (Ms-PL), with portions under MIT from the Mono.Xna team, per
  its [`LICENSE.txt`](https://github.com/MonoGame/MonoGame/blob/develop/LICENSE.txt). GitHub's
  detector cannot identify the license, so the catalog shows `check first`. Ms-PL lets you ship a compiled
  game: keep its notices, and distribute compiled forms only under terms that comply with Ms-PL. Any
  MonoGame source you redistribute must stay under Ms-PL, so treat copying its source into your own
  code like `library use`. Latest release v3.8.5.1 (2026-08-14).
- **Suits:** C# programmers who want a framework rather than an editor, 2D above all, and a home for
  the portable C# core described in [`unity.md`](unity.md#keeping-game-code-portable). Consoles are
  available to registered developers.
- **Starters:**
  - Official templates, per the MonoGame docs (.NET 9 SDK or later recommended):
    `dotnet new install MonoGame.Templates.CSharp::3.8.5.1`, then `dotnet new mgdesktopgl`.
  - [MonoGame/MonoGame.Samples](https://github.com/MonoGame/MonoGame.Samples): Ms-PL; 743 stars;
    Platformer2D, NeonShooter and others.
  - [MonoGame/Starter-Kit-3D-Platformer](https://github.com/MonoGame/Starter-Kit-3D-Platformer):
    MIT; 16 stars; pushed 2026-09-21. A port of Kenney's Godot starter kit; its README says the
    sprites, models and sounds are CC0 and levels are edited in Blender. Its font (Lilita One) is SIL
    OFL 1.1: ship `Content/Assets/Font/license.txt` with the game.
  - The scaffolds list's only MonoGame entry is a Steam depot placeholder, not a game starter.
- **Art pipeline:** the content pipeline's standard importers read FBX (`FbxImporter`), DirectX `.x`,
  textures (.bmp, .dds, .dib, .hdr, .jpg, .pfm, .png, .ppm, .tga) and other 3D formats through the
  Open Asset Import Library (`OpenAssetImporter`). Catalog add-ons include GeonBit.UI, Apos.Gui and
  Penumbra (all MIT).
- **AI tooling:** no MonoGame MCP server met the bar.
- **Catalog:** 24 rows mention MonoGame, 7 `copy`.

## Defold (Lua)

- **License:** the [Defold License](https://defold.com/license/), version 1.0, derived from
  Apache-2.0 with one added condition: you may not "sell or otherwise commercialise the Work or
  Derivative Works as a Game Engine Product." Defold's own `llms.txt` calls it "free,
  source-available." Your games can be commercial and carry your own license: the summary says "You
  are free to commercialise any software created using original or modified (derivative) versions of
  Defold." GitHub's detector cannot identify the license. Latest release 1.13.1 (2026-08-17).
- **Suits:** 2D and 3D games for mobile, desktop, web and consoles, with an editor, Lua scripting
  and native extensions in C++.
- **Starters:** the editor's launch screen offers official templates (empty, mobile, desktop, basic
  3D); their repositories show no license file. [defold/template-platformer](https://github.com/defold/template-platformer)
  is MIT (4 stars, pushed 2026-01-28). None reach the scaffolds list's 25-star bar.
- **Art pipeline:** [atlases](https://defold.com/manuals/atlas/) combine separate images;
  [tile sources](https://defold.com/manuals/tilesource/) feed tilemaps, sprites and particles. 3D
  models, skeletons and animations import as [glTF 2.0](https://defold.com/manuals/importing-models/)
  (`.gltf` or `.glb`); export them from Blender.
- **AI tooling:** [defold.com/llms.txt](https://defold.com/llms.txt) links Markdown versions of the
  manuals, API and examples. Community MCP servers exist but none met the bar (the largest had 18
  stars).
- **Catalog:** 1 row mentions Defold (`copy`).

## three.js, PixiJS and Excalibur (web)

### three.js

- **License:** MIT. Latest release r186 (2026-09-08). A 3D library for browsers using WebGL and
  WebGPU, not a game engine: you supply the game loop, physics and input.
- **Starters:** [SahilK-027/threejs-gamedev-template](https://github.com/SahilK-027/threejs-gamedev-template)
  (Apache-2.0 code, 49 stars, pushed 2026-02-09). Its two character models in `public/assets/models/`
  are CC-BY-4.0 ("Zooba, Jade" and "Zooba, Nix"): credit the author as the two `license.*.txt` files
  there say, or better, replace them. React users can build on
  [pmndrs/react-three-fiber](https://github.com/pmndrs/react-three-fiber) (MIT, 32,444 stars).
- **Art pipeline:** the [manual](https://github.com/mrdoob/three.js/blob/dev/manual/pages/loading-3d-models.html)
  recommends glTF (`.glb` or `.gltf`) and names Blender among the tools that export it.
- **AI tooling:** [threejs.org/docs/llms.txt](https://threejs.org/docs/llms.txt) gives models
  current usage rules. No three.js MCP server is recommended here.
  [DmitriyGolub/threejs-devtools-mcp](https://github.com/DmitriyGolub/threejs-devtools-mcp) (MIT, 109
  stars, last push 2026-04-07) inspects and edits a running scene through a bridge it injects into a
  browser tab, but **its bridge (port 9222) listens on all network interfaces, even in stdio mode, and
  its HTTP transport (9223) does too, with CORS `*` and a `run_js` tool**; it has no setting to bind
  localhost. If you try it anyway: stdio only, a host firewall blocking 9222 and 9223, and a pinned
  `threejs-devtools-mcp@0.4.1`.
- **Catalog:** 15 rows mention three.js, 10 `copy`.

### PixiJS

- **License:** MIT. Latest release v8.21.0 (2026-09-17). A fast 2D rendering library with WebGL and
  WebGPU renderers; game structure is yours to add.
- **Starters:** `npm create pixi.js@1.4.0` ([pixijs/create-pixi](https://github.com/pixijs/create-pixi),
  MIT, 26 stars, pushed 2025-06-10), with presets such as `bundler-vite`, `creation-web` and
  `framework-react`.
- **Art pipeline:** the `Assets` loader loads textures, and the `spritesheet` module handles sheets;
  [pixijs/assetpack](https://github.com/pixijs/assetpack) (MIT, 168 stars) is an asset pipeline for the web.
- **AI tooling:** [pixijs.com/llms.txt](https://pixijs.com/llms.txt).
- **Catalog:** 9 rows mention PixiJS, 7 `copy`.

### Excalibur

- **License:** BSD-2-Clause. A 2D game engine written in TypeScript. Latest release v0.32.0
  (2025-12-23); its README warns that 0.x versions may still change the API.
- **Starters:** [excaliburjs/template-ts-vite](https://github.com/excaliburjs/template-ts-vite)
  (BSD-2-Clause, 39 stars, pushed 2026-09-23) or `npx create-excalibur@2.0.0`
  ([create-excalibur](https://github.com/excaliburjs/create-excalibur), BSD-2-Clause; its README
  says `@latest`).
- **Art pipeline:** official plugins for [Tiled](https://github.com/excaliburjs/excalibur-tiled)
  (BSD-2-Clause, 55 stars), [Aseprite](https://github.com/excaliburjs/excalibur-aseprite) and
  [LDtk](https://github.com/excaliburjs/excalibur-ldtk) files.
- **AI tooling:** create-excalibur 2.0.0 (2026-08-29) adds an official MCP server, `create-excalibur
  mcp`, over stdio with no listener: docs search, code generation, and in-place edits and codemod
  upgrades of your project's files. Its docs search queries the live docs site by default and falls
  back to an offline cache. Register it pinned: `claude mcp add excalibur -- npx -y create-excalibur@2.0.0 mcp`
  (its README omits the version), commit before an agent runs `upgrade`, and see the
  [safe setup checklist](../ai/graphics.md#safe-setup-checklist).
- **Catalog:** 1 row (Excalibur itself, `copy`).

## Summary

| engine | license | language | best for | starter template |
|---|---|---|---|---|
| Bevy | MIT or Apache-2.0 | Rust | code-first 2D and 3D in an ECS | [bevy_new_2d](https://github.com/TheBevyFlock/bevy_new_2d) via `bevy new` |
| Phaser | MIT | JavaScript, TypeScript | 2D browser games | `npm create @phaserjs/game@1.3.2` |
| LÖVE | zlib | Lua | small 2D games and jams | [bootstrap-love2d-project](https://github.com/Oval-Tutu/bootstrap-love2d-project) |
| raylib | Zlib | C, 70+ bindings | learning; small 2D and 3D in code | [raylib-game-template](https://github.com/raysan5/raylib-game-template) |
| MonoGame | Ms-PL plus MIT | C# | 2D frameworks in C#; a portable C# core | `dotnet new mgdesktopgl` |
| Defold | Defold License (source-available) | Lua | 2D and 3D with an editor, mobile and web | the editor's templates |
| three.js | MIT | JavaScript | 3D in the browser | [threejs-gamedev-template](https://github.com/SahilK-027/threejs-gamedev-template) (replace its CC-BY models) |
| PixiJS | MIT | TypeScript, JavaScript | fast 2D rendering on the web | `npm create pixi.js@1.4.0` |
| Excalibur | BSD-2-Clause | TypeScript | 2D web games in TypeScript | [template-ts-vite](https://github.com/excaliburjs/template-ts-vite) |
