# Game audio with open-source tools

Sound effects, music and voice for small games, made with open-source tools and processed by a script
you can rerun. Versions and dates were checked on 2026-10-01 against each project's releases. Sprites
and tiles: [2d.md](2d.md). Music and sound made from code inside a video or animation:
[../ai/animation.md](../ai/animation.md#music-and-voice). Video tools: [../ai/media-studio.md](../ai/media-studio.md).

## Pick the tool for the job

| job | tool | version, checked 2026-10-01 | license | open source? |
|---|---|---|---|---|
| retro sound effects, designed in a browser and played from code | [jsfxr](https://github.com/chr15m/jsfxr) | 1.4.1 (npm, 2026-05-05) | Unlicense | yes |
| recording, cleanup, cutting, effects | [Audacity](https://github.com/audacity/audacity) | [4.0.1](https://github.com/audacity/audacity/releases/tag/Audacity-4.0.1) (2026-09-30) | GPL-3.0 (its license file; GitHub cannot identify it) | yes |
| music: sequencer, synthesizers, samplers | [LMMS](https://github.com/LMMS/lmms) | stable 1.2.2 (2020); 1.3.0-alpha.2 (2026-09-06) | GPL-2.0 | yes |
| music generated from a prompt, locally | [ACE-Step 1.5](https://github.com/ace-step/ACE-Step-1.5) | read the repository's current release | MIT code | yes (code); check the weights' terms |
| batch conversion and loudness | [FFmpeg](https://github.com/FFmpeg/FFmpeg) | your distribution's build | LGPL-2.1-or-later, or GPL when built with `--enable-gpl` | yes |

**What the licenses mean for your sounds.** The GPL covers Audacity's and LMMS's code, not the audio
you record or compose with them (see [../ai/graphics.md](../ai/graphics.md#the-tools-and-their-licenses)
for the general rule). Bundled presets, samples and sound banks can carry their own licenses: check
any sample you keep in a shipped track. jsfxr's Unlicense puts it in the `copy` class: you may copy
its player code into a game, and list it in `THIRD_PARTY.md`.

## Sound effects

- **jsfxr** is the fastest route to a coherent set of retro effects: tweak a preset (jump, coin,
  hit, explosion) at [sfxr.me](https://sfxr.me), keep the parameter string, and either export a WAV
  or have the game play the parameters through the jsfxr library. Keeping parameters in the repository
  means every sound is a diff an AI tool can read and change. The arcade playbook lists it
  ([../playbooks/arcade.md](../playbooks/arcade.md#4-reusable-permissive-code)).
- **Recorded effects** go through Audacity: trim silence, normalize, fade the ends, export a WAV
  master, then convert by script.
- **Keep masters and exports apart,** as with art: WAV or FLAC masters in `audio-src/` outside the
  engine's import path, compressed exports (Ogg Vorbis, or what your engine and target browsers
  support) in the assets folder.

## Music

- **LMMS** has had no stable release since 1.2.2 in 2020; 1.3 is in alpha (1.3.0-alpha.2 on
  2026-09-06). Expect to use the alpha, and save projects often.
- **ACE-Step 1.5** generates music from a text prompt and optional lyrics on your own GPU. Its code is
  MIT; ACE-Step 1.0 lives in a different repository ([ace-step/ACE-Step](https://github.com/ace-step/ACE-Step))
  under Apache-2.0. **It runs code and downloads model weights:** read the repository, pin a release or
  commit, read the weights' license, and apply the [safe setup checklist](../ai/graphics.md#safe-setup-checklist).
  Generated music has the same ownership questions as generated art
  ([../ai/graphics.md](../ai/graphics.md#generating-images-and-3d-models-with-ai)); record the model,
  prompt, seed and date in `THIRD_PARTY.md`.
- **Music written as code** (Tone.js in the browser, or a Python score rendered to a file) is covered
  in [../ai/animation.md](../ai/animation.md#music-and-voice).

## Automate the conversions

One script turns every master into engine-ready files, so an agent or a person can rebuild them all:

```sh
# tools/export_audio.sh: WAV masters in audio-src/ to loudness-matched Ogg files in assets/audio/.
set -euo pipefail
mkdir -p assets/audio
for f in audio-src/*.wav; do
  ffmpeg -nostdin -y -i "$f" -af loudnorm=I=-16:TP=-1.5:LRA=11 -ar 44100 -c:a libvorbis -q:a 5 \
    "assets/audio/$(basename "${f%.wav}").ogg"
done
masters=$(find audio-src -maxdepth 1 -name '*.wav' | wc -l)
exports=$(find assets/audio -maxdepth 1 -name '*.ogg' | wc -l)
if [ "$masters" -ne "$exports" ]; then echo "masters: $masters, exports: $exports" >&2; exit 1; fi
```

`loudnorm` evens out loudness across effects so no sound jumps out; pick one target for the whole
game. **Keep `-ar 44100`** (or 48000): `loudnorm` resamples to 192 kHz internally and, without `-ar`,
writes 192 kHz files. The last lines fail the run when the count of exports differs from the count of
masters, which also catches a stale export whose master was deleted. We ran it on FFmpeg 6.1.1 with
two 44.1 kHz test tones 20 dB apart: two Ogg files out at 44,100 Hz, both measuring -15.9 LUFS, exit 0;
with a stale extra export in the folder it exited 1; and without `-ar` the same command wrote 192,000 Hz.
(Corrected 2026-10-01 after review: the first version had no `-ar` and wrote 192 kHz files.)

## AI assistance

- **No audio tool here has an MCP server this chassis recommends.** Agents work best on audio through
  files and scripts: jsfxr parameter strings, the export script above, and FFmpeg commands they can
  run and check (duration, sample rate and loudness read back with `ffprobe`).
- **Audacity 4 has no scripting pipe yet.** The
  [Audacity 4.0.0 release notes](https://github.com/audacity/audacity/releases/tag/Audacity-4.0.0)
  list "Macro Manager and the scripting pipe" among the Audacity 3 features "not available in
  Audacity 4.0, but we're working on adding them in future releases" (checked 2026-10-01). Audacity 3
  automation and the Audacity MCP servers built on that pipe (`mod-script-pipe`) do not work with
  Audacity 4.0 or 4.0.1: stay on Audacity 3 for automation until the pipe returns.
- **Anything that runs code on your machine,** a model, an add-on or an MCP server, gets the
  [safe setup checklist](../ai/graphics.md#safe-setup-checklist) first.

## Pitfalls

1. **A sample's license is not the tool's license.** Check every bundled or downloaded sample.
2. **Browser audio starts only after a user gesture**; test the first sound on a real page.
3. **Uneven loudness** makes a game feel unfinished; normalize every file to one target.
4. **Alpha software** (LMMS 1.3) can change its project format; keep exports of every track.
