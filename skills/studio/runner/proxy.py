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
from cache_api import native_request, native_response

MAX_BODY = 1024 * 1024


def attempted_host(path):
    try:
        host = urlsplit(path if "://" in path else "//" + path).hostname or ""
    except ValueError:
        return "unlisted"
    if len(host) > 253 or not all(re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
                                 for label in host.lower().split(".")):
        return "unlisted"
    return host.lower()


class ProviderError(ValueError):
    """Bounded provider error fields; never expose the response through str(error)."""
    def __init__(self, status, error_type, message):
        self.provider_error = {'http_status': status, 'type': error_type[:128], 'message': message[:1024]}
        super().__init__('reviewer model route failed')


class Relay(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True
    block_on_close = False

    def __init__(self, path, routes, keys, model, turn_limit, ca_file=None, cache_prefix=None, review_temperature=0, review_max_tokens=256):
        self.routes = {}
        self.budgets = {}
        for route in routes:
            fields = {"name", "host", "path"}
            if route.get("name") != "model":
                fields |= {"max_calls", "max_bytes"}
            if set(route) != fields:
                raise ValueError("paid route requires explicit call and byte caps")
            host, route_path = route["host"], route["path"]
            if (host, route_path) in self.routes:
                raise ValueError("duplicate proxy route")
            if not re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", host):
                raise ValueError("route must name an exact DNS host")
            if not route_path.startswith("/") or any(c in route_path for c in "?#\r\n"):
                raise ValueError("route must name an exact HTTP path")
            self.routes[(host, route_path)] = route["name"]
            if route["name"] != "model":
                if any(type(route[k]) is not int or route[k] <= 0 for k in ("max_calls", "max_bytes")):
                    raise ValueError("paid caps must be positive integers")
                self.budgets[(host, route_path)] = {"max_calls": route["max_calls"],
                                                   "max_bytes": route["max_bytes"], "calls": 0, "bytes": 0}
        if set(keys) != {host for host, _ in self.routes}:
            raise ValueError("each routed host needs its own explicit key")
        if review_temperature is not None and (type(review_temperature) is not int or review_temperature != 0):
            raise ValueError('reviewer temperature must be zero or explicitly omitted')
        if type(review_max_tokens) is not int or review_max_tokens not in (256, 1024):
            raise ValueError('invalid reviewer token cap')
        if review_max_tokens == 1024 and (model != 'claude-opus-5-5' or
                self.routes != {('api.anthropic.com','/v1/chat/completions'): 'model'} or
                cache_prefix is not None or review_temperature is not None):
            raise ValueError('extended reviewer cap requires the registered Opus relay')
        self.review_max_tokens = review_max_tokens
        self.review_temperature = review_temperature
        self.cache_prefix = cache_prefix
        if cache_prefix is not None and [route for route,name in self.routes.items() if name=='model'] != [('api.anthropic.com','/v1/messages')]:
            raise ValueError('prompt cache requires the exact native route')
        self.keys, self.model, self.turn_limit = keys, model, turn_limit
        defaults = ssl.get_default_verify_paths()
        self.context = ssl.create_default_context(cafile=ca_file or defaults.openssl_cafile,
                                                 capath=None if ca_file else defaults.openssl_capath)
        self.log, self.calls = [], 0
        self.active_requests = 0
        self.incident = False
        self.limit_hit = False
        self.lock = threading.Lock()
        self.slots = threading.BoundedSemaphore(4)
        super().__init__(str(path), Handler)
        os.chmod(path, 0o666)

    def output_has_key(self, body):
        """Existing exact-key/pattern policy, reusable before writing decoded output."""
        return any(key in body for key in self.keys.values()) or bool(KEY_PATTERN.search(body))

    def review_request(self, messages, max_tokens, timeout=60):
        """Host-owned tool-free reviewer request; unreachable from HTTP callers."""
        model_routes = [route for route, name in self.routes.items() if name == 'model']
        if len(model_routes) != 1 or type(max_tokens) is not int or not 1 <= max_tokens <= getattr(self, 'review_max_tokens', 256):
            raise ValueError('invalid trusted reviewer transport')
        host, path = model_routes[0]
        request = {'model': self.model, 'messages': messages, 'stream': False,
                   'temperature': 0, 'seed': 0, 'max_tokens': max_tokens}
        if getattr(self, 'review_temperature', 0) is None:
            del request['temperature']
        if getattr(self, 'cache_prefix', None) is not None:
            request = native_request(request, {'system': messages[0]['content']}, max_tokens)
        payload = json.dumps(request, allow_nan=False).encode()
        if len(payload) > MAX_BODY:
            raise ValueError('review request exceeds relay body limit')
        with self.lock:
            if self.incident or self.calls >= self.turn_limit:
                self.limit_hit = True
                raise ValueError('shared model request limit')
            self.calls += 1
        connection = http.client.HTTPSConnection(host, 443, timeout=timeout, context=self.context)
        try:
            headers = self.model_headers(host)
            connection.request('POST', path, payload, headers)
            response = connection.getresponse()
            self.last_http_status = response.status
            body = response.read(MAX_BODY + 1)
            if self.output_has_key(body):
                self.incident = True
                self.record(host, 'POST', 502, 0)
                raise ValueError('key incident in reviewer response')
            self.record(host, 'POST', response.status, len(body))
            if len(body) > MAX_BODY:
                raise ProviderError(response.status, 'BodyLimit', 'Provider response exceeded the relay limit')
            try:
                value = json.loads(body)
            except (ValueError, UnicodeError):
                if response.status != 200:
                    raise ProviderError(response.status, 'UnstructuredProviderError', 'Provider returned a non-JSON error body') from None
                raise
            has_error = isinstance(value, dict) and isinstance(value.get('error'), dict)
            if (response.status != 200 or has_error) and self.output_has_key(json.dumps(value, ensure_ascii=False).encode()):
                self.incident = True
                raise ValueError('key incident in decoded reviewer response')
            if response.status != 200 or has_error:
                error = value.get('error') if isinstance(value, dict) else None
                error_type = error.get('type') if isinstance(error, dict) else None
                message = error.get('message') if isinstance(error, dict) else None
                raise ProviderError(response.status,
                                    error_type if isinstance(error_type, str) else 'ProviderHTTPError',
                                    message if isinstance(message, str) else 'Provider error object missing type/message')
            return native_response(value, self.model) if getattr(self, 'cache_prefix', None) is not None else value
        finally:
            connection.close()

    def model_headers(self, host):
        if getattr(self, 'cache_prefix', None) is not None:
            return {'Content-Type': 'application/json', 'x-api-key': self.keys[host].decode('ascii'),
                    'anthropic-version': '2023-06-01'}
        return {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + self.keys[host].decode('ascii')}

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
        # Refused hosts are validated DNS names, never arbitrary request text.
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
        self.server.record(attempted_host(self.path), self.command if self.command in {"POST", "GET", "CONNECT"} else "OTHER", status, 0)
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
            if self.server.cache_prefix is not None and self.server.routes[(host,target.path)] == 'model':
                request = native_request(request, self.server.cache_prefix)
            payload = json.dumps(request, allow_nan=False).encode()
            # Native conversion can grow the body. OFF keeps the prior relay
            # behavior, including UTF-8 that expands under JSON normalization.
            if (self.server.cache_prefix is not None
                    and self.server.routes[(host, target.path)] == 'model'
                    and len(payload) > MAX_BODY):
                return self.reject(413)
        except (ValueError, TypeError, OSError):
            return self.reject(400)
        budget = self.server.budgets.get((host, target.path))
        if budget:
            with self.server.lock:
                if budget["calls"] >= budget["max_calls"] or budget["bytes"] + len(payload) > budget["max_bytes"]:
                    self.server.limit_hit = True
                    exhausted = True
                else:
                    budget["calls"] += 1
                    budget["bytes"] += len(payload)
                    exhausted = False
            if exhausted:
                return self.reject(429)
        connection = http.client.HTTPSConnection(host, 443, timeout=60, context=self.server.context)
        try:
            # Do not forward caller headers, cookies, authorization or Host overrides.
            headers = self.server.model_headers(host) if self.server.routes[(host,target.path)] == "model" else {"Content-Type":"application/json","Authorization":"Bearer " + self.server.keys[host].decode("ascii")}
            connection.request("POST", target.path, payload, headers)
            response = connection.getresponse()
            body = response.read(MAX_BODY + 1)
            key_incident = self.server.output_has_key(body)
            if budget:
                with self.server.lock:
                    budget["bytes"] += len(body)
                    exhausted = budget["bytes"] > budget["max_bytes"]
                    self.server.limit_hit |= exhausted
                if exhausted and not key_incident:
                    return self.reject(429)
            if key_incident:
                self.server.incident = True
                self.server.record(host, "POST", 502, 0)
                return self.reply(502, b'{"error":"key incident; operator must rotate key"}')
            if len(body) > MAX_BODY or 300 <= response.status < 400:
                self.server.record(host, "POST", 502, 0)
                return self.reply(502)
            self.server.record(host, "POST", response.status, len(body))
            if self.server.cache_prefix is not None and self.server.routes[(host,target.path)] == 'model' and response.status == 200:
                body = json.dumps(native_response(json.loads(body), self.server.model), allow_nan=False).encode()
                if len(body) > MAX_BODY:
                    return self.reply(502)
            self.reply(response.status, body)
        except (OSError, http.client.HTTPException, ValueError, TypeError, KeyError):
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
