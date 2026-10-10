# Studio evaluation runner

Implementation draft for the [runner contract](../../SPEC-studio.md#evaluation-lane).
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
Node **22 or later**, and ffmpeg **7.0.2** at `/opt/tools/bin/ffmpeg`. UID 1000 must be unused.
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
route name, and that name must appear in the brief. A host such as `pixelforge.example.test` can
therefore be configured explicitly; there is no wildcard or arbitrary URL forwarding.
DNS and TLS validation occur on the host. `--ca-file` can name a public test CA bundle for an
explicit test host; its hash is recorded. It must contain no private key. There is no inherited
TLS environment override. No browser, web search, fetch or connector tool exists.

The proxy log contains only `host`, `method`, `status`, `bytes`, and `time`. Root-owned strace
records refused network syscalls; payload arguments are raw addresses, not headers or bodies.
Only normalized denial metadata enters the published proxy log. The raw audit is destroyed.
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
No downloaded third-party source or binary is committed here. This preparation build needs
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
It attempts a forbidden network connection, root and capture writes, a credential-file read,
and an early-answer read. It also checks empty HOME, a clean environment, zero agent capabilities,
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
  --skill /absolute/skill/SKILL.md --output /absolute/new-result-directory \
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

The final snapshot is scanned again before publication. If `.run/` contains an API key's exact
value or recognizable pattern, or a proxy response contains a key, the result is a failed incident:
no scratch tree is kept, the reason is recorded without the secret, and the operator is told to
rotate the key. Result directories are private by default and are never overwritten. Ordinary
safe agent failures may keep their captured tree. Unsafe archives are refused rather than extracted.

## What remains unverified

The [2026-10-10 synthetic receipt](validation-2026-10-10.json) records a prepared amd64 image
and a passing real self-test: twelve agent refusals/invariants, three checker rules, actual
cgroup limits, and 37 host checks. It used no model or credential and read no studio cases.
The tool recipe's Node account is removed so the supervisor can create its own UID 1000.
The self-test found and corrected tmpfs option compatibility, missing entrypoint PATH, and
the early-answer probe's handling of a protected directory. A successful self-test does not
establish model adapter behavior, paid-service behavior, or studio skill scores.

Independent Claude review and real evaluation-lane acceptance remain pending.
GPU device admission is not implemented; GPU cases
must currently fail rather than silently use a weaker sandbox. The exact tool image and model
snapshot used for scoring remain operator choices. No studio skill has been scored by this draft.
