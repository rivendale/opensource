#!/usr/bin/env python3
"""Build the genre catalog from three public lists of open-source games plus GitHub topic searches.

    python3 tools/build_catalog.py --src <dir-with-sources> --out .

Sources (fetch them first; see tools/fetch_sources.sh):
  bobeff.md          github.com/bobeff/open-source-games README
  michelpereira.md   github.com/michelpereira/awesome-open-source-games README
  trilarion/         a clone of github.com/Trilarion/opensourcegames (entries/*.md)
  topic.json         GitHub search results for topic:open-source-game (top 1000 by stars)
  topics_extra.json  top 100 by stars for a few thin-genre topics (fighting-game, ...)
  tools/overrides.json (in this repo) manual license corrections where GitHub's detector is wrong

SAFETY FILTER (2026-09-23 review). Topic searches pull in malware lures: zero-star repositories
named after commercial games ("...-Full-Version", "...-Premium") whose README points to a zip
and whose workflow is obfuscated. A project found ONLY by a topic search is dropped under 10
stars, and any project whose name or description reads like a lure is dropped unless it has 50
stars. The dropped count is printed in catalog/README.md; nothing is removed silently.

A LIST NEVER UNLOCKS "copy". Only a license GitHub itself reports (or a manual override) can make
a project `copy`. A list's license or a repository GitHub cannot find reads `check first`; a
failed lookup stops the build before anything is written. Decompiled or disassembled commercial
games are `check first` whatever their stated license: reconstructed code does not carry the
original rights holder's permission.

Every GitHub repository is then looked up in GitHub's own API: license (SPDX), primary
language, stars, last push, archived. A list's claim about a license is never trusted when the
repository itself can be asked. Repositories off GitHub keep the license their list states,
marked as such.

Writes data/catalog.json, catalog/<genre>.md and catalog/README.md.

OTHER DOMAINS. `--domain software` builds the non-game list from curated seeds in
tools/domains/software.json (name, url, category, why) instead of parsing lists:

    python3 tools/build_catalog.py --domain software --src sources --out .

The same GitHub lookup, license classes and overrides apply. A seed is dropped, and listed with
its reason, when GitHub cannot find it, it is archived, or it redirects to a repository already
listed. A seed whose `listed_in` names a page in this repository that already lists it is linked
from its category page instead of listed twice; the build stops if that page no longer lists it.
Writes data/software.json, software/catalog/<category>.md and software/README.md.

GITHUB LOOKUPS need the GitHub CLI, `gh`, installed and signed in, for every repository not yet in
the cache; without it the build stops with one line saying so. A batch GitHub does not answer is
retried with exponential backoff and jitter. A batch still unanswered stops the build before any
output is written; the batches answered before it stay cached, so a rerun resumes there.
"""
import argparse, collections, datetime, json, os, random, re, subprocess, sys, time

GENRES = {  # slug: (title, one-line scope)
    "strategy": ("Strategy", "real-time, turn-based, 4X, tower defense, wargames"),
    "simulation": ("Simulation", "city building, business and tycoon, management, vehicle and life sims"),
    "arcade": ("Arcade", "shoot 'em ups, classic arcade, breakout- and asteroids-likes, clickers"),
    "action": ("Action", "action, beat 'em up, hack and slash, third-person"),
    "platformer": ("Platformer", "2D and 3D platformers"),
    "rpg": ("RPG", "role-playing, action RPG, MMORPG"),
    "roguelike": ("Roguelike", "roguelikes and roguelites"),
    "fighting": ("Fighting", "one-on-one and arena fighting games"),
    "shooter": ("Shooter", "first-person and third-person shooters"),
    "puzzle": ("Puzzle", "puzzle, logic, match-three"),
    "racing": ("Racing", "racing and driving"),
    "sports": ("Sports", "sports games"),
    "adventure": ("Adventure", "adventure, point-and-click, interactive fiction, visual novels"),
    "sandbox": ("Sandbox", "sandbox, survival, crafting, voxel"),
    "board-card": ("Board and card", "board, card, tabletop and party games"),
    "rhythm": ("Rhythm", "rhythm and music games"),
    "educational": ("Educational", "educational and programming games"),
    "engines": ("Engines and frameworks", "game engines, frameworks and libraries to build on"),
    "other": ("Other", "games the lists did not place in a genre"),
}

