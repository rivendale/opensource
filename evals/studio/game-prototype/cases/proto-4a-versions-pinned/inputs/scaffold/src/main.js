// mini-scaffold demo: replace this with your game.
'use strict';
const { run } = require('./engine');
let x = 0;
run({ update(frame, actions, emit) { if (actions.includes('right')) x++; if (frame % 100 === 0) emit('X ' + x); } });
