# Video for games: from code, capture and the editor

Trailers, devlogs, tutorials and explainer clips for a game, built in four stages: video rendered from
code, footage captured from the running game, assembly by script, and hand editing where taste
matters. For each stage, which tool to pick, a pinned version, its license, and what an AI agent can
drive. Animation and music written as code: [animation.md](animation.md). Game audio:
[../art/audio.md](../art/audio.md).

Versions, licenses and prices were checked on 2026-10-01 against each project's releases, license and
product pages. This is practical guidance, not legal advice.

## The stages

| stage | tool | version, checked 2026-10-01 | license | agent or MCP hook |
|---|---|---|---|---|
| video from code | [Remotion](https://github.com/remotion-dev/remotion) | 4.0.532 (npm, 2026-10-01) | Remotion License: source-available, not open source | [Remotion Agent Skills](https://www.remotion.dev/docs/ai/skills); its docs MCP server is [deprecated](https://www.remotion.dev/docs/ai/mcp) in their favor |
| video from code | [Motion Canvas](https://github.com/motion-canvas/motion-canvas) | 3.17.2 (npm, 2024-12-14) | MIT | none; plain TypeScript an agent edits |
| assembly | [FFmpeg](https://github.com/FFmpeg/FFmpeg) | your distribution's build | LGPL-2.1-or-later, or GPL when built with `--enable-gpl` | the command line; an agent writes and runs scripts |
| capture | [OBS Studio](https://github.com/obsproject/obs-studio) | [32.2.2](https://github.com/obsproject/obs-studio/releases/tag/32.2.2) (2026-08-14) | GPL-2.0 | its built-in WebSocket remote-control server (off until you enable it) |
| hand editing | [Kdenlive](https://kdenlive.org/download/) | 26.08.1 | GPL-3.0 | projects are MLT XML files an agent can read |
| hand editing | [DaVinci Resolve](https://www.blackmagicdesign.com/products/davinciresolve) | 21 (free tier) | proprietary, not open source | none recommended here |

## Video from code

**Remotion** renders React components frame by frame. Pin it and commit the lockfile:
`npm install --save-exact remotion@4.0.532` (and the same version for every `@remotion/*` package;
they must match).

- **License, checked 2026-10-01 ([license page](https://www.remotion.dev/docs/license)):** free for
  individuals, non-profits and for-profit companies with up to 3 employees; a larger company needs a
  paid company license. Reuse class `check first`: do not copy its code into your own product.
  **Watch the next major version:** a pull request for Remotion 5
  ([remotion-dev/remotion#3750](https://github.com/remotion-dev/remotion/pull/3750)) would count
  contractors toward the limit, which can move a small studio over it. Recheck the terms before you
  upgrade. Current prices are in [animation.md](animation.md#choose-a-rendering-approach).
- **Agent hook:** Remotion's own Agent Skills teach an agent to create, preview and render
  compositions; the older docs MCP server is deprecated in their favor. The skills are listed, with
  their license, in [../software/catalog/agent-skills.md](../software/catalog/agent-skills.md).
  Skills are instructions that change what an agent does: install from a reviewed commit, not a branch.
- **Rendering runs code:** project JavaScript, a headless browser and an encoder on your machine.

**Motion Canvas** is MIT, TypeScript, with a live preview editor; suited to diagram and explainer
animation. Its latest stable release, 3.17.2, is from 2024-12-14, and only an alpha has followed, so
treat it as low maintenance: pin `@motion-canvas/core@3.17.2` and its sibling packages at the same
version, and expect to fix things yourself.

## Capture from the game

- **OBS Studio 32.2.2** records the game window. For trailers, record at the resolution and frame rate
  you will deliver, with game audio on its own track.
- **Agent hook:** OBS ships a WebSocket server that can start and stop recordings and switch scenes,
  so a script or agent can capture a scripted playthrough. It is off until you enable it in
  Tools > WebSocket Server Settings. **Anyone who reaches that port can control OBS:** keep
  authentication on with a generated password, block the port in your firewall, and turn the server
  off when you are done. Community MCP servers for OBS exist; none were reviewed for this guide.
- **Better still, capture from the game itself:** a deterministic replay or a seeded scripted run
  renders the same footage every time, so a trailer can be rebuilt after a balance change.

## Assembly by script

FFmpeg joins clips, lays music under them and evens out loudness. A script an agent can rerun is
better than a one-off edit:

```sh
# clips.txt lists the clips in order, one per line: file 'capture/01.mp4'
ffmpeg -nostdin -y -f concat -safe 0 -i clips.txt -c copy build/cut.mp4
ffmpeg -nostdin -y -i build/cut.mp4 -i audio-src/theme.wav -map 0:v -map 1:a -shortest \
  -c:v copy -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac build/trailer.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 build/trailer.mp4
```

`-c copy` joins without re-encoding only when every clip has the same codec, resolution and frame
rate; re-encode otherwise. Read back the duration and compare it with what you asked for. We ran these
three lines on FFmpeg 6.1.1 with two 2-second test clips and a 10-second tone: `ffprobe` printed 4.0. An FFmpeg
agent skill that checks its own exports is listed in
[../software/catalog/agent-skills.md](../software/catalog/agent-skills.md).

## Hand editing

- **Kdenlive 26.08.1** (GPL-3.0) is the open-source editor here. Its project file is MLT XML, so an
  agent can read a cut list, rename clips or check durations without driving the interface.
- **DaVinci Resolve 21** is proprietary. Its free tier exports up to UHD at 60 frames per second in
  8-bit; DaVinci Resolve Studio is $295 (prices checked 2026-10-01). No agent hook is recommended here.
- Hand editing is where pacing and taste live. Let agents do the repeatable stages (render, capture,
  assemble, check) and keep a person on the final cut.

## Risks

1. **Source-available is not open source.** Remotion's license limits company size and forbids
   reselling it; it can change at a major version.
2. **Everything here runs code or opens a port:** renderers, skills, OBS's WebSocket server. Apply the
   [safe setup checklist](graphics.md#safe-setup-checklist), pin versions, and keep servers local.
3. **Music and footage licenses.** A trailer reuses your game's audio and any licensed music; check the
   terms cover promotional video, and record generated music in `THIRD_PARTY.md`.
4. **Stores have rules for trailers and AI content.** Read your storefront's current requirements
   before you publish; [animation.md](animation.md#publishing-ai-assisted-video) covers disclosure.
