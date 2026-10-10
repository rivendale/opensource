"""Host-side Unix socket relay. No CONNECT, redirects, arbitrary headers or keys in logs."""
from http.server import BaseHTTPRequestHandler
import http.client
import json
import os
import re
import socketserver
import ssl
import threading
import time
from urllib.parse import urlsplit
from common import KEY_PATTERN
from agent import TOOLS

MAX_BODY = 1024 * 1024


class Relay(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True
    block_on_close = False

    def __init__(self, path, routes, keys, model, turn_limit, ca_file=None):
        self.routes = {}
        for route in routes:
            if set(route) != {"name", "host", "path"}:
                raise ValueError("route requires name, host and path")
            host, route_path = route["host"], route["path"]
            if (host, route_path) in self.routes:
                raise ValueError("duplicate proxy route")
            if not re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", host):
                raise ValueError("route must name an exact DNS host")
            if not route_path.startswith("/") or any(c in route_path for c in "?#\r\n"):
                raise ValueError("route must name an exact HTTP path")
            self.routes[(host, route_path)] = route["name"]
        if set(keys) != {host for host, _ in self.routes}:
            raise ValueError("each routed host needs its own explicit key")
        self.keys, self.model, self.turn_limit = keys, model, turn_limit
        defaults = ssl.get_default_verify_paths()
        self.context = ssl.create_default_context(cafile=ca_file or defaults.openssl_cafile,
                                                 capath=None if ca_file else defaults.openssl_capath)
        self.log, self.calls = [], 0
        self.active_requests = 0
        self.incident = False
        self.lock = threading.Lock()
        self.slots = threading.BoundedSemaphore(4)
        super().__init__(str(path), Handler)
        os.chmod(path, 0o666)

    def process_request(self, request, client_address):
        if not self.slots.acquire(blocking=False):
            request.close()
            self.record("unlisted", "OTHER", 503, 0)
            return
        with self.lock:
            self.active_requests += 1
        super().process_request(request, client_address)

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            with self.lock:
                self.active_requests -= 1
            self.slots.release()

    def handle_error(self, request, client_address):
        self.record("unlisted", "OTHER", 400, 0)

    def record(self, host, method, status, size):
        # Host comes from the configured route, never from an untrusted request.
        with self.lock:
            self.log.append({"host": host, "method": method, "status": status,
                             "bytes": size, "time": time.time()})


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def setup(self):
        self.request.settimeout(15)
        super().setup()

    def log_message(self, *args):
        pass

    def send_error(self, code, message=None, explain=None):
        self.server.record("unlisted", "OTHER", code, 0)
        # Do not reflect malformed request text in the response.
        self.reply(code)

    def reply(self, status, body=b'{"error":"relay refused request"}'):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def reject(self, status=403):
        self.server.record("unlisted", self.command if self.command in {"POST", "GET", "CONNECT"} else "OTHER", status, 0)
        self.reply(status)

    def do_POST(self):
        self.connection.settimeout(15)
        try:
            target = urlsplit(self.path)
            host = target.hostname
            if (target.scheme != "https" or target.port not in {None, 443}
                    or target.username or target.password or target.query or target.fragment
                    or (host, target.path) not in self.server.routes):
                return self.reject()
        except ValueError:
            return self.reject(400)
        if self.headers.get("Transfer-Encoding") or len(self.headers.get_all("Content-Length", [])) != 1:
            return self.reject(400)
        try:
            size = int(self.headers["Content-Length"])
            if not 0 < size <= MAX_BODY:
                return self.reject(413)
            payload = self.rfile.read(size)
            request = json.loads(payload)
            if not isinstance(request, dict) or request.get("stream", False):
                return self.reject(400)
            if self.server.routes[(host, target.path)] == "model":
                if (request.get("model") != self.server.model or request.get("tools") != TOOLS
                        or set(request) != {"model", "messages", "tools", "stream", "temperature", "seed"}
                        or request.get("temperature") != 0 or request.get("seed") != 0):
                    return self.reject()
                with self.server.lock:
                    if self.server.calls >= self.server.turn_limit:
                        return self.reject_limit()
                    self.server.calls += 1
            payload = json.dumps(request, allow_nan=False).encode()
        except (ValueError, TypeError, OSError):
            return self.reject(400)
        connection = http.client.HTTPSConnection(host, 443, timeout=60, context=self.server.context)
        try:
            # Do not forward caller headers, cookies, authorization or Host overrides.
            headers = {"Content-Type": "application/json", "Authorization": "Bearer " + self.server.keys[host].decode("ascii")}
            connection.request("POST", target.path, payload, headers)
            response = connection.getresponse()
            body = response.read(MAX_BODY + 1)
            if any(key in body for key in self.server.keys.values()) or KEY_PATTERN.search(body):
                self.server.incident = True
                self.server.record(host, "POST", 502, 0)
                return self.reply(502, b'{"error":"key incident; operator must rotate key"}')
            if len(body) > MAX_BODY or 300 <= response.status < 400:
                self.server.record(host, "POST", 502, 0)
                return self.reply(502)
            self.server.record(host, "POST", response.status, len(body))
            self.reply(response.status, body)
        except (OSError, http.client.HTTPException):
            self.server.record(host, "POST", 502, 0)
            self.reply(502)
        finally:
            connection.close()

    def reject_limit(self):
        # Caller holds the lock; avoid taking it a second time.
        self.server.log.append({"host": "model", "method": "POST", "status": 429,
                                "bytes": 0, "time": time.time()})
        self.reply(429, b'{"error":"turn limit"}')

    do_GET = reject
    do_CONNECT = reject
    do_PUT = reject
    do_DELETE = reject
    do_PATCH = reject
    do_HEAD = reject
    do_OPTIONS = reject
    do_TRACE = reject
