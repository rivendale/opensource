# Independent tests for tools/web/bin/browse (the denying direction)

Written from the failure list in `tools/web/SPEC.md` (items 1-15) before reading the code, by a seat
other than the builder, and kept black box: command line in, behavior out. 212 fixtures. They run on a machine that has
tools/web/bin/browse's venv (Playwright and its Chromium) and a network path to httpbin.org: they use PUBLIC pages (httpbin serves
arbitrary HTML from a base64 path, redirects, response headers) because the tool refuses to open anything local, so a
local test server cannot be the page under test. A fixture whose network dependency is missing reports NOT RUN, never a pass.

    python3 tools/web/tests/browse_tests.py --build tools/web/bin/browse [--only I03,I09] [--list]
    python3 tools/web/tests/make_weakened.py SRC_DIR OUT_DIR       # SRC_DIR is tools/web (it holds bin/browse and bin/fetch)
    python3 tools/web/tests/browse_tests.py --build tools/web/bin/browse --weak W_A2=OUT/w_a2/bin/browse --weak W_B=OUT/w_b/bin/browse \
        --weak W_C=OUT/w_c/bin/browse --weak W_E=OUT/w_e/bin/browse --weak W_F=OUT/w_f/bin/browse

Run it on a COPY of the tool when you test weakened builds; never weaken the live tree.

## How a result is judged
- **The listener's log is the evidence, not the exit code.** A dual-stack listener logs the destination address of every
  connection it receives (127.0.0.1, 127.0.0.2, ::1, ::ffff:127.0.0.1, 0.0.0.0, the LAN and tailnet addresses). A denying fixture
  passes only if it logged zero connections and its response body never reached the output.
- **Every local fixture has a control**: curl to the same listener must log a hit, so "zero hits" cannot be a dead listener.
  Redirect and script vectors also run the SAME mechanism at a public page (example.com) and must succeed, so a refusal cannot be a
  mechanism that never ran.
- **A fixture must fail on a weakened build before it counts** (`make_weakened.py`): W_A2 loopback bypass really re-enabled,
  W_B proxy address filter off, W_C start-URL host check off, W_E scheme and host checks both off, W_F QUIC and WebRTC limits
  removed. Fixtures that cannot discriminate (headless Chrome makes no such request even with the filter off) are kept but
  declared non-biting, and say so in their title.
- A sampler watches /proc and `ss` while the tool runs: Chrome's command line, its listening and connected sockets, and what is
  left after exit (processes, the proxy port, files in TMPDIR, /tmp, the HOME dot-directories).

## What is covered
| item | fixtures |
|---|---|
| 1 schemes | 24: file, ftp, data, chrome, javascript, blob, ws, view-source, mailto, devtools, empty, scheme-less forms |
| 2 private start URLs | 55: every listed spelling plus octal/hex/short forms, trailing dot, userinfo tricks, LAN and tailnet addresses with a live listener, 25 reserved ranges |
| 3 redirects | 19: HTTP 301/302/303/307/308, chains, meta refresh, JS location variants, Refresh header, form POST, clicked link, base href |
| 4 subresources | 43: tags, CSS, fonts, fetch, XHR, beacon, WebSocket, EventSource, import, dynamic iframe/script, IPv6 and numeric hosts |
| 5 rebinding | 7: nip.io, localtest.me, lvh.me, sslip.io, a name that really flips between a public and a loopback address |
| 6 UDP | WebRTC with STUN/TURN servers at a UDP listener |
| 7 launch | the proxy flags, no sandbox-off, no debugging port, QUIC and WebRTC limited, no direct sockets |
| 8 downloads | seven vectors, no file written anywhere |
| 9 timeouts | slow, never settles, changing text at the deadline, busy network with static text, --partial, chained updates |
| 10 block pages | the interstitials, status pages, size and position boundaries of the block-phrase rule |
| 11 size | 1.5 million characters accepted, 2.5 million refused |
| 12 control characters | C0, C1, OSC, format characters, line and paragraph separators |
| 13 header | final URL after an HTTP redirect and after a script navigation |
| 14 proxy closed | after normal exit, error, bad page, SIGINT, SIGTERM, SIGKILL |
| 15 persistence | normal, error, SIGINT, storage APIs |
| extras | cookies do not persist, credentials in the URL, redirect loop, dialogs, permissions, local files and chrome:// from a public page |

Not covered, because it needs infrastructure the tests do not have: real QUIC to a UDP/443 listener, Chrome's own DNS leaks, NAT64.
