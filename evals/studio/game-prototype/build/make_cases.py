#!/usr/bin/env python3
"""Writes evals/studio/game-prototype/cases/<case>/ (brief.md, inputs/, expected.json, check.py) and holds, for each case, a reference solution and the defective outputs a
careless skill would produce, so selfcheck.py can show every checker passes the first and fails each of the others.

    python3 evals/studio/game-prototype/build/make_cases.py        rewrite the case directories

Needs node (22 or later) on PATH. A defect that never starts is run until the checker's 30 s limit, so the self-check takes a few minutes.
"""
import json, pathlib, shutil, stat, sys, textwrap

import numpy as np
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "lib"))
CASES_DIR = HERE.parent / "cases"
SCAFFOLD = HERE / "scaffold"
LAYOUT = textwrap.dedent("""\
    Project layout (the same in every brief): the project root is the game. Code is in `src/` and `scripts/`, third-party credits in `THIRD_PARTY.md` (with the licenses' text kept), assets that
    enter the build in `assets/` with a row each in `assets/MANIFEST.json` (see `skills/studio/manifest.schema.json`). Inputs are in `inputs/` and are read-only. Checks run `node` in a copy of
    the project with no network.
    """)
CHECK_PY = '''#!/usr/bin/env python3
"""Checker for this case. Run as: check.py SCRATCH_DIR EXPECTED_JSON (after the agent has exited). The measurements are in evals/studio/lib/."""
import os, pathlib, sys
sys.path.insert(0, os.environ.get("STUDIO_LIB") or str(pathlib.Path(__file__).resolve().parents[3] / "lib"))
import studio_lib
sys.exit(studio_lib.main([sys.argv[0]] + sys.argv[1:]))
'''
CASES, PURPOSE = [], {}


def case(cid, item, kind, brief, inputs, rules, reference, defects=(), tools=("node 22", "python3"), purpose=None):
    CASES.append(dict(id=cid, item=item, kind=kind, brief=brief, inputs=inputs, rules=rules, reference=reference, defects=list(defects), tools=list(tools)))
    if purpose:
        PURPOSE[cid] = purpose


def ensure(root, rel, text):
    p = pathlib.Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def write_manifest(root, rows):
    ensure(root, "assets/MANIFEST.json", json.dumps({"manifest_version": 1, "assets": rows}, indent=2) + "\n")


def row(file, **kw):
    r = dict(file=file, kind="sprite", tool="python3 + Pillow", tool_version="3.12", seed_or_params="hand-drawn script", date="2026-10-10", model=None, weights_license=None, source=None,
             source_license=None, reference_used_as="none", master="tools/make_assets.py", build_script="tools/make_assets.py", paid_service=None)
    r.update(kw)
    return r


def manifest_rules(files):
    r = [{"id": "manifest_valid", "type": "proto_assets_have_rows"}]
    return r + ([{"id": "manifest_rows", "type": "manifest_rows", "files": files}] if files else [])


def png(root, rel, color):
    p = pathlib.Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    a = np.zeros((16, 16, 4), np.uint8)
    a[3:13, 3:13] = list(color) + [255]
    Image.fromarray(a, "RGBA").save(p)


def scaffold_inputs():
    d = {}
    for f in SCAFFOLD.rglob("*"):
        if f.is_file():
            d["scaffold/" + f.relative_to(SCAFFOLD).as_posix()] = ("text", f.read_text())
    d["reference/asteroid-clone/game.js"] = ("text", (HERE / "gpl/game.js").read_text())
    d["reference/asteroid-clone/README.md"] = ("text", "asteroid-clone: a small arcade game. License GPL-3.0-or-later. This project's reuse class is `study only`: read it, copy nothing from it.\n")
    d["playbooks/arcade.md"] = ("text", textwrap.dedent("""\
        # Arcade playbook (excerpt)

        Core loop of an arcade prototype: the player acts, the game scores a success or takes a life on a miss, and when lives run out the game shows a lose state and offers a restart.
        A prototype without a lose condition, a score or a restart is not an arcade game yet. Print the state changes so a test can watch them.
        """))
    return d


def copy_inputs(root, case):
    for rel, v in case["inputs"].items():
        p = pathlib.Path(root) / "inputs" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(v[1] if isinstance(v, tuple) else v)


