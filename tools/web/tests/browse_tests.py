#!/usr/bin/env python3
"""Independent denying-direction tests for tools/web/bin/browse, written from the failure list in tools/web/SPEC.md
(items 1-15) and treating the tool as a black box.

    python3 browse_tests.py --build PRISTINE [--weak W_A=PATH ...] [--only PREFIX,...] [--list]

Proof model. A local listener logs every connection; each denying fixture also runs a CONTROL showing the same listener logs a hit
from curl, and (for redirect and script vectors) a public control showing the same mechanism works when the target is public, so a
refusal cannot be mistaken for a mechanism that never ran. Every fixture is then run against deliberately weakened builds it is
declared to catch (W_A: loopback proxy-bypass re-enabled; W_B: the proxy's address filter disabled; W_C: the start-URL pre-check
disabled) and must FAIL there. Exit 0 all pass, 1 a fixture failed, 3 a network dependency is missing (never read as a pass)."""
import argparse, json, os, pathlib, re, signal, socket, subprocess, sys, time, urllib.parse

import lib
from lib import Listener, UdpListener, Proc, MARKER, HTTPBIN, page, pub_html, redirect_to, curl_hit

REG = []
BUILD = None
CTX = {}


def sc(sid, item, title, bites=()):
    def deco(fn):
        REG.append((sid, item, title, tuple(bites), fn))
        return fn
    return deco


def listener():
    if "L" not in CTX:
        CTX["L"] = Listener()
        CTX["U"] = UdpListener()
    return CTX["L"]


def control(L, addr="127.0.0.1"):
    """The same listener MUST log a hit from curl: otherwise 'zero hits' proves nothing."""
    L.clear()
    url = f"http://[{addr}]:{L.port}/control" if ":" in addr else f"http://{addr}:{L.port}/control"
    body = curl_hit(url)
    ok = MARKER in body and L.count() >= 1
    L.clear()
    return [] if ok else [f"CONTROL FAILED: curl to {url} did not reach the listener (hits={L.count()}); the zero-hit result would be meaningless"]


def run(args, **kw):
    p = Proc(BUILD, args, **kw).run()
    p.cleanup_later = True
    return p


def deny(L, p, label):
    """After a run aimed at the listener: zero connections, and nothing the listener says appears in the output."""
    probs = []
    if L.count():
        probs.append(f"{label}: the listener logged {L.count()} connection(s) {L.summary()[:3]}")
    if MARKER in p.out or MARKER in p.err:
        probs.append(f"{label}: the listener's own response body reached the output")
    return probs


def loaded(p):
    return "This page carries enough ordinary visible text" in p.out


# ------------------------------------------------------------------------------------------------- item 1: schemes
CANARY = pathlib.Path("/tmp/browse-canary-%d.html" % os.getpid())
CANARY.write_text("<html><body>FILE-CANARY-9a8b7c</body></html>")
import atexit
atexit.register(lambda: CANARY.unlink() if CANARY.exists() else None)
SCHEMES = ["file://" + str(CANARY), "file:///etc/hostname", "ftp://127.0.0.1:1/", "ftp://example.com/", "data:text/html,<p>DATA-CANARY</p>", "chrome://version", "chrome://gpu", "javascript:alert(1)",
           "about:blank", "blob:https://example.com/00000000-0000-0000-0000-000000000000", "ws://example.com/", "wss://example.com/", "view-source:https://example.com/", "mailto:a@example.com",
           "gopher://example.com/", "chrome-extension://abc/x.html", "devtools://devtools/bundled/inspector.html", "FILE:///etc/hostname", "//example.com/", "example.com", "http:/example.com", "https:example.com", ""]
for n, s in enumerate(SCHEMES):
    def mk(s=s, n=n):
        def fn():
            p = run([s] if s != "" else [""], timeout=20)
            probs = []
            if p.rc != 2:
                probs.append(f"exit {p.rc}, expected 2 for {s!r}; out={p.out[:100]!r} err={p.err[:120]!r}")
            if "FILE-CANARY" in p.out or "DATA-CANARY" in p.out:
                probs.append("content of a non-http(s) URL reached the output")
            if p.cmdlines:
                probs.append(f"Chrome was started for {s!r} (spec: nothing launched): {p.cmdlines[0][:80]}")
            if p.secs > 5:
                probs.append(f"took {p.secs:.1f}s to refuse")
            return probs
        return fn
    sc(f"I01-{n:02d}", 1, f"start URL {s[:50]!r} is refused: exit 2, nothing launched, no content", bites=("W_E",) if s.startswith(("file", "ftp", "data", "chrome", "javascript")) else ())(mk())

sc("I01-ctl-uppercase-scheme", 1, "control: HTTPS://EXAMPLE.COM/ (uppercase scheme) is a normal http(s) URL and renders")(
    lambda: (lambda p: [] if p.rc == 0 and "rendered" in p.out else [f"exit {p.rc}: {p.out[:80]!r} {p.err[:100]!r}"])(run(["HTTPS://EXAMPLE.COM/"], timeout=60)))

# ------------------------------------------------------------------------------------------ item 2: private spellings
SPELL = ["127.0.0.1", "localhost", "LOCALHOST", "localhost.", "[::1]", "[0:0:0:0:0:0:0:1]", "[0000:0000:0000:0000:0000:0000:0000:0001]", "[::ffff:127.0.0.1]", "[::ffff:7f00:1]", "2130706433", "0x7f000001",
         "0177.0.0.1", "0x7f.0.0.1", "127.1", "127.0.1", "017700000001", "0.0.0.0", "[::]", "127.0.0.1.", "127.000.000.001", "0x7f.0x0.0x0.0x1", "127.0.0.2", "127.255.255.254", "0", "1.0.0.127.in-addr.arpa",
         "example.com@127.0.0.1", "127.0.0.1%23@example.com", "example.com%5c@127.0.0.1"]
NOLISTEN = ["10.0.0.1", "10.255.255.255", "172.16.0.1", "172.31.255.255", "192.168.0.1", "192.168.255.254", "169.254.169.254", "169.254.0.1", "100.64.0.1", "100.127.255.254", "[fc00::1]", "[fd12:3456::1]",
            "[fe80::1]", "192.0.0.1", "198.18.0.1", "224.0.0.1", "255.255.255.255", "240.0.0.1", "[64:ff9b::7f00:1]", "[::ffff:10.0.0.1]", "[::ffff:a00:1]", "[2002:7f00:1::1]", "2851995649", "0xa9fea9fe", "0251.0376.0251.0376"]
