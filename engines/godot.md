# Building with Godot 4

How to take a game from this chassis to a tested, exported Godot 4 build: what the engine is good and
weak at, project layout, art from Blender and 2D tools, open-source templates to start from, exporting
and CI, and letting AI tools work on the project without handing them your machine.

Checked on 2026-09-23 against Godot 4.7.2-stable (latest stable, 2026-08-18), the stable docs (which
describe 4.7) and every repository named here. We ran the commands on a probe project with the official
Linux build: headless import, `--check-only`, the script checker below, GUT 9.7.1, and Web and Linux
exports; where a sentence says what a command did, it did that there. Stars and dates are a snapshot.

## Why Godot, and when not to

**License.** Godot is MIT (GitHub reports `MIT` for [godotengine/godot](https://github.com/godotengine/godot)),
with no fees or royalties. The one requirement is to include Godot's license text in your game, such as
on a credits screen; the docs page "Complying with licenses" gives the text and notes that Godot bundles
third-party libraries with notices of their own. Your game can use any license, commercial included.

**Good at:** one editor for 2D and 3D, with pixel-based 2D tools (`TileMapLayer`, `SpriteFrames`, stretch
settings for pixel art); plain-text scenes (`.tscn`), resources (`.tres`) and `project.godot` that diff in
git and that AI tools can read; a headless command line that imports, runs scripts and tests, and exports;
direct glTF 2.0 and `.blend` import; export to Windows, macOS, Linux, Web, Android and iOS.

**Weak at:**
- **Web:** WebGL 2 through the Compatibility renderer only (Forward+ and Mobile do not run on the web; no
  WebGPU). C# projects cannot export to the web at all in Godot 4.
- **Consoles:** no official ports. The Godot website says consoles need NDAs and official SDKs, so you need
  the platform holder's approval, then your own port or licensed third-party middleware.
- **C# on mobile:** Android and iOS support arrived in 4.2 and the docs still call it experimental.
- **`.blend` import** needs Blender on every machine that imports the project, CI runners included.

For a proprietary engine see [unity.md](unity.md) (Unity is not open source; even its C# reference source
is under a reference-only license); for code-first engines, [others.md](others.md).

## Project structure and conventions

```text
project.godot  AGENTS.md  THIRD_PARTY.md  export_presets.cfg
addons/                 # third-party plugins, one folder each
assets/                 # exported, engine-ready files the game loads: .glb, .png, .ogg
characters/player/      # player.tscn and player.gd together, grouped by feature
levels/  ui/  test/  tools/check_scripts.gd
art-src/.gdignore       # sources: .blend, .kra, .xcf, .aseprite, .svg masters; never imported
build/.gdignore         # export output; see "Exporting"
```

Art sources live in `art-src/`, outside the import path: beside the project folder when you can,
or inside it with an empty `.gdignore` as above. Export from there into `assets/`.

From Godot's "Project organization" and "Version control systems" pages:
- **`snake_case` files and folders** (C# scripts take their PascalCase class name), **PascalCase node
  names**. The exported pack is case sensitive where Windows and macOS are not, so a wrong-case path
  works in the editor and breaks in the build.
- **Third-party code in a top-level `addons/`.** An empty **`.gdignore`** stops Godot importing a folder
  (no patterns; nothing in it can be loaded).
- **Ignore `.godot/`**, the cache; the project manager's Git option writes a `.gitignore` of `.godot/` and
  `/android/`. **Commit `.import` and `.uid` files:** since 4.4 Godot writes `name.gd.uid` beside each
  script and shader (our import made one per script), and without them other machines fall back to paths.
- **Commit `export_presets.cfg`; never commit `.godot/export_credentials.cfg`** (passwords, encryption
  keys). Set up Git LFS for big art before the first art commit.

## Importing art

**3D from Blender.** Blender is GPL, and [its license page](https://www.blender.org/about/license/) says
"What you create with Blender is your sole property", `.blend` files included: the GPL covers the tool,
not your models. Modeling and export are in [../art/blender.md](../art/blender.md).

- **glTF 2.0 is Godot's recommended format** (`.glb`, or `.gltf` plus `.bin` for text diffs). FBX imports
  through ufbx; OBJ has no skeletons, animation or PBR materials.
- **`.blend` directly:** Godot runs Blender's glTF exporter on import. It needs Blender 3.0 or later (3.5
  or later recommended), ideally an official blender.org build, not a distro or Flatpak package. The CI
  image below has no Blender, and `.blend` files in `art-src/` are never imported: export `.glb` into
  `assets/` and commit it.
- **Name suffixes build nodes:** `-col` adds collision, `-colonly` and `-convcolonly` make collision only,
  `-noimp` skips the object, `-navmesh` and `-occ` make navigation and occluder meshes. In Blender,
  enable Backface Culling on materials or Godot imports them with culling disabled; with shape keys, set
  the glTF option **Data > Armature > Export Deformation Bones Only**.
- **[Goblend](https://github.com/Togira123/Goblend-Export-Addon)** (one-click Blender to Godot export) is
  GPL-3.0, `study only`; its Godot half sits in your project, so exclude it from exports (see "Plugins").
  Both halves are add-ons that run code inside Blender and the Godot editor with your permissions; its
  README describes no network listener. Read both and pin a release (v2.1.1 on 2026-09-23).

**Textures and pixel art.** 2D imports default to Lossless compression without mipmaps; **Detect 3D**
switches a texture to VRAM Compressed with mipmaps once a 3D material uses it. For pixel art set
`rendering/textures/canvas_textures/default_texture_filter` to **Nearest** (the default, Linear, blurs),
`display/window/stretch/mode` to `viewport` and `display/window/stretch/scale_mode` to `integer` (4.2+),
and optionally `rendering/2d/snap/snap_2d_transforms_to_pixel` (crisper, less smooth motion). Keep
Compress Mode on **Lossless**, the docs' advice for pixel art; for pixel textures in 3D set
**Detect 3D > Compress To** to Lossless first. Setting names checked in the 4.7.2 class reference.

**Sheets, atlases and tiles.** `SpriteFrames` on an `AnimatedSprite2D` for animation, `AtlasTexture` for a
region, Import As **TextureAtlas** to pack images (2D only), and a `TileSet` with a `TileSetAtlasSource`
painted with `TileMapLayer`. Making sheets in GIMP, Krita, Inkscape and pixel tools: [../art/2d.md](../art/2d.md).

**AI-generated art.** Record the tool, model, prompt, date and the generator's terms in the game repo's
`THIRD_PARTY.md`, in its section "AI-generated and AI-assisted assets"
([template](../templates/THIRD_PARTY.md#ai-generated-and-ai-assisted-assets)), not in a separate file. Whether you can own or license the
output depends on those terms and your jurisdiction: treat it as `check first` until you know. The
Godot Asset Store requires authors to disclose AI use. More in [../ai/graphics.md](../ai/graphics.md).

## Starting from a scaffold

The best-maintained general templates and three genre kits in [../scaffolds/scaffolds.md](../scaffolds/scaffolds.md).
All code is MIT; "Godot" is the version the repository's `project.godot` declares.

| scaffold | Godot | stars, last push | what it gives you | watch for |
|---|---|---|---|---|
| [Maaack/Godot-Game-Template](https://github.com/Maaack/Godot-Game-Template) | 4.7 (4.4+) | 1,658, 2026-09-10 | main, options and pause menus, credits, loading screen, persistent settings, gamepad, music and UI sound controllers, level loader, win and lose screens, basic save, itch.io upload script, GitHub Actions build-and-publish workflow | saves are resource files; its own docs warn they can carry injected scripts. Its plugin logo (every `plugin_logo/logo.png`) is CC BY-NC-ND 4.0: replace it before shipping |
| [crystal-bit/godot-game-template](https://github.com/crystal-bit/godot-game-template) | 4.7 | 980, 2026-06-21 | scene changes with transitions and parameters, threaded loading with a single-thread web fallback, audio, language, resolution and FPS settings in `ConfigFile`, gettext localization, debug keys stripped from release builds, GitHub Actions builds and GitHub Pages deploy | no save-game system in its feature list |
| [bitbrain/godot-gamejam](https://github.com/bitbrain/godot-gamejam) | 4.7 | 811, 2026-08-19 | settings, boot splash, menus, pause, JSON save of the `Persist` group, CSV translations, itch.io deploy | its workflow uses `manleydev/butler-publish-itchio-action@master`: pin it |
| [chickensoft-games/GodotGame](https://github.com/chickensoft-games/GodotGame) | 4.7, C# | 420, 2026-09-10 | `dotnet new` template, GoDotTest tests run inside the game, coverage, CI visual tests on Ubuntu with Mesa, spell check, Renovate | no menus; C# limits apply |
| [stesproject/godot-2d-topdown-template](https://github.com/stesproject/godot-2d-topdown-template) | 4.7 (4.4+) | 190, 2026-09-07 | top-down controller, health, interactions, state machines, inventory, dialogue, save and load, debug panel | saves are `.tres` and `.res` resource files |
| [KenneyNL/Starter-Kit-3D-Platformer](https://github.com/KenneyNL/Starter-Kit-3D-Platformer) | 4.6 | 1,235, 2026-03-12 | 3D platformer controller with double jump, coins, falling platforms, a camera you rotate and zoom, gamepad; CC0 sprites, models and sounds | small by design; its font (Lilita One) is SIL OFL 1.1: ship `fonts/license.txt` with the game |
| [nezvers/Godot-GameTemplate](https://github.com/nezvers/Godot-GameTemplate) | 4.7 | 1,651, 2026-06-18 | top-down shooter: menus, input rebinding, pooling, A* enemies, waves, resource saving | art is under the author's own terms (commercial use, no resale), not MIT; README says not for beginners |
| [godotengine/godot-demo-projects](https://github.com/godotengine/godot-demo-projects) | varies | 9,559, 2026-09-08 | official demos of each subsystem | `master` tracks Godot's development branch; version branches stop at 4.3 |

- **Pick** Maaack or crystal-bit for menus, settings and CI, or a genre kit beside your playbook; skip
  archived rows (sempitern0/indie-blueprint). **Record the source commit in `THIRD_PARTY.md`** with the
  MIT notice. Asset licenses are separate: Maaack's plugin logo is CC BY-NC-ND 4.0 (non-commercial, no
  changes), and the Godot logo (CC BY 4.0) and Git logo (CC BY 3.0) it ships need credit; Kenney's art
  is CC0 but the kit's font is SIL OFL 1.1; nezvers' art is not MIT.
- **Replace a save system that loads `.tres` or `.res` from `user://`** before players can share saves.
  Godot's class reference warns that deserialized objects "can contain code which gets executed"
  (`FileAccess.get_var(true)`, `bytes_to_var_with_objects`). Use JSON, as Godot's saving tutorial does.

## Exporting

Install export templates, create presets in Project > Export, and export headless with a preset name
from `export_presets.cfg`: `godot --headless --export-release "Web" build/web/index.html`.

- **Put an empty `.gdignore` in the output folder.** We exported Web into `build/web/`, then Linux: the
  Linux pack had imported the web build's PNGs (27 KB instead of 3 KB). With `build/.gdignore`, 3 KB.
- **Keep tests and editor-only add-ons out** with the preset's exclude filter (`test/*, addons/gut/*`);
  our packs then held no test or GUT files.

**Web.**
- **Single-threaded is the default and preferred mode** since 4.3: more compatible with itch.io, Poki
  and CrazyGames, and good on macOS and iOS. Our 4.7.2 export set `GODOT_THREADS_ENABLED = false`.
- **Thread Support needs cross-origin isolation:** `Cross-Origin-Opener-Policy: same-origin` and
  `Cross-Origin-Embedder-Policy: require-corp`, served from a secure context (HTTPS; localhost is usually
  exempt). Without header control, **Progressive Web App > Enable** simulates them with a service worker,
  still over HTTPS. With neither, a threaded build does not start.
- **Limits:** clipboard and gamepad need a secure context; saves live in IndexedDB, so players must allow
  cookies (third-party cookies in an iframe) and private browsing loses them; audio defaults to Sample
  playback, with no AudioEffects, reverb, doppler or procedural audio unless you choose Stream.
- **Serving:** our `.wasm` was 39.5 MB. Serve it as `application/wasm`, compressed (GitHub Pages gzips,
  itch.io does not), keep exported file names, and test with the docs' `python serve.py --root .`.

**Desktop and mobile.** macOS apps downloaded from the internet are blocked by Gatekeeper unless signed and
notarized, which needs an Apple Developer ID certificate. Android needs OpenJDK 17, the Android SDK (the
docs list Platform 35, Build-Tools 35.0.1) and your own release keystore, never committed; C# Android
needs .NET 9 or later. iOS exports from macOS with Xcode.

## CI export with GitHub Actions

Maintained options, all MIT: **[abarichello/godot-ci](https://github.com/abarichello/godot-ci)** (1,128
stars, pushed 2026-08-18), a Docker image per Godot version (`4.7.2`, `mono-4.7.2`) with export
templates, butler and the Android SDK, no iOS or Blender; **[firebelley/godot-export](https://github.com/firebelley/godot-export)**
(v8.0.0), which exports every preset in `export_presets.cfg`; **[chickensoft-games/setup-godot](https://github.com/chickensoft-games/setup-godot)**
(v2.4.2), which installs Godot (.NET build and templates optional) on Linux, macOS and Windows runners.

A workflow on the first. We ran its `run` script locally with passing tests, a failing test, no tests
and a type error; it exited 0 only for the first.

```yaml
name: build
on: [push]
permissions: { contents: read }
jobs:
  build:
    runs-on: ubuntu-24.04
    container:
      image: barichello/godot-ci:4.7.2  # digest: @sha256:cdcca31e9194fd59a68a63f4b1b9c3981716819c520cd6f7966c5d72ca7246bd
    defaults: { run: { shell: bash } }  # adds pipefail; without it a failing test piped to tee passes
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1
        with: { lfs: true }
      - run: |
          mkdir -p ~/.local/share/godot/export_templates ~/.config
          mv /root/.local/share/godot/export_templates/4.7.2.stable ~/.local/share/godot/export_templates/
          mv /root/.config/godot ~/.config/godot
      - run: |
          godot --headless --import
          godot --headless --script res://tools/check_scripts.gd
          godot --headless -d -s --path "$PWD" addons/gut/gut_cmdln.gd -gdir=res://test -ginclude_subdirs -gexit | tee gut.log
          if grep -q 'Nothing was run' gut.log; then echo "no tests ran"; exit 1; fi
          mkdir -p build/web build/linux && touch build/.gdignore
          godot --headless --export-release "Web" build/web/index.html
          godot --headless --export-release "Linux" build/linux/game.x86_64
      - uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a  # v7.0.1
        with: { name: builds, path: build }
```

GitHub adds `pipefail` only when the shell is named: under `sh -e` a failing test exited 0. Pin actions to
a SHA and the image to a digest; keys, keystores and passwords go in Actions secrets, never in the repo.

## Plugins: the Asset Store and the Asset Library

The [Godot Asset Store](https://store.godotengine.org) is in beta and succeeds the Asset Library, which is
still online; assets were not moved over. **Licenses vary:** the Store requires the listed license to match
a `LICENSE` file with a copyright line in the asset's repository, and requires AI-use disclosure. Apply the
reuse classes: a GPL add-on shipped in your game is GPL code you distribute, so exclude it from exports or
pick a permissive one. **Plugins run code:** editor plugins and `@tool` scripts execute in the editor with
your permissions once enabled. Read one first, pin a release or commit, and list it in `THIRD_PARTY.md`;
the [safe setup checklist](../ai/graphics.md#safe-setup-checklist) applies to every add-on here, the test
frameworks below included (GUT v9.7.1 and gdUnit4 v6.2.1 were the latest tags on 2026-09-23).

## GDScript or C#

**GDScript** is built into every Godot download, exports everywhere including the web, and is what
most templates, add-ons and AI tools here assume; godot-ai parse-validates and hot-reloads scripts it
writes. **C#** needs the .NET build of Godot plus the .NET SDK (the docs say .NET 8 or later; Android
export needs .NET 9), cannot export to the web in Godot 4, is experimental on Android and iOS, tests with
gdUnit4Net or GoDotTest (both MIT), and godot-ai writes `.cs` as text it does not build. Choose GDScript
unless you need .NET libraries or a C# team; for C#, start from chickensoft-games/GodotGame.

## AI tooling

**Point Claude Code or Codex at the project.** Copy [../templates/AGENTS.md](../templates/AGENTS.md) into
the game repository and add the block below; [../ai/README.md](../ai/README.md) covers one instruction file
and checking each tool loaded it. Keep this chassis beside the game (`claude --add-dir ../opensource`;
Codex reads siblings without a flag). Give agents commands that fail loudly. Two do not, on 4.7.2:
`--import` exits 0 with broken scripts, and `--check-only --script` reports any script using an autoload
as broken ("Identifier not found: GameState"). This checker compiles with autoloads registered; it failed
on a type error and a parse error, and counted the same six scripts `find` did. Loading runs `_static_init()`.

```gdscript
extends SceneTree
# tools/check_scripts.gd: compiles every .gd outside addons/, with autoloads registered.
var checked := 0
var failed := 0

func _initialize() -> void:
	_walk("res://")
	print("checked %d scripts, %d failed" % [checked, failed])
	quit(1 if failed > 0 or checked == 0 else 0)

func _walk(dir: String) -> void:
	for sub in DirAccess.get_directories_at(dir):
		if sub != "addons" and not sub.begins_with("."):
			_walk(dir.path_join(sub))
	for file in DirAccess.get_files_at(dir):
		if file.ends_with(".gd"):
			checked += 1
			var script := load(dir.path_join(file)) as Script
			if script == null or not script.can_instantiate():
				failed += 1
				printerr("FAIL ", dir.path_join(file))
```

**An AGENTS.md block for a Godot game:**

```markdown
## Godot
- Godot 4.7.2, GDScript, Compatibility renderer. Never upgrade the engine inside a feature change.
- Import: `godot --headless --import` (exit 0 does not mean scripts compile).
- Compile: `godot --headless --script res://tools/check_scripts.gd`. Never `--check-only` scripts that use autoloads.
- Test: `godot --headless -d -s --path "$PWD" addons/gut/gut_cmdln.gd -gdir=res://test -ginclude_subdirs -gexit`;
  "Nothing was run" in the output is a failure.
- Edit `.tscn`/`.tres` by hand only for small property changes; keep `ext_resource` ids and `uid://` values.
- Commit `.uid` and `.import` files; never `.godot/`. snake_case files, PascalCase nodes. `addons/` is
  third-party: unedited, listed in THIRD_PARTY.md.
- Saves are JSON or ConfigFile; never load a `.tres`, `.res` or object-encoded file a player could edit.
```

**The language server.** A running editor serves GDScript's language server on 127.0.0.1:6005 and the
debug adapter on 127.0.0.1:6006 by default; a headless editor (`--headless --editor --lsp-port <port>`)
listened on both, loopback only. Claude Code's LSP plugins run servers over stdio and Godot's listens on
TCP, so they need a bridge; minimal-godot-mcp, below, bridges it to MCP instead.

**MCP servers.** From [../scaffolds/mcps.md](../scaffolds/mcps.md), maintained ones first. Each row says
what the server listens on, what it runs and what leaves your machine; go through the
[safe setup checklist](../ai/graphics.md#safe-setup-checklist) before you install any of them.

| server | license | stars, last push | how it connects | what it can do | risk, and a pinned install |
|---|---|---|---|---|---|
| [ryanmazzolini/minimal-godot-mcp](https://github.com/ryanmazzolini/minimal-godot-mcp) | MIT | 47, 2026-09-01 | stdio; connects to the running editor's LSP and DAP ports and opens none of its own | four read-only tools: diagnostics for a file or the project, console output. The safest first server | runs nothing inside Godot. `npx -y @ryanmazzolini/minimal-godot-mcp@0.1.6` |
| [hi-godot/godot-ai](https://github.com/hi-godot/godot-ai) | MIT | 2,570, 2026-09-23 | editor add-on plus a Python server run by `uvx`; the client attaches over stdio, then HTTP on 127.0.0.1:8000 and a loopback-only WebSocket on 9500, both authenticated with rotating tokens | 46 tools, 120+ operations: scenes, nodes, scripts, signals, UI, materials, animation, file write and remove, `game_eval`. Godot 4.7+ | `game_eval` runs any GDScript. Usage telemetry is on unless `GODOT_AI_DISABLE_TELEMETRY=true`. Its README says the tokens do not stop a compromised process running as you. Install a release (v4.2.1 on 2026-09-23) with its verification steps; **decline the dock's one-click Update**, which also rewrites your client entries, and move to a new release only after reading its diff |
| [satelliteoflove/godot-mcp](https://github.com/satelliteoflove/godot-mcp) | MIT | 169, 2026-09-18 | npx server; the editor add-on listens on a WebSocket at 127.0.0.1:6550 and reaches the game through Godot's debugger | 21 tools: scene edits, input injection, frozen and stepped game time, runtime state as JSON, profiling, `godot_exec` (GDScript in the game); read and write tools are separate | **the WebSocket has no authentication and no `Origin` check** (`websocket_server.gd`), so any program on your machine that connects first can call `godot_exec`. Keep the bind mode on Localhost: the WSL and Custom modes put that open socket on another interface. `npx -y @satelliteoflove/godot-mcp@4.1.11`, and install the add-on with the same version's `--install-addon` |
| [Erodenn/godot-mcp-runtime](https://github.com/Erodenn/godot-mcp-runtime) | MIT | 77, 2026-09-20 | npx server, no add-on: headless edits, and while the game runs an injected `McpBridge` autoload listening on 127.0.0.1 | screenshots, input, UI discovery, live GDScript, profiling | the bridge checks a per-session token, but the profiling channel has none, and its docs call the script scanner "not a sandbox". Leave `GODOT_MCP_DISABLE_SECURITY` unset, and commit before a run, since it injects an autoload into your project. `npx -y godot-mcp-runtime@3.8.0` |
| [IvanMurzak/Godot-MCP](https://github.com/IvanMurzak/Godot-MCP) | Apache-2.0 | 253, 2026-09-23 | C# editor add-on, **through a hosted relay at ai-game.dev by default**; signing in stores a credential in `~/.ai-game-dev/credentials.json` | 42 tools, including calling any C# method by reflection | set `GODOT_MCP_CONNECTION_MODE=Custom` and a loopback `GODOT_MCP_HOST`. In that mode the dock's Start Server downloads a pinned server build from GitHub; it binds loopback and checks `Origin`, but has no authentication unless you configure OAuth. Install a tagged release (v0.24.0 on 2026-09-23), not the README's `releases/latest` link |
| [Coding-Solo/godot-mcp](https://github.com/Coding-Solo/godot-mcp) | MIT | 5,802, 2026-04-16 | stdio npx server calling Godot's CLI and a bundled `godot_operations.gd`; opens no port | launch the editor, run the project, capture debug output, create scenes, add nodes; the most starred | **no pushes since 2026-04-16, and open issue #118 (2026-06-17, unanswered) reports published CVEs in its exact-pinned MCP SDK 0.6.0 and in axios.** Prefer the servers above. Its README runs it unpinned; if you use it, `npx -y @coding-solo/godot-mcp@0.1.1` |

Add one pinned; Claude Code's `--scope project` writes `.mcp.json`, approved on your next `claude` run:

```sh
claude mcp add --scope project godot-lsp -- npx -y @ryanmazzolini/minimal-godot-mcp@0.1.6
codex mcp add godot-lsp -- npx -y @ryanmazzolini/minimal-godot-mcp@0.1.6
```

`@0.1.6` pins the package, not its dependencies: they are `^` ranges that npm resolves again on a cold
cache. For a fixed set, install it into a folder outside the Godot project with a committed
`package-lock.json` (`npm ci` there) and register `node <folder>/node_modules/@ryanmazzolini/minimal-godot-mcp/dist/index.js`.

**Security: MCP servers and add-ons run code on your machine with your permissions.**
- **Anything that can write and run a script or evaluate GDScript** (`game_eval`, `godot_exec`) can do
  what your account can: read files, reach the network, delete things.
- **Prefer maintained projects and read the code**, server and add-on (ee0pdt/Godot-MCP has not been
  pushed since 2025-03-19). **Pin** a version, tag or SHA; never a bare package, `@latest` or `@master`,
  and decline in-editor updates.
- **Least privilege:** start read-only, approve writes one at a time, commit before an agent edits scenes.
- **Never expose an MCP server to the network:** keep binds on 127.0.0.1, open no ports, use SSH for a
  remote editor, and refuse any `0.0.0.0` listener. Loopback does not stop other programs on your own
  machine, which is why an unauthenticated socket such as satelliteoflove's matters.
- **Know where traffic goes:** IvanMurzak's default relay sends tool traffic off your machine, godot-ai's
  default telemetry sends usage events, and its Configure button can rewrite a checked-in `.mcp.json`.
- The rest is in the [safe setup checklist](../ai/graphics.md#safe-setup-checklist).

## Testing

- **[GUT](https://github.com/bitwes/Gut)** (2,739 stars, pushed 2026-08-18) is MIT in
  `addons/gut/LICENSE.md`; GitHub's API reports no license because the file is not at the root. GUT 9.7.1
  (branch `godot_4_7`) targets 4.7. On 4.7.2 it exited 0 with passing tests, 1 with a failing test, and
  **0 with "Nothing was run" for an empty or misspelled test folder**, hence the grep in CI.
- **[gdUnit4](https://github.com/godot-gdunit-labs/gdUnit4)** (MIT, 1,241 stars, pushed 2026-08-30): GDScript
  and C# tests, a scene runner that simulates mouse, keyboard, touch and input actions and waits for
  signals, a command-line runner and an official GitHub Action; its table lists v6.2.x for Godot 4.5 to
  4.7.1. For C#: [gdUnit4Net](https://github.com/godot-gdunit-labs/gdUnit4Net) or [GoDotTest](https://github.com/chickensoft-games/GoDotTest), both MIT.

Prefer end-to-end checks: a scene-runner test or scripted playtest that plays the loop from start to game
over proves more than unit tests the same agent wrote beside the code.

## Pitfalls

1. **Exit codes that mislead:** `--import` and GUT's "Nothing was run" exit 0, so does a failing run piped
   through `tee` without `pipefail`, and `--check-only` fails correct code that uses autoloads.
2. **Exporting inside the project** packs the last build into the next; add `.gdignore`.
3. **Case mismatches** work in the editor and break in the exported pack.
4. **`.blend` files fail in CI** without Blender; **resource-file saves** can run code from a shared save.
5. **Threaded web builds** do not start without isolation headers or the PWA workaround.
6. **A template's code license is not its art license.**

## Genre playbooks

All 17 playbooks name Godot as an engine option. These also point to Godot projects, add-ons or docs:
[adventure](../playbooks/adventure.md) (Escoria, Dialogic), [board and card](../playbooks/board-card.md)
(Tabletop Club and the Godot Card Game Framework, both Godot 3), [fighting](../playbooks/fighting.md)
(Sakuga-Engine, FightEngine), [racing](../playbooks/racing.md) (`VehicleBody3D`, netfox),
[rhythm](../playbooks/rhythm.md) (the docs page "Sync the gameplay with audio and music"),
[RPG](../playbooks/rpg.md) (TetraForce, Dialogic), [shooter](../playbooks/shooter.md) (the TPS demo),
[sports](../playbooks/sports.md) (netfox) and [strategy](../playbooks/strategy.md) (OpenCiv3, GDHexGrid).
The rest name it as an option: [action](../playbooks/action.md), [arcade](../playbooks/arcade.md),
[educational](../playbooks/educational.md), [platformer](../playbooks/platformer.md),
[puzzle](../playbooks/puzzle.md), [roguelike](../playbooks/roguelike.md),
[sandbox](../playbooks/sandbox.md) and [simulation](../playbooks/simulation.md).
