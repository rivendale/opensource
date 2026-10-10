#!/usr/bin/env python3
"""Check an assets/MANIFEST.json against skills/studio/manifest.schema.json and the rules a schema cannot state.

    python3 skills/studio/validate_manifest.py MANIFEST.json [--root DIR] [--exports SUBDIR] [--import-path SUBDIR ...]
    python3 skills/studio/validate_manifest.py --self-check

  MANIFEST.json   the manifest to check
  --root DIR      the project root: every file, master and build_script must exist under it
  --exports SUBDIR  (default: assets; needs --root) every file under it, except MANIFEST.json, must have a row
  --import-path SUBDIR  (repeatable; needs --root) the engine's import path: no master and no build_script may sit inside it

Exit 0 valid, 1 invalid (one "path: message" line per problem), 2 not readable as JSON. Standard library only. The rules are written out here, not
read from the schema; --self-check runs the fixtures in manifest-examples/ and, when the jsonschema package is installed, checks that the schema
file says the same as this validator on each of them.
"""
import json, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
SCHEMA = HERE / "manifest.schema.json"
EXAMPLES = HERE / "manifest-examples"
KINDS = {"sprite", "tile", "ui", "background", "key-art", "title", "icon", "sfx", "music", "voice", "video", "model3d", "build", "other"}
REFERENCE = {"none", "layout", "style", "character"}
REQUIRED = ["file", "kind", "tool", "tool_version", "seed_or_params", "date", "model", "weights_license", "source", "source_license", "reference_used_as", "master", "build_script", "paid_service"]
OPTIONAL = ["text", "consent_record"]
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def nonempty(x):
    return isinstance(x, str) and x.strip() != ""


def path_error(x):
    if not isinstance(x, str) or not x:
        return "must be a non-empty string"
    if x.startswith("/") or x.startswith("\\") or "\\" in x:
        return "must be relative, with forward slashes"
    if ".." in x.split("/"):
        return "must not contain a .. segment"
    return None


def check_row(i, r, errs):
    p = f"assets[{i}]"
    if not isinstance(r, dict):
        errs.append((p, "must be an object"))
        return
    for k in REQUIRED:
        if k not in r:
            errs.append((f"{p}.{k}", "is required"))
    for k in r:
        if k not in REQUIRED and k not in OPTIONAL:
            errs.append((f"{p}.{k}", "is not a manifest field"))
    for k in ("file",):
        if k in r and (e := path_error(r[k])):
            errs.append((f"{p}.{k}", e))
    for k in ("master", "build_script", "consent_record"):
        if k in r and r[k] is not None and (e := path_error(r[k])):
            errs.append((f"{p}.{k}", e))
    if "kind" in r and r["kind"] not in KINDS:
        errs.append((f"{p}.kind", f"must be one of {sorted(KINDS)}"))
    for k in ("tool", "tool_version"):
        if k in r and not nonempty(r[k]):
            errs.append((f"{p}.{k}", "must be a non-empty string"))
    if "seed_or_params" in r:
        v = r["seed_or_params"]
        if not (nonempty(v) or (isinstance(v, int) and not isinstance(v, bool)) or (isinstance(v, dict) and v)):
            errs.append((f"{p}.seed_or_params", "must be a non-empty string, an integer or a non-empty object"))
    if "date" in r and not (isinstance(r["date"], str) and DATE.match(r["date"])):
        errs.append((f"{p}.date", "must be YYYY-MM-DD"))
    for k in ("model", "weights_license", "source", "source_license"):
        if k in r and r[k] is not None and not nonempty(r[k]):
            errs.append((f"{p}.{k}", "must be a non-empty string or null"))
    if r.get("model") is not None and nonempty(r.get("model")) and not nonempty(r.get("weights_license")):
        errs.append((f"{p}.weights_license", "is required when a model made the file"))
    if r.get("source") is not None and nonempty(r.get("source")) and not nonempty(r.get("source_license")):
        errs.append((f"{p}.source_license", "is required when the file reuses material"))
    if "reference_used_as" in r and r["reference_used_as"] not in REFERENCE:
        errs.append((f"{p}.reference_used_as", f"must be one of {sorted(REFERENCE)}"))
    if "paid_service" in r and r["paid_service"] is not None:
        ps = r["paid_service"]
        if not isinstance(ps, dict) or set(ps) != {"name", "named_in_brief"} or not nonempty(ps.get("name")) or not isinstance(ps.get("named_in_brief"), bool):
            errs.append((f"{p}.paid_service", "must be null or {name, named_in_brief: true or false}"))
    if "text" in r:
        t = r["text"]
        if not isinstance(t, list) or any(not isinstance(e, dict) or set(e) != {"string", "font"} or not nonempty(e.get("string")) or not nonempty(e.get("font")) for e in t):
            errs.append((f"{p}.text", "must be a list of {string, font}"))