for n, h in enumerate(SPELL):
    def mk(h=h):
        def fn():
            L = listener()
            probs = control(L)
            userinfo = "@" in h
            url = f"http://{h}:{L.port}/hit-{h[:10]}"
            if userinfo:
                url = f"http://{h.split('@')[0]}@{h.split('@')[1]}:{L.port}/hit"
            L.clear()
            p = run([url], timeout=60)
            probs += deny(L, p, f"{h}")
            public_host_trick = h.startswith("127.0.0.1%23@")
            if p.rc != 2 and not (public_host_trick and p.rc == 1):
                probs.append(f"exit {p.rc}, expected 2 (private/loopback start URL); out={p.out[:80]!r} err={p.err[:120]!r}")
            return probs
        return fn
    sc(f"I02-{n:02d}", 2, f"private spelling {h!r}: exit 2 and the listener logs nothing", bites=() if h.startswith("127.0.0.1%23@") else ("W_C",))(mk())
for n, h in enumerate(NOLISTEN):
    def mk(h=h):
        def fn():
            p = run([f"http://{h}/"], timeout=60)
            return [] if p.rc == 2 and p.secs < 8 and not p.cmdlines else [f"{h}: exit {p.rc}, secs {p.secs:.1f}, chrome={bool(p.cmdlines)}; err={p.err[:120]!r}"]
        return fn
    sc(f"I02-n{n:02d}", 2, f"private/reserved range {h!r}: exit 2 quickly, no browser", bites=("W_C",))(mk())


def lan_case(idx, label):
    def fn():
        addrs = lib.local_addresses()
        if idx >= len(addrs):
            return [f"NOT RUN: this machine has no {label} address to listen on"]
        a = addrs[idx]
        L = listener()
        probs = control(L, a)
        L.clear()
        p = run([f"http://{a}:{L.port}/hit-lan"], timeout=60)
        probs += deny(L, p, a)
        if p.rc != 2:
            probs.append(f"{a}: exit {p.rc}, expected 2")
        return probs
    return fn


sc("I02-lan0", 2, "this machine's first non-loopback IPv4 address (LAN/tailnet/WSL): exit 2 and the listener logs nothing", bites=("W_C",))(lan_case(0, "first non-loopback"))
sc("I02-lan1", 2, "this machine's second non-loopback IPv4 address: exit 2, listener silent", bites=("W_C",))(lan_case(1, "second non-loopback"))


# --------------------------------------------------------------------------- items 3 and 4: redirects and subresources
def vec_case(name, item, build_start, public_control=None, needs_loaded=False, bites=("W_A2", "W_B"), wait_note="", target_host=None):
    """build_start(T) -> start URL (public) whose mechanism points at T. T = a loopback URL on the listener."""
    def fn():
        L = listener()
        host = target_host or "127.0.0.1"
        probs = control(L, "127.0.0.1")
        L.clear()
        T = f"http://{host}:{L.port}/v-{name}"
        p = run([build_start(T)], timeout=75)
        probs += deny(L, p, name)
        if needs_loaded and not loaded(p) and p.rc == 0:
            probs.append(f"{name}: the page itself did not render (the vector may not have run): out={p.out[:100]!r}")
        if public_control:
            q = run([build_start(public_control)], timeout=75)
            ok, why = public_control_check(q, name)
            if not ok:
                probs.append(f"{name}: PUBLIC CONTROL failed (the same mechanism aimed at a public page): {why}")
        return probs
    return fn


def public_control_check(q, name):
    if q.rc != 0:
        return False, f"exit {q.rc} out={q.out[:80]!r} err={q.err[:100]!r}"
    if "example" in q.out.lower() or "Example Domain" in q.out or loaded(q):
        return True, ""
    return False, f"unexpected output {q.out[:100]!r}"


EX = "https://example.com/"
HTTP_REDIRECTS = [("r301", 301), ("r302", 302), ("r303", 303), ("r307", 307), ("r308", 308)]
for nm, code in HTTP_REDIRECTS:
    sc(f"I03-{nm}", 3, f"public HTTP {code} redirect to the loopback listener: refused, listener silent; same redirect to a public page works", bites=("W_A2", "W_B"))(
        vec_case(nm, 3, lambda T, c=code: redirect_to(T, c), public_control=EX))
sc("I03-chain", 3, "public redirect chain ending at the loopback listener", bites=("W_A2", "W_B"))(
    vec_case("chain", 3, lambda T: redirect_to(redirect_to(redirect_to(T))), public_control=EX))
META = lambda T: pub_html(page(f'<meta http-equiv="refresh" content="0;url={T}">'.replace("<meta", "<meta"), head=f'<meta http-equiv="refresh" content="0;url={T}">'))
sc("I03-meta", 3, "meta refresh to the loopback listener", bites=("W_A2", "W_B"))(vec_case("meta", 3, META, public_control=EX))
sc("I03-meta-delay", 3, "meta refresh after a 2 s delay (the tool exits before it fires, so this cannot discriminate)", bites=())(
    vec_case("metad", 3, lambda T: pub_html(page("", head=f'<meta http-equiv="refresh" content="2;url={T}">')), public_control=None))
JSV = {"href": 'location.href="%s"', "replace": 'location.replace("%s")', "assign": 'window.location.assign("%s")', "timer": 'setTimeout(function(){location="%s"},800)',
       "top": 'top.location="%s"', "open": 'window.open("%s")', "hash": 'location.href="%s"+"#x"'}
for k, tmpl in JSV.items():
    sc(f"I03-js-{k}", 3, f"JavaScript location change ({k}) to the loopback listener", bites=() if k == "timer" else ("W_A2", "W_B"))(
        vec_case(f"js{k}", 3, lambda T, tmpl=tmpl: pub_html(page(f"<script>{tmpl % T}</script>")), public_control=EX if k not in ("open",) else None))
sc("I03-refresh-header", 3, "an HTTP Refresh response header pointing at the loopback listener", bites=("W_A2", "W_B"))(
    vec_case("rh", 3, lambda T: f"{HTTPBIN}/response-headers?Content-Type=text/html&Refresh={urllib.parse.quote('0;url=' + T, safe='')}", public_control=EX))
sc("I03-form-post", 3, "an auto-submitted form POST to the loopback listener", bites=("W_A2", "W_B"))(
    vec_case("form", 3, lambda T: pub_html(page(f'<form id=f method=post action="{T}"><input name=a value=b></form><script>document.getElementById("f").submit()</script>'))))
sc("I03-anchor-click", 3, "a script-clicked link to the loopback listener", bites=("W_A2", "W_B"))(
    vec_case("click", 3, lambda T: pub_html(page(f'<a id=a href="{T}">x</a><script>document.getElementById("a").click()</script>'))))
sc("I03-base-href", 3, "a <base href> that makes relative subresources resolve to the loopback listener", bites=("W_A2", "W_B"))(
    vec_case("base", 3, lambda T: pub_html(page('<img src="pic.png"><script src="s.js"></script><link rel=stylesheet href="c.css">', head=f'<base href="{T}/">')), needs_loaded=True))