# label (lower case, from any list) -> genre slug; checked in order, first hit wins
LABELS = [
    (r"fight|beat 'em|beat em|beat-em|rollback", "fighting"), (r"rogue", "roguelike"),
    (r"tower def|real-time strat|turn-based strat|\bstrateg|\brts\b|4x|wargame|war game", "strategy"),
    (r"city-build|city build|tycoon|business|manag|simulat|\bsim\b", "simulation"),
    (r"shoot 'em up|shmup|\barcade|clicker|idle", "arcade"),
    (r"platform", "platformer"), (r"mmorpg|role[- ]playing|\brpg\b", "rpg"),
    (r"first-person|\bfps\b|third-person shoot|shooter", "shooter"),
    (r"puzzle|match-3|match three|logic", "puzzle"), (r"racing|driving|kart", "racing"),
    (r"sport|soccer|football|golf|tennis|basketball", "sports"),
    (r"point and click|point-and-click|adventure|visual novel|interactive fiction|text-based", "adventure"),
    (r"sandbox|survival|crafting|voxel|minecraft", "sandbox"),
    (r"board|card|chess|tabletop|party", "board-card"), (r"rhythm|music", "rhythm"),
    (r"education|programming|learning", "educational"),
    (r"game engine|framework|library|engine|toolkit|\btool\b", "engines"),
    (r"action|third-person|hack and slash", "action"),
]
PERMISSIVE = {"MIT", "MIT-0", "BSD-2-Clause", "BSD-3-Clause", "BSD-3-Clause-Clear", "0BSD", "Apache-2.0",
              "Zlib", "ISC", "Unlicense", "CC0-1.0", "BSL-1.0", "WTFPL", "NCSA", "PostgreSQL",
              "BSD-2-Clause-Patent", "UPL-1.0", "PHP-3.01", "Python-2.0"}
WEAK = {"LGPL-2.1", "LGPL-3.0", "LGPL-2.0", "MPL-2.0", "MPL-1.1", "EPL-1.0", "EPL-2.0", "CDDL-1.0", "MS-PL",
        "LGPL-2.1-only", "LGPL-2.1-or-later", "LGPL-3.0-only", "LGPL-3.0-or-later"}
COPYLEFT_RE = re.compile(r"^(A?GPL|CC-BY-SA|EUPL|OSL|CECILL)", re.I)
TRILARION_LICENSE = {"mit": "MIT", "bsd": "BSD-3-Clause", "2-clause bsd": "BSD-2-Clause", "3-clause bsd": "BSD-3-Clause",
                     "apache-2.0": "Apache-2.0", "zlib": "Zlib", "isc": "ISC", "public domain": "public domain",
                     "cc0": "CC0-1.0", "gpl-2.0": "GPL-2.0", "gpl-3.0": "GPL-3.0", "agpl-3.0": "AGPL-3.0",
                     "lgpl-2.1": "LGPL-2.1", "lgpl-3.0": "LGPL-3.0", "mpl-2.0": "MPL-2.0", "boost-1.0": "BSL-1.0",
                     "unlicense": "Unlicense", "wtfpl": "WTFPL", "cc-by-sa-4.0": "CC-BY-SA-4.0"}


LURE = re.compile(r"full[- _]?version|premium|free[- _]?download|\bcrack|keygen|unlocked|mod[- _]?menu|"
                  r"\bcheats?\b|\bhacks?\b|torrent|\btrainer\b|activation|for[- _]pc\b|\bdownload\b", re.I)
DECOMP = re.compile(r"decomp|disassembl|reverse[- ]?engineer", re.I)


def genre_of(labels):
    text = " ".join(labels).lower()
    for pat, g in LABELS:
        if re.search(pat, text):
            return g
    return "other"


def license_class(spdx):
    if spdx and " AND " in spdx and all(p in PERMISSIVE for p in spdx.split(" AND ")):
        return "copy"       # an SPDX AND of permissive licenses: keep every notice when copying
    if not spdx or spdx in ("NOASSERTION", "OTHER"):
        return "check"      # no clear license: all rights reserved until shown otherwise
    if spdx in PERMISSIVE:
        return "copy"
    if spdx in WEAK or spdx.startswith(("LGPL", "MPL", "EPL")):
        return "library"
    if COPYLEFT_RE.match(spdx):
        return "study"
    return "check"


def reuse_of(lic, lic_src, ov):
    """Only GitHub's own answer or a reviewed override (reuse_ok) can make a project `copy`;
    a license made of several parts (" + ") is always `check`."""
    reuse = license_class(lic) if (lic_src == "github" or (ov and ov.get("reuse_ok"))) else \
        ("check" if license_class(lic) == "copy" else license_class(lic))
    if " + " in (lic or ""):
        reuse = "check"
    return reuse


def load_overrides():
    ov_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "overrides.json")
    if not os.path.exists(ov_path):
        return {}
    return {k.lower(): v for k, v in json.load(open(ov_path)).items() if not k.startswith("_")}


def gh_slug(url):
    m = re.match(r"https?://(?:www\.)?github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?(?:[/#?].*)?$", url or "")
    return f"{m.group(1)}/{m.group(2)}" if m and m.group(1).lower() not in ("topics", "orgs", "sponsors") else None


