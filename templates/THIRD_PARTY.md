# Third-party code and assets (template)

Every file or asset this game did not write itself, added in the same change that brings it in.
A permissive license still requires keeping the copyright notice; this file is where it lives.

| path in this repo | source (URL at a commit or tag) | license | copyright holder | what we changed |
|---|---|---|---|---|
| `src/vendor/pathfinding.js` | https://github.com/OWNER/REPO/blob/COMMIT/FILE | MIT | [name] | [e.g. ported to TypeScript] |
| `assets/sfx/jump.ogg` | https://example.org/asset-page | CC0-1.0 | [name] | none |

## AI-generated and AI-assisted assets

Every asset an AI model generated or helped make, added when you make it. What to record and why:
[`ai/graphics.md`](../ai/graphics.md#record-provenance-in-third_partymd).

| exported file | source file | base: source, license, URL, download date (or "from scratch") | tools and pinned versions: art tool, MCP server, AI client and model | AI generation: model and version, service, date terms read and where saved, prompt, seed, inputs | human changes | checks: look-alike search date, credits entry |
|---|---|---|---|---|---|---|
| `assets/art/crate.png` | `art-src/crate.blend` | from scratch | Blender [version], [MCP server and version], [client and model] | none | [e.g. retopology, repainted texture] | [date], [credits line or none] |

## Rules

- Code: only `copy`-class licenses (MIT, BSD, Apache-2.0, zlib, ISC, CC0, Unlicense...).
- Libraries under LGPL or MPL: use unmodified, list them here, do not copy their files into ours.
- Assets: record the asset license separately; code licenses do not cover art or audio.
- Paste the full license text for each entry into `licenses/` if the license asks for it
  (MIT, BSD and Apache-2.0 do).
- Apache-2.0 also requires carrying forward the project's NOTICE file, if it has one, and marking
  the files you changed (section 4 of the license).
