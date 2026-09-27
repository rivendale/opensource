# Local AI and agents

Model runners and servers, coding agents, agent frameworks and evaluation. 25 projects; 21 with a permissive code license. Sorted by reuse, then stars. Part of the [software list](../README.md), which explains the reuse classes.

Agents run code and edit files with your access. Read the code, pin a version and give them the least access that works; the [safe setup checklist](../../ai/graphics.md#safe-setup-checklist) applies. A code license says nothing about model weights; read each model card.

| project | reuse | license | language | stars | last push | why |
|---|---|---|---|---|---|---|
| [anomalyco/opencode](https://github.com/anomalyco/opencode) | copy | MIT | TypeScript | 210264 | 2026-09-27 | Terminal coding agent that works with many providers including local ones. |
| [ollama/ollama](https://github.com/ollama/ollama) | copy | MIT | Go | 181786 | 2026-09-26 | Runs open-weight language models on your own machine behind a one-line CLI and a local HTTP API; the usual starting point for local AI. |
| [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) | copy | MIT | C++ | 129630 | 2026-09-27 | C/C++ inference engine and GGUF model format underneath most local runners; works on CPUs and on Vulkan, Metal, CUDA and ROCm GPUs. |
| [openai/codex](https://github.com/openai/codex) | copy | Apache-2.0 | Rust | 126653 | 2026-09-27 | OpenAI's open-source terminal coding agent. |
| [vllm-project/vllm](https://github.com/vllm-project/vllm) | copy | Apache-2.0 | Python | 92736 | 2026-09-27 | High-throughput model server with continuous batching; the choice when one GPU box serves many requests at once. |
| [OpenHands/OpenHands](https://github.com/OpenHands/OpenHands) | copy | MIT | TypeScript | 89244 | 2026-09-26 | Open agent platform for autonomous software tasks in a sandbox. |
| [cline/cline](https://github.com/cline/cline) | copy | Apache-2.0 | TypeScript | 69407 | 2026-09-27 | VS Code agent that plans and edits with approval gates, any model provider. |
| [microsoft/autogen](https://github.com/microsoft/autogen) | copy (see note) | MIT (per license file) | Python | 61180 | 2026-04-15 | Framework for multi-agent conversations and tool use. **documentation is CC-BY-4.0; in maintenance mode, and its README points new users to Microsoft Agent Framework ([microsoft/agent-framework](https://github.com/microsoft/agent-framework), MIT)** |
| [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) | copy | MIT | Python | 59073 | 2026-09-26 | Role-based multi-agent orchestration framework in Python. |
| [aaif-goose/goose](https://github.com/aaif-goose/goose) | copy | Apache-2.0 | Rust | 54692 | 2026-09-25 | Extensible local agent that drives tools through MCP. |
| [Aider-AI/aider](https://github.com/Aider-AI/aider) | copy | Apache-2.0 | Python | 49209 | 2026-05-22 | Terminal pair-programmer that edits a git repo with any LLM, local or hosted. |
| [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) | copy | MIT | Python | 42335 | 2026-09-27 | Graph-based stateful agent orchestration with checkpoints. |
| [stanfordnlp/dspy](https://github.com/stanfordnlp/dspy) | copy | MIT | Python | 38361 | 2026-09-27 | Program LLM pipelines declaratively and optimize their prompts against metrics. |
| [openai/openai-agents-python](https://github.com/openai/openai-agents-python) | copy | MIT | Python | 29713 | 2026-09-25 | Lightweight multi-agent SDK with handoffs, guardrails and tracing. |
| [huggingface/smolagents](https://github.com/huggingface/smolagents) | copy | Apache-2.0 | Python | 29506 | 2026-09-23 | Small agent library where agents write code as their actions. |
| [vercel/ai](https://github.com/vercel/ai) | copy | Apache-2.0 (per license file) | TypeScript | 26976 | 2026-09-27 | TypeScript toolkit for streaming chat and tool calls across providers. |
| [promptfoo/promptfoo](https://github.com/promptfoo/promptfoo) | copy | MIT | TypeScript | 25482 | 2026-09-27 | Test and red-team prompts and models from a config file, locally. |
| [pydantic/pydantic-ai](https://github.com/pydantic/pydantic-ai) | copy | MIT | Python | 20200 | 2026-09-27 | Typed Python agent framework with structured outputs and evals. |
| [dottxt-ai/outlines](https://github.com/dottxt-ai/outlines) | copy | Apache-2.0 | Python | 15886 | 2026-09-21 | Constrained generation so model output always matches a schema or grammar. |
| [simonw/llm](https://github.com/simonw/llm) | copy | Apache-2.0 | Python | 12558 | 2026-09-22 | CLI and Python library for prompting many models and logging every call to SQLite. |
| [mostlygeek/llama-swap](https://github.com/mostlygeek/llama-swap) | copy | MIT | Go | 5758 | 2026-09-26 | Proxy that starts and stops local model servers on demand behind one OpenAI-compatible endpoint, so several models share one GPU. |
| [open-webui/open-webui](https://github.com/open-webui/open-webui) | check first | BSD-3-Clause + Open WebUI branding clause (per license file) | Python | 153281 | 2026-09-26 | Self-hosted chat interface for local and cloud models with accounts, document upload and retrieval. **materials under earlier licenses keep them, per LICENSE_HISTORY** |
| [unclecode/crawl4ai](https://github.com/unclecode/crawl4ai) | check first | Apache-2.0 + Crawl4AI attribution requirement (per license file) | Python | 84316 | 2026-09-25 | Crawls sites, renders JavaScript and returns clean Markdown for model pipelines and agents. **the added section requires a fixed credit line in every distribution, publication or public use, such as a README or NOTICE file, a website's About or Credits page, or a command-line tool's help output** |
| [BerriAI/litellm](https://github.com/BerriAI/litellm) | check first | MIT + BerriAI Enterprise license (per license file) | Python | 59686 | 2026-09-27 | One OpenAI-compatible proxy in front of many model providers, with budgets and logging. **code outside enterprise/ is MIT** |
| [langfuse/langfuse](https://github.com/langfuse/langfuse) | check first | MIT + Langfuse Enterprise license (per license file) | TypeScript | 35087 | 2026-09-27 | Self-hostable tracing, evals and prompt management for LLM apps. **code outside the ee/ directories is MIT** |

A license marked *per license file* was read from the repository's own license files, because GitHub's detector could not classify it or reported only part of it; the file and the reason are recorded in [tools/overrides.json](../../tools/overrides.json).
