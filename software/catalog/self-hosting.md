# Self-hosting

Servers, reverse proxies, remote access, monitoring and household apps you run yourself. 34 projects; 17 with a permissive code license. Sorted by reuse, then stars. Part of the [software list](../README.md), which explains the reuse classes.

| project | reuse | license | language | stars | last push | why |
|---|---|---|---|---|---|---|
| [louislam/uptime-kuma](https://github.com/louislam/uptime-kuma) | copy | MIT | JavaScript | 92198 | 2026-10-08 | Simple status and uptime monitor with many notification channels. |
| [caddyserver/caddy](https://github.com/caddyserver/caddy) | copy | Apache-2.0 | Go | 77490 | 2026-10-07 | Web server and reverse proxy with automatic HTTPS and a one-file config. |
| [prometheus/prometheus](https://github.com/prometheus/prometheus) | copy | Apache-2.0 | Go | 66416 | 2026-10-07 | Pull-based metrics database with a query language and alert rules; the reference for watching servers and services. |
| [traefik/traefik](https://github.com/traefik/traefik) | copy | MIT | Go | 65102 | 2026-10-07 | Reverse proxy that discovers container services and handles TLS automatically. |
| [coollabsio/coolify](https://github.com/coollabsio/coolify) | copy | Apache-2.0 | PHP | 62699 | 2026-10-07 | Self-hosted Heroku/Netlify-style PaaS for deploying apps and databases on your own servers. |
| [go-gitea/gitea](https://github.com/go-gitea/gitea) | copy | MIT | Go | 58352 | 2026-10-08 | Lightweight self-hosted Git forge with issues, CI and packages. |
| [juanfont/headscale](https://github.com/juanfont/headscale) | copy | BSD-3-Clause | Go | 44410 | 2026-10-07 | Self-hosted control server for Tailscale clients, removing the hosted coordination dependency. |
| [portainer/portainer](https://github.com/portainer/portainer) | copy | Zlib | TypeScript | 38619 | 2026-10-08 | Web UI for managing Docker and Kubernetes hosts. |
| [IceWhaleTech/CasaOS](https://github.com/IceWhaleTech/CasaOS) | copy | Apache-2.0 | Go | 37291 | 2026-09-28 | Simple home-server OS layer with an app store for containers. |
| [tailscale/tailscale](https://github.com/tailscale/tailscale) | copy | BSD-3-Clause | Go | 37251 | 2026-10-08 | WireGuard mesh VPN client that makes private services reachable across devices. |
| [dgtlmoon/changedetection.io](https://github.com/dgtlmoon/changedetection.io) | copy | Apache-2.0 | Python | 34829 | 2026-10-07 | Watches web pages for changes such as prices, restocks or new notices and sends an alert through many channels. |
| [binwiederhier/ntfy](https://github.com/binwiederhier/ntfy) | copy | Apache-2.0 | Go | 34675 | 2026-10-08 | Push notifications over plain HTTP: one curl to a topic reaches phones and desktops. Easy to self-host and easy to call from scripts and alert rules. |
| [NginxProxyManager/nginx-proxy-manager](https://github.com/NginxProxyManager/nginx-proxy-manager) | copy | MIT | TypeScript | 34338 | 2026-10-06 | Point-and-click reverse proxy with certificate management. |
| [authelia/authelia](https://github.com/authelia/authelia) | copy | Apache-2.0 | Go | 29201 | 2026-10-08 | Single sign-on and two-factor gateway in front of self-hosted apps. |
| [oblien/openship](https://github.com/oblien/openship) | copy (see note) | Apache-2.0 | TypeScript | 14599 | 2026-10-08 | Self-hosted deployment platform that builds a repo, runs it in containers and routes it with automatic TLS, driven from a desktop app over SSH. **apps/email/engine is vendored iRedMail under GPL-3.0-or-later and ships in the API image, CLI and desktop app; apps/email/client and apps/email/server are Zero Email code with no license file here; the Linux server install mounts the host Docker socket and takes ports 80 and 443, so give it a host of its own and read its security advisories first** |
| [grocy/grocy](https://github.com/grocy/grocy) | copy | MIT | Blade | 9560 | 2026-09-16 | Household groceries, stock and chores tracker. |
| [RaidOwl/homelab-hub](https://github.com/RaidOwl/homelab-hub) | copy | MIT | Svelte | 907 | 2026-03-14 | Self-hosted inventory for a home lab: hardware, virtual machines, services, storage and networks, with a relationship map and markdown docs. |
| [syncthing/syncthing](https://github.com/syncthing/syncthing) | library use | MPL-2.0 | Go | 89205 | 2026-10-08 | Peer-to-peer continuous file sync between your own devices, no central server. |
| [rustdesk/rustdesk](https://github.com/rustdesk/rustdesk) | study only | AGPL-3.0 | Rust | 125376 | 2026-10-07 | Remote desktop for helping someone at their own computer, with a relay server you run yourself instead of a vendor account. |
| [netdata/netdata](https://github.com/netdata/netdata) | study only | GPL-3.0 | Go | 80834 | 2026-10-08 | Per-second system and container metrics with zero-config dashboards. |
| [grafana/grafana](https://github.com/grafana/grafana) | study only | AGPL-3.0 | TypeScript | 77128 | 2026-10-08 | Dashboards and alerting over Prometheus, logs, SQL and dozens of other sources. |
| [dani-garcia/vaultwarden](https://github.com/dani-garcia/vaultwarden) | study only | AGPL-3.0 | Rust | 68667 | 2026-10-07 | Lightweight Bitwarden-compatible password server for small households. |
| [pi-hole/pi-hole](https://github.com/pi-hole/pi-hole) | study only | EUPL-1.2 (per license file) | Shell | 61197 | 2026-10-07 | Network-wide DNS ad and tracker blocking. **commits before v3.0 keep the licenses they were made under** |
| [jellyfin/jellyfin](https://github.com/jellyfin/jellyfin) | study only | GPL-2.0 | C# | 57886 | 2026-10-07 | Media server for your own films, shows and music, with no subscription or account. |
| [AdguardTeam/AdGuardHome](https://github.com/AdguardTeam/AdGuardHome) | study only | GPL-3.0 | TypeScript | 37280 | 2026-10-07 | Network-wide DNS filtering with encrypted DNS support and a web UI. |
| [nextcloud/server](https://github.com/nextcloud/server) | study only | AGPL-3.0 | PHP | 37029 | 2026-10-08 | File sync, calendar and contacts on your own server; the self-hosted office suite backbone. |
| [gethomepage/homepage](https://github.com/gethomepage/homepage) | study only | GPL-3.0 | JavaScript | 33002 | 2026-10-06 | Config-file dashboard for homelab services with live status widgets. |
| [mealie-recipes/mealie](https://github.com/mealie-recipes/mealie) | study only | AGPL-3.0 | Python | 13472 | 2026-10-08 | Recipe manager and meal planner with URL import and shopping lists. |
| [Freika/dawarich](https://github.com/Freika/dawarich) | study only | AGPL-3.0 | Ruby | 10602 | 2026-10-05 | Self-hosted location history that replaces a phone vendor's timeline; imports old exports and maps trips and visits. |
| [sysadminsmedia/homebox](https://github.com/sysadminsmedia/homebox) | study only | AGPL-3.0 | Go | 7464 | 2026-10-04 | Home inventory for belongings, warranties, receipts and where things are stored, with QR labels. |
| [Kozea/Radicale](https://github.com/Kozea/Radicale) | study only | GPL-3.0 | Python | 5093 | 2026-10-06 | Small CalDAV and CardDAV server for shared calendars and contacts; plain files on disk, almost nothing to maintain. |
| [bitfireAT/davx5-ose](https://github.com/bitfireAT/davx5-ose) | study only | GPL-3.0 | Kotlin | 2931 | 2026-10-07 | Android sync adapter that connects the phone's own calendar, contacts and tasks to any CalDAV or CardDAV server. |
| [goauthentik/authentik](https://github.com/goauthentik/authentik) | check first | MIT + authentik Enterprise Edition license (per license file) | Python | 25876 | 2026-10-08 | Identity provider (OIDC, SAML, LDAP) for a self-hosted stack. **code outside authentik/enterprise/ and website/ is MIT** |
| [stalwartlabs/stalwart](https://github.com/stalwartlabs/stalwart) | check first | AGPL-3.0-only + Stalwart Enterprise License (per license file) | Rust | 14980 | 2026-10-05 | All-in-one mail server in Rust (SMTP, IMAP, JMAP) with spam filtering and built-in calendar and contacts. **enterprise features are under a commercial license** |

A license marked *per license file* was read from the repository's own license files, because GitHub's detector could not classify it or reported only part of it; the file and the reason are recorded in [tools/overrides.json](../../tools/overrides.json).
