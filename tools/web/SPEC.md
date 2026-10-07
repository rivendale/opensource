# browse: design and failure list

`browse` reads a public page that builds itself with JavaScript and prints its text. It exists because a plain
fetch of a form builder, a school site or a government page often returns only a title.

## What failed first

A headless-Chrome route was first added inside `fetch` and removed the same day. Chrome does its own DNS, follows
its own redirects and runs scripts, so `fetch`'s address checks never saw those requests. In testing it followed a
redirect to `127.0.0.1` that `fetch` itself refused, and a review found DNS-rebinding gaps. **A check on the starting
URL is not a control for a browser.**

## Design: the control is the network path

- Chrome gets no direct network. It launches with an HTTP proxy that lives inside `browse` on a random `127.0.0.1`
  port, with QUIC off and WebRTC limited to proxied traffic. Playwright also adds `--proxy-bypass-list=<-loopback>`,
  which stops Chrome's default of sending localhost requests straight past a proxy.
- The proxy resolves each host once, through `fetch`'s public-only filter, and connects to that exact IP. A
  redirect, subresource, WebSocket or rebinding name that lands on a private address is refused with 403.
- The browser context is throwaway: no profile, no cookies kept, downloads refused, service workers blocked, the
  Chrome sandbox on, and a private temp directory removed on every exit. It never signs in.
- Output is text only, with control characters and Unicode format characters (bidi overrides, zero-width) removed.
  Page text is data: the tool never passes it to a model or a shell.

## Failure list (written before the code)

1. A scheme other than http(s) as the start URL (file:, ftp:, data:, chrome:, javascript:): exit 2, nothing launched.
2. A start host that is private, loopback, link-local, CGNAT/tailnet or reserved, in any spelling (`127.0.0.1`,
   `localhost`, `[::1]`, `[::ffff:127.0.0.1]`, `2130706433`, `0x7f000001`, `0177.0.0.1`, `0.0.0.0` and the private
   ranges): exit 2.
3. A public page that redirects (3xx, meta refresh, JavaScript) to an item-2 address: refused at the proxy. A local
   listener receives nothing; the listener's log is the evidence, not the exit code.
4. Subresources (img, script, fetch, XHR, iframe, WebSocket) aimed at item-2 addresses: refused; the listener
   receives nothing.
5. DNS rebinding (a public name that resolves to `127.0.0.1`, or flips between public and private): refused.
6. WebRTC/STUN or any UDP to a LAN address: not possible.
7. Chrome is never started with a loopback proxy bypass, and never with its sandbox off.
8. A URL that serves an attachment: refused, no file written.
9. A page whose text is still changing at the deadline: exit 1, never printed as success (`--partial` prints it,
   labeled). "Settled" means the rendered text was unchanged for 2 seconds; network quiet is not required, because
   analytics beacons keep many real pages busy forever. Stated limit: text a timer adds after a quiet gap longer
   than 2 seconds can be missed.
10. A block or challenge page: exit 1. A block phrase counts only in the title or the first 300 characters, and only
    when the text is under 3,000 characters, so an article that mentions "Access Denied" is still readable.
11. Text over 2 MB: refused, not silently truncated.
12. Control characters, ANSI escapes and Unicode format characters: removed.
13. The output header names the final URL and says "rendered".
14. The proxy port closes on every exit path, including errors and signals.
15. Nothing persists after exit: no profile, cache, cookie or temp file.

## How it was tested

A second agent wrote 212 black-box fixtures from this list without reading the code (`tests/`). Every fixture that
claims to catch something was shown to fail against a deliberately weakened copy (`tests/make_weakened.py`) before it
counted. One measured trap: deleting the tool's own loopback-bypass flag weakens nothing, because Playwright adds the
same flag itself. A test that asserts launch arguments proves nothing; the listener's log does.

Not covered, because it needs infrastructure the tests do not have: real QUIC to a UDP/443 listener, Chrome's own
DNS resolver, and NAT64.
