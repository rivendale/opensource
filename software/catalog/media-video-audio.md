# Video and audio

Editing, encoding, recording, music, stem separation and video made from code. 21 projects; 11 with a permissive code license. Sorted by reuse, then stars. Part of the [software list](../README.md), which explains the reuse classes.

| project | reuse | license | language | stars | last push | why |
|---|---|---|---|---|---|---|
| [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp) | copy | Unlicense | Python | 194346 | 2026-09-27 | Downloader for online video and audio, for content you have rights to. |
| [ManimCommunity/manim](https://github.com/ManimCommunity/manim) | copy | MIT | Python | 41134 | 2026-09-27 | Python engine for precise mathematical and explanatory animations. |
| [browser-use/video-use](https://github.com/browser-use/video-use) | copy (see note) | MIT | Python | 27749 | 2026-09-24 | Agent skill that edits raw footage into a finished cut by reading word-level transcripts and on-demand filmstrip images instead of watching the video: cuts filler words and dead space, adds subtitles, then renders with FFmpeg. **transcription uploads each source's audio to ElevenLabs and needs an ElevenLabs API key, so keep private footage away from it; put the key in .env yourself and do not paste it into the agent chat, where it lands in the transcript** |
| [motion-canvas/motion-canvas](https://github.com/motion-canvas/motion-canvas) | copy | MIT | TypeScript | 19207 | 2026-07-02 | Animations written in TypeScript with a live preview editor, aimed at explainer and diagram videos made from code. |
| [Wan-Video/Wan2.2](https://github.com/Wan-Video/Wan2.2) | copy | Apache-2.0 | Python | 17665 | 2026-09-21 | Open text-to-video and image-to-video models; its README runs the 5B model on a 24 GB GPU and the 14B models on 80 GB. |
| [beetbox/beets](https://github.com/beetbox/beets) | copy | MIT | Python | 15726 | 2026-09-29 | Music library organizer with metadata auto-tagging. |
| [Zulko/moviepy](https://github.com/Zulko/moviepy) | copy | MIT | Python | 14935 | 2026-08-26 | Python library for cutting, compositing, titling and exporting video from a script. |
| [Tonejs/Tone.js](https://github.com/Tonejs/Tone.js) | copy | MIT | TypeScript | 14748 | 2026-09-29 | Web Audio framework for synths, effects and sample-accurate sequencing in the browser. |
| [WyattBlue/auto-editor](https://github.com/WyattBlue/auto-editor) | copy | Unlicense | Nim | 5388 | 2026-09-19 | Command-line editor that cuts silence and dead space from video and audio automatically, then renders the result or exports a timeline for an editor. |
| [Breakthrough/PySceneDetect](https://github.com/Breakthrough/PySceneDetect) | copy | BSD-3-Clause | Python | 5208 | 2026-09-21 | Finds scene cuts and transitions in video from the command line or Python, and can split the file at each cut with FFmpeg. |
| [nomadkaraoke/python-audio-separator](https://github.com/nomadkaraoke/python-audio-separator) | copy | MIT | Python | 1389 | 2026-08-27 | Command-line and Python stem separation (vocals, drums, bass and more) using the UVR and Demucs model families. |
| [FFmpeg/FFmpeg](https://github.com/FFmpeg/FFmpeg) | library use | LGPL-2.1-or-later (per license file) | C | 64645 | 2026-09-29 | The underlying toolkit for converting, cutting and encoding audio and video. **a build configured with --enable-gpl is GPL-2.0-or-later** |
| [obsproject/obs-studio](https://github.com/obsproject/obs-studio) | study only | GPL-2.0 | C | 76790 | 2026-09-26 | Screen recording and live streaming. |
| [mifi/lossless-cut](https://github.com/mifi/lossless-cut) | study only | GPL-2.0 | TypeScript | 44159 | 2026-09-29 | Fast lossless trimming and cutting of video without re-encoding. |
| [HandBrake/HandBrake](https://github.com/HandBrake/HandBrake) | study only | GPL-2.0 (per license file) | C | 24535 | 2026-09-29 | Video transcoder with sensible presets. |
| [navidrome/navidrome](https://github.com/navidrome/navidrome) | study only | GPL-3.0 | Go | 23892 | 2026-09-29 | Self-hosted music streaming server compatible with Subsonic apps. |
| [audacity/audacity](https://github.com/audacity/audacity) | study only | GPL-3.0 (per license file) | C++ | 18602 | 2026-09-29 | Multi-track audio editor and recorder. |
| [musescore/MuseScore](https://github.com/musescore/MuseScore) | study only | GPL-3.0 (per license file) | C++ | 15155 | 2026-09-29 | Music notation editor with playback, parts and MusicXML import and export. **bundled fonts carry their own terms** |
| [KDE/kdenlive](https://github.com/KDE/kdenlive) | study only | GPL-3.0 | C++ | 5767 | 2026-09-29 | Non-linear video editor. |
| [remotion-dev/remotion](https://github.com/remotion-dev/remotion) | check first | Remotion License (custom) (per license file) | TypeScript | 61093 | 2026-09-29 | Builds videos from React components rendered frame by frame. |
| [Lightricks/LTX-2](https://github.com/Lightricks/LTX-2) | check first | LTX-2 Community License (per license file) | Python | 9550 | 2026-09-29 | Inference and LoRA training code for LTX-2, which generates video with matching audio; weights under the LTX community license, not open source. **the agreement requires a paid commercial license for entities with annual revenues of at least $10,000,000** |

A license marked *per license file* was read from the repository's own license files, because GitHub's detector could not classify it or reported only part of it; the file and the reason are recorded in [tools/overrides.json](../../tools/overrides.json).
