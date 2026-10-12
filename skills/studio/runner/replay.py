"""Unprivileged, streaming fixture extraction; never invokes a model or a shell."""
import argparse
import base64
import os
from pathlib import Path
import shutil
import sys
import tarfile

from agent import emit
from common import read_frame


class ReplayStream:
    def __init__(self, limit):
        self.pending = bytearray()
        self.total = 0
        self.limit = limit
        self.ended = False

    def read(self, size):
        while len(self.pending) < size and not self.ended:
            frame = read_frame(sys.stdin.buffer)
            if frame["type"] == "replay-end":
                self.ended = True
                break
            if frame["type"] != "replay-chunk":
                raise ValueError("invalid replay frame")
            data = base64.b64decode(frame["data"], validate=True)
            if len(data) > 65536:
                raise ValueError("replay chunk exceeds limit")
            self.total += len(data)
            if self.total > self.limit + 64 * 1024 * 1024:
                raise ValueError("replay archive exceeds limit")
            self.pending.extend(data)
        data = bytes(self.pending[:size])
        del self.pending[:size]
        return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, required=True)
    args = parser.parse_args()
    if os.getuid() != 1000:
        raise RuntimeError("replay extraction requires agent UID")
    stream = ReplayStream(args.limit)
    total = count = 0
    seen = set()
    with tarfile.open(fileobj=stream, mode="r|") as archive:
        for member in archive:
            path = Path(member.name)
            parts = path.parts
            if not parts and member.isdir():
                continue
            # Only outputs belong in the tar. Inputs/resources/captures come from
            # the regular runner path and must never be replaceable by fixtures.
            if (path.is_absolute() or ".." in parts or not parts
                    or parts[0] in {"inputs", ".run", "brief.md", "skills"}
                    or not (member.isdir() or member.isfile()) or member.size < 0
                    or path in seen):
                raise ValueError("unsafe replay entry")
            seen.add(path)
            count += 1
            total += member.size
            if total > args.limit or count > 100000:
                raise ValueError("replay extraction exceeds limit")
            target = Path("/scratch") / path
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("xb") as output, archive.extractfile(member) as source:
                    shutil.copyfileobj(source, output, 65536)
                target.chmod(0o755 if member.mode & 0o111 else 0o644)
    # Consume the transport terminator even when tar stops at its zero blocks.
    while stream.read(65536):
        pass
    emit("finished", turns=0, usage={}, extraction_uid=os.getuid(), extracted_bytes=total, entries=count)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        emit("failed", reason="replay archive refused")
        sys.exit(1)
