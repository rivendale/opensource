# AI and game graphics

Related guides: [AI agents that play or live in games](game-agents.md) and [code-only animation and video](animation.md).

AI helps with game art in two different ways, and they carry different risks:

1. **An AI tool operates your art tools.** Through MCP, Claude Code, Codex or the Grok CLI can
   model in Blender, edit in GIMP, paint in Krita or build scenes in Godot, Unity or Unreal Engine
   while you direct and review. You and the tool make the art; the risk is mostly security, because
   these bridges run code on your machine.
2. **A generative model makes the asset.** An image or 3D model comes out of a prompt. The risk is
   mostly provenance and license: who owns the result, and what the model's terms allow.

Every claim about a tool, server or license below was checked against its repository or official
documentation on 2026-09-23. Stars are a snapshot from that day. This is practical guidance, not
legal advice.

## The tools and their licenses

| tool | open source? | license | what its own documentation says about your output |
|---|---|---|---|
| [Blender](https://www.blender.org/about/license/) | yes | GNU GPL: source GPL-2.0-or-later (Cycles is Apache-2.0); Blender binaries GPL-3.0-or-later | "What you create with Blender is your sole property." |
| [GIMP](https://www.gimp.org/docs/userfaq.html) | yes | GNU GPL, version 3 or later | its FAQ: GIMP "doesn't put restrictions on the kind of work you produce with it." |
| [Krita](https://docs.krita.org/en/KritaFAQ.html) | yes | GNU GPL (GitHub reads GPL-3.0) | its FAQ: "You own your work and can license your art however you want." |
| [Inkscape](https://inkscape.org/learn/faq/) | yes | GNU GPL: most source GPL-2.0-or-later; its `COPYING` file says complete binaries are GPL-3.0-or-later | its FAQ does not address output (see below) |
| [Godot](https://godotengine.org/license/) | yes | MIT | you are your games' "sole copyright owner(s)"; include Godot's copyright notice and license statement in your documentation; the page accepts a link to it in your credits |
| Unity | no | proprietary; its C# source is published "for reference purposes only" | governed by Unity's terms and plan (Unity Personal: under $200K USD revenue and funds raised in 12 months, per its plan page) |
| Unreal Engine | no | the Unreal Engine EULA; the source is on GitHub only after you link an Epic Games account and accept the EULA | governed by the EULA |
| Aseprite | no: source-available | its EULA lets you compile and modify the source only for your own use or to propose a contribution, and forbids distributing copies | governed by the EULA. [LibreSprite](https://github.com/LibreSprite/LibreSprite) is a GPL-2.0 fork of its last GPL commit (2016). |

**The GPL covers the tool, not your art,** for Blender, GIMP and Krita: each project's own
documentation, quoted above, says so. Inkscape's FAQ does not address output. The general rule is in
the [GNU GPL FAQ](https://www.gnu.org/licenses/gpl-faq.html#WhatCaseIsOutputGPL): "The output of a
program is not, in general, covered by the copyright on the code of the program," with an exception
when the output copies text or art that comes from the program itself. Two practical consequences:

- **Bundled content is not your output.** Brushes, templates, sample assets and fonts that ship with
  a tool can carry their own licenses; check before you ship them inside a game.
- **Scripts and add-ons are code.** Blender's license page says published Python scripts and add-ons
  must use a GPL-compliant license, so most Blender add-on code is `study only` in this chassis.

## Letting AI tools drive art tools

**MCP in one paragraph.** The [Model Context Protocol](https://modelcontextprotocol.io/docs/getting-started/intro)
is, in its own words, "an open-source standard for connecting AI applications to external systems."
A server exposes tools; an AI client such as Claude Code, Codex or the Grok CLI discovers them and
calls them. Art-tool servers usually have two parts: a plugin inside the application that listens on
a local port, and an MCP server that your AI client launches over stdio and that forwards each call
to the plugin. Whatever a tool can do, the AI can do, including the tools that delete, overwrite and
run code.

### Maintained servers, per tool

From [`../scaffolds/mcps.md`](../scaffolds/mcps.md), each read on GitHub. A `study only` license
means copy none of its code into your game; running the server locally, unmodified, to make your
art is a different act from copying its code. The last column is what we found reading each
server's code and README on 2026-09-23: what it listens on, what it executes, what it sends out and
how it installs. It is not an audit. Apply the [safe setup checklist](#safe-setup-checklist) to
every row, including the ones with no bold warning.

| tool | server | license, stars | what it can do | risk; apply the [checklist](#safe-setup-checklist) |
|---|---|---|---|---|
| Blender | [ahujasid/mcp-for-blender](https://github.com/ahujasid/mcp-for-blender) | MIT, 29,249 | scene and object info; create, modify and delete objects; materials; viewport screenshots; export GLB or FBX; search and download from Poly Haven, Sketchfab and Poly Pizza; AI 3D models through Hyper3D Rodin and Hunyuan3D; run any Python | `execute_blender_code` runs any Python in Blender. The add-on listens on `localhost:9876` with no authentication, so any local process can send it code, and its "Auto-Start Server" option is on by default, so the socket opens whenever Blender loads: untick it and use "Connect to MCP server" and "Disconnect" per session. Installs from PyPI with `uvx`; the server runs over stdio. An anonymous usage record goes out by default; `DISABLE_TELEMETRY=true` stops it. Ticking the add-on's telemetry consent box, or accepting a client's opt-in prompt, uploads your prompts, generated code, screenshots and scene data, which its README says may be used to train AI models. `BLENDER_MCP_SAFE_MODE=1` makes the server check each model-written script and block `os`, `subprocess`, `socket`, `open` and similar; saving, opening, import and export through `bpy` still work, and its own docs say it guards the MCP path only, not other processes that reach the socket. |
| Blender | [PatrykIti/blender-ai-mcp](https://github.com/PatrykIti/blender-ai-mcp) | Apache-2.0, 57 | a curated tool API instead of raw `bpy` scripts, with inspection, measurement and assertion tools | **Its add-on listens on `0.0.0.0:8765`, every network interface, with no authentication** (`HOST` in `blender_addon/infrastructure/rpc_server.py`), so anyone on your network can drive Blender, including import and export. Fix: change that line to `HOST = "127.0.0.1"` before you install the add-on, or block inbound port 8765 in your firewall. Its README runs the server from the Docker image tag `:latest`: pin an image digest or a release (`v3.3.0` on 2026-09-23). Its optional vision providers (OpenRouter, Google AI Studio) send your viewport images to those services. |
| Blender | [dhakalnirajan/blender-open-mcp](https://github.com/dhakalnirajan/blender-open-mcp) | MIT, 118 | drives Blender, and has its own LLM tools that call a provider you choose: Ollama, LM Studio, llama.cpp or any OpenAI-compatible endpoint | **By default it serves MCP over unauthenticated HTTP on `0.0.0.0:8000`,** with `blender_execute_code`, which runs any Python in Blender, so anyone on your network can run code on your machine. Fix: start it with `--transport stdio`, or at least `--host 127.0.0.1`. Its README passes the provider key on the command line (`--llm-api-key`), where process listings and shell history can see it; set `BLENDER_OPEN_MCP_API_KEY` in the environment instead. Installs from source with `pip install -e`; no releases are tagged, so check out a commit. A local provider keeps only this server's own LLM calls local; your AI client's model still sees every call. |
| Blender | [HoldMyBeer-gg/blend-ai](https://github.com/HoldMyBeer-gg/blend-ai) | AGPL-3.0 (`study only`), 145 | 175 tools, per its description | Its add-on binds `127.0.0.1:9876` with no authentication; that is mcp-for-blender's default port too, so run one at a time. `execute_blender_code` blocks a list of imports and builtins: a denylist, not a sandbox. Its README says it sends no telemetry. Installs from source with `uv pip install -e .`: check out a release tag (`v1.3.2` on 2026-09-23). Copy none of its code. |
| GIMP | [maorcc/gimp-mcp](https://github.com/maorcc/gimp-mcp) | GPL-3.0 (`study only`), 228 | 56 tools: adjustments, transforms, selections, layers, text, filters, export; `get_state_snapshot` returns a PNG preview mid-edit; GIMP 3.2 | Its plugin listens on `localhost:9877` with no authentication and runs any Python it receives (`exec`), from any local process; sandboxing is on its list of future enhancements. Installs by copying the plugin from a clone into GIMP's plug-ins folder; no releases are tagged, so check out a commit. |
| Krita | [nanayax3/krita-mcp](https://github.com/nanayax3/krita-mcp) | MIT, 40 | new canvas, color, brush, strokes, shapes, fill, undo and redo, open and save, export the canvas to PNG | **Its HTTP listener on `localhost:5678` has no authentication and no `Origin` check,** and parses any POST body as JSON. A web page open in your browser can therefore send it commands with a plain cross-origin POST, including save and open at any path. It starts whenever Krita opens a window with the plugin enabled: enable the plugin only for a session, with no other browser tabs open, and disable it afterwards in Krita's Python Plugin Manager, or skip it. One day of commits (2026-02-26); `requirements.txt` is unpinned. Two source files: read both. |
| Godot | [Coding-Solo/godot-mcp](https://github.com/Coding-Solo/godot-mcp) | MIT, 5,802 | launch the editor, run a project in debug, capture output, create scenes, add nodes, load sprites, export a MeshLibrary, manage UIDs | **Stale, with old dependencies:** no push since 2026-04-16; it pins MCP SDK 0.6.0 (2024), and open issue #118 (2026-06-17, unanswered) reports published CVEs in that SDK and in axios. It runs the Godot binary and your project's scripts. Its README runs `npx @coding-solo/godot-mcp` unpinned. Prefer the maintained Godot servers below. If you use it anyway, pin `npx -y @coding-solo/godot-mcp@0.1.1` and read it first. |
| Godot | [hi-godot/godot-ai](https://github.com/hi-godot/godot-ai) | MIT, 2,570 | a live editor: 46 tools and 120+ operations for scenes, nodes, scripts, signals, UI, materials, animation and particles | Both local hops are authenticated and the editor socket is loopback-only. Install a published release (`v4.2.1` on 2026-09-23) and follow its verification steps. Usage telemetry is on by default; `GODOT_AI_DISABLE_TELEMETRY=true` turns it off. Its README says these controls do not protect against a compromised process running as the same user. |
| Godot | [satelliteoflove/godot-mcp](https://github.com/satelliteoflove/godot-mcp) | MIT, 169 | run the game, inject input, read entity state as JSON, take screenshots; built for letting the agent check its own work | `godot_exec` runs GDScript inside the running game. Its editor add-on listens on an unencrypted WebSocket at `127.0.0.1:6550` with no authentication or `Origin` check that we found, so any local process, or a web page in your browser, can connect while no MCP client holds the connection; keep the default Localhost bind mode. Its README runs `npx -y @satelliteoflove/godot-mcp`, which fetches the latest version: pin `@satelliteoflove/godot-mcp@4.1.11`. `--read-only` registers only its 12 observation tools. |
| Unity | [CoplayDev/unity-mcp](https://github.com/CoplayDev/unity-mcp) | MIT, 14,437 | scenes, GameObjects, C# scripts, assets, tests, profiling and builds | It writes C# scripts that Unity compiles and runs in the editor. Anonymous telemetry to `api-prod.coplay.dev` is on by default; `DISABLE_TELEMETRY=true` or its Settings window turns it off. Its local HTTP mode binds to loopback; leave "Allow LAN Bind" off. Install from its git URL pinned to a tag (`#v10.2.0` on 2026-09-23), not `#main`; a release configures your client to run `uvx --from mcpforunityserver==<version>`, which pins that package but not its dependencies. |
| Unity | [IvanMurzak/Unity-MCP](https://github.com/IvanMurzak/Unity-MCP) | Apache-2.0, 4,328 | editor tools, custom tools, and a runtime part that runs inside a compiled game | `script-execute` compiles and runs any C# through Roslyn. Its CLI setup (`unity-mcp-cli login`) signs in to ai-game.dev and, by default, points your AI client at a cloud relay (`https://ai-game.dev/mcp/p/<pin>`), so editor commands pass through that service; for local use, point your client at the stdio server binary in `Library/mcp-server/` instead. Its README installs the CLI with `npm install -g unity-mcp-cli` and links the `latest` release: pin a version (`0.92.0` on 2026-09-23). Keep the runtime part out of release builds unless you designed for it. |
| Unity | [CoderGamester/mcp-unity](https://github.com/CoderGamester/mcp-unity) | MIT, 1,910 | editor control over a WebSocket inside Unity (`localhost:8090`, token authenticated) | Its WebSocket requires a per-project token and rejects browser `Origin` headers; `add_package` is off by default because packages run editor code when they compile. Leave "Allow Remote Connections" off: it binds to `0.0.0.0`. Its README installs from the bare git URL: add a tag (`#1.5.0` on 2026-09-23). |
| Unreal Engine | [ChiR24/Unreal_mcp](https://github.com/ChiR24/Unreal_mcp) | MIT, 883 | assets, actors, levels, Blueprints, Niagara, Sequencer and console commands | Token auth is on by default; leave `bAllowNonLoopback` off, since it exposes both transports. `execute_python` runs Python in the editor, and console commands pass only a pattern-based blocklist. Its README runs `npx unreal-engine-mcp-server` unpinned: pin `unreal-engine-mcp-server@0.5.30`. |

The finder does not yet search for Inkscape servers. Blender MCP's Sketchfab and Poly Pizza
downloads carry whatever license each author chose, and its Hyper3D and Hunyuan3D generation sends
your prompts and images to those services under their terms: record every such asset in
[`THIRD_PARTY.md`](#record-provenance-in-third_partymd).

## Safe setup checklist

MCP servers and add-ons run code on your machine with your permissions. The MCP specification's
[security best practices](https://modelcontextprotocol.io/specification/2025-06-18/basic/security_best_practices)
list arbitrary code execution and data loss among the risks of local servers.

- [ ] **Prefer well-maintained, widely used projects,** and still treat stars as attention, not an
      audit. Check the last push, open security issues and whether releases are tagged. A repository
      under about 60 days old with a lure's shape (large claims, few commits, a prebuilt binary or
      an install script) is a warning sign, not a candidate.
- [ ] **Read the code before you install it,** starting with the plugin that runs inside the art
      tool. Search it for `exec(`, `eval(`, `subprocess`, the address its socket binds to, outbound
      URLs and telemetry. The notes in the table above came from exactly this reading.
- [ ] **Pin a version or commit,** never a branch or `@latest`, and read the diff before you move
      the pin. For a PyPI server, `uvx mcp-for-blender@2.0.3` (uv's exact-version syntax; 2.0.3 was
      the latest release on 2026-09-23). For an npm server, `npx -y <package>@<version>`. For a
      Unity package, a git URL ending in a tag. For anything else, `git clone` then
      `git checkout <commit>`. When a README pipes a remote script to a shell (`curl ... | sh`),
      download the script, read it, and run the copy you read.
- [ ] **A version pin covers one package, not its dependencies.** `uvx` and `npx` resolve every
      dependency fresh on a cold install, anywhere inside the ranges the package allows
      (mcp-for-blender 2.0.3 asks for `mcp>=1.9.0,<2` and `httpx>=0.27.0`). To pin the whole tree:
      - **Date cutoff:** `uvx --exclude-newer 2026-09-22 mcp-for-blender@2.0.3` ignores every
        package uploaded after that date, so the same command resolves the same versions later.
      - **Vendored copy with its lock file:** clone the repository at a reviewed commit and run it
        from there, `uv run --frozen --directory <clone> mcp-for-blender`, which installs exactly
        what its `uv.lock` lists. At 2.0.3 (commit `7cc6022`) that lock still names the package
        itself as 2.0.0, so `--locked` refuses and `--frozen` is the flag that works. For an npm
        server, `npm ci` in a clone installs exactly what its `package-lock.json` lists.
- [ ] **Keep it local.** Prefer the stdio transport. A plugin that listens must bind to
      `127.0.0.1`, never `0.0.0.0`; never forward its port or put it behind a tunnel. The MCP spec
      says a local HTTP server "SHOULD bind only to localhost" and must validate the `Origin` header,
      because otherwise "attackers could use DNS rebinding to interact with local MCP servers from
      remote websites."
- [ ] **Least privilege.** Run the art tool, its plugin and the server as a separate OS user, or in
      a container or VM, with only the project folder available: no SSH keys, cloud credentials,
      password manager or browser profile. Give asset-service API keys to that user only.
- [ ] **Review every destructive action.** Keep your AI client's approval prompts on for tools that
      delete, overwrite, export over files or run code; never auto-approve a run-code tool.
- [ ] **Commit before each session.** Put the project under version control (Git LFS for large
      binaries) and commit before you start. Blender MCP's README says: "ALWAYS save your work
      before using it."
- [ ] **Know what leaves your machine.** Your prompts and every screenshot go to your model provider.
      Turn off telemetry you did not choose. Stop the plugin's server when you are done.

Registering a pinned server, with telemetry off and safe mode on, in each CLI (checked with
Claude Code 2.1.281, Codex CLI 0.156.1 and Grok CLI 1.0.41):

```sh
claude mcp add blender -e DISABLE_TELEMETRY=true -e BLENDER_MCP_SAFE_MODE=1 -- uvx --exclude-newer 2026-09-22 mcp-for-blender@2.0.3
codex mcp add --env DISABLE_TELEMETRY=true --env BLENDER_MCP_SAFE_MODE=1 blender -- uvx --exclude-newer 2026-09-22 mcp-for-blender@2.0.3
grok mcp add blender -e DISABLE_TELEMETRY=true -e BLENDER_MCP_SAFE_MODE=1 -- uvx --exclude-newer 2026-09-22 mcp-for-blender@2.0.3
uvx --exclude-newer 2026-09-22 mcp-for-blender@2.0.3 install-addon   # the matching Blender add-on
```

Safe mode checks only scripts the model sends through the server; the add-on's socket still takes
code from any local process. Untick the add-on's "Auto-Start Server" option and click "Disconnect"
in its panel when the session ends.

## Prompt patterns that work

**Write the asset spec first.** A model guesses every number you leave out. Keep the shared parts
(palette, scale, style) in `docs/art-style.md` and point every prompt at it.

```text
Read docs/art-style.md. Make a wooden crate prop for our top-down 3D game.
Budget: under 500 triangles, one material, one 512x512 texture.
Scale: 1 unit = 1 meter; 0.8 m cube; origin at the bottom center.
Palette: only the 8 hex colors in docs/art-style.md.
Style: flat-shaded low poly, matching assets/props/barrel.glb.
Source: save the working file as art-src/props/crate.blend, outside the engine project.
Export: glTF 2.0 binary to assets/props/crate.glb; apply transforms; no cameras or lights.
Done when: you report triangle count, dimensions and material count read from the scene,
and show a viewport screenshot. Change nothing else in the file.
```

- **One change, then look.** Ask for a screenshot after each step: Blender MCP has
  `get_viewport_screenshot`, GIMP MCP `get_state_snapshot`, Krita MCP `krita_get_canvas`, and
  satelliteoflove's Godot server `screenshot_game`. Correct from the picture, not from the model's
  description of it.
- **Measure, do not trust vision.** Ask for numbers read from the scene: triangle count,
  bounding box, texture size, file size. blender-ai-mcp puts it well: "Vision assists
  interpretation, while deterministic measurement and assertions provide the final truth layer."
- **Turn repeated work into a script.** Once a step works, ask for a Blender Python script in
  `tools/`, review and commit it, then run it without the AI:
  `blender -b art-src/props/crate.blend --python-exit-code 1 --python tools/export_props.py`.
  Without `--python-exit-code 1`, a script that raises an exception still exits 0 and the failure
  looks like success. The script is repeatable and reviewable; a chat session is neither.
- **Keep sources out of the engine's import path.** Keep `.blend`, `.kra`, `.xcf`, `.aseprite` and
  source `.svg` files in an `art-src/` folder outside the engine project, and export engine-ready
  files into the project's assets folder. In Godot, if the sources must sit inside the project, put
  an empty `.gdignore` file in that folder so Godot does not import them. Godot's documentation
  lists glTF 2.0 as its recommended 3D format; importing `.blend` files directly requires Blender
  installed on every machine that opens the project.
- **Give references you have the right to use,** such as your own sketches or CC0 assets, and say
  what to take from each (silhouette, palette, proportions).

## Generating images and 3D models with AI

**Read the model's terms, both halves.** A model license can treat running the model and using its
output differently. The FLUX.1 [dev] license, read on 2026-09-23, grants use of the model for
non-commercial purposes and says revenue-generating use is not one, yet its output clause says "You
may use Output for any purpose (including for commercial purposes)," except to train a competing
model. It also requires content filtering or review of output, and AI disclosure where the law
requires it. FLUX.1 [schnell], from the same company, lists Apache-2.0 on its model card. Read the
license and the service terms of the exact model you run, and save a copy with the date.

**Ownership may be thin.** The U.S. Copyright Office's report on copyrightability (January 29,
2025) concludes that "Copyright does not extend to purely AI-generated material, or material where
there is insufficient human control over the expressive elements," and that "prompts do not alone
provide sufficient control." Human selection, arrangement and creative modification can be
protected. A fully generated asset may be one you cannot stop others from copying. Other countries
differ.

**Stores ask.** Steam's content survey asks you to disclose AI content that ships with the game and
content generated while it runs. You "promise Valve that your game will not include illegal or
infringing content," and Valve reviews AI output the same way as other content.

**Style drifts.** Generated sets rarely match each other. Fix a palette, a resolution and a
reference sheet; keep the same model version and settings for a whole set; then finish every asset
by hand in GIMP, Krita or Blender (palette remap, cleanup, consistent outlines or texel density).

**A CC0 base plus AI touch-up is safer than a fully generated asset.** Start from a known-clean
base such as [Kenney](https://kenney.nl/support), [Poly Haven](https://polyhaven.com/license) or
[ambientCG](https://docs.ambientcg.com/license/), all CC0 by their own license pages. Kenney's page
says the game assets on its asset pages are CC0; a Kenney starter kit can bundle other material:
[Starter-Kit-3D-Platformer](https://github.com/KenneyNL/Starter-Kit-3D-Platformer) ships the Lilita
One font under the SIL Open Font License 1.1, whose license file must ship with the game. Read the
license files in each download. [Quaternius](https://quaternius.com/license.html) is no longer CC0:
the Quaternius Asset License v1.0 (updated 2026-08-28) allows its models in commercial games with
no credit but forbids redistributing the assets as assets. Then:

- the license of the bulk of the asset is known and needs no attribution;
- your edits add human authorship the Copyright Office recognizes;
- the AI's contribution is bounded and written down, so a store question has an answer;
- a fully generated asset has unknown training provenance and may resemble existing work. Before
  shipping any generated asset, search for look-alikes of known characters, logos and brands.

## Record provenance in THIRD_PARTY.md

Provenance lives in one place: the **AI-generated and AI-assisted assets** section of your game's
[`THIRD_PARTY.md`](../templates/THIRD_PARTY.md#ai-generated-and-ai-assisted-assets). Add an asset's
entry when you make it, not before release. For each asset, record:

- the exported file, and its source file in `art-src/`;
- the base, if any: source name, license, URL and download date (or "made from scratch");
- the tools: the art tool's version, the MCP server and its pinned version, the AI client and model;
- AI generation, if any: model and version, service, the date you read its terms and where you
  saved a copy, the exact prompt, the seed and the input files you supplied;
- the human changes: for example retopology to 480 triangles, a repainted texture, new UVs;
- the checks: the date of your look-alike search, and the credits-screen entry when a license
  needs one.

Before a release, ask a model to list every file under `assets/` with no entry in that section, and
every entry whose base or AI terms are missing. Fix those before you ship.