def cross_checks(m, errs, root=None, exports="assets", import_paths=()):
    rows = [r for r in m["assets"] if isinstance(r, dict)]
    seen = {}
    for i, r in enumerate(rows):
        f = r.get("file")
        if isinstance(f, str):
            if f in seen:
                errs.append((f"assets[{i}].file", f"duplicates assets[{seen[f]}]: one row per file"))
            seen.setdefault(f, i)
        ps = r.get("paid_service")
        if isinstance(ps, dict) and ps.get("named_in_brief") is False:
            errs.append((f"assets[{i}].paid_service", "a paid service was used that the brief did not name"))
    if root is None:
        return
    root = pathlib.Path(root)
    for i, r in enumerate(rows):
        for k in ("file", "master", "build_script", "consent_record"):
            v = r.get(k)
            if isinstance(v, str) and not path_error(v) and not (root / v).is_file():
                errs.append((f"assets[{i}].{k}", f"{v!r} does not exist under the project root"))
        for k in ("master", "build_script"):
            v = r.get(k)
            if isinstance(v, str) and not path_error(v):
                for ip in import_paths:
                    ip = ip.strip("/")
                    if v == ip or v.startswith(ip + "/"):
                        errs.append((f"assets[{i}].{k}", f"{v!r} is inside the engine import path {ip!r}"))
    ex = root / exports
    if ex.is_dir():
        have = set(seen)
        for f in sorted(p for p in ex.rglob("*") if p.is_file()):
            rel = f.relative_to(root).as_posix()
            if f.name == "MANIFEST.json" and f.parent == ex:
                continue
            if rel not in have:
                errs.append(("assets", f"{rel!r} is in {exports}/ and has no manifest row"))


def validate(m, root=None, exports="assets", import_paths=()):
    errs = []
    if not isinstance(m, dict):
        return [("$", "must be an object")]
    for k in m:
        if k not in ("manifest_version", "assets"):
            errs.append((k, "is not a manifest field"))
    if m.get("manifest_version") != 1 or isinstance(m.get("manifest_version"), bool):
        errs.append(("manifest_version", "must be 1"))
    if not isinstance(m.get("assets"), list):
        errs.append(("assets", "must be a list"))
        return errs
    for i, r in enumerate(m["assets"]):
        check_row(i, r, errs)
    cross_checks(m, errs, root, exports, import_paths)
    return errs


