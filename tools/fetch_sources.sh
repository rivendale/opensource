#!/usr/bin/env bash
# Fetch the four public lists the catalog is built from, into ./sources. Needs `gh` (logged in)
# and `git`. Read-only against every source.
set -euo pipefail
mkdir -p sources && cd sources
gh api repos/bobeff/open-source-games/contents/README.md -H 'Accept: application/vnd.github.raw' > bobeff.md
gh api repos/michelpereira/awesome-open-source-games/contents/README.md -H 'Accept: application/vnd.github.raw' > michelpereira.md
rm -rf trilarion && git clone -q --depth 1 https://github.com/Trilarion/opensourcegames.git trilarion
# GitHub search returns at most 1000 results: the top 1000 by stars for the topic.
python3 - <<'PY'
import json, subprocess
out = []
for page in range(1, 11):
    r = subprocess.run(["gh", "api", "-X", "GET", "search/repositories", "-f", "q=topic:open-source-game",
                        "-f", "sort=stars", "-f", "per_page=100", "-f", f"page={page}"],
                       capture_output=True, text=True)
    items = json.loads(r.stdout).get("items", []) if r.returncode == 0 else []
    out += [{"name": i["name"], "html_url": i["html_url"], "topics": i.get("topics", []),
             "description": i.get("description")} for i in items]
    if len(items) < 100:
        break
json.dump(out, open("topic.json", "w"))
print(f"topic:open-source-game: {len(out)} repositories")
# The four lists are thin on some genres (fighting: 11 projects in all four). Top 100 by stars
# for a few genre topics fills them; each result keeps the topic that found it.
extra = []
for t in ["fighting-game", "beat-em-up", "rollback-netcode", "racing-game", "sports-game", "rhythm-game", "sandbox-game"]:
    r = subprocess.run(["gh", "api", "-X", "GET", "search/repositories", "-f", f"q=topic:{t}",
                        "-f", "sort=stars", "-f", "per_page=100"], capture_output=True, text=True)
    items = json.loads(r.stdout).get("items", []) if r.returncode == 0 else []
    extra += [{"name": i["name"], "html_url": i["html_url"], "topics": [t] + i.get("topics", []),
               "description": i.get("description"), "via": t} for i in items]
    print(f"topic:{t}: {len(items)}")
json.dump(extra, open("topics_extra.json", "w"))
PY
