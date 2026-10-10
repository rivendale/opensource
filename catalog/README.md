# Catalog

Built 2026-10-06 from three public lists, GitHub topic searches and curated seeds; every GitHub project's license and activity read from GitHub's API that day. Rebuild with `tools/fetch_sources.sh && python3 tools/build_catalog.py --src sources --out .`

**Left out on purpose:** 5 name or description reads like a download lure; 457 found only by a topic search, under 10 stars; 10 found only by a topic search, with no code or tagged leak/crack/apk; 1 removed by a reviewed override (see tools/overrides.json). Those are mostly malware lures named after commercial games. **Never download a release, zip or installer from a catalog repository; read and build from source.** Report a lure you still find as an issue.

**Reuse column:** `copy` = permissive code license (MIT, BSD, Apache, zlib...), code may be reused with attribution. `library use` = weak copyleft (LGPL, MPL): use unmodified as a library, do not copy into our code. `study only` = copyleft (GPL, AGPL): read it for design and mechanics, copy nothing. `check first` = no clear license, a license only a list states, or a decompiled commercial game: treat it as all rights reserved until you confirm otherwise. **A code license says nothing about the art, audio or data**, which often carry their own (frequently non-commercial) licenses.

| genre | projects | copy | active in the last 2 years |
|---|---|---|---|
| [Strategy](strategy.md) | 426 | 38 | 144 |
| [Simulation](simulation.md) | 180 | 31 | 77 |
| [Arcade](arcade.md) | 315 | 66 | 70 |
| [Action](action.md) | 137 | 22 | 26 |
| [Platformer](platformer.md) | 104 | 16 | 36 |
| [RPG](rpg.md) | 234 | 37 | 76 |
| [Roguelike](roguelike.md) | 69 | 11 | 23 |
| [Fighting](fighting.md) | 78 | 40 | 41 |
| [Shooter](shooter.md) | 205 | 22 | 79 |
| [Puzzle](puzzle.md) | 241 | 54 | 62 |
| [Racing](racing.md) | 68 | 16 | 27 |
| [Sports](sports.md) | 11 | 2 | 1 |
| [Adventure](adventure.md) | 76 | 18 | 23 |
| [Sandbox](sandbox.md) | 34 | 15 | 16 |
| [Board and card](board-card.md) | 35 | 12 | 18 |
| [Rhythm](rhythm.md) | 101 | 37 | 67 |
| [Educational](educational.md) | 9 | 0 | 2 |
| [Engines and frameworks](engines.md) | 262 | 105 | 144 |
| [Other](other.md) | 155 | 59 | 48 |

## Curated seeds

15 seeds = 14 catalog rows + 1 listed drops.
Edit [games-seeds.json](../tools/domains/games-seeds.json), then rebuild. Metadata hosts other than GitHub are not enriched.

| repository | reason left out | reference note |
|---|---|---|
| [https://codeberg.org/OpenBoE/oboe](https://codeberg.org/OpenBoE/oboe) | metadata host unsupported: the games build enriches GitHub repositories only | Open Blades of Exile; inspect its README objection to Copilot use before any AI use. |
