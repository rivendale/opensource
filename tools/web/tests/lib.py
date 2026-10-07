"""Helpers for the independent denying-direction tests of tools/web/bin/browse (black box: command line in, behaviour out).

Everything the tests claim is observed from outside: a listener that logs every connection (the proof is ITS log, not the
exit code), a control that shows the same listener does log a hit from curl, a sampler of /proc and `ss` that sees
Chrome's command line and its sockets while it runs, and before/after snapshots of the places a browser leaves files."""
import base64, os, pathlib, re, shutil, signal, socket, subprocess, tempfile, threading, time, urllib.parse

HTTPBIN = "https://httpbin.org"
MARKER = "LISTENER-MARKER-7f3a9c"          # the body the listener answers with: if it ever shows in output, a request got through


class Listener:
    """TCP listener on '::' (dual stack: it also receives 127.0.0.1, 127.0.0.2, 0.0.0.0, ::1, the LAN and tailnet addresses).
    Logs the DESTINATION address each connection was made to, the peer, and the first bytes. Answers a tiny HTTP 200 with MARKER."""

    def __init__(self, port=0):
        self.s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        self.s.bind(("::", port))
        self.s.listen(64)
        self.port = self.s.getsockname()[1]
        self.hits = []
        self.lock = threading.Lock()
        self.alive = True
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while self.alive:
            try:
                c, peer = self.s.accept()
            except OSError:
                return
            threading.Thread(target=self._one, args=(c, peer), daemon=True).start()

    def _one(self, c, peer):
        try:
            dst = c.getsockname()[0]
            c.settimeout(0.5)
            try:
                first = c.recv(400)
            except OSError:
                first = b""
            with self.lock:
                self.hits.append({"t": time.time(), "dst": dst, "peer": peer[0], "first": first.decode("latin1")[:160]})
            body = MARKER.encode()
            if first.startswith(b"GET") or first.startswith(b"POST"):
                c.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: %d\r\nConnection: close\r\n\r\n" % len(body) + body)
        except OSError:
            pass
        finally:
            try:
                c.close()
            except OSError:
                pass

    def clear(self):
        with self.lock:
            self.hits.clear()

    def count(self):
        with self.lock:
            return len(self.hits)

    def summary(self):
        with self.lock:
            return [(h["dst"], h["first"].split("\r\n")[0][:60]) for h in self.hits]

    def close(self):
        self.alive = False
        try:
            self.s.close()
        except OSError:
            pass


class UdpListener:
    def __init__(self):
        self.s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        self.s.bind(("::", 0))
        self.port = self.s.getsockname()[1]
        self.hits = []
        self.alive = True
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while self.alive:
            try:
                d, peer = self.s.recvfrom(2048)
                self.hits.append((peer[0], len(d)))
            except OSError:
                return

    def close(self):
        self.alive = False
        self.s.close()


def curl_hit(url, family_flag=None):
    """The positive control: the same listener MUST log this."""
    cmd = ["curl", "-s", "-m", "8", "-g"] + ([family_flag] if family_flag else []) + [url]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout


def local_addresses():
    """LAN and tailnet addresses of this machine (what a private-range fixture can really listen on)."""
    out = subprocess.run(["ip", "-o", "-4", "addr", "show"], capture_output=True, text=True).stdout
    addrs = re.findall(r"inet (\d+\.\d+\.\d+\.\d+)/", out)
    return [a for a in addrs if not a.startswith("127.")]


def pub_html(html):
    """A PUBLIC page with arbitrary HTML: httpbin decodes a base64 path segment and serves it as text/html."""
    b = base64.urlsafe_b64encode(html.encode()).decode()
    assert len(b) < 3800, "html too long for a request line"
    return f"{HTTPBIN}/base64/{b}"


def redirect_to(target, status=302):
    return f"{HTTPBIN}/redirect-to?url={urllib.parse.quote(target, safe='')}&status_code={status}"


FILLER = ("This page carries enough ordinary visible text to be a normal page and not a block page. " * 4)


def page(body, head=""):
    return f"<!doctype html><html><head><meta charset=utf-8><title>vector</title>{head}</head><body><p id=o>start</p><p>{FILLER}</p>{body}</body></html>"


