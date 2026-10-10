# mini-scaffold 1.2.0 (MIT)

A headless game loop with scripted input, for tests and prototypes.

- `node src/main.js --headless --frames N` runs N fixed steps. Input comes on stdin, one `FRAME ACTION` per line.
- The engine prints `FIRST_INTERACTIVE_FRAME` after frame 0.
- `node scripts/build.js` copies `src/` to `dist/`. By default it sends the package name and the scaffold version to the scaffold authors' server (`scripts/telemetry.js`); `--no-telemetry` skips that.
- License: MIT. Keep `LICENSE` and add the scaffold to your `THIRD_PARTY.md`.