def add(entries, name, url, source, labels, desc="", extra=None):
    slug = gh_slug(url)
    key = (slug or (url or name)).lower()
    e = entries.setdefault(key, {"name": name, "repo": url, "github": slug, "sources": [], "labels": [],
                                 "description": desc, "homepage": None})
    if source not in e["sources"]:
        e["sources"].append(source)
    e["labels"] += [l for l in labels if l and l not in e["labels"]]
    if desc and not e["description"]:
        e["description"] = desc
    for k, v in (extra or {}).items():
        if v and not e.get(k):
            e[k] = v


def parse_markdown_list(path, source, entries, skip_sections=()):
    h2 = h3 = ""
    for line in open(path, encoding="utf-8"):
        if line.startswith("## "):
            h2, h3 = line[3:].strip(), ""
            continue
        if line.startswith("### "):
            h3 = re.sub(r"[*\[\]]|\(http[^)]*\)", "", line[4:]).strip()
            continue
        if not re.match(r"\s*[-*] ", line) or any(s.lower() in h2.lower() for s in skip_sections):
            continue
        links = re.findall(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", line)
        if not links:
            continue
        name = re.sub(r"[*_]", "", links[0][0]).strip()
        src = next((u for t, u in links if "source" in t.lower()), None)
        gh = next((u for _, u in links if gh_slug(u)), None)
        url = src or gh or links[0][1]
        desc = re.sub(r"\[\[?[^\]]*\]?\]\([^)]*\)|\*|\[|\]", "", line.split(" - ", 1)[1] if " - " in line else "").strip()
        platform = "browser" if "browser" in h2.lower() else None
        add(entries, name, url, source, [h2, h3], desc[:200], {"platform": platform})


def parse_trilarion(root, entries):
    d = os.path.join(root, "entries")
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".md"):
            continue
        text = open(os.path.join(d, fn), encoding="utf-8", errors="replace").read()
        name = (re.search(r"^# (.+)$", text, re.M) or [None, fn[:-3]])[1].strip()
        field = lambda k: (re.search(rf"^- {k}: (.+)$", text, re.M) or [None, ""])[1].strip()
        repo = field("Code repository").split(",")[0].strip().split(" ")[0]
        kw = [k.strip() for k in field("Keyword").split(",") if k.strip()]
        lics = [x.strip().lower() for x in field("Code license").split(",") if x.strip()]
        lic = " + ".join(TRILARION_LICENSE.get(x, x.upper()) for x in lics)
        # ALL keywords: Trilarion often leads with "remake" and names the genre later
        add(entries, name, repo or field("Home").split(",")[0].strip(), "trilarion", kw, "",
            {"homepage": field("Home").split(",")[0].strip() or None,
             "list_license": lic or None,
             "list_language": field("Code language").split(",")[0].strip() or None,
             "deps": field("Code dependency") or None, "state": field("State") or None})


def parse_topic(path, entries):
    if not os.path.exists(path):
        return
    for r in json.load(open(path)):
        src = f"github-topic:{r['via']}" if r.get("via") else "github-topic"
        add(entries, r["name"], r["html_url"], src, r.get("topics", []), (r.get("description") or "")[:200])


def read_batch(stdout, n):
    """GitHub's answers for aliases r0..r{n-1}, or (None, why) when the reply is not an answer.
    A batch is answered only when "data" is an object. A null is kept only when GitHub sent a
    NOT_FOUND error for that alias; any other error, or a null nobody explained, is not an answer."""
    try:
        body = json.loads(stdout)
    except ValueError:
        return None, "the reply is not JSON"
    data = body.get("data") if isinstance(body, dict) else None
    errors = body.get("errors") if isinstance(body, dict) else None
    if not isinstance(data, dict):
        kinds = sorted({str(e.get("type") or e.get("message")) for e in errors if isinstance(e, dict)}) \
            if isinstance(errors, list) else []
        return None, "no data in the reply" + (f" (errors: {', '.join(kinds)})" if kinds else "")
    if not isinstance(errors, (list, type(None))):
        return None, "the reply's errors field is not a list"
    missing = set()
    for e in errors or []:
        path = e.get("path") if isinstance(e, dict) else None
        if isinstance(e, dict) and e.get("type") == "NOT_FOUND" and isinstance(path, list) and len(path) == 1:
            missing.add(path[0])
        else:
            return None, f"GitHub error {(e.get('type') or e.get('message')) if isinstance(e, dict) else e!r}"
    answers = []
    for j in range(n):
        g = data.get(f"r{j}")
        if g is None and f"r{j}" not in missing:
            return None, f"r{j} is null without a NOT_FOUND error"
        answers.append(g)   # None only here: GitHub says there is no such repository
    return answers, None


RETRIES = 4           # a batch GitHub does not answer is asked 5 times in all
BACKOFF_SECONDS = 4   # waits of 4, 8, 16 and 32 seconds before the retries, each stretched by up to 100% at random