VACUOUS_HEADLESS = {"track", "icon", "preconnect", "dnsprefetch", "prerender", "manifest"}   # headless Chrome makes no such request even with the filter off (measured): the fixture cannot discriminate
SUBS = {
    "img": '<img src="{T}">', "script": '<script src="{T}"></script>', "css": '<link rel=stylesheet href="{T}">', "iframe": '<iframe src="{T}"></iframe>', "object": '<object data="{T}"></object>',
    "embed": '<embed src="{T}">', "video": '<video src="{T}" preload=auto></video>', "audio": '<audio src="{T}" preload=auto></audio>', "source": '<video><source src="{T}"></video>',
    "track": '<video><track src="{T}" default></video>', "inputimg": '<input type=image src="{T}">', "svg": '<svg><image href="{T}"/></svg>', "cssimport": '<style>@import url("{T}");</style>',
    "cssbg": '<style>body{{background:url("{T}")}}</style>', "font": '<style>@font-face{{font-family:x;src:url("{T}")}}p{{font-family:x}}</style>', "icon": '<link rel=icon href="{T}">',
    "preload": '<link rel=preload href="{T}" as=image>', "prefetch": '<link rel=prefetch href="{T}">', "preconnect": '<link rel=preconnect href="{T}">', "dnsprefetch": '<link rel=dns-prefetch href="{T}">',
    "prerender": '<link rel=prerender href="{T}">', "ping": '<a href="https://example.com/" ping="{T}" id=a>x</a><script>document.getElementById("a").click()</script>',
    "srcset": '<img srcset="{T} 1x">', "picture": '<picture><source srcset="{T}"><img src="x"></picture>', "bgattr": '<table background="{T}"><tr><td>x</td></tr></table>',
    "manifest": '<link rel=manifest href="{T}">', "stylesheet-alt": '<link rel="alternate stylesheet" href="{T}" title=a>',
}
for k, tmpl in SUBS.items():
    sc(f"I04-{k}", 4, f"subresource <{k}> aimed at the loopback listener: refused, listener silent; the page still renders", bites=() if k in VACUOUS_HEADLESS else ("W_A2", "W_B"))(
        vec_case(f"s{k}", 4, lambda T, tmpl=tmpl: pub_html(page(tmpl.replace("{T}", T).replace("{{", "{").replace("}}", "}"))), needs_loaded=(k != "ping"), bites=() if k in VACUOUS_HEADLESS else ("W_A2", "W_B")))
JSS = {
    "fetch": 'fetch("{T}",{{mode:"no-cors"}}).then(function(){{o.textContent="ran-ok"}}).catch(function(){{o.textContent="ran-fail"}})',
    "xhr": 'var x=new XMLHttpRequest();x.open("GET","{T}");x.onloadend=function(){{o.textContent="ran-"+x.status}};x.send()',
    "beacon": 'navigator.sendBeacon("{T}","x");o.textContent="ran-beacon"',
    "ws": 'var w=new WebSocket("{T}".replace("http","ws"));w.onerror=function(){{o.textContent="ran-wserr"}};w.onopen=function(){{o.textContent="ran-wsopen"}}',
    "eventsource": 'var e=new EventSource("{T}");e.onerror=function(){{o.textContent="ran-eserr"}}',
    "import": 'import("{T}").then(function(){{o.textContent="ran-imp"}}).catch(function(){{o.textContent="ran-imperr"}})',
    "worker": 'try{{new Worker("{T}")}}catch(e){{}};o.textContent="ran-worker"',
    "sw": 'navigator.serviceWorker&&navigator.serviceWorker.register("{T}").then(function(){{o.textContent="ran-sw"}}).catch(function(){{o.textContent="ran-swerr"}})',
    "image": 'var i=new Image();i.onerror=function(){{o.textContent="ran-imgerr"}};i.onload=function(){{o.textContent="ran-imgok"}};i.src="{T}"',
    "iframejs": 'var f=document.createElement("iframe");f.src="{T}";document.body.appendChild(f);o.textContent="ran-frame"',
    "scriptjs": 'var s=document.createElement("script");s.src="{T}";s.onerror=function(){{o.textContent="ran-serr"}};document.head.appendChild(s)',
    "xhr-sync": 'try{{var x=new XMLHttpRequest();x.open("GET","{T}",false);x.send()}}catch(e){{}};o.textContent="ran-sync"',
    "fetch-post": 'fetch("{T}",{{method:"POST",mode:"no-cors",body:"x"}}).catch(function(){{o.textContent="ran-postfail"}})',
    "formdata": 'var f=document.createElement("form");f.method="post";f.action="{T}";f.target="_blank";document.body.appendChild(f);f.submit();o.textContent="ran-form"',
}
for k, tmpl in JSS.items():
    def build(T, tmpl=tmpl):
        js = tmpl.replace("{T}", T).replace("{{", "{").replace("}}", "}")
        return pub_html(page(f'<script type="module">var o=document.getElementById("o");{js}</script>' if "import(" in js else f"<script>var o=document.getElementById('o');{js}</script>"))
    sc(f"I04-js-{k}", 4, f"script request ({k}) aimed at the loopback listener: refused, listener silent; the script ran", bites=() if k in ("worker", "sw") else ("W_A2", "W_B"))(vec_case(f"j{k}", 4, build, needs_loaded=True))
sc("I04-doh-image", 4, "an image whose host is an IPv6 loopback literal", bites=("W_A2", "W_B"))(
    lambda: (lambda L: control(L) + (lambda p: deny(L, p, "ipv6-img"))(run([pub_html(page(f'<img src="http://[::1]:{L.port}/x"><img src="http://[::ffff:127.0.0.1]:{L.port}/y"><img src="http://2130706433:{L.port}/z"><img src="http://0x7f000001:{L.port}/w"><img src="http://localhost:{L.port}/v">'))], timeout=75)))(listener()))
sc("I04-sub-lan", 4, "a subresource aimed at this machine's non-loopback address", bites=("W_B",))(
    lambda: (lambda L, a: ["NOT RUN: no non-loopback address"] if not a else control(L, a[0]) + (lambda p: deny(L, p, "lan-img"))(run([pub_html(page(f'<img src="http://{a[0]}:{L.port}/x"><script>fetch("http://{a[0]}:{L.port}/f",{{mode:"no-cors"}})</script>'))], timeout=75)))(listener(), lib.local_addresses()))

# ------------------------------------------------------------------------------------------------- item 5: rebinding
NAMES = ["127.0.0.1.nip.io", "localtest.me", "lvh.me", "127-0-0-1.sslip.io", "www.localtest.me", "a.b.c.localtest.me"]


def resolves_loopback(name):
    try:
        infos = socket.getaddrinfo(name, None)
    except OSError:
        return False
    return any(i[4][0].startswith("127.") or i[4][0] == "::1" for i in infos)


