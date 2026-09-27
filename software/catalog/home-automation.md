# Home automation

Hubs, device bridges, cameras and automations that run locally. 6 projects; 4 with a permissive code license. Sorted by reuse, then stars. Part of the [software list](../README.md), which explains the reuse classes.

| project | reuse | license | language | stars | last push | why |
|---|---|---|---|---|---|---|
| [home-assistant/core](https://github.com/home-assistant/core) | copy | Apache-2.0 | Python | 91160 | 2026-09-26 | Home automation hub that runs locally and integrates thousands of devices without a cloud account. |
| [blakeblackshear/frigate](https://github.com/blakeblackshear/frigate) | copy | MIT | Python | 36118 | 2026-09-26 | Local camera recorder with real-time object detection, so alerts fire on people or cars rather than every moving shadow; no cloud subscription. |
| [node-red/node-red](https://github.com/node-red/node-red) | copy | Apache-2.0 | JavaScript | 23688 | 2026-09-18 | Browser-based flow editor that wires devices, APIs and schedules together; the usual step up when simple automation rules run out. |
| [music-assistant/server](https://github.com/music-assistant/server) | copy | Apache-2.0 | Python | 3112 | 2026-09-26 | Music library server that merges local files and streaming accounts and plays to many speaker brands; integrates with Home Assistant. |
| [Koenkk/zigbee2mqtt](https://github.com/Koenkk/zigbee2mqtt) | study only | GPL-3.0 | TypeScript | 15672 | 2026-09-23 | Bridges Zigbee devices from many brands to MQTT through one USB coordinator, replacing each vendor's hub and cloud app. |
| [esphome/esphome](https://github.com/esphome/esphome) | check first | MIT + GPL-3.0 (per license file) | C++ | 11731 | 2026-09-26 | Builds firmware for ESP32 and similar boards from a short YAML file, so cheap sensors and switches report locally to Home Assistant. **the Python code is MIT; the C and C++ runtime is GPL-3.0** |

A license marked *per license file* was read from the repository's own license files, because GitHub's detector could not classify it or reported only part of it; the file and the reason are recorded in [tools/overrides.json](../../tools/overrides.json).
