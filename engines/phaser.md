# 2D, sprite and isometric games with Phaser 4

When to build a browser 2D game on Phaser, which versions to pin, how isometric and hex maps work
now, and what AI tooling exists. For browser 3D see [threejs-r3f.md](threejs-r3f.md); starter
templates, the asset loader and Phaser's `llms.txt` are in [others.md](others.md#phaser-javascript-and-typescript).

Versions and dates were checked on 2026-10-01 against npm and each project's GitHub releases.

## When to choose it

- **Choose it** for 2D in the browser: arcade, platformer, puzzle, card, top-down and isometric
  games, with sprites, tile maps, cameras, input, sound and two physics engines (Arcade and Matter)
  built in. It is TypeScript-friendly and has no editor binary, so an AI coding tool works on plain
  files.
- **Choose something else** for 3D ([threejs-r3f.md](threejs-r3f.md) or [Godot](godot.md)), or when
  you want a visual editor for scenes and animation: Phaser Editor exists but is paid (below).
  For a smaller, simpler 2D library, Kaplay and Excalibur are in [others.md](others.md).

## Pinned versions

| tool | version, checked 2026-10-01 | license | notes |
|---|---|---|---|
| [Phaser](https://github.com/phaserjs/phaser) | 4.2.1 ([2026-07-09](https://github.com/phaserjs/phaser/releases/tag/v4.2.1)) | MIT | Phaser 4 is the stable line: [4.0.0](https://github.com/phaserjs/phaser/releases/tag/v4.0.0) shipped 2026-04-10. Start new games on 4, not 3 |
| [Tiled](https://github.com/mapeditor/tiled) | [v1.12.2](https://github.com/mapeditor/tiled/releases/tag/v1.12.2) (2026-05-27) | editor GPL-2.0, `libtiled` BSD-2-Clause | the map editor Phaser reads (JSON or CSV export) |

```sh
npm install --save-exact phaser@4.2.1
```

Official templates pin Phaser 4.0.0 in `package.json`; move them to the version you tested. Their
default `dev` and `build` scripts send a usage ping: see
[../scaffolds/README.md](../scaffolds/README.md#how-to-choose), step 5.

## Tile maps, isometric and hex

- **Orthogonal, isometric, staggered and hexagonal Tiled maps are built into Phaser** (since 3.50):
  load the Tiled JSON with `this.load.tilemapTiledJSON` and create layers as usual. The 2018
  community isometric plugin is unmaintained; do not start with it.
- **Depth in isometric scenes** is yours to manage: sort sprites by their screen `y` (or a computed
  depth) every frame so characters pass behind walls correctly.
- **Pixel art:** set `pixelArt: true` in the game config (nearest-neighbor filtering, rounded
  positions) and scale by whole numbers.
- **Sheets and atlases** come from Aseprite JSON exports, free-tex-packer or similar; see
  [../art/2d.md](../art/2d.md#sprite-sheets-and-texture-atlases). For 3D models rendered to
  isometric sprites, see [../art/blender.md](../art/blender.md#3d-to-2d-sprite-sheets-and-isometric-tiles).

## Web constraints

- Phaser renders with WebGL and falls back to Canvas. Audio unlocks only after a user gesture.
- Output is static files; no special server headers are needed.
- Test on a phone early: texture memory and many large tile layers are where 2D browser games slow
  down. Pack atlases and keep tile layers few.

## AI tooling

- **Phaser publishes two official MCP servers, checked 2026-10-01:**
  - **Phaser Game Agent MCP** ([phaser.io/agent/mcp](https://phaser.io/agent/mcp);
    [phaserjs/phaser-game-agent](https://github.com/phaserjs/phaser-game-agent), MIT; npm
    `@phaserjs/game-agent` 1.0.0, published 2026-07-01). It does not need the editor: it connects your
    coding agent to a hosted service that builds the game in a Phaser cloud sandbox, billed in credits
    per minute and per generated image or sound. Its setup command signs you in to a Phaser account and
    writes the MCP configuration of every AI client it detects. **Your prompts go to Phaser's service,
    and its page says your projects live in that cloud sandbox**, not in your local repository. If you
    try it, pin
    `npx -y @phaserjs/game-agent@1.0.0`, use its `manual` command to print a config you add yourself,
    and read its terms first.
  - **Phaser Editor MCP**, which works only with a running Phaser Editor v5, a paid, proprietary
    desktop app ([phaser.io/editor](https://phaser.io/editor); listed at $12 a month on 2026-10-01).
    See [others.md](others.md#phaser-javascript-and-typescript) for its pin and why it is not
    recommended here.
- **You do not need an MCP server to build a Phaser game.** The game is TypeScript an agent edits
  directly. Name the pinned version in the game's `AGENTS.md` and say "Phaser 4": models trained
  mostly on Phaser 3 code produce APIs that changed. [phaser.io/llms.txt](https://phaser.io/llms.txt)
  is an index of the examples, not usage rules or Phaser 3 to 4 migration notes, so pair it with the
  [Phaser 4 release notes](https://github.com/phaserjs/phaser/releases/tag/v4.0.0).
- **Check the game in a browser, not from source.** A Playwright test that loads the page, plays a
  scripted input sequence and saves screenshots gives the agent something to verify against.
- Anything that runs code on your machine goes through the
  [safe setup checklist](../ai/graphics.md#safe-setup-checklist) first.

## Risks

1. **Phaser 3 habits:** tutorials, plugins and model output often assume Phaser 3. Check each plugin
   supports Phaser 4 before you add it.
2. **Template telemetry:** the official templates' default scripts call a Phaser Studio domain; use
   the `-nolog` scripts or remove `log.js`.
3. **Tiled is GPL:** that covers the editor, not the maps you make; `libtiled` is BSD.