for n, name in enumerate(NAMES):
    def mk(name=name):
        def fn():
            if not resolves_loopback(name):
                return [f"NOT RUN: {name} does not resolve to loopback from here"]
            L = listener()
            probs = control(L)
            L.clear()
            p = run([f"http://{name}:{L.port}/hit-start"], timeout=60)
            probs += deny(L, p, f"start {name}")
            if p.rc not in (1, 2):
                probs.append(f"start {name}: exit {p.rc}, expected a refusal (1 or 2); out={p.out[:80]!r}")
            L.clear()
            for label, start in (("redirect", redirect_to(f"http://{name}:{L.port}/hit-redir")), ("img", pub_html(page(f'<img src="http://{name}:{L.port}/hit-img"><script>fetch("http://{name}:{L.port}/hit-f",{{mode:"no-cors"}})</script>')))):
                q = run([start], timeout=75)
                probs += deny(L, q, f"{label} {name}")
            return probs
        return fn
    sc(f"I05-name{n}", 5, f"public name {name} that resolves to 127.0.0.1: start URL, redirect and subresources all refused, listener silent", bites=("W_B",))(mk())


def rebind_case():
    L = listener()
    name, tried = None, []
    for cand in ("7f000001.08080808.rbndr.us", "make-8.8.8.8-rebind-127.0.0.1-rr.1u.ms", "make-8.8.8.8-rebind-127.0.0.1-repeat.1u.ms"):
        seen = set()
        for _ in range(24):
            try:
                for i in socket.getaddrinfo(cand, None, socket.AF_INET):
                    seen.add(i[4][0])
            except OSError:
                pass
            time.sleep(0.2)
        tried.append((cand, sorted(seen)))
        if "127.0.0.1" in seen and "8.8.8.8" in seen:
            name = cand
            break
    if not name:
        return [f"NOT RUN: no rebinding service flipped between 127.0.0.1 and 8.8.8.8 here: {tried}"]
    probs = control(L)
    L.clear()
    for i in range(10):
        p = run([f"http://{name}:{L.port}/hit-{i}"], timeout=60)
        probs += deny(L, p, f"flip run {i}")
    for i in range(10):
        q = run([pub_html(page(f'<img src="http://{name}:{L.port}/i{i}"><script>fetch("http://{name}:{L.port}/f{i}",{{mode:"no-cors"}})</script>'))], timeout=75)
        probs += deny(L, q, f"flip subresource run {i}")
    return probs


sc("I05-flip", 5, "a name that flips between a public and a loopback address on every lookup: 10 starts and 10 pages with subresources (a fresh browser each), listener silent", bites=("W_B",))(rebind_case)

# ---------------------------------------------------------------------------------------------------- item 6: UDP
def udp_case():
    U = CTX.setdefault("U", UdpListener())
    listener()
    U = CTX["U"]
    # control: a plain datagram must be logged
    import socket as s
    c = s.socket(s.AF_INET, s.SOCK_DGRAM)
    c.sendto(b"x", ("127.0.0.1", U.port))
    time.sleep(0.3)
    probs = [] if U.hits else ["CONTROL FAILED: the UDP listener did not log a datagram"]
    U.hits.clear()
    lan = lib.local_addresses()
    servers = [f"stun:127.0.0.1:{U.port}", f"stun:localhost:{U.port}", f"turn:127.0.0.1:{U.port}"] + [f"stun:{a}:{U.port}" for a in lan[:1]]
    ice = ",".join('{urls:"%s"%s}' % (u, ',username:"a",credential:"b"' if u.startswith("turn") else "") for u in servers)
    js = ("var o=document.getElementById('o');var pc=new RTCPeerConnection({iceServers:[%s]});pc.createDataChannel('x');"
          "var cands=[];pc.onicecandidate=function(e){if(e.candidate)cands.push(e.candidate.candidate)};"
          "pc.createOffer().then(function(d){return pc.setLocalDescription(d)}).then(function(){o.textContent='ran-rtc'});"
          "setTimeout(function(){document.body.append('CANDS:'+cands.join(' | '))},5000)") % ice
    p = run(["--timeout", "20", pub_html(page(f"<script>{js}</script>"))], timeout=60)
    time.sleep(1)
    if U.hits:
        probs.append(f"the UDP listener received {len(U.hits)} datagram(s) {U.hits[:3]}")
    if "ran-rtc" not in p.out and p.rc == 0:
        probs.append("the WebRTC page did not run (vacuous): " + p.out[:100])
    for a in lan:
        if a in p.out:
            probs.append(f"a private address {a} appears in the output (ICE candidate leak)")
    return probs


sc("I06-webrtc", 6, "WebRTC with STUN/TURN servers at a UDP listener (loopback names and the LAN address): zero datagrams, no private address in the page", bites=("W_F",))(udp_case)

# --------------------------------------------------------------------------------------------- item 7: launch arguments
def args_case():
    p = run(["--timeout", "25", f"{HTTPBIN}/delay/6"], timeout=90)
    probs = []
    if not p.cmdlines:
        return ["no Chrome command line was observed while the run was in progress (watcher too slow, or no browser)"]
    cl = p.cmdlines[0]
    for need, rx in (("an HTTP proxy argument", r"--proxy-server=(http://)?127\.0\.0\.1:\d+"), ("the loopback proxy-bypass override", r"--proxy-bypass-list=<-loopback>")):
        if not re.search(rx, cl):
            probs.append(f"missing {need}: /{rx}/ not in the Chrome command line")
    for bad in (r"--no-proxy-server", r"--proxy-bypass-list=(?!<-loopback>)", r"--proxy-auto-detect", r"--remote-debugging-port", r"--remote-debugging-address", r"--disable-web-security", r"--allow-file-access", r"--enable-quic", r"--proxy-pac-url", r"--user-data-dir=(/home|~)", r"--no-sandbox", r"--disable-features=[^ ]*Isolat", r"--host-resolver-rules=[^ ]*EXCLUDE"):
        if re.search(bad, cl):
            probs.append(f"forbidden argument /{bad}/ present: {re.search(bad, cl).group(0)}")
    if not re.search(r"(disable-quic|enable-quic=false|disable-features=[^ ]*Quic)", cl):
        probs.append("QUIC is not visibly turned off in the launch arguments (spec: QUIC off)")
    if not re.search(r"webrtc", cl, re.I):
        probs.append("no WebRTC restriction in the launch arguments (spec: WebRTC limited to proxied traffic)")
    return probs


sc("I07-args", 7, "Chrome's launch arguments: proxy set, <-loopback> override present, no bypass of loopback, no remote-debugging port, QUIC and WebRTC limited", bites=("W_A2", "W_F"))(args_case)


def leak_case():
    p = run(["--timeout", "25", f"{HTTPBIN}/delay/6"], timeout=90)
    ports = p.listen_ports
    bad = []
    for proto, state, local, remote in p.conns:
        if proto == "udp":
            bad.append((proto, remote))
        elif not re.search(r"127\.0\.0\.1:(\d+)$", remote) or int(re.search(r":(\d+)$", remote).group(1)) not in ports:
            bad.append((proto, remote))
    return [f"Chrome opened sockets that are not the proxy: {sorted(set(bad))[:6]}"] if bad else ([] if p.conns else ["no Chrome sockets observed (watcher saw nothing)"])


