# AI agents that play or live in games

Project details and activity snapshots were checked on 2026-09-24. Read each current license and code before use. Do not run an agent from an unreviewed branch or connect it to a public game server.

## Minecraft agents

| Project | What it does, license, activity and model | World access and risk |
|---|---|---|
| [rmalde/minecraft-agent](https://github.com/rmalde/minecraft-agent) | A demonstration that attempts a Minecraft Java 1.16.5 speedrun from an empty inventory through the Ender Dragon. No license was declared. GitHub showed it created and last pushed 2026-09-20, with 538 stars on 2026-09-24. It calls GPT-6 Astra by default or GPT-5.6 Sol through OpenRouter for planning, and Jev 1.13 for typed action selection. [README and GitHub metadata, read 2026-09-24](https://github.com/rmalde/minecraft-agent) | It uses Mineflayer against a local vanilla server started by the operator. Its Java observer is described as read-only and local. This is a narrow demo, not a shared-server safety layer. The project materials reviewed here give no release or commit pin, so do not use a floating clone command. Review the code and choose a specific commit before running it. |
| [Mineflayer](https://github.com/PrismarineJS/mineflayer) | JavaScript API for Minecraft bots, including movement, blocks, inventory, crafting and entities. MIT. GitHub showed a 2026-09-22 last push and about 7,492 stars on 2026-09-24. [Project and GitHub metadata, read 2026-09-24](https://github.com/PrismarineJS/mineflayer) | It is a protocol client, not a sandbox, and can connect to the server address its caller supplies. Restrict it to a local test world or a server you control. The project materials reviewed here supply no release pin or safe install command. |
| [Voyager](https://github.com/MineDojo/Voyager) | A Minecraft agent built around a task curriculum, a skill library and self-checking. It calls GPT-4 through the OpenAI API. MIT. GitHub showed its last push as 2024-04-03, making it dormant in this 2026-09-24 snapshot. [README and GitHub metadata, read 2026-09-24](https://github.com/MineDojo/Voyager) | It uses a local Minecraft instance and a Fabric mod bridge. The README does not document shared-world safety controls. It writes and reuses executable code as learned skills. Treat it as code to study until you have reviewed and pinned a specific revision. |
| [MineDojo](https://github.com/MineDojo/MineDojo) | A research framework and simulation suite for Minecraft tasks, with an associated knowledge base. The code is MIT. The included YouTube and Reddit data are listed as CC BY 4.0, while Wiki data are CC BY-NC-SA 3.0. GitHub showed a last push of 2024-03-18 on 2026-09-24. [Repository, README and GitHub metadata, read 2026-09-24](https://github.com/MineDojo/MineDojo) | This is a research environment, not a child-safe multiplayer bot. Check the licenses of code and data separately. The project materials reviewed here give no pinned install revision. |
| [Mindcraft](https://github.com/kolbytn/mindcraft) | An LLM-driven collaborative Minecraft agent built on Mineflayer. MIT. Its README lists OpenAI, Anthropic, Gemini, Ollama and OpenRouter providers, configurable by bot and function. GitHub showed a last push of 2026-06-10 and about 5,788 stars on 2026-09-24. [README and GitHub metadata, read 2026-09-24](https://github.com/kolbytn/mindcraft) | The README says code execution starts disabled and can be enabled with the `allow_insecure_coding` setting. Prompt injection remains possible. It warns against connecting a bot with coding enabled to a public server and suggests Docker before remote-server use, while making clear that Docker does not guarantee safety. The project materials reviewed here have no pinned revision or dependency lock verification, so review and pin the full install before running it. |

[mindcraft-ce](https://github.com/mindcraft-ce/mindcraft-ce) is an MIT-licensed community fork that includes experimental features and unmerged changes from the main project. GitHub showed a 2026-09-22 last push and 139 stars on 2026-09-24. Review it and pin a specific revision before use; it is still subject to the same local-code and world-access risks as its upstream project.

These projects run code on your machine or connect to a game process. Keep experiments in a disposable local world, inspect code and dependencies, and choose a release or commit before installing. Follow the [safe setup checklist](graphics.md#safe-setup-checklist).

## Agent toolkits for game engines

| Toolkit | Scope, license and dated status |
|---|---|
| [Unity ML-Agents](https://github.com/Unity-Technologies/ml-agents) | Trains agents in games and simulations with deep reinforcement learning and imitation learning. Apache-2.0. The project describes reinforcement and imitation learning for Unity environments. Check its current release notes for engine compatibility before upgrading. GitHub showed a last push of 2026-09-17 on 2026-09-24. [README, LICENSE.md and GitHub metadata, read 2026-09-24](https://github.com/Unity-Technologies/ml-agents) |
| [Godot RL Agents](https://github.com/edbeeching/godot_rl_agents) | Connects Godot environments to Python training loops, including Stable Baselines3 and RLlib. MIT. GitHub showed a last push of 2026-07-10 and 1,588 stars on 2026-09-24. [Repository and GitHub metadata, read 2026-09-24](https://github.com/edbeeching/godot_rl_agents) |
| [Unreal Learning Agents](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/PluginIndex/LearningAgents) | Epic's engine plugin for training NPCs with reinforcement and imitation learning. It is distributed with Unreal Engine and governed by Epic's EULA, not a separate permissive open-source license. Documentation is versioned with Unreal releases. [Epic API index, read 2026-09-24](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/PluginIndex/LearningAgents); check Epic's current Unreal EULA before relying on its terms |

These toolkits execute training or game code in local environments. Review their installation instructions, pin a release and dependencies, and use a disposable project. The project pages do not provide an install pin in the material checked here. Review the current installation steps and pin a release and dependencies before use.

## Split planning from action choice

A useful design is to let a large generative model set a goal at a slower cadence, then give a small typed classifier the current state and a fixed list of legal next actions. The calling game code validates the selected action before it can affect the world. The Minecraft demo above documents this division: a generative planner chooses the objective and a typed decision model chooses an action. [Project README, read 2026-09-24](https://github.com/rmalde/minecraft-agent)

[Jev](https://typesafe.ai/blog/introducing-system-one-models-and-jev) is TypeSafe's typed decision service: it takes state plus typed questions and returns choices, scores or yes/no-style decisions. Its public price on 2026-09-24 was $0.042 per million input tokens; the TypeSafe site described output tokens as free. [TypeSafe product page and pricing, read 2026-09-24](https://typesafe.ai/). No accuracy, speed or benchmark figures are included here.

### Real-time games: one planner, many fast deciders

The same split scales to real-time strategy: a large model writes a plan once before an
encounter, and each squad or key unit gets its own small, fast decider that picks the next
action from a list the game code builds, several times a second. The decider never writes
code or free text; it only chooses. That keeps the expensive model out of the tight loop and
keeps every action inside an allowlist. Developers have reported trying this with a hosted
decision model and with a small local model; no public code or paper for those experiments was
found on 2026-09-24, so treat the numbers in such posts as claims.

To experiment in StarCraft II, the maintained Python option is
[BurnySc2/python-sc2](https://github.com/BurnySc2/python-sc2) (MIT, last push 2026-04-25).
DeepMind's [PySC2](https://github.com/google-deepmind/pysc2) (Apache-2.0) and the multi-agent
benchmarks [SMAC](https://github.com/oxwhirl/smac) and [SMACv2](https://github.com/oxwhirl/smacv2)
(both MIT) are widely cited but have had no push since 2024. All four read from GitHub's API on
2026-09-24. You need a licensed copy of the game client to run any of them.

### Tev1: a local option for typed choices (license pending)

[Tev1-4B-experimental](https://huggingface.co/togethercomputer/Tev1-4B-experimental) is a public, ungated supervised fine-tune of Qwen3.5-4B. It takes a structured state, a question and 2 to 24 labeled options, then returns the chosen option's letter. It is an autoregressive, Jev-inspired experiment, not the Jev runtime. A community GGUF build can run through Ollama or llama.cpp, including on CPU; its Q6_K file is 3.46 GB. These model card and build details were checked 2026-09-24.

Its model card says, as read on 2026-09-24, that "the release license for these fine-tuned weights is being finalized before public conversion": the weights are downloadable, but no license for them has been granted yet. Treat it as something to evaluate, not to ship, until that license is published. The [training code](https://github.com/togethercomputer/tev1) is MIT, but its listed training data have mixed, unknown or unspecified licenses, and the recipe warns that redistribution needs license review. Do not infer that the model weights or combined data are MIT licensed. Together's published hosted price on 2026-09-24 was $0.042 per million input tokens, with output free. Use the local model when avoiding a hosted classifier matters, but validate its selected letter against your own legal-action list before it can affect a game.

## Shared worlds with children

The projects reviewed here do not provide a complete child-safe shared-server policy. Mindcraft's README warns against public servers when code execution is enabled. [Mindcraft README, read 2026-09-24](https://github.com/kolbytn/mindcraft)

For a world children use, put these rules in the server-side game code:

- Expose an allowlist of small actions with validated arguments, such as move, look, or offer a non-game-changing message.
- Deny destructive actions such as placing or breaking blocks, attacking players, changing inventory, running commands, or executing code.
- Apply per-action cooldowns, request-rate limits and resource caps to the agent process.
- Never enable agent code execution on a public server. Test changes in an isolated local world first.
- Keep a human able to stop or remove the bot. A player allowlist controls who can join; it does not restrict what an admitted bot can do.

These are design recommendations based on the cited project warnings and the absence of built-in allowlists and rate limits in the reviewed projects. They are not features supplied by Mineflayer or the listed toolkits.
