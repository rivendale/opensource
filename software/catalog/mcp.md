# MCP servers and SDKs

Model Context Protocol servers, SDKs, gateways and debuggers that connect AI tools to other software. 16 projects; 15 with a permissive code license. Sorted by reuse, then stars. Part of the [software list](../README.md), which explains the reuse classes.

**Every MCP server runs code on your machine with the access you give it.** Read the code, pin a version, keep it local, and apply the [safe setup checklist](../../ai/graphics.md#safe-setup-checklist) before connecting one to an agent.

| project | reuse | license | language | stars | last push | why |
|---|---|---|---|---|---|---|
| [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) | copy (see note) | Apache-2.0 AND MIT (per license file) | TypeScript | 90614 | 2026-09-27 | Reference MCP servers (filesystem, git, fetch, memory) to read before trusting third-party ones. **keep both the Apache-2.0 and MIT notices when copying; documentation is CC-BY-4.0** |
| [upstash/context7](https://github.com/upstash/context7) | copy | MIT | TypeScript | 62454 | 2026-09-26 | Serves current library documentation to coding agents to cut stale-API mistakes. |
| [ChromeDevTools/chrome-devtools-mcp](https://github.com/ChromeDevTools/chrome-devtools-mcp) | copy | Apache-2.0 | TypeScript | 52644 | 2026-09-27 | Lets an agent inspect and debug a live Chrome with DevTools. |
| [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp) | copy | Apache-2.0 | TypeScript | 37596 | 2026-09-25 | Browser automation for agents via accessibility snapshots rather than screenshots. |
| [github/github-mcp-server](https://github.com/github/github-mcp-server) | copy | MIT | Go | 33226 | 2026-09-25 | GitHub's official MCP server for repos, issues and pull requests. |
| [PrefectHQ/fastmcp](https://github.com/PrefectHQ/fastmcp) | copy | Apache-2.0 | Python | 27907 | 2026-09-27 | High-level Python framework for building MCP servers quickly. |
| [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) | copy | MIT | Python | 24408 | 2026-09-25 | Official Python SDK for writing MCP servers and clients. |
| [modelcontextprotocol/typescript-sdk](https://github.com/modelcontextprotocol/typescript-sdk) | copy (see note) | Apache-2.0 AND MIT (per license file) | TypeScript | 13467 | 2026-09-27 | Official TypeScript SDK for writing MCP servers and clients. **keep both the Apache-2.0 and MIT notices when copying; documentation is CC-BY-4.0** |
| [modelcontextprotocol/inspector](https://github.com/modelcontextprotocol/inspector) | copy (see note) | Apache-2.0 AND MIT (per license file) | TypeScript | 10963 | 2026-09-27 | Interactive debugger for testing an MCP server's tools before wiring it to an agent. **keep both the Apache-2.0 and MIT notices when copying; documentation is CC-BY-4.0** |
| [awslabs/mcp](https://github.com/awslabs/mcp) | copy (see note) | Apache-2.0 | Python | 9732 | 2026-09-25 | AWS's collection of MCP servers for its services and docs. **its README names Agent Toolkit for AWS as the successor to these servers; this repository still works and accepts contributions** |
| [idosal/git-mcp](https://github.com/idosal/git-mcp) | copy | Apache-2.0 | TypeScript | 8431 | 2026-05-08 | Turns any GitHub repo into a documentation MCP endpoint. |
| [firecrawl/firecrawl-mcp-server](https://github.com/firecrawl/firecrawl-mcp-server) | copy | MIT | JavaScript | 7517 | 2026-09-26 | Web scraping and crawling tools for agents (needs a Firecrawl backend). |
| [grafana/mcp-grafana](https://github.com/grafana/mcp-grafana) | copy | Apache-2.0 | Go | 3502 | 2026-09-26 | Query dashboards, metrics and logs in Grafana from an agent. |
| [stacklok/toolhive](https://github.com/stacklok/toolhive) | copy | Apache-2.0 | Go | 2211 | 2026-09-26 | Runs MCP servers in isolated containers with scoped permissions. |
| [docker/mcp-gateway](https://github.com/docker/mcp-gateway) | copy | MIT | Go | 1587 | 2026-09-23 | Docker's gateway for running and brokering containerized MCP servers. |
| [oraios/serena](https://github.com/oraios/serena) | study only | GPL-3.0-or-later (per license file) | Python | 29830 | 2026-09-24 | Semantic code navigation and editing tools for agents via language servers. **src/solidlsp/ is MIT and can be reused on its own; releases up to v1.7.0 are MIT** |

A license marked *per license file* was read from the repository's own license files, because GitHub's detector could not classify it or reported only part of it; the file and the reason are recorded in [tools/overrides.json](../../tools/overrides.json).

Listed once elsewhere in this repository, so not repeated here:

- [ahujasid/mcp-for-blender](https://github.com/ahujasid/mcp-for-blender), in [scaffolds/mcps.md](../../scaffolds/mcps.md): Connects an agent to a running Blender over MCP so it can build and edit scenes, materials and renders by instruction. **sends an anonymous usage record by default (install and session IDs, tool name, versions, operating system) until `DISABLE_TELEMETRY=true` is set; a pinned setup with telemetry off is in [ai/graphics.md](../../ai/graphics.md#safe-setup-checklist)**