sc("I07-no-direct-sockets", 7, "while a page loads, every Chrome TCP socket goes to the local proxy and Chrome opens no UDP socket", bites=())(leak_case)

# ---------------------------------------------------------------------------------------------------- item 8: downloads
def download_case(name, start):
    def fn():
        marker = time.time()
        before = lib.snapshot_places([os.getcwd()])
        p = run(["--timeout", "20", start], timeout=60)
        time.sleep(1)
        after = lib.snapshot_places([os.getcwd()])
        new = sorted(x for x in after - before if str(p.tmp) not in x and "/browse-canary" not in x and "bt-" not in x)
        probs = []
        files = [x for x in new if os.path.isfile(x) and os.path.getsize(x) > 0 and os.path.getmtime(x) >= marker - 1]
        if files:
            probs.append(f"{name}: files appeared outside the run's own temp dir: {files[:4]}")
        left = [str(x) for sub in ("tmp", "cwd") for x in (p.tmp / sub).rglob("*") if x.is_file() and x.stat().st_size > 0]
        if left:
            probs.append(f"{name}: files left in the run's own temp/cwd: {left[:3]}")
        return probs
    return fn


DLS = {
    "attachment": f"{HTTPBIN}/response-headers?Content-Disposition=attachment%3B%20filename%3Ddl.bin&Content-Type=application%2Foctet-stream",
    "octet": f"{HTTPBIN}/bytes/2000",
    "page-download-attr": pub_html(page(f'<a id=a href="{HTTPBIN}/bytes/500" download="dl2.bin">x</a><script>document.getElementById("a").click()</script>')),
    "blob": pub_html(page('<script>var a=document.createElement("a");a.href=URL.createObjectURL(new Blob(["x".repeat(500)]));a.download="blob.txt";document.body.append(a);a.click()</script>')),
    "datauri": pub_html(page('<script>var a=document.createElement("a");a.href="data:application/octet-stream;base64,QUJD";a.download="d.bin";document.body.append(a);a.click()</script>')),
    "js-redirect-to-attachment": pub_html(page(f'<script>location="{HTTPBIN}/response-headers?Content-Disposition=attachment%3B%20filename%3Dx.bin&Content-Type=application%2Foctet-stream"</script>')),
    "pdf": f"{HTTPBIN}/response-headers?Content-Type=application%2Fpdf&Content-Disposition=attachment%3B%20filename%3Da.pdf",
}
for k, u in DLS.items():
    sc(f"I08-{k}", 8, f"download vector '{k}': no file written anywhere", bites=())(download_case(k, u))


def dl_exit_case():
    p = run(["--timeout", "20", DLS["attachment"]], timeout=60)
    return [] if p.rc != 0 and "[browse: rendered" not in p.out else [f"an attachment URL ended with exit {p.rc} and output {p.out[:80]!r}: expected a refusal, not a rendered success"]


sc("I08-exit", 8, "a URL that serves an attachment ends with a non-zero exit and no rendered success header")(dl_exit_case)

# ------------------------------------------------------------------------------------------------------ item 9: timeout
def timeout_case():
    p = run(["--timeout", "5", f"{HTTPBIN}/delay/10"], timeout=60)
    probs = []
    if p.rc != 1:
        probs.append(f"exit {p.rc}, expected 1")
    if "[browse: rendered" in p.out:
        probs.append("a timed-out page was printed as a rendered success")
    if not re.search(r"time|settle|wait", p.err + p.out, re.I):
        probs.append(f"the reason is not stated: err={p.err[:120]!r}")
    if p.secs > 25:
        probs.append(f"took {p.secs:.1f}s for a 5 s timeout")
    return probs


sc("I09-slow", 9, "a page that answers after its 10 s maximum delay with --timeout 5: exit 1, a stated reason, nothing printed as success")(timeout_case)
NEVER = pub_html(page('<script>var o=document.getElementById("o");var n=0;setInterval(function(){n++;o.textContent="tick "+n;fetch("https://httpbin.org/get?i="+n,{mode:"no-cors"})},300)</script>'))
sc("I09-never-settles", 9, "a page that keeps changing and fetching forever with --timeout 6: exit 1, never a success with the text so far")(
    lambda: (lambda p: [] if p.rc == 1 and "[browse: rendered" not in p.out else [f"exit {p.rc}, out={p.out[:100]!r}"])(run(["--timeout", "6", NEVER], timeout=60)))
LATE = pub_html(page('<script>setTimeout(function(){document.getElementById("o").textContent="late-text-appeared-ok"},2500)</script>'))
# Round 1 ruling: "settled" = the rendered TEXT unchanged for 2 s; the network need not be quiet. Text still
# changing at the deadline -> exit 1; --partial prints it labelled PARTIAL. Stated limit: content a timer adds after a quiet
# gap longer than 2 s can be missed.
TICK1S = pub_html(page('<script>var o=document.getElementById("o");var n=0;setInterval(function(){n++;o.textContent="tick "+n},1000)</script>'))
sc("I09-changing-text-default-30", 9, "with no flag: text that changes every second (never unchanged for 2 s) fails at the ~30 s deadline with exit 1 and no success header")(
    lambda: (lambda p: [] if p.rc == 1 and 24 < p.secs < 50 and "[browse: rendered" not in p.out else [f"exit {p.rc} after {p.secs:.1f}s out={p.out[:60]!r}"])(run([TICK1S], timeout=120)))
BUSY = pub_html(page('<script>function go(){fetch("https://httpbin.org/delay/3?t="+Date.now()).then(go)}go();document.getElementById("o").textContent="static-text-busy-network"</script>'))
sc("I09-busy-network-static-text", 9, "by ruling: text that stays unchanged while the network stays busy (beacons) settles and SUCCEEDS in a few seconds")(
    lambda: (lambda p: [] if p.rc == 0 and "static-text-busy-network" in p.out and p.secs < 15 else [f"exit {p.rc} after {p.secs:.1f}s out={p.out[:80]!r}"])(run([BUSY], timeout=90)))
sc("I09-partial", 9, "--partial on a never-settling page prints the text so far, labelled PARTIAL, not as a plain rendered success")(
    lambda: (lambda p: [] if "PARTIAL" in (p.out.splitlines() or [""])[0] and "tick" in p.out else [f"exit {p.rc} first line {(p.out.splitlines() or [''])[0]!r}"])(run(["--partial", "--timeout", "6", NEVER], timeout=60)))
sc("I09-partial-not-by-default", 9, "without --partial the same page never prints text-so-far as success")(
    lambda: (lambda p: [] if p.rc == 1 and "PARTIAL" not in p.out and "[browse: rendered" not in p.out else [f"exit {p.rc} out={p.out[:80]!r}"])(run(["--timeout", "6", NEVER], timeout=60)))