# ------------------------------------------------------------------------------------------------ the reference project
MAIN = """'use strict';
const { run } = require('./engine');
const LANES = 5;
const state = { lane: 2, lives: 3, score: 0, over: false, coins: [] };

function reset() {
  state.lane = 2;
  state.lives = 3;
  state.score = 0;
  state.over = false;
  state.coins = [];
}

run({
  update(frame, actions, emit) {
    for (const action of actions) {
      if (state.over) {
        if (action === 'restart') { reset(); emit('RESTART'); }
        continue;
      }
      if (action === 'left') state.lane = Math.max(0, state.lane - 1);
      if (action === 'right') state.lane = Math.min(LANES - 1, state.lane + 1);
    }
    if (state.over) return;
    if (frame % 30 === 0) state.coins.push({ lane: (frame / 30) % LANES, land: frame + 60 });
    for (const coin of state.coins.filter((c) => c.land === frame)) {
      if (coin.lane === state.lane) {
        state.score += 1;
        emit('SCORE ' + state.score);
      } else {
        state.lives -= 1;
        emit('LIVES ' + state.lives);
        if (state.lives === 0) { state.over = true; emit('GAME_OVER'); }
      }
    }
    state.coins = state.coins.filter((c) => c.land > frame);
  },
});
"""
BUILD = """'use strict';
const fs = require('fs');
const path = require('path');
fs.mkdirSync('dist', { recursive: true });
for (const f of fs.readdirSync('src')) fs.copyFileSync(path.join('src', f), path.join('dist', f));
console.log('built', fs.readdirSync('dist').length, 'files');
"""
THIRD = "# Third-party code\n\n| name | version | license | where used | license text |\n|---|---|---|---|---|\n| mini-scaffold | 1.2.0 | MIT | src/engine.js | licenses/mini-scaffold.txt |\n"
PKG = {"name": "coin-catcher", "version": "0.1.0", "private": True, "scaffold": "mini-scaffold 1.2.0", "scripts": {"start": "node src/main.js", "build": "node scripts/build.js"}, "dependencies": {}}


def project(root, main=MAIN, build=BUILD, pkg=None, node_version="22.11.0", third=THIRD, license_text=True, engine=True, assets=("coin",), rows=None, extra_files=None):
    root = pathlib.Path(root)
    for child in list(root.iterdir()):       # a project is built from nothing but the inputs, so a defect can leave a file out
        if child.name != "inputs":
            shutil.rmtree(child) if child.is_dir() else child.unlink()
    ensure(root, "src/main.js", main)
    if engine:
        ensure(root, "src/engine.js", (SCAFFOLD / "src/engine.js").read_text())
    ensure(root, "scripts/build.js", build)
    ensure(root, "package.json", json.dumps(pkg if pkg is not None else PKG, indent=2) + "\n")
    if node_version:
        ensure(root, ".node-version", node_version + "\n")
    if third is not None:
        ensure(root, "THIRD_PARTY.md", third)
    if license_text:
        ensure(root, "licenses/mini-scaffold.txt", (SCAFFOLD / "LICENSE").read_text())
    for a in assets:
        png(root, f"assets/sprites/{a}.png", (240, 200, 40))
    write_manifest(root, rows if rows is not None else [row(f"assets/sprites/{a}.png") for a in assets])
    ensure(root, "tools/make_assets.py", "# draws the sprites\n")
    for rel, text in (extra_files or {}).items():
        ensure(root, rel, text)


def reference(**kw):
    return lambda root: project(root, **kw)


def edit(text, old, new):
    assert old in text, old
    return text.replace(old, new)


ARGS = ["src/main.js", "--headless"]
BUILD_ARGS = ["scripts/build.js"]
BRIEF = ("Make a small arcade game, a coin catcher, as a playable prototype. Start from the scaffold in `inputs/scaffold/` (copy what you use into the project root) and follow the core loop in `inputs/playbooks/arcade.md`. "
         "Game rules: five lanes, 0 to 4; the player starts in lane 2; the actions `left` and `right` move one lane and stop at the ends. A coin appears at frame 30*i in lane i%5 (i = 0, 1, 2, ...) and lands 60 frames "
         "later: if the player is in the coin's lane at that frame (after that frame's actions) print `SCORE n` with the new score; otherwise the player loses a life and the game prints `LIVES n` (n = lives left; the "
         "player starts with 3); at 0 lives print `GAME_OVER` and stop updating until a `restart` action arrives, which resets everything and prints `RESTART`. Run it with `node src/main.js --headless --frames N`, input on stdin as "
         "`FRAME ACTION` lines. The build is `node scripts/build.js`. Record the versions the project depends on (the scaffold and Node) so the build can be reproduced. Any art goes in `assets/`. It will run on Node 22 on a machine with no network and must start within 30 s.\n")
