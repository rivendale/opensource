#!/usr/bin/env python3
"""Build the deliberately weakened copies of tools/web/bin/browse that the fixtures must FAIL against.
usage: make_weakened.py SRC_DIR OUT_DIR      (SRC_DIR holds bin/browse and bin/fetch, i.e. tools/web; OUT_DIR gets w_a2 w_b w_c w_e w_f)

  W_A2  loopback proxy-bypass really re-enabled (an explicit bypass list; merely deleting the tool's own
        --proxy-bypass-list=<-loopback> is a NO-OP because Playwright adds that flag itself)
  W_B   the proxy's address filter disabled (both layers: the public-only getaddrinfo and the per-address check)
  W_C   the start-URL host pre-check disabled
  W_E   the scheme check AND the host pre-check disabled (the scheme check alone is shadowed by the host check)
  W_F   QUIC off and the WebRTC non-proxied-UDP limits removed
Every edit must match exactly once, so a changed tools/web/bin/browse fails loudly here instead of producing a no-op copy."""
import pathlib, shutil, sys

src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])


def variant(name, edits):
    d = out / name
    if d.exists():
        shutil.rmtree(d)
    shutil.copytree(src, d)
    t = (d / "bin/browse").read_text()
    for old, new in edits:
        if t.count(old) != 1:
            raise SystemExit(f"{name}: expected exactly one match for {old!r}, found {t.count(old)}")
        t = t.replace(old, new)
    (d / "bin/browse").write_text(t)


variant("w_a2", [('    "--proxy-bypass-list=<-loopback>",\n', ''), ('"bypass": "<-loopback>"', '"bypass": "127.0.0.1,localhost,[::1]"')])
variant("w_b", [("addrs = [a for a in addrs if fetch._is_public_ip(a)]", "addrs = list(addrs)"), ("socket.getaddrinfo, host, port,", "fetch._REAL_GETADDRINFO, host, port,")])
variant("w_c", [("if not fetch.public_host(u.hostname):", "if False:")])
variant("w_e", [('if u.scheme not in ("http", "https"):', 'if False:'), ("if not fetch.public_host(u.hostname):", "if False:")])
variant("w_f", [('    "--disable-quic",\n', ''), ('    "--force-webrtc-ip-handling-policy=disable_non_proxied_udp",\n', ''), ('    "--webrtc-ip-handling-policy=disable_non_proxied_udp",\n', '')])
print("built", sorted(p.name for p in out.iterdir() if p.name.startswith("w_")))