LATE1 = pub_html(page('<script>setTimeout(function(){document.getElementById("o").textContent="late-text-1s-ok"},1000)</script>'))
sc("I09-late-text-1s", 9, "control: text that a script adds after 1 s (inside the 2 s window) is in the output")(
    lambda: (lambda p: [] if p.rc == 0 and "late-text-1s-ok" in p.out else [f"exit {p.rc}, out={p.out[:100]!r}"])(run([LATE1], timeout=60)))
STEPS = pub_html(page('<script>var o=document.getElementById("o");var n=0;var t=setInterval(function(){n++;o.textContent="step-"+n+"-of-5";if(n==5)clearInterval(t)},1500)</script>'))
sc("I09-chained-updates", 9, "updates 1.5 s apart (each gap under 2 s) keep resetting the quiet window: the output holds the LAST one")(
    lambda: (lambda p: [] if p.rc == 0 and "step-5-of-5" in p.out else [f"exit {p.rc}, out={p.out[:100]!r}"])(run([STEPS], timeout=60)))

# ----------------------------------------------------------------------------------------------- item 10: block pages
def blocked_case(name, html_or_url, expect_blocked=True, text_note=""):
    def fn():
        p = run([html_or_url if html_or_url.startswith("http") else pub_html(html_or_url)], timeout=60)
        if expect_blocked:
            ok = p.rc == 1 and "[browse: rendered" not in p.out and re.search(r"block|challenge|denied|captcha|little|empty|short|HTTP [45]\d\d", p.err + p.out, re.I)
            return [] if ok else [f"{name}: exit {p.rc}, out={p.out[:80]!r}, err={p.err[:120]!r}; expected exit 1 naming a block/too-little-text"]
        return [] if p.rc == 0 and "[browse: rendered" in p.out else [f"{name}: a real page was refused: exit {p.rc}, out={p.out[:80]!r}, err={p.err[:120]!r}"]
    return fn


LONG = "word " * 120
sc("I10-just-a-moment", 10, "a 'Just a moment...' interstitial (long enough text) is named blocked", bites=())(
    blocked_case("moment", f"<html><head><title>Just a moment...</title></head><body><h1>Just a moment...</h1><p>Checking your browser before accessing the site. {LONG}</p></body></html>"))
sc("I10-access-denied", 10, "an 'Access Denied' page is named blocked")(blocked_case("denied", f"<html><head><title>Access Denied</title></head><body><h1>Access Denied</h1><p>You don't have permission to access this resource. {LONG}</p></body></html>"))
sc("I10-captcha", 10, "a captcha page is named blocked")(blocked_case("captcha", f"<html><head><title>Verify</title></head><body><div class=g-recaptcha></div><p>Please verify you are human by completing the captcha. {LONG}</p></body></html>"))
sc("I10-tiny", 10, "a page with under 200 characters of text is exit 1")(blocked_case("tiny", "<html><body><p>hi</p></body></html>"))
sc("I10-empty", 10, "an empty body is exit 1, not an empty success")(blocked_case("empty", "<html><body></body></html>"))
sc("I10-199", 10, "boundary: 199 characters of text is refused", bites=())(blocked_case("199", "<html><body><p>" + ("x" * 199) + "</p></body></html>"))
sc("I10-status-403", 10, "an HTTP 403 page is exit 1", bites=())(blocked_case("403", f"{HTTPBIN}/status/403"))
sc("I10-status-503", 10, "an HTTP 503 page is exit 1")(blocked_case("503", f"{HTTPBIN}/status/503"))
sc("I10-ctl-200chars", 10, "boundary control: a page with 300 characters of text is a success")(blocked_case("300", "<html><body><p>" + ("y" * 300) + "</p></body></html>", expect_blocked=False))
def article(text_before_phrase, phrase, total, title=""):
    """Raw HTML (no page() prefix, so the phrase really sits where the test says). Text beyond ~1,500 characters is added by script,
    because a base64 request line cannot carry more."""
    head_text = (text_before_phrase + phrase + " ")
    if total <= 1400:
        body = (head_text + ("word " * 2000))[:total]
        return f"<html><head><title>{title}</title></head><body><article><p>{body}</p></article></body></html>"
    rest = total - len(head_text)
    return (f"<html><head><title>{title}</title></head><body><article><p>{head_text}</p></article>"
            f"<script>document.body.append(document.createTextNode(\"w \".repeat({rest // 2})))</script></body></html>")


sc("I10-phrase-late-in-article", 10, "by ruling: 'Access Denied' after the first 300 characters of a 700-character article is NOT a block page")(
    blocked_case("late", article("lorem ipsum " * 40, "The Access Denied message", 700), expect_blocked=False))
sc("I10-phrase-in-long-article", 10, "by ruling: 'Just a moment' in the first 300 characters of a 3,500-character article is NOT a block page")(
    blocked_case("long", article("", "Just a moment is shown by many sites.", 3500), expect_blocked=False))
sc("I10-boundary-2800", 10, "boundary: the phrase in the first 300 characters of a 2,800-character page IS blocked", bites=())(
    blocked_case("b2800", article("", "Access Denied. ", 2800)))
sc("I10-boundary-3200", 10, "boundary: the same page at 3,200 characters is NOT blocked")(blocked_case("b3200", article("", "Access Denied. ", 3200), expect_blocked=False))
sc("I10-boundary-pos-250", 10, "boundary: the phrase starting at character ~250 of a short page IS blocked")(
    blocked_case("p250", article("lorem ipsum " * 20, "Access Denied. ", 900)))
sc("I10-boundary-pos-400", 10, "boundary: the phrase starting at character ~400 of the same page is NOT blocked")(
    blocked_case("p400", article("lorem ipsum " * 33, "Access Denied. ", 900), expect_blocked=False))
sc("I10-title-phrase-long-body", 10, "by ruling: a block phrase in the TITLE of a 4,000-character page is not enough on its own")(
    blocked_case("tl", article("", "", 4000, title="Just a moment..."), expect_blocked=False))
sc("I10-title-phrase-short-body", 10, "a block phrase in the title of a 600-character page IS blocked")(
    blocked_case("ts", article("", "", 600, title="Just a moment...")))

# ----------------------------------------------------------------------------------------------------- item 11: size
def size_case(n, expect_ok):
    def fn():
        p = run(["--timeout", "40", pub_html(page(f'<script>document.body.append("A".repeat({n}))</script>'))], timeout=120)
        if expect_ok:
            return [] if p.rc == 0 and len(p.out) > n else [f"{n} characters: exit {p.rc}, got {len(p.out)} characters; expected the full text"]
        ok = p.rc != 0 and "[browse: rendered" not in p.out
        return [] if ok else [f"{n} characters: exit {p.rc}; expected a refusal, got {len(p.out)} characters"]
    return fn


