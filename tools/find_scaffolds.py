#!/usr/bin/env python3
"""Find the best-maintained open-source starter templates and AI bridges (MCP servers) for game
development, and verify each on GitHub.

    python3 tools/find_scaffolds.py --out .        (needs `gh`, logged in)

For every query below, GitHub search returns the top results by stars; each repository is then
read from GitHub's API (license, language, stars, last push, archived). Kept only if it has code,
a license GitHub can identify, 25+ stars, and a push in the last three years. The same lure filter
as the catalog applies, off-topic matches are excluded by name, and an MCP server's repo and its
owner's account must both be at least 60 days old. INCLUDE adds official templates that search
misses. Writes data/scaffolds.json and scaffolds/<kind>.md. Art-tool add-ons are not generated:
the hand-checked add-on tables live in art/blender.md and art/2d.md.
"""
import argparse, collections, datetime, json, os, re, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_catalog import license_class, LURE, esc  # noqa: E402

# (kind, group, GitHub search query)
QUERIES = [
    ("scaffold", "Godot", "topic:godot-template"), ("scaffold", "Godot", "godot template in:name,description"),
    ("scaffold", "Godot", "topic:godot-starter-kit"), ("scaffold", "Godot", "godot starter kit in:name,description"),
    ("scaffold", "Unity", "topic:unity-template"), ("scaffold", "Unity", "unity template in:name"),
    ("scaffold", "Unity", "unity boilerplate in:name,description"),
    ("scaffold", "Bevy", "topic:bevy-template"), ("scaffold", "Bevy", "bevy template in:name"),
    ("scaffold", "Phaser", "topic:phaser-template"), ("scaffold", "Phaser", "phaser template in:name"),
    ("scaffold", "LOVE", "love2d template in:name,description"), ("scaffold", "LOVE", "topic:love2d-template"),
    ("scaffold", "raylib", "raylib template in:name,description"),
    ("scaffold", "MonoGame", "monogame template in:name,description"),
    ("scaffold", "Defold", "defold template in:name,description"),
    ("scaffold", "Three.js", "threejs game template in:name,description"),
    ("scaffold", "PixiJS", "pixi game template in:name,description"),
    ("scaffold", "Excalibur", "excalibur template in:name,description"),
    ("scaffold", "Any engine", "topic:game-template"), ("scaffold", "Any engine", "topic:game-boilerplate"),
    ("mcp", "Blender", "blender mcp in:name,description"), ("mcp", "Godot", "godot mcp in:name,description"),
    ("mcp", "Unity", "unity mcp in:name,description"), ("mcp", "GIMP", "gimp mcp in:name,description"),
    ("mcp", "Krita", "krita mcp in:name,description"), ("mcp", "Unreal", "unreal mcp in:name,description"),
]
KIND_TITLE = {"scaffold": "Starter templates (scaffolds)", "mcp": "AI bridges (MCP servers) for game and art tools"}
# Official templates that keyword search misses; the hand-written guides recommend them first.
INCLUDE = [("scaffold", "Bevy", "TheBevyFlock/bevy_new_2d"), ("scaffold", "Phaser", "phaserjs/template-vite-ts"),
           ("scaffold", "Phaser", "phaserjs/template-vite"), ("scaffold", "Phaser", "phaserjs/template-webpack")]
# Search matches that are not game or art tools ("Unity Catalog" is a Databricks product).
OFF_TOPIC = re.compile(r"databricks|unity[ -]catalog|decompil|\bifc\b|\bbim\b|\bdscs\b", re.I)
MIN_AGE_DAYS = 60
HEADER = {
    "scaffold": "The hand-checked shortlist, with what each template includes and its asset licenses, is in "
                "[README.md](README.md#shortlist-by-engine); start there.",
    "mcp": "**Metadata checked, not security-reviewed.** Every entry can run code on your machine, and some listen "
           "on every network interface by default. Read the [safe setup checklist](../ai/graphics.md#safe-setup-checklist) "
           "and the [maintained servers per tool](../ai/graphics.md#maintained-servers-per-tool) first.",
}