def gh_graphql(query):
    """gh's reply to one GraphQL query. Stops the build with one line when gh is missing, not
    signed in, or its token is rejected: no retry can fix those."""
    try:
        p = subprocess.run(["gh", "api", "graphql", "-f", f"query={query}"], capture_output=True, text=True)
    except FileNotFoundError:
        sys.exit("gh, the GitHub CLI, is not installed: install it from https://cli.github.com, run "
                 "`gh auth login`, then rerun. Nothing written.")
    if p.returncode == 4:   # gh's exit status when it has no credentials at all
        sys.exit("gh is not signed in to GitHub: run `gh auth login` (or set GH_TOKEN), then rerun. Nothing written.")
    if p.returncode and "(HTTP 401)" in p.stderr:
        sys.exit("GitHub rejected gh's token (HTTP 401, bad credentials): run `gh auth login`, then rerun. "
                 "Nothing written.")
    return p.stdout


def save_cache(info, cache_path):
    """Replace the cache whole, so a build stopped mid-write keeps the previous file."""
    os.makedirs(os.path.dirname(os.path.abspath(cache_path)), exist_ok=True)   # sources/ is not in a fresh clone
    tmp = cache_path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(info, f)
    os.replace(tmp, cache_path)


def enrich(entries, cache_path, batch=50):
    """One GraphQL query per 50 repositories: GitHub's own answer for license and activity.
    Cached in the sources directory so a rebuild does not re-query; delete it to refresh.
    A batch is cached as soon as it is answered (see read_batch: "data" is an object and the only
    errors are NOT_FOUND). An unanswered batch is retried RETRIES times with exponential backoff
    and jitter; if it is still unanswered, the build stops before any output is written. What was
    answered before it stays cached, so a rerun resumes at the failed batch."""
    slugs = sorted({e["github"] for e in entries.values() if e["github"]})
    info = json.load(open(cache_path)) if os.path.exists(cache_path) else {}
    todo = [s for s in slugs if s.lower() not in info]
    batches = (len(todo) + batch - 1) // batch
    for k, i in enumerate(range(0, len(todo), batch), 1):
        chunk = todo[i:i + batch]
        parts = []
        for j, s in enumerate(chunk):
            o, n = s.split("/", 1)
            parts.append(f'r{j}: repository(owner: {json.dumps(o)}, name: {json.dumps(n)}) '
                         '{ nameWithOwner licenseInfo { spdxId } primaryLanguage { name } stargazerCount '
                         'pushedAt isArchived description homepageUrl }')
        q = "query {" + " ".join(parts) + "}"
        for attempt in range(RETRIES + 1):
            if attempt:
                wait = BACKOFF_SECONDS * 2 ** (attempt - 1) * (1 + random.random())
                print(f"  batch {k}/{batches} not answered ({why}); retry {attempt}/{RETRIES} in {wait:.0f}s",
                      file=sys.stderr)
                time.sleep(wait)
            answers, why = read_batch(gh_graphql(q), len(chunk))
            if answers is not None:
                break
        if answers is None:
            sys.exit(f"GitHub lookup failed for batch {k} of {batches} ({len(chunk)} repositories starting at "
                     f"{chunk[0]}) after {RETRIES} retries: {why}. Nothing written; {len(slugs) - len(todo) + i} of "
                     f"{len(slugs)} lookups are cached in {cache_path}, so a rerun resumes there.")
        info.update({s.lower(): a for s, a in zip(chunk, answers)})
        save_cache(info, cache_path)
        print(f"  enriched {min(i + batch, len(todo))}/{len(todo)} (cached {len(slugs) - len(todo)})", file=sys.stderr)
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--domain", default="games", help="games (default) or a seed file in tools/domains/, e.g. software")
    a = ap.parse_args()
    if a.domain != "games":
        return build_domain(a)
    entries = {}
    parse_markdown_list(os.path.join(a.src, "bobeff.md"), "bobeff", entries, skip_sections=("Other lists", "Table of contents"))
    parse_markdown_list(os.path.join(a.src, "michelpereira.md"), "awesome-open-source-games", entries,
                        skip_sections=("Contents", "Contributing", "License", "Related", "Other", "Tools"))
    parse_trilarion(os.path.join(a.src, "trilarion"), entries)
    parse_topic(os.path.join(a.src, "topic.json"), entries)
    parse_topic(os.path.join(a.src, "topics_extra.json"), entries)
    counts = collections.Counter(s for e in entries.values() for s in e["sources"])
    print(f"parsed {len(entries)} unique projects: {dict(counts)}", file=sys.stderr)

    info = enrich(entries, os.path.join(a.src, "github_cache.json"))
    overrides = load_overrides()
    today = datetime.date.today()
    out, dropped = [], collections.Counter()
    for e in entries.values():
        key = (e["github"] or "").lower()
        g = info.get(key) if e["github"] else None
        if e["github"] and g is None:
            e["github_status"] = "repository not found on GitHub"
        stars = (g or {}).get("stargazerCount") or 0
        topic_only = all(s.startswith("github-topic") for s in e["sources"])
        text = f"{e['name']} {e['github'] or ''} {(g or {}).get('description') or e['description'] or ''}"
        if topic_only and stars < 10:
            dropped["found only by a topic search, under 10 stars"] += 1
            continue
        # A topic-only repository with no code (README only) or tagged leak/crack/apk is the
        # lure shape the final review still found at 10+ stars.
        if topic_only and (g is not None and not (g.get("primaryLanguage") or {}).get("name")
                           or re.search(r"leak|pre-?release|crack|\bapk\b", " ".join(e["labels"]), re.I)):
            dropped["found only by a topic search, with no code or tagged leak/crack/apk"] += 1
            continue
        if overrides.get(key, {}).get("drop"):
            dropped["removed by a reviewed override (see tools/overrides.json)"] += 1
            continue
        if LURE.search(text) and stars < 50:
            dropped["name or description reads like a download lure"] += 1
            continue
        spdx = (g or {}).get("licenseInfo", {}) or {}
        spdx = spdx.get("spdxId") if isinstance(spdx, dict) else None
        if g:
            lic, lic_src = spdx, "github"
            if spdx in (None, "NOASSERTION", "OTHER") and e.get("list_license"):
                lic, lic_src = e["list_license"], "per list, GitHub could not read the license file"
        else:
            lic = e.get("list_license")
            lic_src = "per list, unverified" if lic else None
        ov = overrides.get(key)
        if ov and ov.get("license"):
            lic, lic_src = ov["license"], f"corrected: {ov['why']}"
        reuse = reuse_of(lic, lic_src, ov)
        decomp = bool(DECOMP.search(text + " " + " ".join(e["labels"]))) or bool(ov and ov.get("decompiled"))
        if decomp:
            reuse = "check"
        pushed = (g or {}).get("pushedAt")
        age_days = (today - datetime.date.fromisoformat(pushed[:10])).days if pushed else None
        out.append({
            "name": e["name"], "genre": genre_of(e["labels"]), "labels": e["labels"][:6],
            "sources": e["sources"], "repo": (g or {}).get("nameWithOwner") and f"https://github.com/{g['nameWithOwner']}" or e["repo"],
            "homepage": (g or {}).get("homepageUrl") or e.get("homepage"),
            "description": re.sub(r"\s*[\u2014\u2013]\s*", " - ", ((g or {}).get("description") or e["description"] or "")).strip()[:200],
            "language": ((g or {}).get("primaryLanguage") or {}).get("name") if g else e.get("list_language"),
            "license": lic, "license_from": lic_src, "reuse": reuse,
            "stars": (g or {}).get("stargazerCount"), "pushed": pushed[:10] if pushed else None,
            "active": age_days is not None and age_days <= 730, "archived": (g or {}).get("isArchived"),
            "deps": e.get("deps"), "platform": e.get("platform"), "state": e.get("state"),
            "note": "; ".join(x for x in [e.get("github_status"), (ov or {}).get("note"),
                                          "decompiled or disassembled commercial game: legal status unclear" if decomp else None] if x) or None,
        })
    out.sort(key=lambda r: (r["genre"], {"copy": 0, "library": 1, "study": 2, "check": 3}[r["reuse"]], -(r["stars"] or 0), r["name"].lower()))
    os.makedirs(os.path.join(a.out, "data"), exist_ok=True)
    os.makedirs(os.path.join(a.out, "catalog"), exist_ok=True)
    json.dump({"built": today.isoformat(), "count": len(out), "dropped": dict(dropped), "entries": out},
              open(os.path.join(a.out, "data", "catalog.json"), "w"), indent=1, ensure_ascii=False)
    print(f"dropped: {dict(dropped)}", file=sys.stderr)
    write_markdown(out, a.out, today, dropped)
    print(f"wrote {len(out)} entries", file=sys.stderr)