INPUTS = scaffold_inputs()
START = {"id": "starts", "type": "proto_starts", "args": ARGS + ["--frames", "60"], "limit": 30}
LOSE = {"id": "lose", "type": "proto_loop_lose", "args": ARGS}
RESTART = {"id": "restart", "type": "proto_loop_restart", "args": ARGS}
SCORE = {"id": "score", "type": "proto_loop_score", "args": ARGS}
NOPHONE = {"id": "phone_home", "type": "proto_no_phone_home", "args": ARGS + ["--frames", "700"], "also": [BUILD_ARGS], "allowed_hosts": []}
PINNED = {"id": "pinned", "type": "proto_pinned", "scaffold": "mini-scaffold"}
COPIED = {"id": "not_copied", "type": "proto_not_copied", "reference": "inputs/reference", "run": 4}
CREDITED = {"id": "credited", "type": "proto_credited", "reference": "inputs/scaffold", "run": 6, "scaffold": "mini-scaffold", "license": "MIT", "holder": "Mini Scaffold Authors"}
ALL = [START, LOSE, RESTART, SCORE, NOPHONE, PINNED, COPIED, CREDITED] + manifest_rules([])


def only(*ids):
    return [r for r in ALL if r["id"] in ids or r["id"].startswith("manifest")]


# ============================================================================================ proto 1: it starts
SYNTAX = edit(MAIN, "const state = {", "const state = {{")
NO_FIRST = "'use strict';\nlet n = 0;\nfor (let f = 0; f < 5; f++) n += f;\nconsole.log('loaded', n);\n"
SLOW = "'use strict';\nAtomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 35000);\n" + MAIN.split("'use strict';\n", 1)[1]
case("proto-1a-it-starts", "proto-1", "M", BRIEF, INPUTS, only("starts"), reference(),
     [("a syntax error in main.js", reference(main=SYNTAX), {"starts"}),
      ("it runs but never reaches the first frame", reference(main=NO_FIRST), {"starts"}),
      ("it reaches the first frame after 35 s", reference(main=SLOW), {"starts"})])

# ============================================================================================ proto 2: code reuse
GPL_COPY = MAIN.replace("run({", """function stepRocks(state) {
  for (const rock of state.rocks) {
    rock.y += rock.speed * state.difficulty;
    if (rock.y > state.height) {
      rock.y = -rock.size;
      rock.x = Math.floor(state.random() * (state.width - rock.size));
      state.escaped += 1;
    }
  }
  state.difficulty = Math.min(3, 1 + Math.floor(state.escaped / 10) * 0.25);
}

run({""", 1)
THIRD_NONE = None
THIRD_NO_NOTICE = THIRD
case("proto-2a-reuse-class", "proto-2", "M", BRIEF, INPUTS, only("not_copied", "credited", "starts"), reference(),
     [("a function copied from the study-only GPL project", reference(main=GPL_COPY), {"not_copied"}),
      ("the scaffold's engine used, no THIRD_PARTY.md", reference(third=None, license_text=False), {"credited"}),
      ("a THIRD_PARTY row but the license text not kept", reference(license_text=False, third=THIRD.replace("| licenses/mini-scaffold.txt |", "| |")), {"credited"})])

# ============================================================================================ proto 3: the core loop
NO_LIVES = edit(MAIN, "state.lives -= 1;", "")
NO_SCORE = edit(MAIN, "emit('SCORE ' + state.score);", "")
NO_RESTART = edit(MAIN, "if (action === 'restart') { reset(); emit('RESTART'); }", "")
NEVER_OVER = edit(MAIN, "if (state.lives === 0) { state.over = true; emit('GAME_OVER'); }", "")
case("proto-3a-the-core-loop", "proto-3", "M", BRIEF, INPUTS, only("lose", "restart", "score"), reference(),
     [("lives are never taken", reference(main=NO_LIVES), {"lose", "restart"}),
      ("no score is ever printed", reference(main=NO_SCORE), {"score"}),
      ("no way to restart", reference(main=NO_RESTART), {"restart"}),
      ("lives run out and nothing happens", reference(main=NEVER_OVER), {"lose", "restart"})])

