# AI bridges (MCP servers) for game and art tools

Found by GitHub search on 2026-10-01, then verified on GitHub: code, a license GitHub can identify, 25+ stars, a push in the last three years. Search is a starting point, not an endorsement: read a repository before you build on it. Reuse classes as in the main catalog.

**Metadata checked, not security-reviewed.** Every entry can run code on your machine, and some listen on every network interface by default. Read the [safe setup checklist](../ai/graphics.md#safe-setup-checklist) and the [maintained servers per tool](../ai/graphics.md#maintained-servers-per-tool) first.

## Aseprite

| repository | reuse | license | language | stars | last push | about |
|---|---|---|---|---|---|---|
| [diivi/aseprite-mcp](https://github.com/diivi/aseprite-mcp) | copy | MIT | Python | 616 | 2026-07-29 | MCP server for interacting with the Aseprite API |
| [willibrandon/pixel-mcp](https://github.com/willibrandon/pixel-mcp) | copy | MIT | Go | 147 | 2025-10-18 | MCP server for creating pixel art with Aseprite through AI assistants. Supports animation, retro palettes, dit |
| [Gamezxz/pixel-art-studio](https://github.com/Gamezxz/pixel-art-studio) | copy | MIT | Python | 68 | 2026-07-11 | Agent Skill that makes Claude a pixel artist - no Aseprite, no MCP, no diffusion. Every pixel is a decision. |
| [youichi-uda/aseprite-mcp-pro](https://github.com/youichi-uda/aseprite-mcp-pro) | copy | MIT | Lua | 32 | 2026-07-20 | Aseprite MCP Pro - AI-powered pixel art creation for Aseprite via Model Context Protocol. 121 tools for sprite |

## Blender

Blender's own server, [Blender Lab MCP](https://www.blender.org/lab/mcp-server/), is hosted on projects.blender.org, so GitHub search cannot list it. It is the recommended first choice; its risk row is in [art/blender.md](../art/blender.md#driving-blender-with-ai-tools).

| repository | reuse | license | language | stars | last push | about |
|---|---|---|---|---|---|---|
| [ahujasid/mcp-for-blender](https://github.com/ahujasid/mcp-for-blender) | copy | MIT | Python | 29810 | 2026-09-30 | Community plugin to control Blender 3D with any LLM of your choice |
| [VxASI/blender-mcp-vxai](https://github.com/VxASI/blender-mcp-vxai) | copy | MIT | Python | 300 | 2025-03-21 |  |
| [arjun988/blender-skills](https://github.com/arjun988/blender-skills) | copy | MIT | TypeScript | 256 | 2026-07-10 | 94 specialist Blender skills for Cursor, Claude Code, Kiro & Codex -> MCP-powered production pipeline from blo |
| [DMontgomery40/bambu-printer-mcp](https://github.com/DMontgomery40/bambu-printer-mcp) | study only | GPL-2.0 | TypeScript | 168 | 2026-09-30 | MCP server for Bambu Lab 3D printers - STL manipulation, BambuStudio or FULU/orca slicing, Blender MCP integra |
| [HoldMyBeer-gg/blenderwright](https://github.com/HoldMyBeer-gg/blenderwright) | study only | AGPL-3.0 | Python | 151 | 2026-10-01 | MCP server for Blender. 186 tools for modelling, materials, rendering and more, driven by Claude, Cursor, Code |
| [dhakalnirajan/blender-open-mcp](https://github.com/dhakalnirajan/blender-open-mcp) | copy | MIT | Python | 120 | 2026-09-04 | MCP for Blender Using Open Weights Models |
| [pranav-deshmukh/blender-mcp](https://github.com/pranav-deshmukh/blender-mcp) | copy | MIT | Python | 98 | 2025-08-06 |  |
| [seehiong/blender-mcp-bridge](https://github.com/seehiong/blender-mcp-bridge) | copy | MIT | Python | 64 | 2026-09-13 | Automate Blender 3D modeling with AI via MCP - 93 tools for modeling, sculpting, architecture/MEP, materials,  |
| [PatrykIti/blender-ai-mcp](https://github.com/PatrykIti/blender-ai-mcp) | copy | Apache-2.0 | Python | 62 | 2026-06-27 | Production-shaped MCP server for Blender with goal-first routing, curated tools, deterministic verification, a |
| [ifBars/blender-agent-studio](https://github.com/ifBars/blender-agent-studio) | copy | MIT | TypeScript | 58 | 2026-09-29 | Codex plugin for reproducible Blender modeling, validation, animation, MCP tooling, and agent benchmarking |
| [sandraschi/blender-mcp](https://github.com/sandraschi/blender-mcp) | copy | MIT | Python | 52 | 2026-09-28 | Headless Blender automation via FastMCP - 41 portmanteau tools (150+ ops). Batch mesh/VSE/Grease Pencil, VRM,  |
| [dcc-mcp/dcc-mcp-blender](https://github.com/dcc-mcp/dcc-mcp-blender) | copy | MIT | Python | 43 | 2026-10-01 | Blender addon for the DCC Model Context Protocol (MCP) ecosystem - embeds a Streamable HTTP MCP server directl |
| [ig-shadow-walker/BlenderXAlpha-3DGenSkill](https://github.com/ig-shadow-walker/BlenderXAlpha-3DGenSkill) | copy | MIT | JavaScript | 30 | 2026-07-21 | Agent Skill that turns plain-English scene descriptions into AI-generated 3D models built live in Blender, via |
| [djeada/blender-mcp-server](https://github.com/djeada/blender-mcp-server) | copy | MIT | Python | 28 | 2026-09-23 | Control Blender from AI assistants like Claude Desktop using the Model Context Protocol (MCP). 22 tools across |
| [Yuan-ManX/BlenderMCP](https://github.com/Yuan-ManX/BlenderMCP) | copy | MIT | Python | 25 | 2025-03-14 | Python implementation of BlenderMCP (Blender Model Context Protocol Integration). |

## GIMP

| repository | reuse | license | language | stars | last push | about |
|---|---|---|---|---|---|---|
| [maorcc/gimp-mcp](https://github.com/maorcc/gimp-mcp) | study only | GPL-3.0 | Python | 245 | 2026-05-29 | GIMP MCP server |
| [libreearth/gimp-mcp](https://github.com/libreearth/gimp-mcp) | study only | GPL-3.0 | Python | 122 | 2025-03-18 | Gimp MCP Server |

## Godot

There is no official Godot MCP server: the godotengine organization has no MCP repository (checked 2026-10-01). A repository calling itself an "Official Plugin" is a personal account's. Risk notes for the maintained servers are in [engines/godot.md](../engines/godot.md#ai-tooling).

| repository | reuse | license | language | stars | last push | about |
|---|---|---|---|---|---|---|
| [Coding-Solo/godot-mcp](https://github.com/Coding-Solo/godot-mcp) | copy | MIT | JavaScript | 5902 | 2026-04-16 | MCP server for interfacing with Godot game engine. Provides tools for launching the editor, running projects,  |
| [hi-godot/godot-ai](https://github.com/hi-godot/godot-ai) | copy | MIT | GDScript | 2728 | 2026-10-01 | Production-grade MCP server and AI tools for the Godot engine. A Snap to install. Totally free and fun. |
| [yurineko73/Godot-MCP-Native](https://github.com/yurineko73/Godot-MCP-Native) | copy | MIT | GDScript | 819 | 2026-08-03 | 一款支持godot开源引擎的的mcp插件，支持常见godot引擎操作，使用Godot原生实现MCPServer，无需安装依赖，开箱即用，支持多种AI工具调用。An MCP plugin that supports the |
| [ee0pdt/Godot-MCP](https://github.com/ee0pdt/Godot-MCP) | copy | MIT | GDScript | 616 | 2025-03-19 | An MCP for Godot that lets you create and edit games in the Godot game engine with tools like Claude |
| [tugcantopaloglu/godot-mcp](https://github.com/tugcantopaloglu/godot-mcp) | copy | MIT | JavaScript | 472 | 2026-07-13 | MCP server for full Godot 4.x engine control: 157 tools for AI-driven game development (GDScript and C#/.NET). |
| [tomyud1/godot-mcp](https://github.com/tomyud1/godot-mcp) | copy | MIT | GDScript | 434 | 2026-08-24 | MCP Server and Godot Plugin for AI-assisted game development |
| [fennaraOfficial/fennara-godot-ai](https://github.com/fennaraOfficial/fennara-godot-ai) | copy | MIT | Rust | 298 | 2026-10-01 | AI chat and agent tooling for Godot, with both MCP support and in-built native chat window. |
| [IvanMurzak/Godot-MCP](https://github.com/IvanMurzak/Godot-MCP) | copy | Apache-2.0 | C# | 262 | 2026-09-27 | Godot-MCP - Model Context Protocol (MCP) integration for the Godot Engine. AI tools for the Godot Editor in C# |
| [HaD0Yun/Doyunha-Gopeak](https://github.com/HaD0Yun/Doyunha-Gopeak) | copy | MIT | TypeScript | 262 | 2026-09-12 | GoPeak - The most comprehensive MCP server for Godot Engine. 95+ tools: scene management, GDScript LSP, DAP de |
| [Glade-tool/glade-mcp](https://github.com/Glade-tool/glade-mcp) | copy | MIT | C# | 225 | 2026-09-02 | Connect any MCP-compatible AI client (Claude Code, Cursor, Windsurf) to Unity or Godot. 275+ granular tools, a |
| [satelliteoflove/godot-mcp](https://github.com/satelliteoflove/godot-mcp) | copy | MIT | GDScript | 171 | 2026-09-25 | Give your AI assistant eyes and hands in the Godot editor: scene editing, input injection, deterministic playt |
| [bradypp/godot-mcp](https://github.com/bradypp/godot-mcp) | copy | MIT | TypeScript | 90 | 2025-05-31 | A Model Context Protocol (MCP) server for interacting with the Godot game engine. |
| [wangdiandao/godot-devtool](https://github.com/wangdiandao/godot-devtool) | copy | MIT | TypeScript | 90 | 2026-06-29 | Godot 4 MCP server for AI-assisted project inspection, editing, validation, and runtime automation. |
| [Erodenn/godot-mcp-runtime](https://github.com/Erodenn/godot-mcp-runtime) | copy | MIT | TypeScript | 82 | 2026-09-30 | A lightweight, zero-footprint TypeScript MCP server that lets AI assistants drive the Godot 4.x game engine. |
| [Nihilantropy/godot-mcp-docs](https://github.com/Nihilantropy/godot-mcp-docs) | copy | MIT | Python | 74 | 2025-07-25 | MCP server for godot docs |
| [regiellis/godot-mcp-go](https://github.com/regiellis/godot-mcp-go) | copy | MIT | HTML | 65 | 2026-09-26 | Build, inspect, test, and debug Godot games from your terminal. Automate repetitive work with scripts, or let  |
| [Derfirm/godot-mcp](https://github.com/Derfirm/godot-mcp) | copy | MIT | JavaScript | 57 | 2026-07-27 |  |
| [salvo10f/godotiq](https://github.com/salvo10f/godotiq) | copy | MIT | GDScript | 54 | 2026-08-03 | The intelligent MCP server for AI-assisted Godot 4 development. 35 tools for spatial intelligence, code unders |
| [ryanmazzolini/minimal-godot-mcp](https://github.com/ryanmazzolini/minimal-godot-mcp) | copy | MIT | TypeScript | 47 | 2026-09-27 | Lightweight MCP server bridging Godot LSP to MCP clients for GDScript validation |
| [hhhh124hhhh/godot-mcp](https://github.com/hhhh124hhhh/godot-mcp) | copy | MIT | TypeScript | 43 | 2025-11-15 | godot-mcp 自然语言游戏开发利器 |
| [aigengame/godot-agent](https://github.com/aigengame/godot-agent) | copy | MIT | Python | 43 | 2026-10-01 | Godot automation for AI agents to build and verify projects through a CLI, Agent Skill, or MCP server, with st |
| [FunplayAI/funplay-godot-mcp](https://github.com/FunplayAI/funplay-godot-mcp) | copy | MIT | GDScript | 41 | 2026-07-31 | The Most Advanced MCP Server for Godot Editor with execute_code, prompts/resources, project maps, runtime insp |
| [LuoxuanLove/godot-dotnet-mcp](https://github.com/LuoxuanLove/godot-dotnet-mcp) | copy | MIT | GDScript | 38 | 2026-07-14 | A Godot 4.6+ editor plugin that gives AI agents a real MCP interface to the live Godot editor: project state,  |
| [yanhuifair/Godot-MCP](https://github.com/yanhuifair/Godot-MCP) | study only | AGPL-3.0 | TypeScript | 38 | 2026-09-28 |  |

## Inkscape

| repository | reuse | license | language | stars | last push | about |
|---|---|---|---|---|---|---|
| [sandraschi/inkscape-mcp](https://github.com/sandraschi/inkscape-mcp) | copy | MIT | Python | 79 | 2026-09-28 | Headless Inkscape SVG automation via FastMCP - 60+ ops: create, boolean, LPE, export, text, fleet pipeline. Ba |
| [aravindev/inkscape_mcp](https://github.com/aravindev/inkscape_mcp) | copy | MIT | Python | 72 | 2026-09-14 | MCP server that lets AI agents drive Inkscape - interactively alongside the GUI or headlessly from the CLI |
| [Shriinivas/inkmcp](https://github.com/Shriinivas/inkmcp) | study only | AGPL-3.0 | Python | 72 | 2026-01-14 | Inkscape MCP Server - Control Inkscape through AI assistants via Model Context Protocol |
| [grumpydevorg/inkscape-mcps](https://github.com/grumpydevorg/inkscape-mcps) | copy | MIT | Python | 55 | 2025-10-22 | Inkscape MCP Server - FastMCP-based server for Inkscape CLI and DOM operations with security boundaries and au |

## Krita

| repository | reuse | license | language | stars | last push | about |
|---|---|---|---|---|---|---|
| [nanayax3/krita-mcp](https://github.com/nanayax3/krita-mcp) | copy | MIT | Python | 40 | 2026-02-26 | Let AI paint in Krita via the Model Context Protocol. Includes fix for the common export timeout issue. |

## Unity

| repository | reuse | license | language | stars | last push | about |
|---|---|---|---|---|---|---|
| [CoplayDev/unity-mcp](https://github.com/CoplayDev/unity-mcp) | copy | MIT | C# | 14635 | 2026-09-30 | Unity MCP acts as a bridge between AI assistants and your Unity Editor. Give your LLM tools to manage assets,  |
| [IvanMurzak/Unity-MCP](https://github.com/IvanMurzak/Unity-MCP) | copy | Apache-2.0 | C# | 4370 | 2026-09-28 | AI Skills, MCP Tools, and CLI for Unity Engine. Full AI develop and test loop. Use cli for quick setup. Effici |
| [CoderGamester/mcp-unity](https://github.com/CoderGamester/mcp-unity) | copy | MIT | C# | 1918 | 2026-09-03 | Model Context Protocol (MCP) plugin to connect with Unity Editor - designed for Cursor, Claude Code, Codex, Wi |
| [isuzu-shiranui/UnityMCP](https://github.com/isuzu-shiranui/UnityMCP) | copy | MIT | C# | 329 | 2026-09-17 | Drive the Unity Editor from an AI agent or the terminal. The Editor serves MCP itself over HTTP, so there is n |
| [youngwoocho02/unity-cli](https://github.com/youngwoocho02/unity-cli) | copy | MIT | Go | 315 | 2026-08-28 | Control Unity Editor from the command line. No MCP, no Python, no dependencies - just a single binary. |
| [FunplayAI/funplay-unity-mcp](https://github.com/FunplayAI/funplay-unity-mcp) | copy | MIT | C# | 255 | 2026-09-17 | The Most Advanced MCP Server for Unity Editor with execute_code, prompts/resources, input simulation, screensh |
| [notargs/UnityNaturalMCP](https://github.com/notargs/UnityNaturalMCP) | copy | MIT | C# | 163 | 2026-01-19 archived | UnityNaturalMCP is an MCP server implementation for Unity that aims for a "natural" user experience. |
| [quazaai/UnityMCPIntegration](https://github.com/quazaai/UnityMCPIntegration) | copy | MIT | C# | 159 | 2025-04-15 | Enable AI Agents to Control Unity |
| [IvanMurzak/Unity-AI-Animation](https://github.com/IvanMurzak/Unity-AI-Animation) | copy | MIT | C# | 115 | 2026-09-28 | MCP Tools for Unity Animation - create and edit clips and animators with AI. |
| [TomLeeLive/openclaw-unity-plugin](https://github.com/TomLeeLive/openclaw-unity-plugin) | copy | Apache-2.0 | C# | 107 | 2026-09-08 | 55 MCP tools to drive the Unity Editor from any MCP-compatible AI agent - scenes, GameObjects, prefabs, assets |
| [killop/puerts-unity-mcp](https://github.com/killop/puerts-unity-mcp) | copy | MIT | C# | 81 | 2026-07-29 | unity-mcp driven by tencent puerts , invoke js/ts call c# in your cell phone and unity editor |
| [youichi-uda/unity-mcp-pro-plugin](https://github.com/youichi-uda/unity-mcp-pro-plugin) | copy | MIT | C# | 81 | 2026-07-21 | 147 AI tools for Unity game development via MCP (Model Context Protocol). Connect Claude, Cursor, and AI assis |
| [Codeturion/unity-api-mcp](https://github.com/Codeturion/unity-api-mcp) | copy | MIT | Python | 67 | 2026-07-19 | Instant, accurate Unity API lookups instead of expensive source file reads, saving your agent tokens, context, |
| [LiShengYang-yiyi/YIUI-UnityMCP](https://github.com/LiShengYang-yiyi/YIUI-UnityMCP) | copy | Apache-2.0 | C# | 58 | 2026-04-03 |  |
| [IvanMurzak/Unity-AI-ProBuilder](https://github.com/IvanMurzak/Unity-AI-ProBuilder) | copy | Apache-2.0 | C# | 55 | 2026-09-28 | MCP Tools for Unity ProBuilder - model and edit meshes with AI. |
| [IvanMurzak/Unity-AI-ParticleSystem](https://github.com/IvanMurzak/Unity-AI-ParticleSystem) | copy | MIT | C# | 54 | 2026-09-28 | MCP Tools for Unity Particle System - create and edit particle effects with AI. |
| [TheArcForge/UniClaude](https://github.com/TheArcForge/UniClaude) | copy | MIT | C# | 51 | 2026-05-11 | Claude Code, natively inside Unity Editor. A dockable chat window with full project awareness, 60+ MCP tools,  |
| [VR-Jobs/UnityMCPbeta](https://github.com/VR-Jobs/UnityMCPbeta) | copy | MIT | C# | 48 | 2025-07-03 |  |

## Unreal

| repository | reuse | license | language | stars | last push | about |
|---|---|---|---|---|---|---|
| [ChiR24/Unreal_mcp](https://github.com/ChiR24/Unreal_mcp) | copy | MIT | C++ | 902 | 2026-10-01 | A comprehensive Model Context Protocol (MCP) server that enables AI assistants to control Unreal Engine throug |
| [prajwalshettydev/UnrealGenAISupport](https://github.com/prajwalshettydev/UnrealGenAISupport) | copy | MIT | C++ | 652 | 2026-04-28 | Unreal Engine plugin for LLM/GenAI models & MCP UE5 server. OpenAI GPT-5, Deepseek R1, Claude Opus/Sonnet, Gem |
| [db-lyon/ue-mcp](https://github.com/db-lyon/ue-mcp) | copy | MIT | C++ | 377 | 2026-09-29 | Complete Unreal Engine development toolkit exposed as MCP tools. |
| [tumourlove/monolith](https://github.com/tumourlove/monolith) | copy | MIT | C++ | 321 | 2026-09-09 | MCP plugin for Unreal Engine 5.7 & 5.8 - gives AI assistants full read/write access to Blueprints, Materials,  |
| [winyunq/UnrealMotionGraphicsMCP](https://github.com/winyunq/UnrealMotionGraphicsMCP) | copy | MIT | C++ | 204 | 2026-08-02 | 🚀 UE5-UMG-MCP: A deep-focused MCP for Unreal Engine UMG layout. Designed to maximize AI efficiency within limi |
| [ayeletstudioindia/unreal-analyzer-mcp](https://github.com/ayeletstudioindia/unreal-analyzer-mcp) | copy | MIT | TypeScript | 159 | 2025-08-06 | MCP server for Unreal Engine 5 |
| [GenOrca/unreal-mcp](https://github.com/GenOrca/unreal-mcp) | copy | Apache-2.0 | Python | 144 | 2026-07-07 | Unreal Engine MCP Server: Control UE5 with Claude & AI Agents. Supports Python and C++ for custom tool develop |
| [believer-oss/Claireon](https://github.com/believer-oss/Claireon) | copy | MIT | C++ | 139 | 2026-09-15 | MCP server for Unreal Editor |
| [runreal/unreal-mcp](https://github.com/runreal/unreal-mcp) | copy | MIT | Python | 116 | 2025-06-06 | MCP server for Unreal Engine that uses Unreal Python Remote Execution |
| [Codeturion/unreal-api-mcp](https://github.com/Codeturion/unreal-api-mcp) | copy | MIT | Python | 97 | 2026-07-19 | Instant, accurate Unreal Engine API lookups instead of expensive source file reads, saving your agent tokens,  |
| [softdaddy-o/yes-ue-mcp](https://github.com/softdaddy-o/yes-ue-mcp) | copy | MIT | C++ | 88 | 2026-03-16 | Native C++ Model Context Protocol (MCP) plugin for Unreal Engine 5.4+ |
| [mirno-ehf/ue5-mcp](https://github.com/mirno-ehf/ue5-mcp) | copy | MIT | C++ | 75 | 2026-05-27 | Let AI edit your Unreal Engine Blueprints. MCP server plugin for Claude Code - describe what you want in plain |
| [remiphilippe/mcp-unreal](https://github.com/remiphilippe/mcp-unreal) | copy | Apache-2.0 | Go | 74 | 2026-02-20 | MCP server that gives AI coding agents (Claude Code, Cursor, etc.) full control over Unreal Engine 5.7 project |
| [KirChuvakov/uefn-mcp-server](https://github.com/KirChuvakov/uefn-mcp-server) | copy | MIT | Python | 69 | 2026-10-01 | MCP server for controlling UEFN (Unreal Editor for Fortnite) from Claude Code - 22 tools for actors, assets, l |
| [appleweed/UnrealMCPBridge](https://github.com/appleweed/UnrealMCPBridge) | copy | MIT | C++ | 65 | 2026-05-12 | An Unreal Engine plugin that implements an MCP server allowing MCP clients to access the UE Editor Python API. |
| [runeape-sats/unreal-mcp](https://github.com/runeape-sats/unreal-mcp) | copy | MIT | Python | 47 | 2026-03-31 | pure python Unreal Engine MCP server |
| [ArtisanGameworks/SpecialAgentPlugin](https://github.com/ArtisanGameworks/SpecialAgentPlugin) | copy | Apache-2.0 | C++ | 47 | 2026-01-06 | SpecialAgent is an Unreal Engine 5 plugin that implements a Model Context Protocol (MCP) server, allowing Larg |
| [IvanMurzak/Unreal-MCP](https://github.com/IvanMurzak/Unreal-MCP) | copy | Apache-2.0 | C++ | 40 | 2026-09-27 | AI Game Developer for Unreal Engine - MCP plugin (C++ editor plugin + .NET bridge), unreal-cli, connects Unrea |
| [aadeshrao123/Unreal-MCP](https://github.com/aadeshrao123/Unreal-MCP) | library use | MPL-2.0 | C++ | 39 | 2026-08-06 | AI bridge for Unreal Engine 5. Control the editor from Claude Code, Cursor, Windsurf, and any MCP client. Comm |