class Proc:
    """One run of tools/web/bin/browse with a watcher sampling /proc and `ss` while it runs."""

    def __init__(self, build, args, timeout=90, sig_after=None, sig=signal.SIGINT, env=None):
        self.build, self.args, self.timeout, self.sig_after, self.sig = build, list(args), timeout, sig_after, sig
        self.extra_env = env or {}
        self.cmdlines, self.listen_ports, self.conns, self.chrome_pids = [], set(), [], set()
        self.rc = None
        self.out = self.err = ""
        self.secs = 0.0

    def run(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="bt-"))
        (self.tmp / "tmp").mkdir()
        (self.tmp / "cwd").mkdir()
        env = dict(os.environ, TMPDIR=str(self.tmp / "tmp"), **self.extra_env)
        t0 = time.time()
        self.p = subprocess.Popen([self.build] + self.args, cwd=self.tmp / "cwd", env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
        self.stop = False
        w = threading.Thread(target=self._watch, daemon=True)
        w.start()
        if self.sig_after is not None:
            time.sleep(self.sig_after)
            try:
                os.killpg(self.p.pid, self.sig)
            except ProcessLookupError:
                pass
        try:
            self.out, self.err = self.p.communicate(timeout=self.timeout)
        except subprocess.TimeoutExpired:
            os.killpg(self.p.pid, signal.SIGKILL)
            self.out, self.err = self.p.communicate()
            self.timed_out = True
        self.rc = self.p.returncode
        self.secs = time.time() - t0
        self.stop = True
        w.join(timeout=2)
        return self

    def _descendants(self):
        kids = {}
        for pid in os.listdir("/proc"):
            if pid.isdigit():
                try:
                    st = open(f"/proc/{pid}/stat").read()
                    ppid = int(st.rsplit(")", 1)[1].split()[1])
                    kids.setdefault(ppid, []).append(int(pid))
                except (OSError, ValueError, IndexError):
                    pass
        out, todo = set(), [self.p.pid]
        while todo:
            x = todo.pop()
            for k in kids.get(x, []):
                if k not in out:
                    out.add(k)
                    todo.append(k)
        return out

    def _watch(self):
        seen = set()
        while not self.stop:
            try:
                ds = self._descendants() | {self.p.pid}
                for pid in ds:
                    try:
                        cl = open(f"/proc/{pid}/cmdline", "rb").read().replace(b"\0", b" ").decode("utf-8", "replace").strip()
                    except OSError:
                        continue
                    is_chrome = pid != self.p.pid and ("chrom" in cl.split(" ")[0] or "headless_shell" in cl.split(" ")[0])
                    if is_chrome and "--type=" not in cl and cl not in seen:
                        seen.add(cl)
                        self.cmdlines.append(cl)
                    if is_chrome:
                        self.chrome_pids.add(pid)
                ss = subprocess.run(["ss", "-tunapH"], capture_output=True, text=True).stdout
                for ln in ss.splitlines():
                    m = re.search(r"pid=(\d+)", ln)
                    if not m or int(m.group(1)) not in ds:
                        continue
                    parts = ln.split()
                    if parts[0] == "tcp" and parts[1] == "LISTEN":
                        pm = re.search(r":(\d+)$", parts[4])
                        if pm:
                            self.listen_ports.add(int(pm.group(1)))
                    elif parts[0] in ("tcp", "udp") and int(m.group(1)) in self.chrome_pids:
                        self.conns.append((parts[0], parts[1], parts[4], parts[5]))
            except Exception:
                pass
            time.sleep(0.12)

    def listening_now(self, port):
        ss = subprocess.run(["ss", "-tlnH"], capture_output=True, text=True).stdout
        return any(re.search(r":%d\s" % port, ln) for ln in ss.splitlines())

    def chrome_left(self):
        left = []
        for pid in self.chrome_pids:
            if os.path.exists(f"/proc/{pid}"):
                try:
                    st = open(f"/proc/{pid}/stat").read().rsplit(")", 1)[1].split()[0]
                except OSError:
                    continue
                if st != "Z":
                    left.append(pid)
        return left

    def cleanup(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


def snapshot_places(extra=()):
    """Where a browser leaves files: /tmp, the real HOME's dot-directories, and any extra dirs. Entries only (path + type)."""
    roots = [pathlib.Path("/tmp"), pathlib.Path.home() / ".config", pathlib.Path.home() / ".cache", pathlib.Path.home() / ".local/share", pathlib.Path.home() / "Downloads"] + [pathlib.Path(x) for x in extra]
    seen = set()
    for r in roots:
        if not r.exists():
            continue
        for dp, dn, fn in os.walk(r):
            depth = len(pathlib.Path(dp).relative_to(r).parts)
            if "ms-playwright" in dp or "browse-venv" in dp:
                dn[:] = []
                continue
            for n in dn + fn:
                seen.add(str(pathlib.Path(dp) / n))
            if depth >= 3:
                dn[:] = []
    return seen