# ============================================================================================ proto 4: versions are pinned
CARET = dict(PKG, dependencies={"left-pad": "^1.3.0"})
LATEST = dict(PKG, dependencies={"left-pad": "latest"})
NO_VER_PKG = {k: v for k, v in PKG.items() if k != "scaffold"}
case("proto-4a-versions-pinned", "proto-4", "M", BRIEF, INPUTS, only("pinned", "credited"), reference(),
     [("a caret range on a dependency", reference(pkg=CARET), {"pinned"}),
      ("a dependency at latest", reference(pkg=LATEST), {"pinned"}),
      ("no Node version anywhere", reference(node_version=None), {"pinned"}),
      ("the scaffold named without its version", reference(pkg=NO_VER_PKG, third=THIRD.replace("| 1.2.0 |", "| |")), {"pinned", "credited"})])

# the same item without the sentence that asks for versions to be recorded: does the skill think to pin?
BRIEF_PLAIN = BRIEF.replace("Record the versions the project depends on (the scaffold and Node) so the build can be reproduced. ", "")
assert BRIEF_PLAIN != BRIEF
case("proto-4b-pins-unprompted", "proto-4", "M", BRIEF_PLAIN, INPUTS, only("pinned", "credited"), reference(),
     [("no Node version and the scaffold named without its version", reference(node_version=None, pkg=NO_VER_PKG, third=THIRD.replace("| 1.2.0 |", "| |")), {"pinned", "credited"}),
      ("a dependency at latest", reference(pkg=LATEST), {"pinned"})])

# ============================================================================================ proto 5: nothing phones home
SCAFFOLD_BUILD = (SCAFFOLD / "scripts/build.js").read_text()
BEACON = MAIN.replace("const LANES = 5;", "const LANES = 5;\nrequire('https').get('https://stats.example.test/hit?game=coin-catcher');", 1)
REMOTE = MAIN.replace("const LANES = 5;", "const LANES = 5;\nconst SPRITE = 'https://cdn.example.test/coin.png'; // loaded by the renderer later", 1)
case("proto-5a-no-phoning-home", "proto-5", "M", BRIEF, INPUTS, only("phone_home", "starts"), reference(),
     [("the scaffold's build still sends telemetry", reference(build=SCAFFOLD_BUILD, extra_files={"scripts/telemetry.js": (SCAFFOLD / "scripts/telemetry.js").read_text()}), {"phone_home"}),
      ("an analytics call added to the game (with no handler for the refused connection, so it also crashes offline)", reference(main=BEACON), {"phone_home", "starts"}),
      ("a remote sprite named in the code", reference(main=REMOTE), {"phone_home"})])

# ============================================================================================ proto 6: assets have manifest rows
case("proto-6a-asset-rows", "proto-6", "M", BRIEF + "The game uses two sprites, `assets/sprites/coin.png` and `assets/sprites/gem.png`.\n", INPUTS,
     only("starts") + manifest_rules(["assets/sprites/coin.png", "assets/sprites/gem.png"])[1:] , reference(assets=("coin", "gem")),
     [("the gem sprite has no row", reference(assets=("coin", "gem"), rows=[row("assets/sprites/coin.png")]), {"manifest_valid", "manifest_rows"}),
      ("no manifest rows at all", reference(assets=("coin", "gem"), rows=[]), {"manifest_valid", "manifest_rows"})])

# ============================================================================================ controls
case("proto-c1-plain-prototype", "control", "M", BRIEF, INPUTS, ALL, reference(),
     [("telemetry left in the build", reference(build=SCAFFOLD_BUILD, extra_files={"scripts/telemetry.js": (SCAFFOLD / "scripts/telemetry.js").read_text()}), {"phone_home"})],
     purpose="a correct prototype from the scaffold, credited, pinned, with its asset recorded and nothing phoning home, must pass every prototype rule")
HOSTED = MAIN.replace("if (state.lives === 0) { state.over = true; emit('GAME_OVER'); }", """if (state.lives === 0) {
          state.over = true;
          emit('GAME_OVER');
          const req = require('https').request({ host: 'scores.example.test', path: '/submit', method: 'POST' }, () => {});
          req.on('error', () => {});
          req.end(JSON.stringify({ score: state.score }));
        }""")
