# Agent skills and instruction files

Instruction files, skills and plugins that change how a coding agent works. 5 projects; 4 with a permissive code license. Sorted by reuse, then stars. Part of the [software list](../README.md), which explains the reuse classes.

A skill is instructions your agent follows with your access, and some plugins add hooks that run at every session start. Read it before installing, install from a reviewed commit rather than a branch, and check each skill's license: one repository can mix licenses. The [safe setup checklist](../../ai/graphics.md#safe-setup-checklist) applies.

| project | reuse | license | language | stars | last push | why |
|---|---|---|---|---|---|---|
| [obra/superpowers](https://github.com/obra/superpowers) | copy (see note) | MIT | Shell | 292876 | 2026-09-27 | A library of agent skills for planning, test-driven development, debugging and code review, installed as a plugin for several coding agents. **installs a SessionStart hook that runs at every start, `/clear` and compaction; install from a reviewed commit** |
| [mattpocock/skills](https://github.com/mattpocock/skills) | copy | MIT | Shell | 271970 | 2026-09-29 | One engineer's working set of agent skills, published from his own agents directory, for planning, reviewing, testing and writing code. |
| [mvanhorn/last30days-skill](https://github.com/mvanhorn/last30days-skill) | copy (see note) | MIT | Python | 63194 | 2026-09-27 | Agent skill that researches a topic across Reddit, X, YouTube, Hacker News, GitHub and more over the last 30 days and summarizes what people say. **its GitHub search falls back to `gh auth token`, so it acts as whatever account your shell is signed in to; first-run setup installs extra command-line tools; read what each source connector needs before enabling it** |
| [agentsmd/agents.md](https://github.com/agentsmd/agents.md) | copy | MIT | TypeScript | 24683 | 2026-09-10 | The AGENTS.md convention: one plain Markdown file of project instructions that many coding agents read, with the format's site and examples. |
| [anthropics/skills](https://github.com/anthropics/skills) | check first | per skill: Apache-2.0, except the docx, pdf, pptx and xlsx skills (all rights reserved) (per license file) | Python | 178981 | 2026-09-29 | Anthropic's example agent skills, from building MCP servers to editing documents; most carry Apache-2.0 per skill, the four document skills do not. **read the LICENSE.txt inside each skill before copying it; the docx, pdf, pptx and xlsx skills may be used only under Anthropic's terms** |

A license marked *per license file* was read from the repository's own license files, because GitHub's detector could not classify it or reported only part of it; the file and the reason are recorded in [tools/overrides.json](../../tools/overrides.json).
