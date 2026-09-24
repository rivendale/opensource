# Unity

**Unity is not open source.** It is a proprietary engine licensed under Unity's Terms of Service and
its Unity Editor Software Terms. You install and run the Editor under a license grant "solely for
internal use", you may not modify or redistribute its source, and the plan you must use depends on
your revenue and funding. The C# part of the engine is published on GitHub for reference only (see
below). Everything else in this chassis (Godot, Blender, GIMP and the catalog's `copy` projects) is
open source; Unity is the exception, which is why its terms get a section of their own.

Every term below was read on Unity's official pages on 2026-09-23. Terms change: re-read
[unity.com/pricing](https://unity.com/pricing), [unity.com/products/pricing-updates](https://unity.com/products/pricing-updates)
and the [Editor Software Terms](https://github.com/Unity-Technologies/TermsOfService) before you
commit a project to Unity. This is practical guidance, not legal advice.

## Plans and license terms (checked 2026-09-23)

| plan | price listed | who must use it |
|---|---|---|
| Personal | free | allowed only while your Total Finances stay at or under $200,000 for the last 12 months; "for gaming and entertainment applications only" |
| Pro | $2,310 per seat per year prepaid, or $210 per seat per month | required above $200K in revenue or funding; adds publishing to game consoles and Apple Vision Pro |
| Enterprise | custom; minimum commitments may apply | required at $25 million and over; adds read-only source code access |
| Industry | custom | required for applications outside games or entertainment when your total finances exceed $1,000,000 |
| Student | see Unity's student terms | Financial Threshold of $1,000,000 |

What the Editor Software Terms (version of June 30, 2026) say, in plain words:

- **Tier eligibility is measured every day you use Unity**, over the trailing 12 months. Once your
  Total Finances pass $200,000, "you may not use Unity Personal at all, even for internal projects or
  prototyping." If you do contract work, your *client's* revenue and funding count.
- **No mixing tiers.** You may not use tiers with different thresholds at the same time in one
  organization, or combine projects built simultaneously on different tiers.
- **No runtime fee or revenue share.** Unity canceled the Runtime Fee on September 12, 2024. The terms
  grant the right to distribute the Unity Runtime "without royalty, revenue share, or a runtime fee"
  for projects made with Unity 6 or earlier, provided you pay your seat fees and stay tier eligible.
- **Prior Terms.** If Unity updates the terms in a way that affects your rights, you may keep using
  your current named version (for example Unity 6) under the terms you accepted, unless the law
  requires otherwise. Moving to a later named version accepts the newest terms; Unity 6 to 6.1 does
  not count as a new named version. You must keep records proving which terms you accepted.
- **Credits notice.** If your game has credits, they must include "[Project name] was made with
  Unity®. Unity is a trademark or registered trademark of Unity Technologies" and the Unity copyright
  line given in section 2.12.
- **Splash screen.** Unity's pricing-updates page says the splash screen is optional with Unity 6 on
  Personal.
- **No hosted Editor for others.** You may not make the Editor or its functionality available to
  anyone other than your authorized users through a cloud, SaaS or similar service without a
  separate grant. Running Unity inside your own team's CI or agent pipeline is a different question
  from offering it to outsiders; if you plan either at scale, check Unity's current terms.
- **Unsupported platforms.** You may not distribute modifications that target a platform Unity does
  not support without a separate grant.
- **Prices move.** Unity raised Pro and Enterprise prices 5% from January 12, 2026 (announced November
  10, 2025). Anything not listed here, such as account and activation rules or the terms on output of
  Unity's AI features: check Unity's current terms.

## Unity code licenses you will meet

| code | license | what it means for you |
|---|---|---|
| Your own scripts | yours | license them as you like |
| [Unity-Technologies/UnityCsReference](https://github.com/Unity-Technologies/UnityCsReference) | Unity Reference-Only License | read it to understand the engine; its README says the terms "do not permit you to modify or redistribute the C# code". Stricter than `study only` |
| Many Unity samples and packages, for example [EntityComponentSystemSamples](https://github.com/Unity-Technologies/EntityComponentSystemSamples) | [Unity Companion License](https://unity.com/legal/licenses/unity-companion-license) | usable only "in connection with" content made under a valid Unity engine license, and never to build a competing product. Code under it cannot move to another engine, so it is not `copy` in this chassis's sense |
| Packages from the Package Manager | each package's own terms | section 2.7 of the terms: a package "may be subject to separate or additional terms" |
| Community Unity projects on GitHub | their own license | apply the chassis reuse classes as usual |

## Unity projects in this chassis

**Starter templates.** [`scaffolds/scaffolds.md`](../scaffolds/scaffolds.md) lists 10 repositories
under Unity and one Unity kit under "Any engine", all MIT, verified on GitHub on 2026-09-23. The
ones worth starting from:

| repository | stars | last push | use it for |
|---|---|---|---|
| [SamuelAsherRivello/unity-project-template](https://github.com/SamuelAsherRivello/unity-project-template) | 143 | 2025-09-28 | a general project layout with C# coding conventions |
| [striderzz/2D-Platformer-Unity](https://github.com/striderzz/2D-Platformer-Unity) | 139 | 2024-05-16 | a 2D platformer with a player controller |
| [Roo-Roo-Roo/survivors-roguelike-kit](https://github.com/Roo-Roo-Roo/survivors-roguelike-kit) | 31 | 2026-07-26 | a complete 2D survivors-like, first released on the Asset Store |
| [hsadler/unity-2d-topdown-template](https://github.com/hsadler/unity-2d-topdown-template) | 32 | 2024-01-27 | a 2D top-down game |
| [IvanMurzak/Unity-Package-Template](https://github.com/IvanMurzak/Unity-Package-Template) | 105 | 2026-05-27 | publishing your own reusable package to OpenUPM or npm |
| [OmiyaGames/template-unity-package](https://github.com/OmiyaGames/template-unity-package) | 72 | 2024-09-03 | the same, as a GitHub template |

Several of these have not been pushed in over a year: open them in your Unity version before you
build on them. The rest of the list is niche (a VR template for 2022 LTS, a modding template, a
blockchain sample, a T4 text processor, an MVVM framework).

**Catalog.** A keyword search of [`data/catalog.json`](../data/catalog.json) finds 51 rows that
mention Unity: 30 `copy`, 9 `study only`, 1 `library use`, 11 `check first`. Some match only by
keyword, so confirm the engine in each repository.

```sh
jq -r '.entries[] | select([.name, .description, (.labels // [] | join(" ")), (.deps // "" | tostring)]
  | map(. // "") | join(" ") | test("\\bunity\\b"; "i")) | [.reuse, .license, .stars, .repo] | @tsv' data/catalog.json
```

The most useful `copy` rows: [Red Runner](https://github.com/BayatGames/RedRunner) (2D platformer,
MIT), [UltraStar Play](https://github.com/UltraStar-Deluxe/Play) (singing game, MIT, active),
[2D Platformer Hunter](https://github.com/ta-david-yu/2D-Platformer-Hunter) (a platformer
controller, MIT) and [Daggerfall Unity](https://github.com/Interkarma/daggerfall-unity) (MIT, active).
Daggerfall Unity and several other "remake" rows need the original commercial game's data; the code
license says nothing about those assets.

## Bringing Blender, GIMP and Krita art into Unity

The art tools are open source even though Unity is not. [Blender](https://www.blender.org/about/license/)
is GPL (source GPL v2 or later; binaries GPL v3 or later), and its license page says "What you create
with Blender is your sole property." [GIMP](https://www.gimp.org/docs/userfaq.html) is GPL v3 or
later, and its FAQ says it "doesn't put restrictions on the kind of work you produce with it."
[Krita](https://github.com/KDE/krita) is GPL-3.0. The GPL covers the tools, not the art you make.
[Aseprite](https://github.com/aseprite/aseprite) is source-available under its own EULA, not open
source. See [`art/blender.md`](../art/blender.md) and [`art/2d.md`](../art/2d.md) for the tools.

**3D models.** Per Unity's [model formats page](https://docs.unity3d.com/Manual/3D-formats.html):

- Unity reads `.fbx`, `.dae`, `.dxf` and `.obj` directly. Export `.fbx` from Blender, which ships
  FBX and glTF 2.0 exporters as core add-ons.
- Unity can import a `.blend` file, but only when Blender is installed on the machine, and then it
  converts it to FBX; "everybody working on your Unity project must have the correct software
  installed." Unity's advice is to export `.fbx` instead.
- glTF is not in Unity's built-in list. Use [Unity glTFast](https://github.com/Unity-Technologies/com.unity.cloud.gltfast)
  (package `com.unity.cloud.gltfast`, Apache-2.0 per its README) or Khronos
  [UnityGLTF](https://github.com/KhronosGroup/UnityGLTF) (MIT). glTF keeps the same file usable in
  Godot, Bevy, three.js and Defold.
- Keep editable sources (`.blend`, `.xcf`, `.kra`, `.aseprite`, `.svg` masters) in an `art-src/` folder
  outside `Assets/`, where Unity never imports them, and export engine-ready files into `Assets/Art/`.
- **FBX from Blender, settings to start from.** In Blender's FBX exporter: Apply Scalings **FBX Units
  Scale** (the default is All Local), Forward **-Z** and Up **Y** (the exporter's defaults), Apply Unit
  on, and Apply Transform off for anything rigged: Blender marks it experimental and "known to be broken
  with armatures/animations". In Unity's Model import settings, keep Convert Units on and turn on
  **Bake Axis Conversion**, which bakes the axis change into the vertex and animation data instead of
  rotating the root object. Export a 1 m cube and a forward-facing character first, check both in
  Unity, and save the exporter and import settings as presets. More in
  [`art/blender.md`](../art/blender.md#exporting-to-engines).

**2D art.** Unity [reads](https://docs.unity3d.com/Manual/ImportingTextures.html) BMP, EXR, GIF, HDR,
IFF, JPG, PICT, PNG, PSD, TGA, TIFF and SVG, and flattens multi-layer PSD and TIFF files on import
without changing the file. In a 2D project images import as sprites. Export PNG from GIMP or Krita.
For Aseprite files, Unity's [2D Aseprite Importer](https://docs.unity3d.com/Packages/com.unity.2d.aseprite@1.1/manual/index.html)
package (`com.unity.2d.aseprite`) imports `.aseprite` directly; with it, the `.aseprite` file is the
engine-ready file and goes in `Assets/Art/`.

Record every asset you did not make, with its license, in the game repo's `THIRD_PARTY.md`
([template](../templates/THIRD_PARTY.md)). Record AI-generated and AI-assisted art in the same file,
in its section "AI-generated and AI-assisted assets", not in a separate file; read
[`ai/graphics.md`](../ai/graphics.md) before you ship any.

## Package management

- Dependencies live in `Packages/manifest.json`; the Package Manager writes the resolved versions to
  `Packages/packages-lock.json`. Commit both.
- **Pin git dependencies.** Per Unity's [Git dependency docs](https://docs.unity3d.com/Manual/upm-git.html),
  you can add a revision (tag, branch or commit hash) after `#`; without one, Unity clones the
  default branch and locks onto whatever commit was latest. A branch name moves; pin a tag or a
  commit hash. Example: `https://github.com/CoplayDev/unity-mcp.git?path=/MCPForUnity#v10.2.0`, the
  latest release on 2026-09-23. That project's README defaults to `#main`, and the `#v10.0.0` it
  suggests (2026-06-30) is four releases old.
- **Scoped registries** add third-party sources. [OpenUPM](https://github.com/openupm/openupm)
  (BSD-3-Clause) is a community registry of open-source packages; each package keeps its own license
  and is someone else's code running in your Editor.
- Asset Store assets carry their own license terms: check them before you commit such files to a
  public repository.

## AI tooling

**Unity's own.** Unity's AI Assistant package (`com.unity.ai.assistant`, Unity 6 or later) includes
a [Unity MCP server](https://docs.unity3d.com/Packages/com.unity.ai.assistant@2.20/manual/integration/unity-mcp-overview.html).
It talks to the Editor over a local named pipe or Unix socket through a relay installed in
`~/.unity/relay/`; direct connections from external MCP clients need approval in Project Settings,
while Unity's own AI gateway connections are approved automatically. The current docs mark it
**deprecated** in favor of the [Unity CLI](https://docs.unity.com/en-us/unity-cli), which Unity
labels experimental. Unity's AI tools are a paid subscription after a 14-day trial.

**Community MCP servers** (from [`scaffolds/mcps.md`](../scaffolds/mcps.md), checked 2026-09-23). Each
row says what the tool listens on, what it runs and what leaves your machine; go through the
[safe setup checklist](../ai/graphics.md#safe-setup-checklist) before you install any of them.

| repository | license | stars | latest release | what it does | risk, and a pinned install |
|---|---|---|---|---|---|
| [CoplayDev/unity-mcp](https://github.com/CoplayDev/unity-mcp) | MIT | 14,437 | v10.2.0, 2026-09-01 | Unity 2021.3 LTS to 6.x; Python 3.10+ via uv; manages assets, scenes and scripts | serves HTTP on 127.0.0.1:8080 by default, with no authentication in local mode; binding all interfaces is an opt-in setting, so leave it off, and never use its remote-hosted mode. Its script tools write C# that Unity compiles and runs. Usage telemetry is on unless `UNITY_MCP_DISABLE_TELEMETRY=true`. It starts its Python server with `uvx`. Pin `...MCPForUnity#v10.2.0` or `openupm add com.coplaydev.unity-mcp@10.2.0` |
| [IvanMurzak/Unity-MCP](https://github.com/IvanMurzak/Unity-MCP) | Apache-2.0 | 4,328 | 0.92.0, 2026-09-23 | Editor and in-game runtime; `script-execute` compiles and runs C# with Roslyn; stdio or HTTP transport | **its quick-start CLI signs in to ai-game.dev, and the agent config it writes sends tool traffic, `script-execute` included, through a hosted relay by default** (`https://ai-game.dev/mcp/p/<pin>`), with the credential in `~/.ai-game-dev/credentials.json`. Use Custom mode with a loopback URL: `UNITY_MCP_CONNECTION_MODE=Custom` and `UNITY_MCP_CLOUD_URL=http://localhost:8080`; its local server (GameDev-MCP-Server) then binds loopback and checks `Origin`, but requires no authentication unless you configure OAuth. Pin `openupm add com.ivanmurzak.unity.mcp@0.92.0`, not the README's `releases/latest` installer, and turn off its startup update popup (Project Settings has a team-wide switch) |
| [CoderGamester/mcp-unity](https://github.com/CoderGamester/mcp-unity) | MIT | 1,910 | 1.5.0, 2026-09-03 | Unity 6+, Node.js 18+; the Editor runs a WebSocket server on localhost:8090 | a per-project 256-bit token sent as HTTP Basic credentials, and it refuses browser `Origin` headers. **"Allow Remote Connections" binds `0.0.0.0` over unencrypted `ws://`: leave it off.** The package runs `npm install` for its Node bridge. Pin `https://github.com/CoderGamester/mcp-unity.git#1.5.0` or `openupm add com.gamelovers.mcp-unity@1.5.0` |
| [youngwoocho02/unity-cli](https://github.com/youngwoocho02/unity-cli) | MIT | 313 | v0.4.1, 2026-08-28 | not MCP: one Go binary; its `exec` command runs arbitrary C# in the Editor | its connector package serves HTTP on 127.0.0.1:8090 (or the next free port to 8099) with no authentication, so any program on your machine can run C# through it; it does refuse requests that carry a browser `Origin` header. **Do not pipe its `install.sh` or `install.ps1` to a shell:** they fetch `releases/latest` with no checksum and edit your shell profile. Use `go install github.com/youngwoocho02/unity-cli@v0.4.1`, which Go checks against its checksum database, or download the v0.4.1 binary and compare it with the SHA-256 digest on the release page; pin the connector URL with `#v0.4.1` |
| [Codeturion/unity-api-mcp](https://github.com/Codeturion/unity-api-mcp) | MIT | 67 | v2.1.0, 2026-07-19 | Unity API documentation lookup only; needs no Unity installation | the lowest-risk option for code execution: it runs nothing in Unity. It does download a 20 to 30 MB API database from its GitHub releases on first run and checks for a newer one on every start, and CI rebuilds those weekly, so a pinned package still receives changing content. `uvx unity-api-mcp@2.1.0` |

Skip [notargs/UnityNaturalMCP](https://github.com/notargs/UnityNaturalMCP) (archived) and
[akiojin/unity-mcp-server](https://github.com/akiojin/unity-mcp-server) (marked deprecated).

**These tools run code on your machine with your permissions.** Any server that can write a C#
script can run code, because Unity compiles and runs it. Before you install one:

1. Prefer a well-maintained project: recent releases, an issue tracker that gets answers, a
   `SECURITY.md`.
2. Read the code, at least the tool list and the network setup.
3. Pin a release tag or commit hash in `manifest.json`; never track `main`, and decline in-Editor
   update prompts until you have read the new release's diff.
4. Run with least privilege: a dedicated project copy under version control, no credentials in the
   project, and only the tool groups you need.
5. **Never expose an MCP server to the network.** Keep every port bound to localhost, never forward
   it, and do not use "remote" or hosted modes.
6. Never ship an MCP bridge or runtime AI plugin in a release build.

The workflow for building with Claude, Codex and Grok is in [`ai/README.md`](../ai/README.md).

## Keeping game code portable

- Put the rules (combat math, inventory, save format, level generation) in plain C# classes with no
  `UnityEngine` references, and keep a thin layer of MonoBehaviours that calls them. Test that core
  with `dotnet test`, outside the Editor.
- That core can move to [MonoGame](others.md#monogame-c) or to [Godot](godot.md)'s .NET build, which
  both run C#. Godot's [C# docs](https://docs.godotengine.org/en/stable/tutorials/scripting/c_sharp/c_sharp_basics.html)
  warn that Godot 4 C# projects "cannot be exported to the web platform" and that Android and iOS
  support is experimental.
- Keep data in JSON or CSV. Scenes, prefabs and ScriptableObject assets are Unity formats and do not
  open in other engines.
- Keep art in glTF, FBX and PNG, with the masters in Blender, GIMP or Krita.
- Keep Unity Companion License and reference-only code out of the portable core.

## When an open-source engine is the better choice

Choose [Godot](godot.md) (MIT) or one of the [other engines](others.md) when:

- you want no revenue tiers, seat fees or terms that can change under you, and the right to read,
  fork and fix the engine itself;
- your revenue or funding is near $200,000, or you do contract work for clients above it;
- you target the web and want small builds (see Phaser, PixiJS, three.js and Excalibur in
  [`others.md`](others.md));
- you want to copy from the catalog's `copy` projects: most are not Unity projects.

Unity remains a reasonable choice when you need its console publishing path (Unity Pro plus each
platform holder's program), your team already knows it, or a specific Unity package does work you
would otherwise build. If you choose it, keep the portable core above so the choice stays reversible.
