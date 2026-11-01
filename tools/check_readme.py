#!/usr/bin/env python3
"""Check that the counts written by hand in README.md and the playbooks match the data they come from.

    python3 tools/check_readme.py              exit 1 and one line per number that disagrees
    python3 tools/check_readme.py --selftest   check the checker against altered copies of the files

Sources: data/catalog.json (games, genres, copy and active counts, build date, left-out count), data/software.json
(projects and categories), and the fixture list of tools/web/tests/browse_tests.py (its independent tests). The
generated pages (catalog/, software/README.md) are written by the build and are not checked here.
"""
import collections, json, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
# Playbooks that state no project count, on purpose. Any other playbook without a count sentence is reported.
NO_COUNT = {"fighting", "racing"}


def n(x):
    return f"{x:,}"


def facts(root):
    cat = json.loads((root / "data/catalog.json").read_text(encoding="utf-8"))
    sw = json.loads((root / "data/software.json").read_text(encoding="utf-8"))
    rows = cat["entries"]
    genres = collections.defaultdict(lambda: [0, 0, 0])
    for r in rows:
        g = genres[r["genre"]]
        g[0] += 1
        g[1] += r["reuse"] == "copy"
        g[2] += bool(r["active"])
    listing = subprocess.run([sys.executable, str(root / "tools/web/tests/browse_tests.py"), "--build",
                              str(root / "tools/web/bin/browse"), "--list"], capture_output=True, text=True, cwd=root)
    if listing.returncode != 0:
        sys.exit(f"check_readme: browse_tests.py --list failed: {listing.stderr.strip()[:300]}")
    return {"games": len(rows), "copy": sum(r["reuse"] == "copy" for r in rows), "built": cat["built"],
            "left_out": sum(cat["dropped"].values()), "genres": dict(genres), "software": len(sw["entries"]),
            "categories": len(sw["categories"]), "web_tests": len(listing.stdout.splitlines())}


def problems(root, f):
    out = []
    readme = (root / "README.md").read_text(encoding="utf-8")

    def expect(pattern, want, what, text=readme, where="README.md"):
        found = re.findall(pattern, text)
        if not found:
            out.append(f"{where}: no sentence found for {what} (pattern {pattern!r})")
        for got in found:
            if got != want:
                out.append(f"{where}: {what} reads {got}, the data says {want}")

    expect(r"a genre catalog of ([\d,]+) open-source games", n(f["games"]), "games in the catalog (domains table)")
    expect(r"\n([\d,]+) open-source games and engines with", n(f["games"]), "games in the catalog (Games)")
    expect(r"([\d,]+) of [\d,]+ projects have a permissive", n(f["copy"]), "copy projects")
    expect(r"[\d,]+ of ([\d,]+) projects have a permissive", n(f["games"]), "games in the catalog (Genres)")
    expect(r"permissive code license verified on GitHub\. Built (\d{4}-\d\d-\d\d)", f["built"], "catalog build date")
    expect(r"so ([\d,]+) projects found\s+only by a topic search", n(f["left_out"]), "projects left out")
    expect(r"\| ([\d,]+) hand-picked open-source", n(f["software"]), "software projects")
    expect(r"hand-picked open-source[^|]*? in (\d+) categories", str(f["categories"]), "software categories")
    expect(r"public-only proxy\. ([\d,]+) independent tests", n(f["web_tests"]), "tools/web independent tests")

    table = dict((m[0], m[1:]) for m in re.findall(r"^\| \[[^\]]+\]\(catalog/([\w-]+)\.md\) \| (\d+) \| (\d+) \| (\d+) \|",
                                                   readme, re.M))
    for genre, (total, copy, active) in sorted(f["genres"].items()):
        if genre not in table:
            out.append(f"README.md: genre table has no row for {genre} ({total} projects in the data)")
            continue
        for what, got, want in (("projects", table[genre][0], total), ("copy", table[genre][1], copy),
                                ("active", table[genre][2], active)):
            if int(got) != want:
                out.append(f"README.md: genre table, {genre} {what} reads {got}, the data says {want}")
    for genre in sorted(set(table) - set(f["genres"])):
        out.append(f"README.md: genre table has a row for {genre}, which the data does not have")

    for page in sorted((root / "playbooks").glob("*.md")):
        genre, text, where = page.stem, page.read_text(encoding="utf-8"), f"playbooks/{page.name}"
        total, copy, _ = f["genres"].get(genre, [0, 0, 0])
        seen = 0
        for got in re.findall(r"The full list of ([\d,]+)\s+projects", text):
            seen += 1
            if got != n(total):
                out.append(f"{where}: full list reads {got} projects, the data says {n(total)}")
        for got, got_copy in re.findall(r"The catalog lists ([\d,]+)\s+[\w-]+\s+projects,\s+(?:only\s+)?([\d,]+)\s+of them", text):
            seen += 1
            if got != n(total):
                out.append(f"{where}: catalog lists {got} projects, the data says {n(total)}")
            if got_copy != n(copy):
                out.append(f"{where}: catalog lists {got_copy} of them copy, the data says {n(copy)}")
        for got, none in re.findall(r"is thin: ([\d,]+)\s+projects(,\s+none with a permissive)?", text):
            seen += 1
            if got != n(total):
                out.append(f"{where}: thin list reads {got} projects, the data says {n(total)}")
            if none and copy:
                out.append(f"{where}: says none has a permissive license, the data says {copy} are copy")
        if not seen and genre not in NO_COUNT:
            out.append(f"{where}: no count sentence found (add one, or add {genre} to NO_COUNT in tools/check_readme.py)")
    return out


