"""Bounded protocol and artifact validation shared by the studio runner."""
import hashlib
import json
import os
from pathlib import Path
import re
import stat

VERSION = "studio-runner/0.1.0"
MAX_FRAME = 2 * 1024 * 1024
KEY_PATTERN = re.compile(rb"(?:sk-[A-Za-z0-9_-]{16,}|AIza[A-Za-z0-9_-]{20,}|Bearer\s+[A-Za-z0-9_.-]{16,})")


def encode(value):
    data = json.dumps(value, ensure_ascii=True, allow_nan=False).encode() + b"\n"
    if len(data) > MAX_FRAME:
        raise ValueError("protocol frame too large")
    return data


def read_frame(stream):
    line = stream.readline(MAX_FRAME + 1)
    if not line or len(line) > MAX_FRAME or not line.endswith(b"\n"):
        raise ValueError("missing, truncated or oversized protocol frame")
    return json.loads(line)


def plain_tree(source, destination):
    """Copy ordinary files only; preserve execute bits, never setuid or links."""
    source, destination = Path(source), Path(destination)
    if not source.is_dir() or source.is_symlink():
        raise ValueError("input root must be an ordinary directory")
    destination.mkdir()
    destination.chmod(0o755)
    total = 0

    def copy(directory_fd, target):
        nonlocal total
        for entry in os.scandir(directory_fd):
            fd = os.open(entry.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd)
            try:
                info = os.fstat(fd)
                dest = target / entry.name
                if stat.S_ISDIR(info.st_mode):
                    dest.mkdir()
                    dest.chmod(0o755)
                    copy(fd, dest)
                elif stat.S_ISREG(info.st_mode):
                    if total + info.st_size > 256 * 1024 * 1024:
                        raise ValueError("inputs exceed 256 MiB staging limit")
                    with dest.open("xb") as output:
                        while True:
                            data = os.read(fd, 65536)
                            if not data:
                                break
                            total += len(data)
                            if total > 256 * 1024 * 1024:
                                raise ValueError("inputs exceed 256 MiB staging limit")
                            output.write(data)
                    dest.chmod(0o755 if info.st_mode & 0o111 else 0o644)
                else:
                    raise ValueError("inputs contain a link or special file")
            finally:
                os.close(fd)

    fd = os.open(source, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        copy(fd, destination)
    finally:
        os.close(fd)
    return total


def leak_reason(root, key=b""):
    """Return a generic reason only. Never return the matched secret."""
    path = Path(root) / ".run"
    if not path.is_dir() or path.is_symlink():
        return "missing or unsafe .run directory"
    for folder, dirs, files in os.walk(path, followlinks=False):
        for name in dirs + files:
            file = Path(folder) / name
            if file.is_symlink() or not (file.is_dir() or file.is_file()):
                return "unsafe .run entry"
        for name in files:
            file = Path(folder) / name
            # Scan chunks with overlap; never load a whole transcript into memory.
            overlap = max(4096, len(key))
            tail = b""
            with file.open("rb") as stream:
                while True:
                    chunk = stream.read(65536)
                    if not chunk:
                        break
                    data = tail + chunk
                    if (key and key in data) or KEY_PATTERN.search(data):
                        return "API key exact value or pattern in .run; rotate the key"
                    tail = data[-overlap:]
    return None


def checker_result(value, case_id):
    if not isinstance(value, dict) or set(value) != {"case", "rules"}:
        raise ValueError("checker must print exactly case and rules")
    if value["case"] != case_id or not isinstance(value["rules"], list) or not value["rules"]:
        raise ValueError("checker case mismatch or empty rules")
    ids = set()
    for rule in value["rules"]:
        if not isinstance(rule, dict) or set(rule) != {"id", "pass", "measured", "threshold"}:
            raise ValueError("invalid checker rule fields")
        if not isinstance(rule["id"], str) or not rule["id"] or rule["id"] in ids:
            raise ValueError("invalid or duplicate rule id")
        if type(rule["pass"]) is not bool:
            raise ValueError("rule pass must be boolean")
        ids.add(rule["id"])
    # Also rejects NaN/Infinity from a lenient JSON decoder.
    encode(value)
    return value


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
