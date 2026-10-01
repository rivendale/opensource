# Code-only animation and video with AI coding agents

Project licenses, versions and vendor terms below were checked on 2026-09-24. Recheck them before installing. Code-only animation draws frames at render time with HTML, Canvas, SVG or WebGL instead of storing image assets. Review animation, renderer and audio code as you would any other executable project. For capturing, assembling and editing game video, with versions pinned on 2026-10-01, see [media-studio.md](media-studio.md).

## Choose a rendering approach

| Tool or library | Use and license, checked 2026-09-24 | Risk and install pin |
|---|---|---|
| [HyperFrames](https://github.com/heygen-com/hyperframes) | Apache-2.0 tooling for turning browser timelines into video files through a headless Chrome and FFmpeg pipeline. It supports CSS, SVG, Canvas and JavaScript animation libraries. Its audio tools combine supplied clips, including TTS, but do not create speech or music from text. [Repository and project site, read 2026-09-24](https://hyperframes.dev/) | Its CLI executes project code and launches a browser and encoder on your machine. No exact release pin is listed here. Review the current release and dependency lock, then pin both before use. See the [safe setup checklist](graphics.md#safe-setup-checklist). |
| [Remotion](https://github.com/remotion-dev/remotion) | React components render frame by frame and can use DOM, Canvas, SVG or WebGL. Its custom Remotion License is free for an individual, a for-profit organization of up to three people, or a nonprofit. A for-profit organization with four or more people needs a Company License, and the license FAQ counts contractors, freelancers and other agencies working on the same project toward that four-person threshold (checked 2026-10-01). Company License pricing: the 2026-09-24 pricing page listed $25 per seat per month without automation, or $0.01 per render in blocks of 1,000 with a $100 monthly minimum for automated rendering. [Terms](https://www.remotion.dev/docs/terms), [pricing](https://www.remotion.dev/docs/license/pricing), [FAQ](https://www.remotion.dev/docs/license/faq), read 2026-09-24. | Rendering executes project JavaScript and uses local browser and media tools. The latest release on 2026-10-01 was 4.0.532; pin the exact version and lockfile ([media-studio.md](media-studio.md#video-from-code)). Do not use the library's code outside the license terms. |
| [Motion Canvas](https://github.com/motion-canvas/motion-canvas) | TypeScript timeline library and visual editor for procedural animation. MIT as of 2026-09-24. [License](https://github.com/motion-canvas/motion-canvas/blob/main/LICENSE) and [license discussion](https://github.com/orgs/motion-canvas/discussions/1015), read 2026-09-24. | The editor and project execute JavaScript on your machine. Its latest stable release, 3.17.2, is from 2024-12-14 (checked 2026-10-01): pin it, lock dependencies, and expect slow maintenance. |
| [Theatre.js](https://github.com/theatre-js/theatre) | Keyframe editor with a code-driven runtime for DOM, Canvas and WebGL projects. `@theatre/core` is Apache-2.0; `@theatre/studio` is AGPL-3.0. The license split was checked in the repository on 2026-09-24. | Project code and the editor run locally. Pin the runtime and, if used, the separate editor package. No exact versions are listed here. |
| [GSAP](https://gsap.com/licensing/) | JavaScript timeline and tween library for DOM, SVG and Canvas. Its No Charge license permits commercial use and AI-generated code, with a restriction on use inside a no-code visual animation builder that competes with Webflow. This license took effect 2025-04-30; the page was read 2026-09-24. [License](https://gsap.com/licensing/), [Webflow announcement](https://webflow.com/updates/gsap-becomes-free). | It runs project JavaScript in the browser or renderer. Pin the package version in the project lockfile; the references checked here did not record a patch version. |
| [Three.js](https://github.com/mrdoob/three.js) | WebGL 3D rendering library. MIT, confirmed from the repository LICENSE on 2026-09-24. [LICENSE](https://github.com/mrdoob/three.js/blob/dev/LICENSE). | Runs project JavaScript and GPU shaders in the browser. Pin the package and lockfile; the references checked here did not record an exact release. |
| [p5.js](https://github.com/processing/p5.js) | Canvas-based creative coding library. LGPL-2.1, checked 2026-09-24. [License](https://github.com/processing/p5.js/blob/main/license.txt). | Runs project JavaScript in the browser. Review how LGPL-2.1 applies to your distribution, then pin the package and lockfile. |
| [Tone.js](https://github.com/Tonejs/Tone.js) | Web Audio library for synthesizers, effects and musical timing. MIT, checked 2026-09-24. [License](https://github.com/Tonejs/Tone.js/blob/dev/LICENSE.md). | Runs audio code in the browser. Pin the package and lockfile; do not pass untrusted code to it. |

HTML, Canvas, SVG and WebGL are rendering surfaces, not licenses or video exporters. A project may combine them with a renderer such as HyperFrames or Remotion. For any tool that executes code locally, read the code and dependencies, pin exact versions, keep it local, and follow the [safe setup checklist](graphics.md#safe-setup-checklist). The references checked on 2026-09-24 do not provide exact release pins for most listed tools, so no unpinned install command is provided.

## Four prompt approaches

These are prompting patterns, not claims about guaranteed results. Each makes a visual target that can be checked in a render.

1. **Study a reference.** Give the agent a reference URL, identify the title and subtitle transitions to reproduce, and require a single HTML file using SVG with no image files.
2. **Set a scene and duration.** Request a 20-second looping Canvas scene with a lighthouse beam over a stormy sea and a quiet Tone.js sound bed. Keep image and sound assets out of the deliverable.
3. **Describe motion separately from appearance.** Supply a character design, ask for SVG paths, then specify a four-second idle cycle with one blink and subtle breathing.
4. **Make the output testable.** Name a three-color palette, flat 3px strokes and no gradients. Specify a 16:9 frame, title timing, a three-bar chart interval and the final fade, then inspect a rendered frame at each transition.

## Music and voice

[Tone.js](https://github.com/Tonejs/Tone.js) can synthesize music and effects in browser code using Web Audio. It is MIT-licensed, checked 2026-09-24. [License](https://github.com/Tonejs/Tone.js/blob/dev/LICENSE.md). [HyperFrames](https://github.com/heygen-com/hyperframes) can mix supplied music, effects or speech into a render, but its audio engine is a mixer, not a text-to-speech or music generator; checked 2026-09-24.

Open voice projects and licenses checked 2026-09-24 include [Kokoro-82M](https://github.com/hexgrad/kokoro) (Apache-2.0, runs on CPU) and [Chatterbox](https://github.com/resemble-ai/chatterbox) (MIT). For music, [ACE-Step 1.5](https://github.com/ace-step/ACE-Step-1.5) is MIT (ACE-Step 1.0, in [its own repository](https://github.com/ace-step/ACE-Step), is Apache-2.0; corrected 2026-10-01) and [YuE](https://github.com/multimodal-art-projection/YuE) is Apache-2.0. [F5-TTS](https://github.com/SWivid/F5-TTS) and [XTTS v2](https://github.com/coqui-ai/TTS) weights use non-commercial licenses. Check the model and voice terms, not just the inference code, and pin versions before installing. These tools execute local code; review them and follow the [safe setup checklist](graphics.md#safe-setup-checklist). HyperFrames remains a mixer, not a text-to-speech or music generator.

Music and effects can also be synthesized offline by a script and handed to the renderer as files. The pattern worth copying is the split: scenes are components, narration and score are rendered to audio files by scripts, and the video renderer only mixes what it is given. Every frame and every sound can then be regenerated from source, reviewed as a diff, and fixed with a one-line critique like any other code. A widely shared explainer film from 2026-09-23 was reportedly made this way (Remotion, SVG and Canvas visuals, open-source text-to-speech, a score written in Python); that account is relayed, not checked, and no repository was found.

## Building a showpiece by iteration

Tidewater is an MIT-licensed browser project built with Three.js, WebGPU and TSL. GitHub metadata verified its creation date as 2026-09-23 on 2026-09-24. In the author's reported opening prompt, the goal was a realistic browser ocean with a 60 fps target. The requested scene included an FFT ocean, air-to-water transitions, caustics, reflections and refraction, subsurface scattering, breaking shoreline waves with foam and spray, wet sand, a boat with wake and bow spray, a fishing village, first- and third-person views, a dynamic sky with volumetric clouds, ACES tonemapping, ambient occlusion and shadows, an underwater reef with fog, and a tuning interface. The prompt also asked the agent to identify useful omissions and keep performance in mind. These creative-process details are relayed from the author's public account; the project's creation date and MIT license were verified from GitHub metadata. [Project and license](https://github.com/dgreenheck/tidewater), checked 2026-09-24.

The reported iteration used about eighty short critiques, each identifying one visible defect or missing detail. Examples included noisy caustics, foam showing inside a wave before its break, grainy clouds and performance regressions. Other requests asked for real-world references or a known implementation when visual behavior needed investigation. Treat this as the author's account of one project, not as an independently measured workflow study.

Lessons from that account: state the target and budget in the opening prompt; inspect each render; give one concrete critique at a time; ask the agent to research a named reference instead of guessing; watch performance through each round; and check the running result after each change.


## GPT-6 Luna as a slow background worker

GPT-6 Luna is a reasonable fit for a bounded task that can finish without a live conversation. In one operator report, deep-reasoning turns took about 2 to 6 minutes and streamed output was not displayed until the turn ended. That is an individual report, not a service guarantee. Use a fast interactive model when someone needs to watch the result arrive.

Run an unattended job in a dedicated Git worktree, give it a narrow prompt and a checkable definition of done, and cap the wall-clock time. For example:

```sh
timeout 20m codex exec \
  -m gpt-6-luna \
  -c model_reasoning_effort="max" \
  --sandbox workspace-write \
  "Update the animation scene. Change only the timing curve in src/scene.ts. Run the project build and report the changed file and result. Stop if the build fails."
```

`codex exec` runs code-writing tasks without interactive approval. Keep the job in a worktree with only the project files it needs, inspect the diff and build output afterward, and retain the timeout because a background agent loop can run away. The `workspace-write` sandbox limits writes to the working tree but is not a security boundary against code with access to that environment. Review the CLI and project before use.

OpenAI's API prices checked 2026-09-22 were $0.10 per million input tokens, $0.01 per million cached input tokens and $0.50 per million output tokens for GPT-6 Luna. GPT-6 Sol was $2, $0.20 cached input and $10 output per million tokens. These are token rates, not a promised cost per task. ([OpenAI API pricing](https://openai.com/api/pricing/), [Codex plan pricing](https://developers.openai.com/codex/pricing/), checked 2026-09-24.)

## Publishing AI-assisted video

Not legal advice. YouTube's monetization and disclosure pages were re-read on 2026-09-29, and the name of the disclosure setting had changed since August 2026, so re-read the platform's current pages before you publish.

- **Never publish a generated export as it is.** Split out its audio, slides and transcript. Add a human layer: a rewritten first-person narration, short synthetic segments with commentary between them, or at least a spoken intro and outro. Re-pace it by cutting dead air and repeated loops and adding B-roll and captions. Write your own title, description and thumbnail.
- **"30 to 50 percent human value-add" is a creator heuristic, not a number in YouTube's policy.** The [monetization policies](https://support.google.com/youtube/answer/1311392) are qualitative: each video "materially varied", reused material changed by "significant original commentary, substantive modifications, or educational or entertainment value". Use the number as a target, never as a guarantee.
- **C2PA Content Credentials are a provenance record, not a test for synthetic content.** A file without them proves nothing either way. YouTube reads them: its [disclosure page](https://support.google.com/youtube/answer/14328491) says content containing C2PA metadata can be labeled as AI automatically, and that such a label cannot be adjusted.
- **Disclosure has two separate mechanisms:** the platform's setting (YouTube Studio's "AI use" setting, required for realistic generated or meaningfully altered content), and wording on screen or in the description. Do both.
- **Most legal exposure comes from the inputs.** List your sources in the description, and flag any paid, proprietary or copyrighted input before rendering. A summary is not fair use because a model wrote it.
- **Machine-generated narration may have thin copyright protection.** The defensible value is in selection, arrangement and editing.