def selftest():
    import shutil, tempfile
    f = facts(ROOT)
    if problems(ROOT, f):
        sys.exit("selftest: the checked-in files must pass first; run without --selftest")
    edits = [
        ("README.md", f"a genre catalog of {n(f['games'])} ", f"a genre catalog of {n(f['games'] + 1)} "),
        ("README.md", f"{n(f['copy'])} of {n(f['games'])} projects", f"{n(f['copy'] - 1)} of {n(f['games'])} projects"),
        ("README.md", f"Built {f['built']}.", "Built 2000-01-01."),
        ("README.md", f"so {n(f['left_out'])} projects", f"so {n(f['left_out'] + 1)} projects"),
        ("README.md", f"| {n(f['software'])} hand-picked", f"| {n(f['software'] + 1)} hand-picked"),
        ("README.md", f" in {f['categories']} categories", f" in {f['categories'] + 1} categories"),
        ("README.md", f"{n(f['web_tests'])} independent tests", f"{n(f['web_tests'] + 1)} independent tests"),
        ("README.md", "| [Sports](catalog/sports.md) | ", "| [Sports](catalog/sports.md) | 9"),
        ("README.md", "| [Other](catalog/other.md) |", "| [Misc](catalog/misc.md) |"),
        ("README.md", "permissive code license verified on GitHub", "permissive license"),
        ("playbooks/puzzle.md", "The full list of ", "The full list of 1"),
        ("playbooks/strategy.md", f"The full list of {n(f['genres']['strategy'][0])}", "The full list of 999"),
        ("playbooks/arcade.md", f"lists {f['genres']['arcade'][0]} arcade", "lists 9 arcade"),
        ("playbooks/arcade.md", f"projects, {f['genres']['arcade'][1]} of them", "projects, 1 of them"),
        ("playbooks/action.md", f"only\n{f['genres']['action'][1]} of them", "only\n99 of them"),
        ("playbooks/educational.md", f"is thin: {f['genres']['educational'][0]}\nprojects", "is thin: 8\nprojects"),
        ("playbooks/sandbox.md", "The full list of ", "A list of "),
    ]
    failed = 0
    for path, old, new in edits:
        with tempfile.TemporaryDirectory() as tmp:
            t = pathlib.Path(tmp)
            for name in ("README.md", "playbooks"):
                (shutil.copytree if (ROOT / name).is_dir() else shutil.copy)(ROOT / name, t / name)
            text = (t / path).read_text(encoding="utf-8")
            if old not in text:
                print(f"FAIL selftest: {old!r} not in {path}")
                failed += 1
                continue
            (t / path).write_text(text.replace(old, new, 1), encoding="utf-8")
            found = problems(t, f)
        print(f"{'PASS' if found else 'FAIL'} selftest: {path} {old!r} -> {new!r} is caught")
        failed += not found
    print(f"{len(edits)} selftests, {failed} failed")
    return 1 if failed else 0


def main():
    if sys.argv[1:] == ["--selftest"]:
        return selftest()
    found = problems(ROOT, facts(ROOT))
    for line in found:
        print(line)
    print(f"README counts: {len(found)} disagree with the data" if found else "README counts match the data")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
