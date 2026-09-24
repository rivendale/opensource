# Rust games for the browser: WebAssembly, WebGPU and WebGL2

This guide covers Rust game code compiled to WebAssembly (Wasm), with WebGPU for modern
browsers and a WebGL2 build for browsers that lack WebGPU. Facts, versions, licenses and
browser support below were checked on 2026-09-24; follow the linked release and support
pages before starting a new project because Rust game APIs move quickly.

## Choose a stack

For a code-first 2D or 3D game, start by comparing Bevy with a smaller library. The crate
versions and license declarations below are from crates.io, checked 2026-09-24:

| Project | Version | License | Fit |
|---|---:|---|---|
| [Bevy](https://crates.io/crates/bevy) | 0.19.1 | MIT or Apache-2.0 | A full ECS game engine for 2D and 3D. Its web renderer needs explicit feature selection. |
| [wgpu](https://crates.io/crates/wgpu) | 30.0.1 | MIT or Apache-2.0 | A lower-level Rust graphics API that targets WebGPU in browsers and graphics APIs on native platforms. |
| [macroquad](https://crates.io/crates/macroquad) | 0.4.16 | MIT or Apache-2.0 | A compact library for games written mostly as one Rust loop; the wasm WebGPU path is not established by the sources checked here. |
| [Fyrox](https://crates.io/crates/fyrox) | 1.0.1 | MIT | A larger engine with an editor; its Wasm renderer uses WebGL2, not WebGPU. |
| [Trunk](https://crates.io/crates/trunk) | 0.21.14 | MIT or Apache-2.0 | Builds and serves Rust/Wasm browser apps. |
| [wasm-bindgen](https://crates.io/crates/wasm-bindgen) | 0.2.128 | MIT or Apache-2.0 | Connects Rust/Wasm code to browser JavaScript APIs. |
| [wasm-pack](https://crates.io/crates/wasm-pack) | 0.15.0 | MIT or Apache-2.0 | Builds and packages Rust/Wasm projects. |
| [gilrs](https://crates.io/crates/gilrs) | 0.11.2 | Apache-2.0 or MIT | Cross-platform gamepad input; its Wasm path depends on the selected backend and needs verification. |
| [Rapier](https://crates.io/crates/rapier3d) | 0.35.3 | Apache-2.0 | General-purpose 2D and 3D physics. |
| [bevy_rapier3d](https://crates.io/crates/bevy_rapier3d) | 0.36.0 | Apache-2.0 | Bevy integration for Rapier 3D. |
| [Avian](https://crates.io/crates/avian3d) | 0.7.0 | MIT or Apache-2.0 | ECS-oriented 3D physics alternative for Bevy. |

Bevy ships breaking releases roughly every three months. Version 0.20.0-rc.1 was available
on 2026-09-15, while 0.19.1 was the stable version checked here. Pin Bevy and matching
plugins in `Cargo.toml`, commit `Cargo.lock`, and check a template's tags before adopting it.
([Bevy crate history](https://crates.io/crates/bevy), checked 2026-09-24.)

## Browser support and Bevy's two builds

As checked on 2026-09-24, WebGPU is available by default in Chrome and Edge on supported
desktop and mobile hardware, Safari 26 on Apple platforms, and Firefox 141 on Windows,
Firefox 145 on Apple Silicon, and Firefox 147 on macOS. Firefox on Linux and Android remains
Nightly-only. Chrome on Linux support depends on GPU and driver: Intel Gen12+ from Chrome
144 and NVIDIA on Wayland with driver 535.183.01 or newer from Chrome 147. Hardware and
operating-system limits still apply, so feature-detect in the browser instead of assuming every user has a
working WebGPU adapter. ([GPU for the Web implementation status](https://github.com/gpuweb/gpuweb/wiki/Implementation-Status),
[WebGPU browser status](https://web.dev/blog/webgpu-supported-major-browsers), and
[WebKit Safari 26 announcement](https://webkit.org/blog/16993/news-from-wwdc25-web-technology-coming-this-fall-in-safari-26-beta/),
checked 2026-09-24.)

Bevy's web build uses WebGL2 by default. Its optional `webgpu` Cargo feature selects
WebGPU instead; that binary does not fall back to WebGL2 when the browser lacks WebGPU.
For Bevy, supporting both therefore means compiling and hosting two Wasm builds, then
using JavaScript feature detection to load the compatible one. ([Bevy issue #8315](https://github.com/bevyengine/bevy/issues/8315),
checked 2026-09-24.) WebGL2 cannot run compute shaders, so effects that depend on GPU
compute need the WebGPU build or a separate non-compute implementation.

### Build both browser variants

Pin the example to Bevy 0.19.1 and expose its renderer feature through the project feature
in `Cargo.toml`:

```toml
[dependencies]
bevy = "=0.19.1"

[features]
webgpu = ["bevy/webgpu"]
```

Compile once without the feature for WebGL2 and once with it for WebGPU. These commands
assume the project targets `wasm32-unknown-unknown` and has Trunk installed:

```sh
rustup target add wasm32-unknown-unknown
cargo install trunk --version 0.21.14 --locked
cargo install wasm-pack --version 0.15.0 --locked
cargo install wasm-bindgen-cli --version 0.2.128 --locked
trunk build --release --dist dist/webgl2
trunk build --release --features webgpu --dist dist/webgpu
```

Trunk and wasm-pack run build steps on your machine. Install the pinned versions, review
their dependencies, and follow the [safe setup checklist](../ai/graphics.md#safe-setup-checklist).
If you call `wasm-bindgen` directly, match its CLI to the crate in `Cargo.lock`; version
0.2.128 was checked on 2026-09-24.

Select a build before loading the game. This API check is a first filter; adapter creation
can still fail on an individual device:

```js
async function chooseBuild() {
  let hasAdapter = false;
  if ("gpu" in navigator) {
    hasAdapter = (await navigator.gpu.requestAdapter()) !== null;
  }
  window.location.replace(hasAdapter ? "/webgpu/" : "/webgl2/");
}

chooseBuild();
```

To check whether a usable adapter exists before selecting a build, call
`await navigator.gpu.requestAdapter()` and select WebGL2 if it returns `null`.

## Size, loading, audio and input

A minimal optimized Bevy web build has been reported at about 3.5 MB, while an unoptimized
build can be much larger. Treat those as reported examples, not a promise for your game.
The Bevy size guide recommends size-focused release settings and running `wasm-opt -Oz`;
measure your own compressed download and test on a cold load. ([Bevy Cheat Book: optimize
Wasm size](https://bevy-cheatbook.github.io/platforms/wasm/size-opt.html), checked
2026-09-24.) Serve Brotli or gzip where available and show a loading screen while the
browser downloads and compiles the game.

A size-focused profile in `Cargo.toml` is:

```toml
[profile.release]
opt-level = "z"
lto = true
codegen-units = 1
strip = true
panic = "abort"
```

Install Binaryen's pinned [version 131 release](https://github.com/WebAssembly/binaryen/releases/tag/version_131),
then run `wasm-opt -Oz -o game.optimized.wasm game.wasm` on the generated Wasm module and
point the web loader at the optimized file. `wasm-opt` processes the local Wasm file, so
review the input and use the official, versioned Binaryen release. Recheck generated
filenames when upgrading Trunk or Bevy.

For Bevy audio, [`kira`](https://crates.io/crates/kira) 0.12.4 and the pre-release
[`bevy_kira_audio`](https://crates.io/crates/bevy_kira_audio) 0.27.0-rc.1 list MIT or
Apache-2.0 licenses, as checked on 2026-09-24. The audio plugin is a release candidate;
its compatibility with Bevy 0.19.1 is not established here, so verify that pairing before
adopting it. The plugin supports web builds and notes
that Chrome requires a user gesture before audio playback; it also records reports of
Firefox audio distortion when the game is under heavy load. Test audio on real target
browsers and start sound after a click or key press. ([plugin repository](https://github.com/NiklasEi/bevy_kira_audio),
checked 2026-09-24.)

Keyboard and pointer input use browser event plumbing through the engine. For gamepads,
the [`gamepads` crate](https://crates.io/crates/gamepads) 0.1.7 (MIT or Apache-2.0, checked
2026-09-24) wraps the browser Gamepad API, including rumble support. Its repository had a
small user base and its last push was 2025-02-25, so verify browser behavior and maintenance
before depending on it. ([project repository](https://github.com/fornwall/gamepads) and
[documentation](https://fornwall.github.io/gamepads/), checked 2026-09-24.)

## Starter projects and examples

These repository licenses and activity notes were checked on GitHub on 2026-09-24. A
template license covers its code only; inspect and credit bundled assets separately.

| Project | License | What it offers |
|---|---|---|
| [NiklasEi/bevy_game_template](https://github.com/NiklasEi/bevy_game_template) | CC0-1.0 | A template with web and desktop CI builds. Read its asset credits before reuse. The source does not state a Bevy version. |
| [TheBevyFlock/bevy_new_2d](https://github.com/TheBevyFlock/bevy_new_2d) | MIT | A 2D project template with versioned tags, including Bevy 0.17 and 0.18. Match the tag to your engine release. |
| [olekspickle/bevy_new_3d_rpg](https://github.com/olekspickle/bevy_new_3d_rpg) | No license declared | A 3D RPG starting point. Check first; do not copy code or assets without permission. |
| [rustcycles/rustcycles](https://github.com/rustcycles/rustcycles) | AGPL-3.0 | A Rust vehicle-combat game built with Fyrox. Study its approach or review AGPL obligations before reusing code. |
| [heroiclabs/fishgame-macroquad](https://github.com/heroiclabs/fishgame-macroquad) | Apache-2.0 | A Macroquad multiplayer demo. Its last push was 2022-05-23, so use it as an older example, not a current dependency recipe. |
| [Ruddle/oxidator](https://github.com/Ruddle/oxidator) | MIT | An RTS example built directly on wgpu. Its last push was 2023-09-11, so expect older APIs. |

No widely used, actively maintained, finished commercial game on this exact Rust, Wasm and
WebGPU stack with public source was identified in the project review dated 2026-09-24.
Available examples are templates, older demonstrations, or games using other Rust renderers.
Treat the templates as starting points, not proof of a mature shipped-game pipeline.

## 3D assets, particles and water

Tripo describes generating textured meshes from text or reference images and exporting GLB or
glTF. Its Blender DCC Bridge requires Blender 4.1 or later. Those are vendor
claims checked against [Tripo's game development page](https://www.tripo3d.ai/game-development)
and [format and integration page](https://www.tripo3d.ai/game-development/fbx-gltf-usd-game-development-tripo-ai)
on 2026-09-24. A workable pipeline is **Tripo → Blender → glTF/GLB → Bevy's glTF loader**:
inspect topology, materials, scale, rigging and license terms in Blender before shipping.
Tripo's claim that some generated meshes have clean topology is vendor-reported; the sources
here do not independently evaluate mesh quality or establish that cleanup can be skipped.

The Tripo Blender API plugin is listed as version 0.7.3, compatible with Blender 3.0 or
newer in Tripo's developer documentation checked 2026-09-24. It runs within Blender and
sends generation requests to Tripo, so prompts and reference images leave the machine.
Download only the listed 0.7.3 release, retain that archive as the pin, and review its code
before enabling it. Treat generated models as unverified until you inspect topology,
materials, scale, rigging and asset terms. Follow the [safe setup checklist](../ai/graphics.md#safe-setup-checklist).

For Bevy GPU particles, [bevy_hanabi](https://github.com/djeedai/bevy_hanabi) 0.19.0
supports compute particles in a Wasm build when using WebGPU. Its documentation says the
WebGL2 path cannot run those compute shaders. This plugin version and its MIT or Apache-2.0
license were checked 2026-09-24. ([Wasm notes](https://github.com/djeedai/bevy_hanabi/blob/main/docs/wasm.md).)

For water, [bevy-aqua](https://github.com/wellscrosby/bevy-aqua) describes a Bevy ocean
renderer with Gerstner and FFT waves, reflections, refraction and foam; the source notes
Apache-2.0 and a repository push on 2026-09-23. It is a young project, so expect changes
and verify its current Bevy compatibility before adopting it. A lower-level WebGPU FFT
example is [Ocean Simulation with FFT and WebGPU](https://barthpaleologue.github.io/Blog/posts/ocean-simulation-webgpu/),
read 2026-09-24. These sources describe techniques and project features; they do not
promise a particular frame rate or device compatibility.

## What AI coding agents can help with

An AI coding tool can draft Rust systems, browser glue, build configuration and shaders,
then help respond to compiler and browser-console errors. Keep changes small, build both
web variants, and test on the browser and hardware you plan to support. Rust's compiler
can catch many type and ownership errors, while borrow checking can require iteration;
these observations come from general Rust and agent articles, not an evaluation of browser
games. ([Rust compiler as an agent guardrail](https://belderbos.dev/blog/rust-compiler-ai-agent-guardrail/)
and [Rust and coding agents](https://reltech.substack.com/p/why-learning-rust-still-matters-in),
read 2026-09-24.)

Claude Opus 5.5, GPT-6 Sol, GPT-6 Luna and Grok 4.7 had been announced by 2026-09-24.
The sources checked for this guide do not evaluate them on Bevy, wgpu, Wasm builds, browser
input or game shaders, so this guide does not rank them for this stack. ([OpenAI model
announcement](https://openai.com/index/introducing-gpt-6-sol-and-luna/), [Opus 5.5
reporting](https://venturebeat.com/technology/anthropic-releases-claude-opus-5-5-beating-fable-5-1-on-key-agentic-benchmarks-at-60-cheaper-api-price),
[Grok 4.7 overview](https://www.datacamp.com/blog/grok-4-7), checked 2026-09-24.)
There is no sourced basis here to trust their
generated shader correctness, browser support claims, performance assumptions or engine API
choices. Treat their output as a draft and verify it with pinned dependencies, builds and
hands-on browser testing.