REUSE_TEXT = {"copy": "copy", "library": "library use", "study": "study only", "check": "check first"}


def reuse_text(r):
    """A copy row that carries a note reads "copy (see note)": the note can narrow what may be copied."""
    return REUSE_TEXT[r["reuse"]] + (" (see note)" if r["reuse"] == "copy" and r.get("note") else "")


def write_markdown(out, root, today, dropped):
    by = collections.defaultdict(list)
    for r in out:
        by[r["genre"]].append(r)
    idx = ["# Catalog", "", f"Built {today.isoformat()} from three public lists and GitHub topic searches; every GitHub "
           "project's license and activity read from GitHub's API that day. Rebuild with `tools/fetch_sources.sh && "
           "python3 tools/build_catalog.py --src sources --out .`", "",
           "**Left out on purpose:** " + ("; ".join(f"{n} {why}" for why, n in dropped.items()) or "nothing") +
           ". Those are mostly malware lures named after commercial games. **Never download a release, zip or "
           "installer from a catalog repository; read and build from source.** Report a lure you still find as an "
           "issue.", "",
           "**Reuse column:** `copy` = permissive code license (MIT, BSD, Apache, zlib...), code may be reused "
           "with attribution. `library use` = weak copyleft (LGPL, MPL): use unmodified as a library, do not copy "
           "into our code. `study only` = copyleft (GPL, AGPL): read it for design and mechanics, copy nothing. "
           "`check first` = no clear license, a license only a list states, or a decompiled commercial game: treat "
           "it as all rights reserved until you confirm otherwise. **A code license says nothing about "
           "the art, audio or data**, which often carry their own (frequently non-commercial) licenses.", "",
           "| genre | projects | copy | active in the last 2 years |", "|---|---|---|---|"]
    for slug, (title, scope) in GENRES.items():
        rows = by.get(slug, [])
        if not rows:
            continue
        idx.append(f"| [{title}]({slug}.md) | {len(rows)} | {sum(r['reuse'] == 'copy' for r in rows)} | "
                   f"{sum(1 for r in rows if r['active'])} |")
        md = [f"# {title}", "", f"{scope}. {len(rows)} projects; "
              f"{sum(r['reuse'] == 'copy' for r in rows)} with a permissive code license. Sorted by reuse, then stars.",
              "", "| project | reuse | license | language | stars | last push | about |", "|---|---|---|---|---|---|---|"]
        for r in rows:
            linkable = (r["repo"] or "").startswith(("http://", "https://"))
            name = f"[{esc(r['name'])}]({r['repo']})" if linkable else (f"{esc(r['name'])} (`{esc(r['repo'])}`)" if r["repo"] else esc(r["name"]))
            lic = (r["license"] or "none") + (f" ({r['license_from']})" if r["license_from"] and r["license_from"] != "github" else "")
            last = (r["pushed"] or "") + (" archived" if r["archived"] else "")
            about = esc(r["description"])[:120] + (f" **{esc(r['note'])}**" if r["note"] else "")
            md.append(f"| {name} | {reuse_text(r)} | {esc(lic)} | {esc(r['language'] or '')} | "
                      f"{r['stars'] if r['stars'] is not None else ''} | {last} | {about} |")
        open(os.path.join(root, "catalog", f"{slug}.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    open(os.path.join(root, "catalog", "README.md"), "w", encoding="utf-8").write("\n".join(idx) + "\n")


RANK = {"copy": 0, "library": 1, "study": 2, "check": 3}


def build_domain(a):
    """A domain other than games: curated seeds, GitHub's answer for each, every drop listed."""
    spec_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "domains", f"{a.domain}.json")
    if not os.path.exists(spec_path):
        sys.exit(f"no seed file for domain {a.domain!r}: {spec_path}")
    spec = json.load(open(spec_path, encoding="utf-8"))
    cats = [c["slug"] for c in spec["categories"]]
    seeds, entries, dropped, elsewhere = spec["seeds"], {}, [], collections.defaultdict(list)
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    overrides = load_overrides()
    for s in seeds:
        if s["category"] not in cats:
            sys.exit(f"{s['name']}: category {s['category']!r} is not in {spec_path}")
        slug = gh_slug(s["url"])
        if not slug:
            dropped.append((s, "not a GitHub repository URL"))
        elif slug.lower() in entries:
            dropped.append((s, "listed twice in the seed file"))
        elif s.get("listed_in"):
            # Listed once, where it already is; the category page links there.
            page = os.path.join(repo_root, s["listed_in"])
            text = open(page, encoding="utf-8").read() if os.path.isfile(page) else ""
            if f"](https://github.com/{slug})".lower() not in text.lower():
                sys.exit(f"{s['name']}: listed_in {s['listed_in']}, but that page does not list {s['url']}; "
                         "remove listed_in to list it here. Nothing written.")
            dropped.append((s, f"listed in {s['listed_in']}, not repeated here"))
            elsewhere[s["category"]].append({**s, "note": (overrides.get(slug.lower()) or {}).get("note")})
        else:
            entries[slug.lower()] = {"github": slug, "seed": s}
    print(f"{len(seeds)} seeds, {len(entries)} distinct GitHub repositories", file=sys.stderr)
    info = enrich(entries, os.path.join(a.src, f"github_cache_{a.domain}.json"))   # exits on a failed lookup
    today = datetime.date.today()
    out, kept = [], set()
    for key, e in entries.items():
        s, g = e["seed"], info.get(key)
        if g is None:
            dropped.append((s, "repository not found on GitHub"))
            continue
        canon = g["nameWithOwner"]
        ov = overrides.get(canon.lower()) or overrides.get(key)
        if g.get("isArchived"):
            dropped.append((s, "archived on GitHub"))
            continue
        if ov and ov.get("drop"):
            dropped.append((s, f"removed by a reviewed override: {ov.get('why')}"))
            continue
        if canon.lower() in kept:
            dropped.append((s, f"redirects to {canon}, which is already listed"))
            continue
        kept.add(canon.lower())
        lic, lic_src = (g.get("licenseInfo") or {}).get("spdxId"), "github"
        if ov and ov.get("license"):
            lic, lic_src = ov["license"], f"corrected: {ov['why']}"
        pushed = g.get("pushedAt")
        age_days = (today - datetime.date.fromisoformat(pushed[:10])).days if pushed else None
        out.append({
            "name": canon if s["name"].lower() == key else s["name"], "category": s["category"],
            "repo": f"https://github.com/{canon}", "homepage": g.get("homepageUrl") or None, "why": s["why"],
            "language": (g.get("primaryLanguage") or {}).get("name"),
            "license": lic, "license_from": lic_src, "reuse": reuse_of(lic, lic_src, ov),
            "stars": g.get("stargazerCount"), "pushed": pushed[:10] if pushed else None,
            "active": age_days is not None and age_days <= 730, "note": (ov or {}).get("note") or None,
        })
    if len(out) + len(dropped) != len(seeds):
        sys.exit(f"reconcile failed: {len(seeds)} seeds, {len(out)} rows, {len(dropped)} dropped")
    out.sort(key=lambda r: (cats.index(r["category"]), RANK[r["reuse"]], -(r["stars"] or 0), r["name"].lower()))
    drops = [{"name": s["name"], "url": s["url"], "reason": why, **({"listed_in": s["listed_in"]} if s.get("listed_in") and why.startswith("listed in") else {})} for s, why in dropped]
    os.makedirs(os.path.join(a.out, "data"), exist_ok=True)
    json.dump({"built": today.isoformat(), "domain": a.domain, "count": len(out), "seeds": len(seeds),
               "dropped": drops, "categories": spec["categories"], "entries": out},
              open(os.path.join(a.out, "data", f"{a.domain}.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    write_domain(spec, out, drops, os.path.join(a.out, a.domain), today, a.domain, elsewhere)
    print(f"{len(seeds)} seeds = {len(out)} rows + {len(drops)} dropped", file=sys.stderr)
    for d in drops:
        print(f"  dropped {d['name']}: {d['reason']}", file=sys.stderr)


def write_domain(spec, out, drops, root, today, domain, elsewhere):
    os.makedirs(os.path.join(root, "catalog"), exist_ok=True)
    by = collections.defaultdict(list)
    for r in out:
        by[r["category"]].append(r)
    counts = lambda rows, cls: sum(r["reuse"] == cls for r in rows)
    table = ["| category | projects | copy | library use | study only | check first | covers |", "|---|---|---|---|---|---|---|"]
    for c in spec["categories"]:
        rows = by.get(c["slug"], [])
        if not rows:
            continue
        table.append(f"| [{c['title']}](catalog/{c['slug']}.md) | {len(rows)} | {counts(rows, 'copy')} | "
                     f"{counts(rows, 'library')} | {counts(rows, 'study')} | {counts(rows, 'check')} | {esc(c['scope'])} |")
        md = [f"# {c['title']}", "",
              f"{c['scope'][0].upper() + c['scope'][1:]}. {len(rows)} projects; {counts(rows, 'copy')} with a permissive "
              f"code license. Sorted by reuse, then stars. Part of the [{spec['title'].lower()} list](../README.md), which "
              "explains the reuse classes.", ""]
        if c.get("note"):
            md += [c["note"], ""]
        md += ["| project | reuse | license | language | stars | last push | why |", "|---|---|---|---|---|---|---|"]
        for r in rows:
            lic = (r["license"] or "none") + (" (per license file)" if r["license_from"] != "github" else "")
            why = esc(r["why"]) + (f" **{esc(r['note'])}**" if r["note"] else "")
            md.append(f"| [{esc(r['name'])}]({r['repo']}) | {reuse_text(r)} | {esc(lic)} | {esc(r['language'] or '')} | "
                      f"{r['stars'] if r['stars'] is not None else ''} | {r['pushed'] or ''} | {why} |")
        if any(r["license_from"] != "github" for r in rows):
            md += ["", "A license marked *per license file* was read from the repository's own license files, because "
                   "GitHub's detector could not classify it or reported only part of it; the file and the reason are recorded in "
                   "[tools/overrides.json](../../tools/overrides.json)."]
        if elsewhere.get(c["slug"]):
            md += ["", "Listed once elsewhere in this repository, so not repeated here:", ""]
            md += [f"- [{esc(s['name'])}]({s['url']}), in [{s['listed_in']}](../../{s['listed_in']}): {esc(s['why'])}" +
                   (f" **{esc(s['note'])}**" if s["note"] else "") for s in elsewhere[c["slug"]]]
        open(os.path.join(root, "catalog", f"{c['slug']}.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    res = ["| resource | covers | license | use |", "|---|---|---|---|"]
    for r in spec.get("resources", []):
        res.append(f"| [{esc(r['name'])}]({r['url']}) | {esc(r['covers'])} | {esc(r['license'])} | {esc(r['use'])} |")
    moved = [d for d in drops if d.get("listed_in")]
    gone = [d for d in drops if not d.get("listed_in")]
    left = [f"- [{esc(d['name'])}]({d['url']}): {esc(d['reason'])}" for d in gone] or \
        ["Nothing: every seed was found on GitHub and is not archived."]
    elsewhere_lines = [f"- [{esc(d['name'])}]({d['url']}): see [{d['listed_in']}](../{d['listed_in']})" for d in moved]
    idx = [f"# {spec['title']}", ""]
    for p in spec["intro"]:
        idx += [p, ""]
    idx += ["## Reuse classes", "",
            "The same four classes as the games catalog; which licenses fall in each is set by the "
            "[license rule](../README.md#the-license-rule).", "",
            "| reuse class | what it means for an application or tool |", "|---|---|",
            "| `copy` | copy its code into your project, keep the copyright notice, and record it in `THIRD_PARTY.md` |",
            "| `library use` | depend on it unmodified as a library; do not paste its code into yours |",
            "| `study only` | run it and read it for design; copy none of its code |",
            "| `check first` | treat the code as all rights reserved until you have read its license yourself |", "",
            "A `copy` row that carries a note reads `copy (see note)`: the note names a part under other terms, such "
            "as a bundled GPL file, or something to know before you run or copy it.", "",
            "**Running a GPL or AGPL program unmodified is fine; the class limits copying code.** Installing a "
            "`study only` application and using it as it ships is ordinary use. Obligations start when you copy its "
            "code into your own project, or, for AGPL, when you modify it and let other people use the modified "
            "version over a network. Some `check first` rows are source-available (a Business Source, Elastic or "
            "enterprise license, or an open core with a commercial directory), and those terms can limit production "
            "or commercial use even when you change nothing: read them before you deploy.", "",
            "## Categories", "",
            f"Built {today.isoformat()}: {len(out)} projects, {counts(out, 'copy')} with a permissive code license.",
            ""] + table + ["",
            "## Resources", "",
            "Curated lists and courses that go wider than this one. Each keeps its own license, and that license decides whether a "
            "tool may **parse** the list into generated data like this catalog or only **link** to it. A share-alike "
            "list (CC-BY-SA) would carry its license into this repository's MIT data, so it is linked, never parsed. "
            "A license stated only in a README badge, with no license file, is treated like a list's claim: link only "
            "until confirmed.", "",
            "This catalog's seeds were chosen by hand. Some candidates were found through four permissively licensed "
            "lists, taking project names and addresses only: "
            "[pluja/awesome-privacy](https://github.com/pluja/awesome-privacy) (CC0-1.0), "
            "[krzemienski/awesome-video](https://github.com/krzemienski/awesome-video) (CC0-1.0), "
            "[meichthys/foss_photo_libraries](https://github.com/meichthys/foss_photo_libraries) (MIT) and "
            "[ad-si/awesome-music-production](https://github.com/ad-si/awesome-music-production) (ISC). Thanks to their "
            "maintainers. The one-line descriptions were written for this catalog; some stay close to the project's own "
            "description.", ""] + res + ["",
            "## How this list is built", "",
            f"Seeds live in [`tools/domains/{domain}.json`](../tools/domains/{domain}.json): name, repository, category "
            f"and one line on why. `tools/build_catalog.py --domain {domain}` (it needs the GitHub CLI, `gh`, installed and signed in) asks GitHub's API for each repository's "
            "license, language, stars, last push and archived flag. License corrections, each with the file it was "
            "read from, live in [`tools/overrides.json`](../tools/overrides.json). To add a project, add a seed and "
            "rebuild; do not hand-edit this file, `catalog/` or the data file.", "",
            "```sh", f"python3 tools/build_catalog.py --domain {domain} --src sources --out .", "```", "",
            f"**Left out at build time:** {len(gone)} of {len(out) + len(drops)} seeds.", ""] + left + \
           (["", f"**Listed once, elsewhere in this repository:** {len(moved)}.", ""] + elsewhere_lines if moved else [])
    open(os.path.join(root, "README.md"), "w", encoding="utf-8").write("\n".join(idx) + "\n")


def esc(s):
    s = re.sub(r"\s*[\u2014\u2013]\s*", " - ", s or "")    # no em or en dashes in this repository
    return re.sub(r"\|", "\\|", re.sub(r"\s+", " ", s)).strip()


if __name__ == "__main__":
    main()
