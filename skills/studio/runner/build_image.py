#!/usr/bin/env python3
"""Build the runner layer offline, from an already-loaded immutable tool image."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from common import VERSION, sha256
from run import Runtime


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--tag", default="localhost/studio-runner:0.1.0")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-zA-Z0-9./:_-]+@sha256:[a-f0-9]{64}", args.base):
        parser.error("base must be an immutable image reference")
    directory = Path(__file__).resolve().parent
    sources = {p.name: sha256(p) for p in directory.glob("*.py") if p.name != "run.py"}
    with tempfile.TemporaryDirectory(prefix="studio-image-") as temp:
        root = Path(temp)
        runtime = Runtime(args.store.absolute(), root)
        env = runtime.env
        # Copy only declared source files into the context, never .git, caches or cases.
        context = root / "context"
        context.mkdir()
        for name in [*sources, "Containerfile"]:
            shutil.copyfile(directory / name, context / name)
        subprocess.run(runtime + ["build", "--pull=never", "--network=none", "--build-arg", "BASE_IMAGE=" + args.base,
                                  "--label", "studio.runner=" + VERSION,
                                  "--label", "studio.sources=" + json.dumps(sources, sort_keys=True, separators=(",", ":")),
                                  "--label", "studio.base=" + args.base, "--tag", args.tag,
                                  "--file", str(context / "Containerfile"), str(context)], env=env, check=True)
        # A local tag is a build handle only. Evaluation still requires a manifest digest.
        print("Built local image handle. Resolve its OCI manifest digest before evaluation:", args.tag)


if __name__ == "__main__":
    main()