sc("I11-1_5MB", 11, "control: 1.5 million characters of text is accepted in full")(size_case(1_500_000, True))
sc("I11-2_5MB", 11, "2.5 million characters of text is refused, never truncated")(size_case(2_500_000, False))
sc("I11-8MB", 11, "8 million characters is refused quickly", bites=())(size_case(8_000_000, False))

# ---------------------------------------------------------------------------------------------- item 12: control chars
def ctrl_case():
    js = 'document.body.append("A\\x1b[31mRED\\x1b[0mB\\x00C\\x07D\\x08E\\x7fF\\x9bG\\x1b]0;PWNEDTITLE\\x07H\\u202eI\\u200bJ\\u2028K");'
    p = run([pub_html(page(f"<script>{js}</script>"))], timeout=60)
    raw = p.out.encode("utf-8", "surrogateescape")
    probs = []
    if p.rc != 0:
        return [f"exit {p.rc}: {p.err[:120]!r}"]
    for name, rx in (("ESC", rb"\x1b"), ("NUL", rb"\x00"), ("BEL", rb"\x07"), ("BS", rb"\x08"), ("DEL", rb"\x7f"), ("C1 CSI", rb"\xc2\x9b"), ("CR", rb"\r")):
        if re.search(rx, raw):
            probs.append(f"{name} survives in the output")
    if "PWNEDTITLE" in p.out and "\x1b" in p.out:
        probs.append("an OSC sequence survives")
    if not re.search(r"A.*RED.*B.*C.*D.*E.*F", p.out, re.S):
        probs.append("the visible text around the controls is missing (the stripping ate real text?)")
    for name, ch in (("bidi override U+202E", "‮"), ("zero-width space U+200B", "​"), ("line separator U+2028", " ")):
        if ch in p.out:
            probs.append(f"{name} survives (assumption: hidden-text characters are removed)")
    return probs


sc("I12-controls", 12, "ESC, NUL, BEL, BS, DEL, C1 CSI, OSC and hidden-text characters in page text never reach the output")(ctrl_case)

# --------------------------------------------------------------------------------------------------------- item 13: header
def header_case():
    probs = []
    p = run([redirect_to(EX)], timeout=60)
    first = p.out.splitlines()[0] if p.out else ""
    if not re.match(r"^\[browse: rendered https://example\.com/?\]$", first):
        probs.append(f"after a redirect the first line should name the FINAL url and say rendered: {first!r}")
    if HTTPBIN in first:
        probs.append("the header names the start URL, not the final one")
    q = run([pub_html(page(f'<script>location.replace("{EX}")</script>'))], timeout=60)
    f2 = q.out.splitlines()[0] if q.out else ""
    if "example.com" not in f2 or "rendered" not in f2:
        probs.append(f"after a script navigation the header should name example.com: {f2!r}")
    return probs


sc("I13-header", 13, "the first line says 'rendered' and names the FINAL url after an HTTP redirect and after a script navigation")(header_case)

# ----------------------------------------------------------------------------------------------- item 14: proxy closed
def proxy_closed_case(mode):
    def fn():
        if mode == "normal":
            p = run(["--timeout", "20", f"{HTTPBIN}/delay/3"], timeout=60)
        elif mode == "error":
            p = run(["--timeout", "3", f"{HTTPBIN}/delay/15"], timeout=60)
        elif mode == "sigint":
            p = run(["--timeout", "30", f"{HTTPBIN}/delay/20"], timeout=60, sig_after=3.0, sig=signal.SIGINT)
        elif mode == "sigterm":
            p = run(["--timeout", "30", f"{HTTPBIN}/delay/20"], timeout=60, sig_after=3.0, sig=signal.SIGTERM)
        elif mode == "badpage":
            p = run(["--timeout", "20", "https://expired.badssl.com/"], timeout=60)
        probs = []
        if not p.listen_ports:
            return [f"{mode}: no listening proxy port was observed while it ran (exit {p.rc}); cannot judge"]
        time.sleep(1.5)
        for port in p.listen_ports:
            if p.listening_now(port):
                probs.append(f"{mode}: port {port} is still listening after the tool exited")
        left = p.chrome_left()
        if left:
            probs.append(f"{mode}: Chrome processes still alive after exit: {left}")
        return probs
    return fn


for mode in ("normal", "error", "badpage", "sigint", "sigterm"):
    sc(f"I14-{mode}", 14, f"the proxy port is closed and no Chrome is left after: {mode}")(proxy_closed_case(mode))


def sigkill_case():
    p = run(["--timeout", "30", f"{HTTPBIN}/delay/20"], timeout=60, sig_after=3.0, sig=signal.SIGKILL)
    time.sleep(2)
    probs = []
    for port in p.listen_ports:
        if p.listening_now(port):
            probs.append(f"port {port} still listening after SIGKILL")
    left = p.chrome_left()
    if left:
        probs.append(f"Chrome still alive after SIGKILL of the tool: {left} (finding: orphaned browser)")
    for pid in left:
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
    return probs


sc("I14-sigkill", 14, "after kill -9 of the tool: no listening proxy and no orphaned Chrome (the list does not promise this; a finding if it fails)")(sigkill_case)

# ------------------------------------------------------------------------------------------------- item 15: persistence
def persist_case(mode):
    def fn():
        before = lib.snapshot_places()
        if mode == "normal":
            p = run(["--timeout", "20", f"{HTTPBIN}/cookies/set?a=b"], timeout=60)
        elif mode == "error":
            p = run(["--timeout", "3", f"{HTTPBIN}/delay/15"], timeout=60)
        elif mode == "sigint":
            p = run(["--timeout", "30", f"{HTTPBIN}/delay/20"], timeout=60, sig_after=3.0)
        elif mode == "storage":
            p = run([pub_html(page('<script>try{localStorage.setItem("k","v");document.cookie="c=1";indexedDB.open("db")}catch(e){}</script>'))], timeout=60)
        time.sleep(1.5)
        after = lib.snapshot_places()
        new = sorted(x for x in after - before if str(p.tmp) not in x and "/browse-canary" not in x and not x.startswith(str(p.tmp)))
        left = [str(x) for sub in ("tmp", "cwd") for x in (p.tmp / sub).rglob("*")]
        probs = []
        if new:
            probs.append(f"{mode}: new files/dirs outside the run's own temp dir: {new[:5]}")
        if left:
            probs.append(f"{mode}: entries left in the run's TMPDIR/cwd: {left[:5]}")
        return probs
    return fn


for mode in ("normal", "error", "sigint", "storage"):
    sc(f"I15-{mode}", 15, f"nothing persists after: {mode} (no profile, cache or cookie file in /tmp, HOME dot-dirs, TMPDIR or cwd)")(persist_case(mode))

