# Studio evaluation runner

Implementation for the [runner contract](../../SPEC-studio.md#evaluation-lane).
It awaits independent review before scoring studio skills. Runtime probes must pass on the selected image;
host-only checks do not prove container isolation. No studio acceptance cases are included here.

## Choices

Use rootless Podman with delegated cgroup v2 `cpu`, `memory` and `pids` controllers and
seccomp enabled. The runner refuses a host that lacks them. It never substitutes a host
subprocess, drops a resource limit, enables privileged mode, pulls an image or downloads tools.
The runtime gets a fresh HOME and explicit image-store path, without inherited configuration
or credential environment variables. Podman uses cgroupfs inside the caller's delegated scope,
so it does not need an inherited user-bus address. On systemd hosts, launch build and probe
commands with `systemd-run --user --scope --slice=user.slice -p Delegate=yes` before `python3`.
This temporary scope changes no persistent service configuration. Verify the actual limits;
a controller inventory alone does not prove container enforcement.

The base is an operator-prepared OCI tool image, addressed by an immutable manifest digest,
already loaded in that store. It contains Python 3, NumPy, tesseract, strace, a `useradd` command,
Node **22 or later**, Pillow, fontTools, puppeteer-core **25.3.0**, Chrome for Testing
**150.0.7871.46**, and ffmpeg **7.0.2** at `/opt/tools/bin/ffmpeg`. UID 1000 must be unused.
Add the skill's local tools, fonts and model weights
before preparing that image; pin their versions and licenses there. The runner records observed
tool versions and the exact final image identity. A case needing unavailable tools fails; there is
no download fallback. Tesseract's version is recorded; OCR measurements are not an extra runner gate.

The runner layer contains the fixed `studio-runner/0.1.0` agent and supervisor. Its source hashes
are image labels checked before launch. The host runner's hash is recorded and must match its
passing self-test receipt. The small agent uses a non-streaming, tool-calling JSON API
at an operator-selected HTTPS host and path. It has a local shell tool and PNG/JPEG inspection, temperature 0, seed 0,
and a turn limit. Select an immutable provider model snapshot ID, not a `latest` alias.
It reads only the supplied skill and brief, with no user settings, plugins or memory.
Select a vision-capable snapshot for art cases that require image inspection. Provider-specific
APIs beyond this tool-calling JSON protocol need a suitable pinned adapter before scoring.

Egress is a host process listening on a Unix socket. The container has **no IP network**.
The socket relay accepts only POST requests to exact configured HTTPS host/path pairs, refuses
CONNECT and redirects, checks the pinned model and tool envelope, and adds authorization on the
host. Caller headers are discarded. Each paid-service host requires its own explicit key FD and
route name, and that name must appear in the brief. Each paid route also requires positive
`max_calls` and `max_bytes` caps. Bytes count canonical request bodies plus response bodies;
crossing either cap fails the run, including when the agent ignores a refusal. Counts and caps
are recorded separately in `result.json`. A host such as `pixelforge.example.test` can
therefore be configured explicitly; there is no wildcard or arbitrary URL forwarding.
DNS and TLS validation occur on the host. `--ca-file` can name a public test CA bundle for an
explicit test host; its hash is recorded. It must contain no private key. There is no inherited
TLS environment override. No browser, web search, fetch or connector tool exists.

The proxy log contains only `host`, `method`, `status`, `bytes`, and `time`. Root-owned strace
records refused network syscalls; payload arguments are raw addresses, not headers or bodies.
Only normalized denial metadata enters the published proxy log. The raw audit is destroyed.
Refused relay requests record the attempted DNS hostname when valid (lowercase, at most 253
characters); malformed names are `unlisted`. Nonblocking connects in progress and loopback or
Unix socket operations are not denials. Memory pressure reclaimed at `memory.max` is not OOM;
`oom`, `oom_kill` and the process limit's `max` event fail the run.
The relay blocks key-bearing responses and stops accepting connections before the checker starts.

## Image preparation

An amd64 preparation example is [tools.Containerfile](tools.Containerfile): official Node
at a recorded manifest digest, Debian packages from the 2026-10-01 snapshot, and the
[publisher's FFmpeg 7.0.2 static archive](https://johnvansickle.com/ffmpeg/).
Download `https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz`
as `ffmpeg.tar.xz` into a dedicated build context containing that recipe. Its SHA-256 must be
`abda8d77ce8309141f83ab8edf0596834087c52467f6badf376a6a2a4c87cf67`; the recipe verifies it.
The static FFmpeg build is GPL-3.0; its license is kept in the image. Keep the publisher's
corresponding source and comply with redistribution terms before distributing this image.
Also download the [official Chrome for Testing archive](https://storage.googleapis.com/chrome-for-testing-public/150.0.7871.46/linux64/chrome-linux64.zip)
as `chrome.zip`; its SHA-256 is `ad115a7498a17f53f6ed0914458326c6516addc756224db14c32184a9b1ab078`.
Copy `package.json` and `package-lock.json` beside the recipe. The lock includes integrity values
for every npm dependency; installation disables lifecycle scripts.
The [Puppeteer supported-browser table](https://pptr.dev/supported-browsers) pairs version 25.3.0
with this Chrome version. Chrome dependencies follow the [upstream Linux list](https://pptr.dev/troubleshooting#chrome-doesnt-launch-on-linux).
The tool inventory records all four added versions. `STUDIO_CHROME` and `STUDIO_NODE_MODULES`
point to fixed image paths for agents and checkers. Browser calls inside the isolated container
need `--no-sandbox` and `--disable-dev-shm-usage`; the surrounding Podman sandbox stays enforced.
The image retains Chrome and npm package license files; review redistribution terms before
distributing the image. No downloaded third-party source or binary is committed here. This preparation build needs
package networking; evaluation and the runner-layer build do not.

Build that context with Podman using an explicit store, `--pull=never` and the cgroupfs
manager inside a delegated scope. Download the pinned official base first. Export the resulting
tool image to a local directory with `podman push --digestfile /absolute/tools-digest.txt
localhost/studio-tools:2026-10-10 dir:/absolute/tools-export`. This local export records its
manifest digest and makes the immutable `localhost/studio-tools@sha256:...` reference available
in the store. No registry upload is needed. Record the final runner-layer digest the same way.

Run the offline layer build against your already-loaded base digest:

```sh
python3 skills/studio/runner/build_image.py \
  --store /absolute/image-store \
  --base registry.example/tools@sha256:<64-hex-manifest-digest>
```

This executes the image's build instructions on your machine. Use a reviewed base image and
the [tool checklist](../../../ai/graphics.md); the build does not fetch dependencies.
Resolve the resulting OCI manifest digest and load that immutable reference in the same store.
Local tags are build handles, never evaluation pins. The `Containerfile` deliberately has no
mutable default base and the runner has no default model or usable credential.

Run the real isolation self-test before any case:

```sh
python3 skills/studio/runner/selftest.py \
  --store /absolute/image-store \
  --image registry.example/studio@sha256:<64-hex-manifest-digest> \
  --output /absolute/new-selftest-directory
```

This starts an actual container with synthetic inputs, without model calls or credentials.
It attempts a forbidden network connection and root, input and capture writes.
A strict bind-source receipt verifies that credential directories and checker answers are absent. It also checks empty HOME, a clean environment, zero agent capabilities,
read-only inputs, and logged network denial. A failing probe fails the receipt. Startup refusal
is a failed self-test, never evidence that those in-container probes passed.

## Case execution

The case supplies `brief.md`, `inputs/`, `expected.json`, and `check.py`. The skill author does
not read or write studio acceptance cases. The runner stages only the brief and ordinary input
files into read-only agent mounts. Execute bits under `inputs/bin/` are preserved; links, special
files and setuid bits are refused or removed. Checker answers are frozen privately on the host.
The agent sees fixed neutral paths `/scratch/brief.md`, `/scratch/inputs`, and `/skill/SKILL.md`;
the host case folder and `--case-id` are never sent in its start frame or environment. Staging
uses a random private directory. Input and brief contents remain the case author's responsibility.

Provide secrets through already-open file descriptors, not arguments, environment variables,
files under the case, or the image. The key-FD mapping contains numbers only:

```sh
python3 skills/studio/runner/run.py run \
  --store /absolute/image-store \
  --image registry.example/studio@sha256:<64-hex-manifest-digest> \
  --selftest /absolute/selftest/result.json \
  --case /absolute/case --case-id case-name \
  --skill /absolute/skill --checker-lib /absolute/checker-library \
  --output /absolute/new-result-directory \
  --model immutable-model-snapshot --host api.example.test \
  --key-fds '{"api.example.test":3}'
```

This runs untrusted model-selected shell commands in a container. Require the runtime self-test
and independent review of this runner before treating its results as acceptance evidence.
The supervisor is container root with narrowly selected capabilities for tracing, UID changes,
capture and process cleanup. The agent runs as UID 1000 with zero effective capabilities.
No host directory is writable from the container. No host credential or runtime socket is mounted.

Default limits are 20 minutes wall time, 4 CPUs, 8 GiB memory, 2 GiB scratch, 256 container
processes, and 60 turns. CLI limit overrides must correspond to the case's stated needs and are
recorded in the result. Scratch is tmpfs: the input byte count and 32 MiB capture reserve are
subtracted from its writable asset budget. Fresh HOME tmpfs and the private archive audit area
also count against container memory. Swap is disabled. The supervisor checks the actual cgroup
limits rather than trusting runtime flags.

Additional safety bounds: 256 KiB brief and skill, 256 MiB input staging, 512 KiB per answer file,
1 MiB API request/response and checker output, 512 KiB per inspected PNG/JPEG, 32 KiB shell output, 60 seconds per shell
tool, 120 seconds per checker, and bounded protocol/event captures. Reaching a safety bound fails
the run; it is not a pass with truncated evidence. Excess shell output fails the agent phase.

PID 1 kills and reaps **every** other process in its private PID namespace after agent exit,
including detached children. Only then does it write `.run/transcript.md`, `.run/proxy.log`,
`.run/usage.json`, and `.run/run.json`. Transcript turns use `## assistant` and `## tool` headings;
body text is quoted to prevent tool output from forging headings. Tool calls are included.
The host scans that snapshot before transmitting checker answers. The checker runs as UID 1001
in the same container, with the relay closed and IP networking still disabled. It receives
`check.py /scratch /audit/answers/expected.json` and must emit one strict JSON object with case
and nonempty, uniquely identified rule results. Its exit code must be zero.
Its temporary directory is `/home/checker/tmp`, outside the measured scratch tree.
Pass the full skill directory to `--skill` to expose its helpers and references at `/skill`.
The runner copies regular files only, preserves executable bits, hashes each file, and mounts
the copy read-only. Legacy single-file callers expose only `/skill/SKILL.md`.
The shared manifest schema and validator are copied from this checkout, hashed, and exposed
read-only at `/scratch/skills/studio`, matching the relative paths in studio briefs.
`--checker-lib` accepts a trusted library bundle up to 16 MiB. Its regular files are frozen
and individually hashed before launch, then streamed into root-owned `/audit/lib` only after
agent drain and the snapshot scan. The checker receives `STUDIO_LIB` and `PYTHONPATH` pointing
there. The bundle is never mounted or sent during the agent phase.

The final snapshot is scanned again before publication. If `.run/` contains an API key's exact
value or recognizable pattern, or a proxy response contains a key, the result is a failed incident:
no scratch tree is kept, the reason is recorded without the secret, and the operator is told to
rotate the key. Result directories are private by default and are never overwritten. Ordinary
safe agent failures keep scanned evidence. Exceptions record their type, a bounded message
with exact keys and recognizable key patterns redacted before truncation (or
`message: unavailable` if formatting fails), and source filenames,
functions and line numbers without host paths. FD keys containing quotes or backslashes
are refused, so JSON encoding cannot escape an accepted key. Other encoded or split keys
are not redacted; the scanner does not claim detection of arbitrary encodings. Unsafe archives are refused rather than extracted.

If the container fails before a complete capture arrives, the host retains the events it has
received in `.run/` and scans them before retaining anything. `capture_scope` distinguishes
`host-received-events-only` from `drained-scratch-snapshot`; the former proves neither drain
nor a complete output tree. A failed scan suppresses the tree; an unavailable scan is explicitly
`not_completed`, never a clean scan. Checker answers still require the existing successful drain
and snapshot scan. A successful agent response that ends in questions can reach the checker
without producing exports or making tool calls.

After a fresh isolation selftest, run the local regression fixture with the same immutable image:

```sh
python3 skills/studio/runner/tests/short_runs.py --store /tmp/studio-store --image localhost/studio-runner@sha256:YOUR_LOADED_DIGEST --selftest /tmp/studio-selftest/result.json --output /tmp/studio-short-runs
```

This uses an in-process synthetic provider, never a real credential or external API. It checks
one-response questions, capture transport failure, checker failure, preflight failure, redacted
diagnostics and pattern-scan suppression. Its outputs are runner regressions, not skill scores.

## Fixture replay

Before calling a model, use the independently emitted reference/defect trees to
check library, image and capture compatibility through the actual sandbox:

Prepare the bundle and trees from a pinned case checkout using its
`evals/studio/pack_lib.py` and each set's `build/selfcheck.py --emit DIR`, as
described in the [lane integration notes](https://github.com/rivendale/opensource/blob/78ceb3470edce6d5aa1e24138cbf350cc7cdfd1e/evals/studio/LANE.md).
These are checker inputs, not additional instructions for the evaluated skill.

```sh
python3 skills/studio/runner/run.py replay \
  --store /absolute/image-store \
  --image registry.example/studio@sha256:<64-hex-manifest-digest> \
  --selftest /absolute/selftest/result.json \
  --case /absolute/case --case-id case-name \
  --skill /absolute/skill --checker-lib /absolute/checker-library \
  --replay /absolute/emitted-case/replay.json --tree 0 \
  --output /absolute/new-replay-result-directory
```

Repeat for every zero-based tree index in the emitted metadata. The host freezes
and hashes the archive, then streams bounded chunks to an extractor running as
the agent UID, under the same image, cgroups and readonly mounts. No model or
shell command is involved, so large audio/video fixtures do not hit the shell's
16 KiB command limit. Traversal paths, links, special files, duplicate entries and
attempts to replace inputs, shared resources or `.run/` are refused. Execute bits
are retained; setuid/setgid bits are removed. A missing source `inputs/` directory
becomes an empty readonly inputs mount.

After extraction and process drain, the ordinary capture path quotes fixture
transcript turns and records fixture proxy observations, then admits the real
checker and its library. The checker gets the same environment and outside-scratch
temporary directory as a normal run. Replay passes only when every rule ID and
boolean verdict equals the host's `expect`, including intentionally failing
defects. Checker exit 1 is accepted for a replay defect with valid JSON; other
nonzero exits still fail. `result.json` records the checker exit, archive and
metadata hashes, expected verdict and match. Replay refuses credential FDs and
paid routes. Fixture proxy observations are replay data, not actual provider
requests. A replay pass establishes compatibility, not a skill score or model
acceptance.

## What remains unverified

The [2026-10-10 synthetic receipt](validation-2026-10-10.json) records a prepared amd64 image
and the original passing self-test: twelve reported observations, three checker rules, actual
cgroup limits, and 37 host checks. It used no model or credential and read no studio cases.
The tool recipe's Node account is removed so the supervisor can create its own UID 1000.
The self-test found and corrected tmpfs option compatibility, missing entrypoint PATH, and
the early-answer probe's handling of a protected directory. A successful self-test does not
establish model adapter behavior, paid-service behavior, or studio skill scores.

The same receipt also records an actual-container agent flow with a mocked host upstream:
two model responses, one shell-produced marker, assistant/tool transcript turns, proxy records,
token usage and three checker rules passed. The host case identifier was absent from model
messages. A mocked response containing the synthetic authorization marker correctly failed as
an incident, skipped the checker and kept no scratch tree. Neither run used a real credential
or contacted a model service. Provider TLS, real model behavior and paid services remain unproved.

Independent Claude review found checker integration gaps. The [2026-10-11 integration receipt](validation-2026-10-11.json) records
the fixes; real evaluation-lane acceptance remains pending. Three original observations
(credential-file, credential-sentinel, early-answer-mount) used absent paths and could pass
without proving their claimed protection. They are removed from the nine retained probes.
The exact readonly bind-source receipt still verifies no host credentials or answers are mounted.
Write tracing is retained so an `ENOSPC` failure is still detected when an agent later deletes
files before drain. One synthetic five-minute 1080p30 x264 render took 47.37 seconds without
tracing and 51.89 seconds with it (9.55% more wall time; identical 200,607,207-byte videos).
This single pair is not an overhead bound for other workloads. The integration receipt also
records a checker-launched Chrome mobile screenshot, Pillow inspection, fontTools import,
delayed checker-library import, helper execution, safe scratch copying, and the expected paid-cap
and key-response refusals. The [replay receipt](validation-replay-2026-10-11.json) records all 262 trees across 88 cases: independent
reference/defect compatibility and an actual `view_image` round trip with a mock
upstream; provider TLS and real model behavior still require operator acceptance.
GPU device admission is not implemented; GPU cases
must currently fail rather than silently use a weaker sandbox. The exact tool image and model
snapshot used for scoring remain operator choices. No studio skill has been scored by this draft.

Token usage is accumulated from validated assistant response events as they arrive, and retained in `result.json`, `.run/usage.json` and `.run/run.json` when a later tool or turn limit fails the run. A final cumulative event does not add those tokens a second time. Runs failing before any reported response retain an empty usage object.

The [2026-10-12 follow-up receipt](validation-followup-2026-10-12.json) records the failed-run usage regression, fresh self-test and additional phone replays with a current checker bundle. The [provider transport receipt](validation-provider-2026-10-12.json) covers one real response; its one-call cap deliberately stopped the evaluation, so it is not a completed skill score.
