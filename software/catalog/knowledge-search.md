# Notes, wikis and search

Notes, wikis, bookmarks, web archiving, search engines and vector search. 26 projects; 10 with a permissive code license. Sorted by reuse, then stars. Part of the [software list](../README.md), which explains the reuse classes.

| project | reuse | license | language | stars | last push | why |
|---|---|---|---|---|---|---|
| [usememos/memos](https://github.com/usememos/memos) | copy | MIT | Go | 63427 | 2026-09-28 | Lightweight self-hosted note and memo stream. |
| [qdrant/qdrant](https://github.com/qdrant/qdrant) | copy | Apache-2.0 | Rust | 34882 | 2026-09-29 | Vector database for semantic search and retrieval, one container with filtering and snapshots. |
| [tobi/qmd](https://github.com/tobi/qmd) | copy (see note) | MIT | TypeScript | 30106 | 2026-09-09 | Local search over Markdown notes, transcripts and docs: keyword search, vector search and a reranker on GGUF models through node-llama-cpp, no API key. **downloads three GGUF models from Hugging Face on first use; the default embedder, embeddinggemma-300M, carries Google's Gemma license, and `QMD_EMBED_MODEL` swaps it (re-index after); its HTTP MCP server binds localhost unless `--host` is passed** |
| [assafelovic/gpt-researcher](https://github.com/assafelovic/gpt-researcher) | copy | Apache-2.0 | Python | 29805 | 2026-09-26 | Research agent that searches the web or your own documents and writes a cited report with any model provider; its default writer is a hosted model. |
| [ArchiveBox/ArchiveBox](https://github.com/ArchiveBox/ArchiveBox) | copy | MIT | Python | 28643 | 2026-09-28 | Self-hosted web archiver that saves pages in several formats. |
| [BookStackApp/BookStack](https://github.com/BookStackApp/BookStack) | copy | MIT | PHP | 19065 | 2026-09-29 | Simple self-hosted wiki organized as books and chapters. |
| [quickwit-oss/tantivy](https://github.com/quickwit-oss/tantivy) | copy | MIT | Rust | 16154 | 2026-09-29 | Full-text search engine library in Rust. |
| [asg017/sqlite-vec](https://github.com/asg017/sqlite-vec) | copy | Apache-2.0 | C | 8152 | 2026-05-18 | Vector search as a SQLite extension, for small local semantic search with no server at all. |
| [silverbulletmd/silverbullet](https://github.com/silverbulletmd/silverbullet) | copy | MIT | TypeScript | 6178 | 2026-09-29 | Markdown notebook that is programmable with queries. |
| [neo4j-labs/llm-graph-builder](https://github.com/neo4j-labs/llm-graph-builder) | copy | Apache-2.0 | Jupyter Notebook | 5273 | 2026-09-16 | Turns PDFs, web pages and videos into a Neo4j knowledge graph with a language model, then answers questions over the graph. |
| [AppFlowy-IO/AppFlowy](https://github.com/AppFlowy-IO/AppFlowy) | study only | AGPL-3.0 | Dart | 76992 | 2026-09-22 | Open alternative to Notion with local data. |
| [siyuan-note/siyuan](https://github.com/siyuan-note/siyuan) | study only | AGPL-3.0 | TypeScript | 46560 | 2026-09-29 | Local-first block-based personal knowledge base. |
| [logseq/logseq](https://github.com/logseq/logseq) | study only | AGPL-3.0 | Clojure | 45085 | 2026-09-29 | Local-first outliner and knowledge graph on plain files. |
| [TriliumNext/Trilium](https://github.com/TriliumNext/Trilium) | study only | AGPL-3.0 | TypeScript | 38082 | 2026-09-29 | Hierarchical notes with scripting and self-hosted sync. |
| [searxng/searxng](https://github.com/searxng/searxng) | study only | AGPL-3.0 | Python | 37772 | 2026-09-29 | Private metasearch engine aggregating many search backends. |
| [karakeep-app/karakeep](https://github.com/karakeep-app/karakeep) | study only | AGPL-3.0 | TypeScript | 29345 | 2026-09-27 | Bookmark and read-later app with AI tagging and full-text search. |
| [requarks/wiki](https://github.com/requarks/wiki) | study only | AGPL-3.0 | Vue | 28985 | 2026-09-28 | Wiki.js, a Git-backed self-hosted wiki. |
| [typesense/typesense](https://github.com/typesense/typesense) | study only | GPL-3.0 | C++ | 26611 | 2026-09-24 | Fast in-memory search engine, simple to operate. |
| [docmost/docmost](https://github.com/docmost/docmost) | study only | AGPL-3.0 | TypeScript | 21825 | 2026-09-29 | Collaborative wiki and docs, self-hosted. |
| [linkwarden/linkwarden](https://github.com/linkwarden/linkwarden) | study only | AGPL-3.0 | TypeScript | 19870 | 2026-09-10 | Collaborative bookmark manager that archives page copies. |
| [zotero/zotero](https://github.com/zotero/zotero) | study only | AGPL-3.0 (per license file) | JavaScript | 15428 | 2026-09-29 | Reference and source manager for research. **the Zotero name is a registered trademark** |
| [gramps-project/gramps-web](https://github.com/gramps-project/gramps-web) | study only | AGPL-3.0 | JavaScript | 1707 | 2026-09-29 | Web app for shared genealogy research on the Gramps database: people, sources, media and trees, with multiple editors. |
| [toeverything/AFFiNE](https://github.com/toeverything/AFFiNE) | check first | MIT + AFFiNE Enterprise Edition license (per license file) | TypeScript | 73096 | 2026-09-29 | Docs, whiteboards and databases in one local-first workspace. **code outside packages/backend and packages/common/native is MIT (LICENSE-MIT)** |
| [meilisearch/meilisearch](https://github.com/meilisearch/meilisearch) | check first | MIT + BUSL-1.1 (per license file) | Rust | 59443 | 2026-09-29 | Fast typo-tolerant search engine with hybrid vector search. **code outside the Enterprise Edition modules is MIT** |
| [laurent22/joplin](https://github.com/laurent22/joplin) | check first | AGPL-3.0-or-later + Joplin Server Personal Use License (per license file) | TypeScript | 56530 | 2026-09-29 | Note-taking app for desktop and phone with end-to-end encrypted sync through its own server, WebDAV or common cloud drives. **code outside directories with their own LICENSE is AGPL-3.0-or-later; logos and icons are all rights reserved** |
| [outline/outline](https://github.com/outline/outline) | check first | BUSL-1.1 (per license file) | TypeScript | 40752 | 2026-09-29 | Team wiki and knowledge base with a clean editor. |

A license marked *per license file* was read from the repository's own license files, because GitHub's detector could not classify it or reported only part of it; the file and the reason are recorded in [tools/overrides.json](../../tools/overrides.json).
