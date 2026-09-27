#!/usr/bin/env bash
# Fetch the three public lists and the GitHub topic searches the games catalog is built from, into
# ./sources. Needs `gh` (logged in) and `git`. Read-only against every source.
# All or nothing: everything is fetched into sources/.new first, and the lists already in ./sources
# are replaced only when every download and every search succeeded. A failed, partial or unreadable
# reply exits non-zero and leaves the old lists in place; it never becomes an empty list.
set -euo pipefail
command -v gh >/dev/null || { echo "fetch_sources.sh: gh, the GitHub CLI, is not installed: install it from https://cli.github.com and run \`gh auth login\`." >&2; exit 1; }
mkdir -p sources
rm -rf sources/.new && mkdir sources/.new && cd sources/.new
gh api repos/bobeff/open-source-games/contents/README.md -H 'Accept: application/vnd.github.raw' > bobeff.md
gh api repos/michelpereira/awesome-open-source-games/contents/README.md -H 'Accept: application/vnd.github.raw' > michelpereira.md
git clone -q --depth 1 https://github.com/Trilarion/opensourcegames.git trilarion
# GitHub search returns at most 1000 results: the top 1000 by stars for the topic.
python3 - <<'PY'
import json, subprocess, sys

def search(q, page=None):
    """One page of results, or stop: a failed, unreadable or incomplete reply is not an empty page."""
    args = ["gh", "api", "-X", "GET", "search/repositories", "-f", f"q={q}", "-f", "sort=stars", "-f", "per_page=100"]
    r = subprocess.run(args + (["-f", f"page={page}"] if page else []), capture_output=True, text=True)
    where = q + (f" page {page}" if page else "")
    try:
        body = json.loads(r.stdout)
    except ValueError:
        body = None
    if r.returncode != 0 or not isinstance(body, dict) or not isinstance(body.get("items"), list):
        why = (r.stderr.strip().splitlines() or ["the reply has no list of items"])[-1]
        sys.exit(f"fetch_sources.sh: search {where} failed ({why}); the lists in ./sources are unchanged.")
    if body.get("incomplete_results"):
        sys.exit(f"fetch_sources.sh: search {where} came back incomplete (GitHub timed out); the lists in "
                 "./sources are unchanged. Rerun.")
    return body["items"]

out = []
for page in range(1, 11):
    items = search("topic:open-source-game", page)
    out += [{"name": i["name"], "html_url": i["html_url"], "topics": i.get("topics", []),
             "description": i.get("description")} for i in items]
    if len(items) < 100:
        break
print(f"topic:open-source-game: {len(out)} repositories")
# The three lists and the topic search above are thin on some genres (fighting: 11 projects across
# all four sources). Top 100 by stars for a few genre topics fills them; each result keeps the
# topic that found it.
extra = []
for t in ["fighting-game", "beat-em-up", "rollback-netcode", "racing-game", "sports-game", "rhythm-game", "sandbox-game"]:
    items = search(f"topic:{t}")
    extra += [{"name": i["name"], "html_url": i["html_url"], "topics": [t] + i.get("topics", []),
               "description": i.get("description"), "via": t} for i in items]
    print(f"topic:{t}: {len(items)}")
json.dump(out, open("topic.json", "w"))
json.dump(extra, open("topics_extra.json", "w"))
PY
# Every source arrived: replace the old lists together.
cd ..
rm -rf trilarion
mv .new/trilarion .new/bobeff.md .new/michelpereira.md .new/topic.json .new/topics_extra.json .
rmdir .new