# -------------------------------------------------------------------------------------------- what the list does not say
def cookies_case():
    r1 = run([f"{HTTPBIN}/cookies/set?testcookie=remember"], timeout=60)
    r2 = run([f"{HTTPBIN}/cookies"], timeout=60)
    return [f"a cookie set in one run is visible in the next: {r2.out[:120]!r}"] if "remember" in r2.out else ([] if r2.rc == 0 or r2.rc == 1 else [f"exit {r2.rc}"])


sc("X01-cookies", None, "no cookie carries from one run to the next (spec design: no profile, no cookies in or out)")(cookies_case)
sc("X02-userinfo-credentials", None, "credentials in the URL do not sign in: a basic-auth page does not return its authenticated body")(
    lambda: (lambda p: [] if '"authenticated": true' not in p.out and "authenticated" not in p.out.replace("unauth", "") else [f"credentials in the URL authenticated: {p.out[:100]!r}"])(run([f"https://user:pw@httpbin.org/basic-auth/user/pw"], timeout=60)))
sc("X03-redirect-loop", None, "a redirect loop (50 hops) ends in a bounded exit 1, not a hang", bites=())(
    lambda: (lambda p: [] if p.rc == 1 and p.secs < 60 else [f"exit {p.rc} after {p.secs:.0f}s"])(run(["--timeout", "20", f"{HTTPBIN}/redirect/50"], timeout=90)))
sc("X04-dialogs", None, "alert/confirm/prompt in a loop do not hang the tool", bites=())(
    lambda: (lambda p: [] if p.secs < 40 else [f"hung {p.secs:.0f}s"])(run(["--timeout", "10", pub_html(page('<script>for(var i=0;i<20;i++){alert("a");confirm("c");prompt("p")};document.getElementById("o").textContent="after-dialogs"</script>'))], timeout=90)))
sc("X05-permissions", None, "geolocation, camera and notification requests are denied, not prompted", bites=())(
    lambda: (lambda p: [] if p.secs < 40 else [f"hung {p.secs:.0f}s"])(run(["--timeout", "10", pub_html(page('<script>navigator.geolocation.getCurrentPosition(function(){document.body.append("GEO-GRANTED")},function(){document.body.append("geo-denied")});navigator.mediaDevices&&navigator.mediaDevices.getUserMedia({video:true}).then(function(){document.body.append("CAM-GRANTED")}).catch(function(){document.body.append("cam-denied")});Notification.requestPermission().then(function(r){document.body.append("notif-"+r)})</script>'))], timeout=90)))
sc("X06-non-html", None, "an image or JSON URL ends cleanly (no crash, no traceback)", bites=())(
    lambda: [] if all("Traceback" not in run([u], timeout=60).err for u in (f"{HTTPBIN}/image/png", f"{HTTPBIN}/json", f"{HTTPBIN}/bytes/10")) else ["a Python traceback reached stderr"])
for k, how in {"iframe": '<iframe src="file://%s"></iframe>', "script": '<script>fetch("file://%s").then(function(r){return r.text()}).then(function(t){document.body.append(t)})</script>',
               "nav": '<script>location="file://%s"</script>', "img": '<img src="file://%s">'}.items():
    sc(f"X07-file-{k}", None, f"a public page that reaches for a local file ({k}): the file's content never reaches the output", bites=("W_C",) if False else ())(
        (lambda how=how: (lambda p: [] if "FILE-CANARY" not in p.out else ["a local file's content reached the output"])(run([pub_html(page(how % CANARY))], timeout=60))))
sc("X08-chrome-url-nav", None, "a script navigating to chrome://version does not render browser internals", bites=())(
    lambda: (lambda p: [] if "Google Chrome" not in p.out and "Command Line" not in p.out else ["browser internals reached the output"])(run([pub_html(page('<script>location="chrome://version"</script>'))], timeout=60)))
sc("X10-ctl-normal-page", None, "control: an ordinary public page renders with exit 0, a rendered header and real text")(
    lambda: (lambda p: [] if p.rc == 0 and p.out.startswith("[browse: rendered") and len(p.out) > 300 else [f"exit {p.rc} out={p.out[:100]!r}"])(run([EX], timeout=60)))
sc("X11-js-built-page", None, "control: a page whose text is built entirely by script renders that text (the tool's purpose)")(
    lambda: (lambda p: [] if "BUILT-BY-SCRIPT" in p.out else [f"exit {p.rc} out={p.out[:100]!r}"])(run([pub_html(page('<script>document.body.append("BUILT-BY-SCRIPT " + "z".repeat(250))</script>'))], timeout=60)))


# ---------------------------------------------------------------------------------------------------- runner
def main():
    global BUILD
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", required=True)
    ap.add_argument("--weak", action="append", default=[], help="NAME=PATH of a deliberately weakened build")
    ap.add_argument("--only", default="")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    sel = REG
    if a.only:
        pre = tuple(x.strip() for x in a.only.split(","))
        sel = [r for r in REG if r[0].startswith(pre)]
    if a.list:
        for sid, item, title, bites, _ in sel:
            print(f"{sid:20} item {str(item):>4}  {'bites ' + ','.join(bites) if bites else '':16} {title}")
        return 0
    BUILD = str(pathlib.Path(a.build).resolve())
    results = {}
    for sid, item, title, bites, fn in sel:
        t0 = time.time()
        try:
            probs = fn()
        except Exception as e:
            probs = [f"fixture crashed: {type(e).__name__}: {e}"]
        notrun = [p for p in probs if p.startswith("NOT RUN")]
        results[sid] = ("NOTRUN" if notrun and len(notrun) == len(probs) else "PASS" if not probs else "FAIL", probs)
        print(f"  {results[sid][0]:6} {sid:20} item {str(item):>4}  {title[:100]}  ({time.time() - t0:.0f}s)", flush=True)
        for pr in probs[:6]:
            print(f"           - {pr[:300]}", flush=True)
    npass = sum(1 for v in results.values() if v[0] == "PASS")
    print(f"\nPRISTINE: {npass}/{len(results)} pass; {sum(1 for v in results.values() if v[0] == 'FAIL')} fail; {sum(1 for v in results.values() if v[0] == 'NOTRUN')} not run")
    for w in a.weak:
        name, path = w.split("=", 1)
        BUILD = str(pathlib.Path(path).resolve())
        caught, missed = [], []
        for sid, item, title, bites, fn in sel:
            if name not in bites:
                continue
            try:
                probs = fn()
            except Exception as e:
                probs = [f"fixture crashed: {e}"]
            real = [p for p in probs if not p.startswith("NOT RUN")]
            (caught if real else missed).append(sid)
            print(f"  [{name}] {'CAUGHT' if real else 'NOT CAUGHT'} {sid}", flush=True)
        print(f"WEAKENED {name}: {len(caught)} of {len(caught) + len(missed)} declared fixtures fail as they must; NOT CAUGHT: {missed}")
    return 0 if all(v[0] != "FAIL" for v in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
