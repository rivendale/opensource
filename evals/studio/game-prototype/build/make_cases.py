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
