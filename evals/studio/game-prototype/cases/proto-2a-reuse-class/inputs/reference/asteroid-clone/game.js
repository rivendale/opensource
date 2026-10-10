// asteroid-clone, GPL-3.0-or-later. Study only: this project's reuse class is not `copy`.
'use strict';
function stepRocks(state) {
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
function collide(ship, rocks) {
  return rocks.find((rock) => ship.x < rock.x + rock.size && ship.x + ship.w > rock.x && ship.y < rock.y + rock.size && ship.y + ship.h > rock.y);
}
function applyHit(state, hit) {
  if (!hit) return;
  state.lives -= 1;
  state.invulnerableUntil = state.frame + 90;
  state.flash = 12;
  if (state.lives <= 0) state.mode = 'dead';
}
module.exports = { stepRocks, collide, applyHit };
