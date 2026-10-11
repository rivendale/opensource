#!/usr/bin/env python3
"""Builds the checker library bundle the runner mounts, read-only, when it admits the answers.

    python3 evals/studio/pack_lib.py OUTPUT_DIR

OUTPUT_DIR must not exist. The bundle holds everything a case's `check.py` imports or runs, flat, with a `BUNDLE.json` of file hashes:

    studio_lib.py audio_rules.py music_rules.py video_rules.py proto_rules.py web_rules.py   the rules (those present in this checkout)
    web_probe.mjs net_trap.js                                                               node helpers used by the prototype rules
    validate_manifest.py manifest.schema.json                                               the manifest validator beside the library, where studio_lib looks first

The runner mounts it at a fixed path (say `/opt/studio-lib`), records the hash of `BUNDLE.json` in `result.json`, and sets for the checker: `STUDIO_LIB=/opt/studio-lib`.
The image provides the rest: python3 with numpy, Pillow and fontTools; ffmpeg at `/opt/tools/bin/ffmpeg` (also `STUDIO_FFMPEG`); tesseract; node 22 with puppeteer-core in a fixed
directory (`STUDIO_NODE_MODULES`) and Chrome for Testing 150.0.7871.24 headless shell (`STUDIO_CHROME`). `check.py SCRATCH EXPECTED` needs nothing else.
"""
import hashlib, json, pathlib, shutil, sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
FILES = [HERE / "lib" / n for n in ("studio_lib.py", "audio_rules.py", "music_rules.py", "video_rules.py", "proto_rules.py", "web_rules.py", "web_probe.mjs", "net_trap.js")] + \
        [REPO / "skills/studio/validate_manifest.py", REPO / "skills/studio/manifest.schema.json"]


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    out = pathlib.Path(argv[1])
    out.mkdir(parents=True)
    hashes = {}
    for f in FILES:
        if not f.is_file():
            continue          # a rule file from a later change that this checkout does not have yet
        shutil.copyfile(f, out / f.name)
        hashes[f.name] = hashlib.sha256(f.read_bytes()).hexdigest()
    for needed in ("studio_lib.py", "validate_manifest.py", "manifest.schema.json"):
        if needed not in hashes:
            raise SystemExit("missing " + needed)
    (out / "BUNDLE.json").write_text(json.dumps({"bundle": "studio-lib-1", "files": hashes}, indent=2, sort_keys=True) + "\n")
    print(f"{len(hashes)} files in {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
