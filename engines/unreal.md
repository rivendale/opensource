# Unreal Engine for small teams

Unreal gives a small team a large 3D engine, a visual editor, Blueprints and access to engine source under Epic's terms. It is source-available, not open source. License and feature facts below were checked on 2026-09-24; verify current terms before release.

## EULA, royalties and source access

Unreal Engine is governed by Epic's [Unreal Engine End User License Agreement](https://www.unrealengine.com/en-US/eula/unreal), not an OSI open-source license. Epic's [GitHub source repository](https://github.com/EpicGames/UnrealEngine) is available after linking a verified Epic Games account with GitHub, following Epic's [signup instructions](https://github.com/EpicGames/Signup). Source access remains subject to the EULA.

Secondary coverage read on 2026-09-24 describes the standard game royalty as 5% of worldwide gross revenue after the first $1 million in lifetime gross revenue for a product, with quarters under $10,000 excluded. Eligible Windows, macOS and Android releases using Epic's Launch Everywhere program can qualify for 3.5% starting 2025-01-01, if released on the Epic Games Store before or at the same time as other stores; this change did not apply to games already live there before that date. Meta separately covers the first $5 million of revenue from sales on the Meta Horizon Store for developers who opt into its program. These terms are summarized by [Seele's Unreal pricing guide](https://www.seeles.ai/resources/blogs/unreal-engine-pricing-royalties-and-licensing-guide) and [CG Channel](https://www.cgchannel.com/2024/10/epic-games-to-cut-royalty-rate-on-unreal-engine-games/); Meta describes its program in its [developer documentation](https://developers.meta.com/horizon/documentation/unreal/unreal-oculus-license/). Check Epic's current EULA before relying on thresholds or exceptions.

## Learning Agents

Epic's [Learning Agents plugin](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/PluginIndex/LearningAgents) provides reinforcement and imitation learning tools for training characters inside Unreal. Epic's documentation covers Unreal Engine 5.7 and 5.8 (checked 2026-09-24). It is distributed with the engine and governed by the Unreal EULA, not a separate open-source license.

A practical first experiment is to enable Learning Agents in the editor's Plugins panel, restart if prompted, then make a small training environment with one character and a simple target behavior. Define the observations the learner receives, the actions it can choose, and a measurable reward; start with imitation data or a small reinforcement task, then inspect the learned behavior in the Unreal project. The plugin is for training game characters, not a conversational model or an agent that can automatically play any game. Read the documentation matching your engine version.

A community alternative, [AlanLaboratory/UnrealMLAgents](https://github.com/AlanLaboratory/UnrealMLAgents), describes itself as a port of Unity ML-Agents for Unreal. Its repository did not declare a license in the GitHub API on 2026-09-24, so check first and do not copy its code until its terms are clear.

## Unreal projects to study

These are simulator projects, not game-playing language model agents. Their code licenses were checked on 2026-09-24; assets and data may have separate terms.

| Project | License and use |
|---|---|
| [CARLA](https://github.com/carla-simulator/carla) | MIT. An autonomous-driving simulator built on Unreal Engine. |
| [Microsoft AirSim](https://github.com/microsoft/AirSim) | MIT in its repository LICENSE, although GitHub's API reports no license identifier. A drone and vehicle simulator with an Unreal backend. |
| [Cosys-AirSim](https://github.com/Cosys-Lab/Cosys-AirSim) | MIT. A community-maintained AirSim fork. |

## Where AI tools help

An AI coding assistant can help draft C++ classes, Blueprint logic, editor utility scripts, build configuration and test scaffolding. Ask for a small change, compile it, run it in a development project and inspect the result in the editor. The references checked here do not evaluate named coding models on Unreal projects, so there is no sourced basis to rank models or promise reliable Blueprint graphs, gameplay behavior or performance.

For editor work, [Unreal_mcp](https://github.com/ChiR24/Unreal_mcp) exposes tools for assets, actors, levels, Blueprints, Niagara, Sequencer and console commands. Its MIT license and server version 0.5.30 were checked on 2026-09-23. Its `execute_python` tool runs Python in the editor, and console commands pass only a pattern-based blocklist, so it can change project files or execute editor actions with your user permissions. Review its code, use it in a development project, keep token authentication enabled and its listener bound to localhost, and pin the install:

```sh
npx unreal-engine-mcp-server@0.5.30
```

Follow the [safe setup checklist](../ai/graphics.md#safe-setup-checklist) before connecting an agent. Commit before a session and review actions that write files or execute code.

## When to choose something smaller

Unreal can be a good fit when your game needs its 3D editor, visual scripting, rendering features or established production pipeline and the team can support a large engine and its terms. For a small 2D project, a modest 3D game or a team that wants a smaller codebase, compare [Godot](godot.md): the Godot guide describes an MIT-licensed engine with plain-text scenes and no engine royalty. It also documents limits such as WebGL2-only browser rendering and no official console ports. Its version and license details were checked 2026-09-23.

If browser delivery is central, consider a web stack such as [Rust, WebAssembly and WebGPU](rust-wasm-webgpu.md) or a JavaScript/TypeScript library in [others.md](others.md). The Rust guide, checked 2026-09-24, describes WebGPU support alongside a WebGL2 fallback, with a separate Bevy binary for each renderer. Choose the web route when instant browser access and a lighter deployment model matter more than Unreal's editor-centered workflow; test the actual browsers and devices you intend to support.