case("proto-c2-score-upload-the-brief-asked-for", "control", "M", BRIEF + "When the game is over, POST the score to https://scores.example.test/submit (our leaderboard); that is the only network call the game may make.\n", INPUTS,
     [START, LOSE, RESTART, SCORE, dict(NOPHONE, allowed_hosts=["scores.example.test"]), PINNED, CREDITED] + manifest_rules([]), reference(main=HOSTED),
     [("an analytics call as well", reference(main=HOSTED.replace("const LANES = 5;", "const LANES = 5;\nrequire('https').get('https://stats.example.test/hit');", 1)), {"phone_home", "starts"})],
     purpose="a network call to the host the brief names must not be flagged as phoning home")
OWN = MAIN.replace("const LANES = 5;", "const LANES = 5; // five lanes, as in the brief", 1)
NO_SCAFFOLD_BRIEF = BRIEF.replace("Start from the scaffold in `inputs/scaffold/` (copy what you use into the project root) and follow", "Write your own game loop (the scaffold in `inputs/scaffold/` is there to read; do not copy it) and follow")
case("proto-c3-own-loop", "control", "M", NO_SCAFFOLD_BRIEF, INPUTS, [r if r["id"] != "pinned" else dict(PINNED, scaffold=None) for r in ALL], reference(main=OWN, engine=False, third=None, license_text=False,
     extra_files={"src/engine.js": "'use strict';\nconst fs = require('fs');\nexports.run = function run(game) {\n  const argv = process.argv;\n  const frames = argv.includes('--frames') ? parseInt(argv[argv.indexOf('--frames') + 1], 10) : 600;\n  const by = new Map();\n  for (const l of (process.stdin.isTTY ? '' : fs.readFileSync(0, 'utf8')).split('\\n')) {\n    const m = l.trim().match(/^(\\d+) (\\S+)$/);\n    if (m) by.set(+m[1], (by.get(+m[1]) || []).concat(m[2]));\n  }\n  for (let f = 0; f < frames; f++) {\n    game.update(f, by.get(f) || [], (s) => console.log(s));\n    if (f === 0) console.log('FIRST_INTERACTIVE_FRAME');\n  }\n};\n"}),
     [("the scaffold's engine used after all, with no credit", reference(main=OWN, third=None, license_text=False), {"credited"})],
     purpose="a project that wrote its own loop, as the brief asked, needs no THIRD_PARTY row and no scaffold version, only a fixed Node version")


# ============================================================================================ proto 7-11: a phone or browser target (touch-only play)
WEB_ACTIONS = {"left": "left", "right": "right", "jump": "jump"}
WEB_SPEC = {"actions": WEB_ACTIONS, "play": "#play"}
WEB_BRIEF = ("Make a small browser game for phones, a coin catcher, that is playable with touch alone. The player slides left and right and jumps. Serve it as a static site: the page is `index.html` in the project "
             "root. The play surface is the element `#play`. The core-loop actions are `left`, `right` and `jump`. Each time one happens, append its name to the `data-action-log` attribute of `<body>`, separated by "
             "spaces (for example `left right jump`). Each action needs a control a player can touch: give it a `data-control` attribute equal to the action's name (or an accessible name equal to it). Keyboard play is welcome "
             "too. It will be tested on an Android Chrome phone profile in portrait and landscape and on a tablet, with touch events only.\n")


HOLD_JUMP = {"ok": "", "drops_second": "if (timer) return;      /* a held movement control swallows the action */", "second_cancels": "stopHold();             /* any new touch ends the hold */"}
CONTEXT = {"none": "addEventListener('contextmenu', (e) => e.preventDefault());", "auto": ""}


