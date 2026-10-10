// mini-scaffold engine. MIT License, Copyright (c) 2025 Mini Scaffold Authors (see LICENSE).
'use strict';
const fs = require('fs');

function parseArgs(argv) {
  const args = { headless: false, frames: 600 };
  for (let i = 2; i < argv.length; i++) {
    if (argv[i] === '--headless') args.headless = true;
    else if (argv[i] === '--frames') args.frames = parseInt(argv[++i], 10);
  }
  return args;
}

// Input script on stdin: one `FRAME ACTION` per line (e.g. `55 left`). Several lines may share a frame.
function readInputs() {
  const byFrame = new Map();
  if (process.stdin.isTTY) return byFrame;
  let text = '';
  try { text = fs.readFileSync(0, 'utf8'); } catch (e) { return byFrame; }
  for (const line of text.split('\n')) {
    const m = line.trim().match(/^(\d+)\s+(\S+)$/);
    if (!m) continue;
    const f = parseInt(m[1], 10);
    if (!byFrame.has(f)) byFrame.set(f, []);
    byFrame.get(f).push(m[2]);
  }
  return byFrame;
}

// game = { update(frame, actions, emit) }. Runs `frames` fixed steps. The first frame that accepts input is frame 0:
// the engine prints FIRST_INTERACTIVE_FRAME right after it.
function run(game) {
  const args = parseArgs(process.argv);
  const inputs = readInputs();
  const emit = (line) => console.log(line);
  for (let f = 0; f < args.frames; f++) {
    game.update(f, inputs.get(f) || [], emit);
    if (f === 0) emit('FIRST_INTERACTIVE_FRAME');
  }
}

module.exports = { run, parseArgs };
