# Blender for game graphics

Blender models, unwraps, textures, bakes, rigs, animates and renders game assets, and every step can
be scripted. This guide goes from a mesh to a file an engine loads, and from a 3D model to 2D sprites.
Every tool, license and repository below was checked against its repository or official documentation
on 2026-09-23. The scripts were run on Blender 5.2.2 LTS (Linux, headless) against test files; the
results quoted are from those runs.

## Why Blender

**License.** Blender is free software under the GNU GPL. Its
[license page](https://www.blender.org/about/license/) says the source is GPL version 2 or later,
Cycles is Apache 2.0, and binaries ship under GPL version 3 or later. **The GPL covers the program,
not what you make with it:** "What you create with Blender is your sole property", and your artwork,
including .blend files and other files Blender writes, "is free for you to use as you like". Two rules
do reach you: a script or add-on using Blender's API needs a GPL-compatible license **if you publish
it** (MIT qualifies), and [extensions.blender.org](https://extensions.blender.org) requires
GPL-3.0-or-later for add-ons.

**What it covers:** modeling, sculpting, UVs, texture painting, baking, rigging (bundled Rigify),
animation, Geometry Nodes, the Cycles and EEVEE renderers, and a Python API (`bpy`) over all of it.
**Versions:** 5.2 LTS (5.2.2, 2026-09-15) and 4.5 LTS get two years of fixes. Pin one per project;
the API and exporter options change between releases.

**The engines are not all open source.** Godot is MIT licensed. Unity is proprietary: per Unity's
page, Unity Personal is free for individuals and organizations under US$200K of revenue and funds
raised in the last 12 months. Blender files work with both.

## A game-asset workflow

**Budgets and modeling.**
- Set a triangle budget per asset class (hero, prop, background) before modeling, and watch Overlays >
  Statistics. The glTF exporter triangulates and splits vertices at UV seams and flat-shaded edges,
  so the engine gets more vertices than Blender shows.
- Model at real scale, 1 unit = 1 meter. glTF units are meters, and the exporter does not read Unit
  Scale (only the importer does), so leave it at the default 1.0.
- Face the model's front toward -Y. Godot's docs say glTF assets face +Z, which is -Y in Blender.
- Apply transforms, and add a Triangulate modifier with Apply Modifiers on export, as Godot's docs
  recommend, so the engine does not guess at n-gons.

**UV unwrapping.** Mark seams where a cut will not show, then unwrap; Smart UV Project cuts at sharp
angles and suits hard-surface props. Keep texel density (texture pixels per meter) consistent across
neighboring assets; TexTools has tools for it. Leave padding: the bake adds a margin around islands
because filtering and mipmaps bleed across seams.

**Texturing and baking.**
- Build materials on the Principled BSDF node; the glTF exporter reads base color, metallic,
  roughness, normal and emission from it.
- Bake high-poly detail in Cycles: select the high-poly mesh, then the low-poly one (active), enable
  *Selected to Active*, and tune *Extrusion* or *Max Ray Distance*, or use a cage object. The bake
  writes to the active, selected Image Texture node; a material without one bakes nothing.
- Normal maps: tangent space (the default), +Y up. glTF uses +Y, and Godot requires this "OpenGL
  style"; a DirectX-style map needs its green channel flipped.
- Ambient occlusion: bake it, then connect the image to an `Occlusion` input on a node group named
  `glTF Material Output`, which is where the exporter looks for one (glTF uses the red channel).
- Paint in Krita (GPL-3.0) or GIMP (GPL): see [2d.md](2d.md).
  [Material Maker](https://github.com/RodZill4/material-maker) (MIT) makes procedural PBR textures;
  [ArmorPaint](https://github.com/armory3d/armorpaint) source is zlib, but its binaries are paid.

**Rigging and animation.** Rigify generates a control rig from a metarig; per the manual it "does not
attach the rig to a mesh", so you still skin it. Control rigs carry non-deforming bones: Godot's docs
say a model with shape keys needs *Export Deformation Bones Only* or shading breaks. Make one action
per animation (the exporter turns actions into glTF animations); Godot loops clips whose names start
or end with `loop` or `cycle`. Reset to the rest pose before export. Apply Modifiers drops shape keys.

**LODs.** Decimate (*Collapse*, a ratio of faces to keep) on a copy for each level. **Godot generates
LODs on import** with meshoptimizer, so export only full detail for Godot. **Unity builds a LOD Group**
from FBX meshes named `_LOD0`, `_LOD1`, up to eight levels. The glTF exporter has no LOD extension.

## Exporting to engines

**glTF 2.0 is the default.** Godot marks it recommended, and Blender bundles the Khronos exporter
([glTF-Blender-IO](https://github.com/KhronosGroup/glTF-Blender-IO), Apache-2.0). Export `.glb` (one
file) unless you want reviewable JSON or separate textures (`.gltf` + `.bin` + images). It writes +Y
up by default, can limit output to selected or visible objects or the active collection, and on request
writes custom properties as extras. Materials export with backface culling off unless you enable it on
the material, so Godot renders both sides. **Collection exporters** (Blender 4.2+) keep settings per
collection; File > Export All Collections, or `bpy.ops.wm.collection_export_all()`, reruns them all.

**Godot.**
- `.blend` imports directly: Godot calls Blender to make glTF. It needs Blender 3.0+ (3.5+
  recommended; Godot strongly advises an official blender.org build over a distribution package or
  Flatpak) set in Editor Settings > Filesystem > Import > Blender > Blender Path. Every teammate
  needs Blender, and the web and Android editors cannot do it; exported glTF avoids both.
- Name suffixes set node types on import: `-col`, `-convcol` (collision), `-colonly`, `-convcolonly`
  (collision, mesh removed), `-noimp` (skip), `-rigid`, `-navmesh`, `-occ`, `-occonly`, `-vehicle`,
  `-wheel`. FBX imports through ufbx.

**Unity.**
- Reads `.fbx`, `.dae`, `.dxf` and `.obj`; `.blend` only with Blender installed. Its manual: "Don't
  use proprietary file formats in production and export to the .fbx format wherever possible."
- **FBX export recipe.** Model fronts face -Y in Blender (Z up); for Unity, which is Y up with +Z
  forward, export with:
  - *Forward* -Z and *Up* Y (the exporter's defaults), and *Apply Unit* on (also the default).
  - *Apply Scalings*: **FBX Units Scale**. The default, *All Local*, writes the unit conversion into
    each object's transform instead of the file's unit scale.
  - *Apply Transform* off for anything with an armature or animation: the exporter calls it
    experimental and "known to be broken with armatures/animations". *Add Leaf Bones* (on by default)
    appends an end bone to every chain, meant for re-editing the armature from the export; turn it
    off for a game rig.
  - In Unity's Model import settings, keep *Convert Units* on and turn on **Bake Axis Conversion**,
    which "bakes the results of axis conversion directly into" vertex and animation data instead of
    leaving it on the objects' transforms.

  Save it as an export preset, and keep the `.fbx` in the Unity project's `Assets/` and the `.blend`
  outside it (see "Where the files live" below).
- For glTF, use [glTFast](https://github.com/Unity-Technologies/com.unity.cloud.gltfast) (Apache-2.0,
  Unity's package) or [UnityGLTF](https://github.com/KhronosGroup/UnityGLTF) (MIT).
- Before a batch, export a 1 m cube and a forward-facing character and check both in the engine.

| convention | Blender | glTF | Godot | Unity (FBX recipe above) |
|---|---|---|---|---|
| up axis | +Z | +Y (the exporter converts) | +Y | +Y |
| a model's front | -Y | +Z | +Z | +Z (Unity's forward) |
| units | meters at Unit Scale 1.0 | meters | meters | 1 unit = 1 m; FBX Units Scale, Convert Units on |
| names | `crate`, `crate_LOD1`, `crate-col` | object names kept | suffixes read on import | `_LOD0`, `_LOD1` build a LOD Group |

**Where the files live.** Keep `.blend` sources in an `art-src/` folder outside the engine project's
import path, and export engine-ready `.glb` or `.fbx` files into the project's assets folder (Unity:
under `Assets/`). If `art-src/` has to sit inside a Godot project, put an empty `.gdignore` in it so
Godot skips it. The exception is Godot's direct `.blend` import above, which needs the `.blend`
inside the project and Blender on every machine.

## 3D to 2D: sprite sheets and isometric tiles

Rendering a model from fixed angles gives consistent sprites; a new animation is a rerender, not a
redraw. The settings that matter:
- Orthographic camera with **one Orthographic Scale for every sprite**, so pixels per meter match.
- Camera 30 degrees above the ground: a square tile renders twice as wide as tall, the usual
  pixel-art projection. True isometric is 35.264 degrees.
- Transparent film, and the **Standard** view transform; the default, AgX, shifts colors.
- **No pixel filter.** Measured at 64 px: EEVEE with Film > Filter Size 0 gave hard alpha edges (no
  partly transparent pixels); Cycles at its minimum filter width, 0.01, still left 100 to 216 soft
  edge pixels per frame. Set pixel-art textures to *Closest* interpolation, and render at the final size.
- Lights that turn with the camera, or each direction is shaded differently.

`render_directions.py` does all of that for eight directions. Frame 1 is the diagonal view: a 1 m tile
in a 64 px frame spanning 1.414 m came out as a 62 by 32 pixel diamond (the tips lose a pixel).

```python
"""Render one object from 8 directions as sprite frames. Usage:
blender -b hero.blend --python-exit-code 1 --python render_directions.py -- Hero out 64 2.0
(object name, output folder, frame size in pixels, meters across the frame)"""
import math, os, sys
import bpy

args = sys.argv[sys.argv.index("--") + 1:]
target, out_dir = bpy.data.objects[args[0]], os.path.abspath(args[1])
size, meters = int(args[2]), float(args[3])          # keep meters the same for every sprite
scene, render = bpy.context.scene, bpy.context.scene.render
pivot = bpy.data.objects.new("sprite_pivot", None)     # turning the pivot turns the view
scene.collection.objects.link(pivot)
pivot.location = target.matrix_world.translation
cam = bpy.data.objects.new("sprite_cam", bpy.data.cameras.new("sprite_cam"))
scene.collection.objects.link(cam)
cam.data.type, cam.data.ortho_scale, cam.parent = 'ORTHO', meters, pivot
up = math.radians(30)                                  # a square tile renders 2:1
cam.location = (0.0, -20 * math.cos(up), 20 * math.sin(up))
cam.rotation_euler = (math.radians(90) - up, 0.0, 0.0)
scene.camera = cam
bpy.context.view_layer.update()
for light in [o for o in scene.objects if o.type == 'LIGHT']:   # lights turn with the camera
    light.parent = pivot
    light.matrix_parent_inverse = pivot.matrix_world.inverted()
render.resolution_x = render.resolution_y = size
render.resolution_percentage = 100
render.film_transparent = True
render.image_settings.file_format, render.image_settings.color_mode = 'PNG', 'RGBA'
scene.view_settings.view_transform = 'Standard'        # colors as painted, not AgX
if render.engine == 'CYCLES':
    scene.cycles.pixel_filter_type, scene.cycles.filter_width = 'BOX', 0.01  # still soft
else:
    render.filter_size = 0.0                           # EEVEE: hard pixel edges
os.makedirs(out_dir, exist_ok=True)
for i in range(8):     # frame 0 faces the model's front (-Y), then counterclockwise from above
    pivot.rotation_euler = (0.0, 0.0, math.radians(45 * i))
    render.filepath = os.path.join(out_dir, f"{target.name}_{i}.png")
    bpy.ops.render.render(write_still=True)
    if not os.path.exists(render.filepath):
        sys.exit(f"missing frame: {render.filepath}")
print(f"rendered 8 frames of {target.name} to {out_dir}")
```

For animation, loop over the action's frames inside each direction. Pack frames into a sheet as in
[2d.md](2d.md), or try [blender-spritesheets](https://github.com/theloneplant/blender-spritesheets)
(MIT), which does it in Blender with Unity and Godot importers; it was made for Blender 2.81 and runs
bundled executables, so read what it runs and test it on your version.

## Procedural assets with Geometry Nodes

Geometry Nodes edits geometry with a node graph attached as a modifier. For games it pays off in
variation: scatter rocks with *Distribute Points on Faces* and *Instance on Points*, expose *Seed* and
sizes as modifier inputs, and export one variant per seed. **Realize instances before export.**
Measured: a plane scattering 48 cube instances exported as 2 triangles, the plane alone; with a
*Realize Instances* node before the output, 578. The exporter's instance option is experimental.

## Automating with Python

Everything in the UI is reachable from `bpy`, and `blender -b` runs without a window.

- `blender -b file.blend --python-exit-code 1 --python script.py -- args`: Blender stops reading
  options at `--`, and the script reads the rest from `sys.argv`. Arguments run in order, so put the
  `.blend` first and `--python-exit-code 1` before `--python`.
- **Always pass `--python-exit-code 1`.** Without it, a script that raised an exception exited 0 in
  our test.
- `--factory-startup` skips your personal `startup.blend`, so runs match across machines.
- Auto-running scripts inside `.blend` files is off by default; do not pass `-y` for a downloaded file.

**Worked example: export every collection to glTF.** Keep one collection per asset, then run:

```python
"""Export every collection in the scene to its own .glb (Blender 4.2 or later). Usage:
blender -b assets.blend --python-exit-code 1 --python export_collections.py -- out_dir"""
import json, os, struct, sys
import bpy

out_dir = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
os.makedirs(out_dir, exist_ok=True)
def glb_mesh_count(path):      # read the .glb's JSON chunk: what an engine will load
    with open(path, "rb") as f:
        magic = f.read(12)[:4]
        length, kind = struct.unpack("<I4s", f.read(8))
        if magic != b"glTF" or kind != b"JSON":
            return 0
        return len(json.loads(f.read(length)).get("meshes", []))

colls = list(bpy.context.scene.collection.children_recursive)   # linked to the scene only
done, empty, failed = 0, 0, []
for coll in colls:
    if not any(o.type == 'MESH' for o in coll.all_objects):     # includes child collections
        empty += 1
        continue
    path = os.path.join(out_dir, bpy.path.clean_name(coll.name) + ".glb")
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', collection=coll.name,
                              export_apply=True,   # apply modifiers; drops shape keys
                              export_yup=True)     # +Y up, the glTF convention and default
    if os.path.exists(path) and glb_mesh_count(path) > 0:
        done += 1
    else:
        failed.append(coll.name)
print(f"{len(colls)} collections: {done} exported, {empty} without meshes, failed: {failed}")
sys.exit(1 if failed else 0)
```

Test file: five scene collections (one empty, one nested) and one not linked to the scene. Result:
four `.glb` files, one skipped, exit 0; a read-only output folder gave exit 1. A first draft looped over
`bpy.data.collections` and wrote the unlinked one as a 140-byte file with no mesh, which an "is the
file there" check passed. A parent's file also holds its children's meshes; keep asset collections flat.

## Driving Blender with AI tools

**Start with scripts.** Ask Claude or Codex for a `bpy` script, run it headless, check the output: a
script is reviewable, rerunnable and versioned. Name your Blender version; the API changes:

```text
Write a Blender 5.2 Python script, run headless as `blender -b <file> --python-exit-code 1
--python <script> -- <args>`, that <task>. Use only bpy and the standard library. Exit nonzero on
failure, and verify the files you wrote (count meshes or frames) before exiting.
```

**MCP servers** let an assistant drive a running Blender. Read the
[safe setup checklist](../ai/graphics.md#safe-setup-checklist) before installing any of them.
Blender's own server and the Blender entries in [../scaffolds/mcps.md](../scaffolds/mcps.md), each
read at its source on 2026-09-23:

| project | license | what it does | what it listens on, runs and sends | install, pinned |
|---|---|---|---|---|
| [Blender Lab MCP](https://www.blender.org/lab/mcp-server/) | GPL-3.0-or-later | Blender's own: scene analysis and scripting; Blender 5.1+ | add-on on `localhost:9876`, which starts with Blender by default once enabled; we found no authentication in it; runs generated Python through a "weak sandbox" whose source says it "isn't really a sandbox" | `mcp-1.0.3.zip` (add-on) and `blender-1.0.3.mcpb` from the [v1.0.3 release](https://projects.blender.org/lab/blender_mcp/releases) (2026-09-11) |
| [ahujasid/mcp-for-blender](https://github.com/ahujasid/mcp-for-blender) | MIT | scene edits, any Python, GLB/FBX export; Poly Haven, Sketchfab, Poly Pizza; Hyper3D Rodin and Hunyuan3D | add-on socket on `localhost:9876` with no authentication (its README says so); runs any Python unless `BLENDER_MCP_SAFE_MODE=1`; sends an anonymous usage record by default, which its README says may be used to train AI models, until you set `DISABLE_TELEMETRY=true`; Hyper3D and Hunyuan3D send your prompts and images to those services | `uvx --exclude-newer 2026-09-22 mcp-for-blender@2.0.3` (2.0.3 released 2026-09-21); commands below |
| [HoldMyBeer-gg/blend-ai](https://github.com/HoldMyBeer-gg/blend-ai) | AGPL-3.0 (study only) | 175 tools, mesh quality reports, screenshots | add-on on `127.0.0.1:9876` with no authentication; server over stdio; its code tool refuses `os`, `subprocess`, `socket`, `exec`, `eval` and `open` by name; no telemetry, per its README | `git clone`, `git checkout v1.3.2`, `uv pip install -e .` |
| [PatrykIti/blender-ai-mcp](https://github.com/PatrykIti/blender-ai-mcp) | Apache-2.0 | curated tools with measurement and assertion steps, not raw scripts | **its add-on binds `0.0.0.0:8765` with no authentication** (hard-coded as `HOST` in `blender_addon/infrastructure/rpc_server.py` at `4325315`), and its tools save `.blend` files to any path: edit `HOST` to `"127.0.0.1"` before installing and use its Linux `--network host` setup, or block the port in your firewall; optional vision checks call OpenRouter or Gemini | Docker image `ghcr.io/patrykiti/blender-ai-mcp`, documented as `:latest`: pin a digest (`@sha256:...`), and for its HTTP mode publish `-p 127.0.0.1:8000:8000`, not `-p 8000:8000`; latest release v3.3.0 |
| [djeada/blender-mcp-server](https://github.com/djeada/blender-mcp-server) | MIT | 27 tools, Python, headless render jobs | add-on on `127.0.0.1:9876`; every request carries a shared secret from `~/.blender-mcp/token` (mode 0600); server over stdio; `blender_python_exec` runs any Python | `git clone`, `git checkout v0.2.0`, then read `scripts/setup.sh` before running it: it also installs and enables the add-on |
| [sandraschi/blender-mcp](https://github.com/sandraschi/blender-mcp) | MIT | batch export and render | runs `blender --background` by default; `blender_script_execute` runs inline Python; **its optional web dashboard binds `0.0.0.0:10848` and proxies the MCP endpoint**, though its README says localhost: do not start it, or set `host: "127.0.0.1"` in `webapp/frontend/vite.config.ts` first | its README links `releases/latest` for a `.mcpb`, but v0.11.1 (2026-08-17) ships no files and the newest `.mcpb` is v0.5.0; clone instead: `git clone`, `git checkout v0.11.1`, `uv sync` (see its INSTALL.md) |
| [dcc-mcp/dcc-mcp-blender](https://github.com/dcc-mcp/dcc-mcp-blender) | MIT | Streamable HTTP MCP server inside Blender, one gateway for several apps | gateway on `127.0.0.1:9765`; `execute_python` runs any Python unless `DCC_MCP_BLENDER_DISABLE_ARBITRARY_SCRIPT=true` | `pip install dcc-mcp-blender==0.2.9`; **do not run its README's CLI installer**, which pipes a script from the `main` branch straight into a shell |
| [seehiong/blender-mcp-bridge](https://github.com/seehiong/blender-mcp-bridge) | MIT | 98 tools, including 3D-printing checks; no run-code tool found | **the bridge binds `0.0.0.0:8008` with no authentication and allows any CORS origin** (`config.py` and `server.py` at `e1cdb2c`), though its quick start says `127.0.0.1`: `MCP_BRIDGE_HOST=127.0.0.1` keeps it off the network, but any web page you have open can still call it while it runs | `MCP_BRIDGE_HOST=127.0.0.1 uvx --exclude-newer 2026-09-23 blender-mcp-bridge@0.1.4 serve` |
| [dhakalnirajan/blender-open-mcp](https://github.com/dhakalnirajan/blender-open-mcp) | MIT | pairs Blender with a local model (Ollama, LM Studio, llama.cpp) or an OpenAI-compatible service | **defaults to unauthenticated HTTP on `0.0.0.0:8000`** with a `blender_execute_code` tool (`server.py` at `a98c5a8`): run it with `--transport stdio` (or `--host 127.0.0.1`), and pass a provider key in `BLENDER_OPEN_MCP_API_KEY`, not as `--llm-api-key` on the command line as its README shows | no releases: `git clone`, `git checkout a98c5a8`, `pip install -e .` |

`study only` means do not copy that code into yours; running a tool is a separate question from
reusing its source. **Not recommended:** `bpy-dev/blender-mcp` calls itself an "Independent enhanced
distribution of Blender Lab MCP", and its organization and repository were both created on
2026-09-09. Install Blender Lab's server from projects.blender.org instead.

**Security: MCP servers and add-ons run code with your permissions.** Blender Lab's page warns its
server "will execute LLM generated code in Blender without any guards in place to protect your data
from removal or being sent to a remote location" and suggests a virtual machine. The
[safe setup checklist](../ai/graphics.md#safe-setup-checklist) has the full list; for Blender:

- Prefer maintained projects, and read the add-on and server code before installing.
- Pin a release or commit, never latest or a branch. `uvx mcp-for-blender@2.0.3` pins that package
  but not its dependencies, which resolve fresh on each cold install; `--exclude-newer 2026-09-23`
  makes uv ignore anything uploaded after that date, so the install repeats.
- Never pipe a downloaded install script into a shell. Read the script, pin the version it fetches,
  then run it, or use the pinned package instead.
- Least privilege: a user account or VM with no credentials or private files, plus any restricted
  mode offered (`BLENDER_MCP_SAFE_MODE=1` in mcp-for-blender).
- **Never expose an MCP server or its Blender socket to the network.** Four servers above listen on
  `0.0.0.0` (every interface) by default or through a dashboard; check the bind address yourself,
  and for remote work use an SSH tunnel, not an open port.
- Check telemetry: mcp-for-blender sends a minimal anonymous usage record unless
  `DISABLE_TELEMETRY=true`. Save and commit the `.blend` before an agent edits it.

```sh
claude mcp add blender -e DISABLE_TELEMETRY=true -e BLENDER_MCP_SAFE_MODE=1 -- uvx --exclude-newer 2026-09-22 mcp-for-blender@2.0.3
DISABLE_TELEMETRY=true uvx --exclude-newer 2026-09-22 mcp-for-blender@2.0.3 install-addon   # then enable it in Blender; it auto-starts its server (the "Auto-Start Server" option is on by default; the button is "Connect to MCP server")
```

**AI-generated assets.** Text-to-3D services and local pipelines make meshes whose ownership depends
on the service's or model's terms and on unsettled law that varies by country. One local pipeline,
[asset-studio](https://github.com/zorrobyte/asset-studio) (0BSD code, with an MCP server), was created on
2026-09-13, so treat it as unproven: its API binds `127.0.0.1:8090` by default, and
`scripts/bootstrap.ps1` builds Docker images and downloads model weights, including FLUX.2 Klein 9B
under a non-commercial license and a gated matting model. Read the script, each model's license and
the [safe setup checklist](../ai/graphics.md#safe-setup-checklist) before running it. Record every
generated or AI-assisted asset in the game's [`THIRD_PARTY.md`](../templates/THIRD_PARTY.md#ai-generated-and-ai-assisted-assets), in its
"AI-generated and AI-assisted assets" section, read hosted terms for commercial use, check storefront
disclosure rules, and discard anything resembling a known character or product.

## Free assets that work with Blender

| source | license | notes |
|---|---|---|
| [Poly Haven](https://polyhaven.com/license) | CC0 | HDRIs, textures, models; no credit required |
| [ambientCG](https://docs.ambientcg.com/license/) | CC0 1.0 | PBR materials and HDRIs |
| [Kenney](https://kenney.nl/support) | CC0 | game asset packs; do not use the Kenney logo |
| [Poly Pizza](https://poly.pizza/) | CC0 or CC-BY, per model | CC-BY needs credit (about 69% of models, per mcp-for-blender's README) |
| [Blender Studio](https://studio.blender.org/remixing/) | CC-BY | open-movie assets; each states its license; credit the Blender Foundation |
| [OpenGameArt](https://opengameart.org/content/faq) | per asset: CC0, CC-BY, CC-BY-SA, OGA-BY, GPL | share-alike terms on CC-BY-SA and GPL; with several listed, follow one |
| [Quaternius](https://quaternius.com/license.html) | **not CC0 any more**: Quaternius Asset License v1.0 (2026-08-28) | free in commercial games, no credit; no redistributing the assets as assets, which the license says includes a template or asset pack; the version in effect when you downloaded an asset governs it, so record the date |

Record each file's source and license in [`THIRD_PARTY.md`](../templates/THIRD_PARTY.md), and
credit CC-BY work on screen.

## Add-ons worth knowing

| add-on | license | why | install, and what it can reach |
|---|---|---|---|
| glTF 2.0 import and export | Apache-2.0 | the export path above | bundled with Blender |
| Rigify, Node Wrangler | GPL (part of Blender) | control rigs; node shortcuts (Shift+W) | bundled with Blender |
| [ACT: Game Asset Creation Toolset](https://github.com/mrven/Blender-Asset-Creation-Toolset) | GPL-3.0-or-later | batch FBX and glTF export for Unity, Unreal and Godot, origins, renaming, LOD suffixes | extensions platform, 2025.2.1; declares file access only |
| [TexTools](https://github.com/franMarz/TexTools-Blender) | GPL-3.0-or-later | UV layout, texel density, bake modes | GitHub release v1.6.1 (2024-03-13); not on the extensions platform, so it declares no permissions; last commit 2024-12-02, so test it on your Blender version |
| [Goblend](https://github.com/Togira123/Goblend-Export-Addon) | GPL-3.0-or-later | Blender to Godot scenes, collisions, baked materials | extensions platform, 2.1.1; declares file access only |
| [blender-spritesheets](https://github.com/theloneplant/blender-spritesheets) | MIT | animations to sprite sheets | no releases (pin commit `6cf0442`); made for Blender 2.81; runs prebuilt `bin/assembler` executables; their Rust source is in `assembler/`, so build them yourself rather than trust the binaries |
| [MCprep](https://github.com/Moo-Ack-Productions/MCprep) | GPL-3.0-or-later | Minecraft-style renders; its assets need a legal Minecraft copy | GitHub release 3.6.3; checks GitHub for updates by default (turn off *Auto-check for Update*); usage analytics are opt-in |

GPL add-ons are `study only` as code. Every add-on runs Python inside Blender with your permissions,
like an MCP server: install from the extensions platform or the
project's tagged releases, read the `[permissions]` an extension declares (files, network, clipboard,
camera, microphone), pin the version, and follow the
[safe setup checklist](../ai/graphics.md#safe-setup-checklist).

## Pitfalls

- **Exports that look fine and are not:** unrealized instances (count triangles), shape keys dropped
  by Apply Modifiers, a front facing +Y, a Unit Scale other than 1.0. Check one test asset first.
- **A green run that exported nothing.** Pass `--python-exit-code 1` and check the output files.
- **A `.blend` inside the engine project ties everyone to Blender.** Keep it in `art-src/` and commit
  the exported glTF or FBX to the project.
- **Assuming a source is CC0.** Quaternius is no longer CC0 (Quaternius Asset License v1.0,
  2026-08-28); OpenGameArt and Poly Pizza vary per file.