def search(q, n=30):
    r = subprocess.run(["gh", "api", "-X", "GET", "search/repositories", "-f", f"q={q}", "-f", "sort=stars",
                        "-f", f"per_page={n}"], capture_output=True, text=True)
    try:
        return json.loads(r.stdout).get("items", [])
    except ValueError:
        return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    today = datetime.date.today()
    found = {}
    for kind, group, q in QUERIES:
        items = search(q)
        time.sleep(2.5)   # the search API allows 30 requests a minute
        print(f"  {kind:8} {group:10} {len(items):3}  {q}", file=sys.stderr)
        for i in items:
            key = i["full_name"].lower()
            e = found.setdefault(key, {"repo": i["html_url"], "name": i["full_name"], "kind": kind, "group": group,
                                       "queries": []})
            e["queries"].append(q)
    for kind, group, name in INCLUDE:
        found.setdefault(name.lower(), {"repo": f"https://github.com/{name}", "name": name, "kind": kind, "group": group,
                                        "queries": []})["queries"].append("include list")
    owners, out, dropped = {}, [], collections.Counter()
    for e in found.values():
        r = subprocess.run(["gh", "api", f"repos/{e['name']}"], capture_output=True, text=True)
        try:
            g = json.loads(r.stdout)
        except ValueError:
            dropped["lookup failed"] += 1
            continue
        spdx = (g.get("license") or {}).get("spdx_id")
        pushed = (g.get("pushed_at") or "")[:10]
        age = (today - datetime.date.fromisoformat(pushed)).days if pushed else 99999
        text = f"{e['name']} {g.get('description') or ''}"
        if not g.get("language"):
            dropped["no code"] += 1; continue
        if (g.get("stargazers_count") or 0) < 25:
            dropped["under 25 stars"] += 1; continue
        if age > 1095:
            dropped["no push in 3 years"] += 1; continue
        if not spdx or spdx in ("NOASSERTION", "OTHER"):
            dropped["no license GitHub can identify"] += 1; continue
        if LURE.search(text) and (g.get("stargazers_count") or 0) < 50:
            dropped["reads like a download lure"] += 1; continue
        if OFF_TOPIC.search(text):
            dropped["off-topic (not a game or art tool)"] += 1; continue
        # "mcp" in a search matches names like "MCprep": an AI bridge must say MCP as a word
        if e["kind"] == "mcp" and not (re.search(r"MCP", text) or re.search(r"\bmcp\b|model context protocol", text, re.I)):
            dropped["not an MCP server"] += 1; continue
        if e["kind"] == "mcp":
            owner = g["owner"]["login"]
            if owner not in owners:
                o = subprocess.run(["gh", "api", f"users/{owner}", "--jq", ".created_at"], capture_output=True, text=True)
                owners[owner] = o.stdout.strip()[:10]
            ages = [(today - datetime.date.fromisoformat(d)).days for d in ((g.get("created_at") or "")[:10], owners[owner]) if d]
            if len(ages) < 2 or min(ages) < MIN_AGE_DAYS:
                dropped[f"MCP repo or owner under {MIN_AGE_DAYS} days old"] += 1; continue
        out.append({**{k: e[k] for k in ("name", "repo", "kind", "group")},
                    "description": re.sub(r"\s*[\u2014\u2013]\s*", " - ", (g.get("description") or "")).strip()[:200],
                    "language": g.get("language"), "license": spdx, "reuse": license_class(spdx),
                    "stars": g.get("stargazers_count"), "pushed": pushed, "archived": g.get("archived"),
                    "topics": g.get("topics", [])[:8]})
    out.sort(key=lambda r: (r["kind"], r["group"], -(r["stars"] or 0)))
    os.makedirs(os.path.join(a.out, "data"), exist_ok=True)
    os.makedirs(os.path.join(a.out, "scaffolds"), exist_ok=True)
    json.dump({"built": today.isoformat(), "count": len(out), "dropped": dict(dropped), "entries": out},
              open(os.path.join(a.out, "data", "scaffolds.json"), "w"), indent=1, ensure_ascii=False)
    REUSE = {"copy": "copy", "library": "library use", "study": "study only", "check": "check first"}
    for kind, title in KIND_TITLE.items():
        rows = [r for r in out if r["kind"] == kind]
        md = [f"# {title}", "", f"Found by GitHub search on {today.isoformat()}, then verified on GitHub: code, a license "
              "GitHub can identify, 25+ stars, a push in the last three years. Search is a starting point, not an "
              "endorsement: read a repository before you build on it. Reuse classes as in the main catalog.", "",
              HEADER[kind], ""]
        for grp in sorted({r["group"] for r in rows}):
            md += [f"## {grp}", "", "| repository | reuse | license | language | stars | last push | about |",
                   "|---|---|---|---|---|---|---|"]
            for r in [x for x in rows if x["group"] == grp]:
                md.append(f"| [{esc(r['name'])}]({r['repo']}) | {REUSE[r['reuse']]} | {r['license']} | {esc(r['language'])} | "
                          f"{r['stars']} | {r['pushed']}{' archived' if r['archived'] else ''} | {esc(r['description'])[:110]} |")
            md.append("")
        open(os.path.join(a.out, "scaffolds", f"{kind}s.md"), "w", encoding="utf-8").write("\n".join(md))
    print(f"kept {len(out)}; dropped {dict(dropped)}", file=sys.stderr)


if __name__ == "__main__":
    main()