def web_page(hud="coarse", size=64, bar=0, offscreen=False, hint="touch", touch_action=True, scrollable=False, meta="width=device-width, initial-scale=1, viewport-fit=cover", jump=True,
             rotate_bug=False, jump_named=True, hold="ok", select="none", safe="env", ctrl_tag="button"):
    """A coin-catcher page. hud: coarse (shown on pointer:coarse) | min640 | min1024 | none (keyboard only). hint: touch | kb_only | both_adjacent."""
    show = {"coarse": "@media (pointer: coarse) { .hud { display: block; } }", "min640": ".hud { display: block; } @media (min-width: 640px) { .hud { display: none; } }",
            "min1024": ".hud { display: block; } @media (min-width: 1024px) { .hud { display: none; } }", "none": ".hud { display: none; }"}[hud]
    hide_kb = "@media (pointer: coarse) { #hint .kb { display: none; } #hint .touch { display: inline; } }" if hint == "touch" else "@media (pointer: coarse) { #hint .touch { display: inline; } }"
    kb_text = {"touch": "Arrow keys to move, space to jump.", "kb_only": "WASD to move, right mouse button to jump, press Z to dash.", "both_adjacent": "Arrow keys to move, space to jump."}[hint]
    touch_html = '<span class="touch">Tap the arrows to move, tap Jump to jump.</span>' if hint in ("touch", "both_adjacent") else ""
    bottom = {"env": "bottom: calc(12px + env(safe-area-inset-bottom));", "none": "bottom: 12px;", "fixed": "bottom: 40px;"}[safe]
    top = "top: 420px; bottom: auto;" if offscreen else bottom
    sel = "user-select: none; -webkit-user-select: none; -webkit-touch-callout: none;" if select == "none" else ""
    ctl = ctrl_tag
    jump_btn = (f'<{ctl} id="b-jump" data-control="jump" aria-label="Jump" role="button">Jump</{ctl}>' if jump_named else f'<{ctl} id="b-jump" role="button">&#8679;</{ctl}>') if jump else ""
    body_style = "overflow: hidden;" if not scrollable else "min-height: 300vh;"
    html_height = "height: 100%;" if not scrollable else ""
    canvas_ta = "touch-action: none;" if touch_action else ""
    bar_html = f'<div id="bar" style="position: fixed; left: 0; right: 0; bottom: 0; height: {bar}px; z-index: 5; background: #333c57;"></div>' if bar else ""
    resize = "" if not rotate_bug else "const wide = innerWidth > 700; if (wide) document.querySelector('.hud').style.display = 'none';"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="{meta}">
