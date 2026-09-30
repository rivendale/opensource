# Software

Open-source applications, tools, libraries and curated lists beyond games: self-hosting, home automation, local AI, documents, media, notes, reading, learning, personal finance, privacy and web development.

Each row is a hand-picked project with one line on why it is useful. Its license, language, stars and last push are read from GitHub's API when the list is built, and its reuse class follows the same [license rule](../README.md#the-license-rule) as the games catalog. Rows are chosen for being maintained and widely used, not for completeness; the [resources](#resources) below go wider.

**Anything you install runs code on your machine.** Prefer a project's own releases or an official package, pin a version, read what access it asks for, and keep services that hold your data off the open internet unless you mean to publish them. **A code license says nothing about model weights, voices, fonts, art or data**, which often carry their own terms. This is practical guidance, not legal advice.

## Reuse classes

The same four classes as the games catalog; which licenses fall in each is set by the [license rule](../README.md#the-license-rule).

| reuse class | what it means for an application or tool |
|---|---|
| `copy` | copy its code into your project, keep the copyright notice, and record it in `THIRD_PARTY.md` |
| `library use` | depend on it unmodified as a library; do not paste its code into yours |
| `study only` | run it and read it for design; copy none of its code |
| `check first` | treat the code as all rights reserved until you have read its license yourself |

A `copy` row that carries a note reads `copy (see note)`: the note names a part under other terms, such as a bundled GPL file, or something to know before you run or copy it.

**Running a GPL or AGPL program unmodified is fine; the class limits copying code.** Installing a `study only` application and using it as it ships is ordinary use. Obligations start when you copy its code into your own project, or, for AGPL, when you modify it and let other people use the modified version over a network. Some `check first` rows are source-available (a Business Source, Elastic or enterprise license, or an open core with a commercial directory), and those terms can limit production or commercial use even when you change nothing: read them before you deploy.

## Categories

Built 2026-09-30: 360 projects, 225 with a permissive code license.

| category | projects | copy | library use | study only | check first | covers |
|---|---|---|---|---|---|---|
| [Self-hosting](catalog/self-hosting.md) | 34 | 17 | 1 | 14 | 2 | servers, reverse proxies, remote access, monitoring and household apps you run yourself |
| [Home automation](catalog/home-automation.md) | 6 | 4 | 0 | 1 | 1 | hubs, device bridges, cameras and automations that run locally |
| [Local AI and agents](catalog/local-ai-agents.md) | 32 | 28 | 0 | 0 | 4 | model runners and servers, coding agents, agent frameworks and evaluation |
| [Agent memory](catalog/agent-memory.md) | 11 | 9 | 0 | 2 | 0 | memory layers, knowledge graphs and context stores that keep what an agent learned across sessions |
| [MCP servers and SDKs](catalog/mcp.md) | 18 | 17 | 0 | 1 | 0 | Model Context Protocol servers, SDKs, gateways and debuggers that connect AI tools to other software |
| [Agent skills and instruction files](catalog/agent-skills.md) | 16 | 13 | 0 | 0 | 3 | instruction files, skills and plugins that change how a coding agent works |
| [Speech](catalog/speech.md) | 8 | 7 | 0 | 1 | 0 | speech-to-text and text-to-speech that run locally |
| [Developer tools and security](catalog/dev-security.md) | 27 | 22 | 1 | 3 | 1 | package managers, linters, scanners, supply-chain checks and command-line tools |
| [Photo libraries](catalog/media-photo.md) | 9 | 2 | 0 | 6 | 1 | photo backup and libraries, RAW development, duplicates and metadata |
| [Video and audio](catalog/media-video-audio.md) | 21 | 11 | 1 | 7 | 2 | editing, encoding, recording, music, stem separation and video made from code |
| [Images and diagrams](catalog/media-image.md) | 16 | 7 | 2 | 7 | 0 | image processing, generation, painting, design tools and diagrams |
| [3D, CAD and printing](catalog/media-3d.md) | 11 | 5 | 1 | 4 | 1 | 3D creation, CAD, slicers, scans and 3D on the web |
| [Documents and OCR](catalog/documents-ocr.md) | 28 | 20 | 1 | 5 | 2 | PDF tools, OCR, document conversion and typesetting |
| [Notes, wikis and search](catalog/knowledge-search.md) | 27 | 11 | 0 | 12 | 4 | notes, wikis, bookmarks, web archiving, search engines and vector search |
| [Reading](catalog/reading.md) | 7 | 2 | 0 | 5 | 0 | e-books, audiobooks, comics, feeds and read-it-later |
| [Learning](catalog/learning.md) | 18 | 9 | 0 | 8 | 1 | flashcards, spaced repetition, learning platforms and offline reference |
| [Personal finance](catalog/finance.md) | 23 | 9 | 1 | 11 | 2 | budgeting, plain-text accounting, invoicing and investment tracking |
| [Privacy, passwords and backups](catalog/privacy-backups.md) | 23 | 8 | 1 | 11 | 3 | backups, encryption, passwords, two-factor codes, messaging and file transfer |
| [Web and app frameworks](catalog/web-frontend.md) | 25 | 24 | 0 | 0 | 1 | frameworks, UI libraries, static sites, testing and app wrappers |

## Resources

Curated lists and courses that go wider than this one. Each keeps its own license, and that license decides whether a tool may **parse** the list into generated data like this catalog or only **link** to it. A share-alike list (CC-BY-SA) would carry its license into this repository's MIT data, so it is linked, never parsed. A license stated only in a README badge, with no license file, is treated like a list's claim: link only until confirmed.

This catalog's seeds were chosen by hand. Some candidates were found through four permissively licensed lists, taking project names and addresses only: [pluja/awesome-privacy](https://github.com/pluja/awesome-privacy) (CC0-1.0), [krzemienski/awesome-video](https://github.com/krzemienski/awesome-video) (CC0-1.0), [meichthys/foss_photo_libraries](https://github.com/meichthys/foss_photo_libraries) (MIT) and [ad-si/awesome-music-production](https://github.com/ad-si/awesome-music-production) (ISC). Thanks to their maintainers. The one-line descriptions were written for this catalog; some stay close to the project's own description.

| resource | covers | license | use |
|---|---|---|---|
| [sindresorhus/awesome](https://github.com/sindresorhus/awesome) | lists of curated lists on every subject | CC0-1.0 | parse |
| [awesome-selfhosted/awesome-selfhosted](https://github.com/awesome-selfhosted/awesome-selfhosted) | self-hosted network services and web applications | CC-BY-SA-3.0 (LICENSE file) | link only |
| [awesome-selfhosted/awesome-selfhosted-data](https://github.com/awesome-selfhosted/awesome-selfhosted-data) | the same list as structured YAML | CC-BY-SA-3.0 (LICENSE file) | link only |
| [pluja/awesome-privacy](https://github.com/pluja/awesome-privacy) | privacy-respecting apps and services | CC0-1.0 | parse |
| [meichthys/foss_photo_libraries](https://github.com/meichthys/foss_photo_libraries) | self-hosted photo libraries compared | MIT | parse, keep the notice |
| [krzemienski/awesome-video](https://github.com/krzemienski/awesome-video) | video tools, codecs, players and streaming | CC0-1.0 | parse |
| [ad-si/awesome-music-production](https://github.com/ad-si/awesome-music-production) | music production software and hardware | ISC | parse, keep the notice |
| [frenck/awesome-home-assistant](https://github.com/frenck/awesome-home-assistant) | Home Assistant add-ons, integrations and guides | CC-BY-4.0 | parse with attribution |
| [docker/awesome-compose](https://github.com/docker/awesome-compose) | Docker Compose samples for common stacks | CC0-1.0 | parse |
| [punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) | MCP servers by category | MIT | parse, keep the notice |
| [public-apis/public-apis](https://github.com/public-apis/public-apis) | free public APIs by category | MIT | parse, keep the notice |
| [EbookFoundation/free-programming-books](https://github.com/EbookFoundation/free-programming-books) | free programming books and courses in many languages | CC-BY-4.0 | parse with attribution |
| [mlabonne/llm-course](https://github.com/mlabonne/llm-course) | a course with notebooks on how language models work, fine-tuning, quantization and deployment | Apache-2.0 | parse, keep the notice |
| [terkelg/awesome-creative-coding](https://github.com/terkelg/awesome-creative-coding) | creative coding, generative art and shaders | CC0 stated in the README; no LICENSE file | link only until confirmed |
| [transitive-bullshit/awesome-ffmpeg](https://github.com/transitive-bullshit/awesome-ffmpeg) | FFmpeg guides, wrappers and tools | CC0 stated in the README; no LICENSE file | link only until confirmed |
| [hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) | skills, hooks, slash commands, plugins and workflows for Claude Code | CC-BY-NC-ND-4.0 (LICENSE file) | link only |

## How this list is built

Seeds live in [`tools/domains/software.json`](../tools/domains/software.json): name, repository, category and one line on why. `tools/build_catalog.py --domain software` (it needs the GitHub CLI, `gh`, installed and signed in) asks GitHub's API for each repository's license, language, stars, last push and archived flag. License corrections, each with the file it was read from, live in [`tools/overrides.json`](../tools/overrides.json). To add a project, add a seed and rebuild; do not hand-edit this file, `catalog/` or the data file.

```sh
python3 tools/build_catalog.py --domain software --src sources --out .
```

**Left out at build time:** 0 of 362 seeds.

Nothing: every seed was found on GitHub and is not archived.

**Listed once, elsewhere in this repository:** 2.

- [mrdoob/three.js](https://github.com/mrdoob/three.js): see [catalog/engines.md](../catalog/engines.md)
- [ahujasid/mcp-for-blender](https://github.com/ahujasid/mcp-for-blender): see [scaffolds/mcps.md](../scaffolds/mcps.md)