def self_check():
    man = json.loads((EXAMPLES / "manifest.json").read_text())
    bad, lines = 0, []

    def note(ok, msg):
        nonlocal bad
        bad += (not ok)
        lines.append(f"  {'ok  ' if ok else 'FAIL'} {msg}")

    for name in man["valid"]:
        errs = validate(json.loads((EXAMPLES / "valid" / name).read_text()))
        note(not errs, f"valid/{name}" + (f"  -> {errs[:2]}" if errs else ""))
    for name, meta in man["invalid"].items():
        errs = validate(json.loads((EXAMPLES / "invalid" / name).read_text()))
        hit = any(p == meta["expect"] or p.startswith(meta["expect"] + ".") or p.startswith(meta["expect"] + "[") for p, _ in errs)
        note(bool(errs) and hit, f"invalid/{name}: names {meta['expect']}" + ("" if hit else f"  -> got {[p for p, _ in errs][:4] or 'no error'}"))
    for junk in (None, [], "text", 3, {}):
        try:
            note(bool(validate(junk)), f"non-manifest input {junk!r} is invalid")
        except Exception as e:  # noqa: BLE001
            note(False, f"non-manifest input {junk!r} crashed the validator: {e}")
    # the file-system rules, on a throwaway tree
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        (d / "assets").mkdir(); (d / "masters").mkdir(); (d / "tools").mkdir()
        (d / "assets/a.png").write_bytes(b"x"); (d / "assets/extra.png").write_bytes(b"x"); (d / "masters/a.xcf").write_bytes(b"x"); (d / "tools/make.sh").write_text("x")
        row = json.loads((EXAMPLES / "valid" / man["valid"][0]).read_text())["assets"][0]
        row = dict(row, file="assets/a.png", master="masters/a.xcf", build_script="tools/make.sh")
        m = {"manifest_version": 1, "assets": [row]}
        e = validate(m, root=d)
        note(any("extra.png" in msg and "no manifest row" in msg for _, msg in e) and len(e) == 1, "root: a file in assets/ without a row is named, nothing else is wrong")
        e = validate(dict(m, assets=[dict(row, file="assets/missing.png")]), root=d)
        note(any(p == "assets[0].file" and "does not exist" in msg for p, msg in e), "root: a row whose file is missing is named")
        e = validate(m, root=d, import_paths=["masters"])
        note(any(p == "assets[0].master" and "import path" in msg for p, msg in e), "import path: a master inside it is named")
        e = validate(m, root=d, import_paths=["assets"])
        note(not any(p == "assets[0].master" for p, _ in e), "import path: a master outside it is not named")
    try:
        import jsonschema
        schema = json.loads(SCHEMA.read_text())
        v = jsonschema.Draft202012Validator(schema)
        agree = 0
        for name in man["valid"]:
            note(v.is_valid(json.loads((EXAMPLES / "valid" / name).read_text())), f"jsonschema agrees valid/{name} is valid")
        for name, meta in man["invalid"].items():
            if meta["layer"] == "schema":
                ok = not v.is_valid(json.loads((EXAMPLES / "invalid" / name).read_text()))
                note(ok, f"jsonschema agrees invalid/{name} is invalid")
                agree += ok
        from importlib.metadata import version as _v
        lines.append(f"  (jsonschema {_v('jsonschema')} agreed on {agree} schema-layer invalid fixtures)")
    except ImportError:
        lines.append("  (jsonschema not installed: independent comparison skipped)")
    print("\n".join(lines))
    print("validate_manifest self-check:", "FAILED" if bad else "all fixtures behave", f"({bad} failing)" if bad else "")
    return 1 if bad else 0


def main(argv):
    if "--self-check" in argv:
        return self_check()
    root, exports, imports, rest = None, "assets", [], []
    it = iter(argv)
    for a in it:
        if a == "--root":
            root = next(it, None)
        elif a == "--exports":
            exports = next(it, "assets")
        elif a == "--import-path":
            imports.append(next(it, ""))
        elif a.startswith("--"):
            print(__doc__)
            return 2
        else:
            rest.append(a)
    if len(rest) != 1 or (imports and root is None):
        print(__doc__)
        return 2
    try:
        m = json.loads(pathlib.Path(rest[0]).read_text())
    except Exception as e:  # noqa: BLE001
        print(f"{rest[0]}: not readable as JSON: {e}", file=sys.stderr)
        return 2
    errs = validate(m, root, exports, imports)
    if not errs:
        print(f"{rest[0]}: valid (studio-manifest 1)")
        return 0
    for p, msg in errs:
        print(f"{p or '$'}: {msg}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