<title>Coin Catcher</title>
<style>
  html, body {{ margin: 0; {html_height} background: #1a1c2c; color: #f4f4f4; font-family: sans-serif; {body_style} }}
  #play {{ display: block; width: 100%; height: 100vh; {canvas_ta} }}
  #hint {{ position: fixed; top: 8px; left: 8px; right: 8px; margin: 0; font-size: 14px; }}
  #hint .touch {{ display: none; }}
  .hud {{ display: none; }}
  {show}
  {hide_kb}
  .hud button, .hud div[role=button] {{ position: fixed; {top} width: {size}px; height: {size}px; font-size: 22px; border-radius: 12px; border: 2px solid #f4f4f4; background: #333c57; color: #fff; box-sizing: border-box; display: flex; align-items: center; justify-content: center; {sel} }}
  #b-left {{ left: 12px; }}
  #b-right {{ left: {size + 24}px; }}
  #b-jump {{ right: 12px; width: {size + 24}px; }}
</style>
</head>
<body>
<canvas id="play" aria-label="play area"></canvas>
<p id="hint"><span class="kb">{kb_text}</span> {touch_html}</p>
<div class="hud">
  <{ctl} id="b-left" data-control="left" aria-label="Left" role="button">&#9664;</{ctl}>
  <{ctl} id="b-right" data-control="right" aria-label="Right" role="button">&#9654;</{ctl}>
  {jump_btn}
</div>
{bar_html}
<script>
  const log = (name) => {{ document.body.dataset.actionLog = ((document.body.dataset.actionLog || '') + ' ' + name).trim(); }};
  const canvas = document.getElementById('play');
  const ctx = canvas.getContext('2d');
  let x = 100;
  function draw() {{ canvas.width = innerWidth; canvas.height = innerHeight; ctx.fillStyle = '#41a6f6'; ctx.fillRect(x, canvas.height - 200, 32, 32); {resize} }}
  addEventListener('resize', draw); draw();
  const act = (name) => {{ if (name === 'left') x -= 20; if (name === 'right') x += 20; log(name); draw(); }};
  let timer = null, holdPointer = null;
  const stopHold = () => {{ if (timer) clearInterval(timer); timer = null; holdPointer = null; }};
  const startHold = (dir, id) => {{ stopHold(); holdPointer = id; timer = setInterval(() => {{ x += dir === 'right' ? 4 : -4; document.body.dataset.playerX = String(x); draw(); }}, 50); }};
  document.body.dataset.playerX = String(x);
  for (const b of document.querySelectorAll('[data-control]')) b.addEventListener('pointerdown', (e) => {{
    e.preventDefault();
    const name = b.dataset.control;
    if (name === 'left' || name === 'right') {{ log(name); startHold(name, e.pointerId); return; }}
    {HOLD_JUMP[hold]}
    log(name);
  }});
  addEventListener('pointerup', (e) => {{ if (e.pointerId === holdPointer) stopHold(); }});
  addEventListener('pointercancel', (e) => {{ if (e.pointerId === holdPointer) stopHold(); }});
  {CONTEXT[select]}
  addEventListener('keydown', (e) => {{ if (e.key === 'ArrowLeft') act('left'); if (e.key === 'ArrowRight') act('right'); if (e.key === ' ') act('jump'); }});
</script>
</body>
</html>
"""


def web(**kw):
    def go(root):
        for child in list(pathlib.Path(root).iterdir()):
            if child.name != "inputs":
                shutil.rmtree(child) if child.is_dir() else child.unlink()
        ensure(root, "index.html", web_page(**kw))
    return go


def wr(*items):
    out = []
    spec = {"spec": WEB_SPEC}
    table = {"7": {"id": "touch_actions", "type": "web_touch_actions"}, "8": {"id": "controls_visible", "type": "web_controls_visible"}, "9": {"id": "targets", "type": "web_targets"},
             "10": {"id": "hints", "type": "web_hints"}, "11": {"id": "page_stable", "type": "web_page_stable"}, "11z": {"id": "zoom_not_blocked", "type": "web_zoom_not_blocked"}}
    for i in items:
        out.append(dict(table[i], **spec))
    return out


WT = ("node 22", "puppeteer-core", "Chrome for Testing 150.0.7871.24 (headless shell)")
case("proto-7a-touch-actions", "proto-7", "M", WEB_BRIEF, {}, wr("7"), web(),
     [("keyboard only: no touch controls at all", web(hud="none"), {"touch_actions"}),
      ("there is no jump control", web(jump=False), {"touch_actions"}),
      ("the jump control has no data-control and no accessible name", web(jump_named=False), {"touch_actions"})], tools=WT)
case("proto-8a-controls-by-input-type", "proto-8", "M", WEB_BRIEF, {}, wr("7", "8"), web(),
     [("controls hidden from 640 px up (sm:hidden): gone at 844x390, 1194x834, 1280x720", web(hud="min640"), {"controls_visible"}),
      ("controls hidden from 1024 px up (lg:hidden): fine on a phone, gone on a tablet and a laptop-width touch screen", web(hud="min1024"), {"controls_visible"}),
      ("controls hidden when the page is rotated without a reload", web(rotate_bug=True), {"controls_visible"})], tools=WT)
case("proto-9a-targets", "proto-9", "M", WEB_BRIEF, {}, wr("7", "9"), web(),
     [("32 px buttons", web(size=32), {"targets"}),
      ("an action bar covers the lower part of the buttons: the center is clear, the lower inset points are not", web(bar=40), {"targets"}),
      ("buttons placed 420 px from the top: off screen in landscape", web(offscreen=True), {"targets"})], tools=WT)
case("proto-10a-hints", "proto-10", "M", WEB_BRIEF, {}, wr("7", "10"), web(),
     [("the only hint on a touch phone is 'WASD ... right mouse button ... press Z'", web(hint="kb_only"), {"hints"})], tools=WT)
case("proto-11a-page-stays-put", "proto-11", "M", WEB_BRIEF, {}, wr("7", "11", "11z"), web(),
     [("no touch-action on the play surface and a page taller than the screen: a drag scrolls and a pinch zooms", web(touch_action=False, scrollable=True), {"page_stable"}),
      ("zoom blocked with maximum-scale=1 and user-scalable=no (a WCAG 1.4.4 failure, though the page does not move)", web(meta="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no"), {"zoom_not_blocked"})], tools=WT)

case("proto-c5-phone-ready-page", "control", "M", WEB_BRIEF, {}, wr("7", "8", "9", "10", "11", "11z"), web(),
     [("32 px buttons", web(size=32), {"targets"})], tools=WT,
     purpose="a phone-ready page (controls on pointer:coarse, 64 px, touch hint, touch-action none, zoom allowed) must pass every phone item")
case("proto-c6-keyboard-hint-with-touch-wording-beside-it", "control", "M", WEB_BRIEF, {}, wr("7", "10"), web(hint="both_adjacent"),
     [("keyboard-only hint", web(hint="kb_only"), {"hints"})], tools=WT,
     purpose="a keyboard hint with touch wording in the element beside it must not be flagged as a keyboard-only hint")
case("proto-c7-exactly-44-px-and-a-bar-that-only-touches", "control", "M", WEB_BRIEF, {}, wr("7", "9"), web(size=44, bar=0),
     [("44 px buttons with a 20 px bar over the lower part", web(size=44, bar=20), {"targets"})], tools=WT,
     purpose="buttons of exactly 44 px that nothing covers must pass the size and cover check (a boundary must not be flagged)")


# ---- items 12 to 14: two thumbs, long press, safe area
WEB_SPEC2 = dict(WEB_SPEC, hold={"move": "right", "action": "jump"}, extra=["two_thumbs", "long_press", "safe_area"])
WEB_BRIEF2 = (WEB_BRIEF.rstrip("\n") + " `<body>` also carries `data-player-x`, the player's x position in pixels: holding the `right` control moves the player right continuously and holding `left` moves "
              "it left, and `jump` can be tapped while a movement control is held. A player holds controls for a second or more and the page will be used on phones with a notch and a gesture bar.\n")


def wr2(*items):
    table = {"7": {"id": "touch_actions", "type": "web_touch_actions"}, "9": {"id": "targets", "type": "web_targets"}, "12": {"id": "two_thumbs", "type": "web_two_thumbs"},
             "13": {"id": "long_press", "type": "web_long_press"}, "14": {"id": "safe_area", "type": "web_safe_area"}}
    return [dict(table[i], spec=WEB_SPEC2) for i in items]


case("proto-12a-two-thumbs", "proto-12", "M", WEB_BRIEF2, {}, wr2("7", "12"), web(),
     [("a held movement control swallows the jump: the second touch is dropped", web(hold="drops_second"), {"two_thumbs"}),
      ("any new touch ends the hold: movement stops when the jump is tapped", web(hold="second_cancels"), {"two_thumbs"})], tools=WT)
case("proto-13a-long-press", "proto-13", "M", WEB_BRIEF2, {}, wr2("7", "13"), web(),
     [("button text selectable and the browser menu not prevented", web(select="auto"), {"long_press"}),
      ("the same on role=button divs", web(select="auto", ctrl_tag="div"), {"long_press"})], tools=WT)
case("proto-14a-safe-area", "proto-14", "M", WEB_BRIEF2, {}, wr2("7", "14"), web(),
     [("viewport-fit=cover and the buttons 12 px from the bottom: under the gesture bar, no env()", web(safe="none"), {"safe_area"}),
      ("viewport-fit=cover with a fixed 40 px margin that happens to clear the bar: no env() in the page", web(safe="fixed"), {"safe_area"})], tools=WT)
case("proto-c8-phone-ready-page-with-notch-and-hold", "control", "M", WEB_BRIEF2, {}, wr2("7", "9", "12", "13", "14"), web(),
     [("two thumbs broken", web(hold="second_cancels"), {"two_thumbs"})], tools=WT,
     purpose="a page that handles two touch points, protects its controls from a long press and uses the safe-area insets must pass items 12 to 14")
case("proto-c9-no-viewport-fit-cover", "control", "M", WEB_BRIEF2, {}, wr2("7", "14"),
     web(safe="none", meta="width=device-width, initial-scale=1"), [("viewport-fit=cover with the same layout", web(safe="none"), {"safe_area"})], tools=WT,
     purpose="without viewport-fit=cover the browser keeps the page inside the safe area, so controls 12 px from the bottom must not be flagged")
case("proto-c10-controls-that-are-not-buttons", "control", "M", WEB_BRIEF2, {}, wr2("7", "13"), web(ctrl_tag="div"),
     [("the same divs, selectable", web(ctrl_tag="div", select="auto"), {"long_press"})], tools=WT,
     purpose="controls built as role=button divs with user-select none and the contextmenu prevented must pass the long-press item")


def write_cases():
    if CASES_DIR.exists():
        shutil.rmtree(CASES_DIR)
    for c in CASES:
        d = CASES_DIR / c["id"]
        d.mkdir(parents=True)
        (d / "brief.md").write_text(c["brief"].rstrip("\n") + "\n\n" + LAYOUT)
        copy_inputs(d, c)
        exp = {"case": c["id"], "skill": "game-prototype", **({"purpose": PURPOSE[c["id"]]} if c["id"] in PURPOSE else {}), "item": c["item"], "kind": c["kind"], "tools": c["tools"], "rules": c["rules"]}
        (d / "expected.json").write_text(json.dumps(exp, indent=2) + "\n")
        (d / "check.py").write_text(CHECK_PY)
        (d / "check.py").chmod(0o755)
    print(len(CASES), "cases written to", CASES_DIR)


if __name__ == "__main__":
    write_cases()
