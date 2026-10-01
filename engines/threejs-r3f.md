# Browser 3D with three.js and React Three Fiber

When to build a browser 3D game on three.js with React Three Fiber (R3F), which versions to pin,
what WebGPU does and does not give you yet, and what AI tooling exists. For 2D, sprite and isometric
games see [phaser.md](phaser.md); for a bigger 3D game that still ships to the browser, see
[Godot on the web](godot.md#godot-on-the-web-when-to-choose-it). Other web libraries (Babylon.js,
PlayCanvas, PixiJS, Excalibur) are in [others.md](others.md).

Versions and dates were checked on 2026-10-01 against npm and each project's GitHub releases. Stars
and dates are a snapshot.

## When to choose it

- **Choose it** for a 3D game or interactive scene you build in-house in the browser, where you want
  the whole thing in TypeScript, in one repository an AI coding tool can read and edit as plain
  files, with no editor binary in the loop.
- **R3F** suits a team or agent that already writes React: scenes are components, state lives in
  ordinary React state or a store, and UI overlays are plain React. Plain three.js (no React) is the
  same renderer with less structure; pick it for a small scene or a non-React app.
- **Choose something else** when you need an editor for level layout and animation state machines,
  a large world with streaming, or native and console builds: a full engine such as
  [Godot](godot.md) fits better. three.js is a rendering library, not a game engine: you supply the
  game loop, physics, input, audio and save.

## Pinned versions

| package | version, checked 2026-10-01 | license | notes |
|---|---|---|---|
| [three](https://github.com/mrdoob/three.js) | r186 (`three@0.186.1`, 2026-09-24; r186 itself 2026-09-08) | MIT | the renderer. Its npm versions are `0.<release>.<patch>` |
| [@react-three/fiber](https://github.com/pmndrs/react-three-fiber) | 9.8.1 (2026-09-24) | MIT | React renderer for three.js; v9 pairs with React 19. A 10.0 canary exists: do not use it in a game you ship |
| [@react-three/drei](https://github.com/pmndrs/drei) | 10.7.9 (2026-09-25) | MIT | helpers: cameras, controls, loaders, text, environment maps |
| [@react-three/rapier](https://github.com/pmndrs/react-three-rapier) | 2.2.0 (2025-11-03) | MIT | Rapier physics for R3F. **No release since 2025-11-03** (1,436 stars, last push the same day): check that it still works with the R3F and three versions you pin before you depend on it |

Install exact versions and commit the lockfile:

```sh
npm install --save-exact three@0.186.1 @react-three/fiber@9.8.1 @react-three/drei@10.7.9 @react-three/rapier@2.2.0
```

An exact version pins each package, not its dependencies; `npm ci` from the committed
`package-lock.json` is what makes a build repeat.

## WebGL and WebGPU

- **WebGL 2 is the default** (`WebGLRenderer`) and runs in every current browser.
- **WebGPU** is available through `WebGPURenderer`, imported from `three/webgpu`, since r171
  (2024-11-29). It falls back to a WebGL 2 backend when the browser has no WebGPU, and new materials
  are written in TSL (three.js shading language), which compiles to either backend. See the
  [WebGPURenderer manual page](https://threejs.org/manual/#en/webgpurenderer).
- **"Production-ready" is a claim, not a fact we verified.** That wording comes from blog posts, not
  from three.js release notes or documentation. Treat WebGPU as an option you test on your target
  devices, keep a WebGL path, and pin the three release you tested.
- Some community GPU effects need WebGPU with no fallback (see
  [threejs-particle-fluids](others.md#threejs)); check before you build a game around one.

## Web constraints

- **Mobile GPUs and memory decide your budget.** Test on a mid-range phone early: draw calls, texture
  memory and shader compile time are where browser 3D games stall.
- **Assets:** glTF 2.0 (`.glb`) is the format the three.js manual recommends; compress meshes with
  Draco or Meshopt and textures with KTX2. Export from Blender as in [../art/blender.md](../art/blender.md).
- **Audio** starts only after a user gesture in every major browser; put a "click to start" screen
  in the first build.
- **Hosting** is static files. No special headers are needed unless you use `SharedArrayBuffer`
  (some physics or audio worklets), which needs cross-origin isolation (COOP and COEP headers).

## AI tooling

- **No official three.js or R3F MCP server exists** (checked 2026-10-01). You mostly do not need one:
  the game is TypeScript an agent edits directly. [threejs.org/docs/llms.txt](https://threejs.org/docs/llms.txt)
  gives a model current usage rules; point the agent at it and name the pinned versions above in the
  game's `AGENTS.md`, because three.js renames and removes APIs between releases.
- **Verify in a real browser.** An agent cannot see a canvas from source. Add a Playwright smoke test
  that loads the page, waits for the first frame and saves a screenshot, and read the console for
  WebGL or WebGPU errors.
- Community tools (a scene-inspector MCP whose bridge listens on every interface, and an agent skill
  pack) are reviewed in [others.md](others.md#threejs) with their risks. Anything that runs code on
  your machine goes through the [safe setup checklist](../ai/graphics.md#safe-setup-checklist) first.

## Risks

1. **API churn:** three.js ships a numbered release about monthly and does not follow semver; read
   the migration notes before moving the pin.
2. **Stale physics bindings:** `@react-three/rapier` has had no release since 2025-11-03.
3. **WebGPU differences:** a scene can look or perform differently on the WebGPU and WebGL backends;
   test both.
4. **Asset licenses:** a starter template's models can carry CC-BY or other terms; see
   [../scaffolds/README.md](../scaffolds/README.md#how-to-choose).
