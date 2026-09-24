# Board and card playbook

Abstract board games (chess, Connect Four), card games (solitaire, trick-taking, collectible and
deck-building), dice games and virtual tabletops. The full list of 34 projects, with license and
activity, is in [../catalog/board-card.md](../catalog/board-card.md). The catalog's genre mapping
put several of the strongest references under strategy, so this playbook also draws on
[../catalog/strategy.md](../catalog/strategy.md). Every project named here was checked against its
repository on 2026-09-23; reuse classes are quoted as the catalog states them (`copy`, `library
use`, `study only`, `check first`).

## 1. What defines the genre

**Core loop:** read the public state and your private hand, choose one legal move, let the rules
resolve it (with any draw or roll), pass the turn. Every decision is discrete and can be written
down, which makes these games the easiest genre to test, replay and put online.

**Player verbs:** draw, play, discard, place, move, capture, bid, trade, roll, pass.

**Win and lose:** checkmate or capture a key piece, connect a line, reach a point total, empty your
hand, be the last player standing, or hold the most points when the deck runs out. A draw is a real
outcome and needs its own rule (repetition, stalemate, turn limit).

Decide early which kind you are building, because it changes the AI and the netcode:
- **Perfect information, no chance** (chess, Connect Four): minimax search works, and the client can
  safely hold the whole state.
- **Hidden information or chance** (cards, dice): the server must hide each player's private state,
  shuffles must be seeded and server-side, and a bot needs sampling (Monte Carlo) rather than plain
  minimax.

## 2. The systems to build, in build order

### First playable vertical slice

- [ ] State as plain data: board or zones (deck, hand, discard, table), whose turn, the phase.
- [ ] `legal_moves(state, player)`, and `apply(state, move)` that rejects anything not in that list.
- [ ] Turn order and phases (draw, main, end) as data the flow code reads.
- [ ] A seeded RNG owned by the state for shuffles and dice; never `Math.random` in the rules.
- [ ] Win, lose and draw checks after every move.
- [ ] Hotseat play for two players, hiding each hand behind a "pass the device" screen.
- [ ] A random-move bot that plays through the same `apply` as a human.
- [ ] A move log: the initial seed plus every move reproduces the game.

### v1

- [ ] Player views: a function that strips everything a player may not see, applied on the server
      before anything is sent (boardgame.io's `src/core/player-view.ts`).
- [ ] Online play with an authoritative server that validates every move, reconnection, and resume
      from the move log. Lobby or invite links.
- [ ] A real bot: minimax with alpha-beta for perfect-information games (c4), Monte Carlo tree
      search for hidden information (boardgame.io's `src/ai/mcts-bot.ts`).
- [ ] Rules content as data or as code, decided on purpose: Forge scripts each card as text, XMage
      writes each card as a Java class.
- [ ] Undo within a turn until the player commits, never after the opponent has seen the move.
- [ ] Save and resume for long games, timers for online games.
- [ ] A rules reference and a tutorial game against a scripted opponent.

### Polish

- [ ] Card movement tweens, hand fanning, drag and drop, hover to enlarge (the Godot Card Game
      Framework's feature list is a good checklist of expected card behavior).
- [ ] Legal-move highlights and a readable game log.
- [ ] Ratings (XMage uses Glicko), spectating, rematch.
- [ ] Localization from v1 (Lichess's interface is in more than 140 languages).
- [ ] Accessibility: keyboard play, screen-reader move announcements (c4 has a dedicated module and a
      Playwright test for it).

## 3. Reference projects to study

`study only` projects are read for design; copy nothing from them
([../ai/README.md](../ai/README.md), "License hygiene").

**[boardgame.io](https://github.com/boardgameio/boardgame.io)**: `copy`, MIT, TypeScript
(cataloged under strategy). "An engine for creating turn-based games": you write moves as functions
and it supplies state sync, multiplayer, storage and bots. Pushed in September 2026. Learn from:
- Turn and phase flow (`src/core/turn-order.ts`, `src/core/flow.ts`).
- Hidden information: `src/core/player-view.ts` and `src/master/filter-player-view.ts`.
- Seeded randomness as a plugin (`src/plugins/plugin-random.ts`) and bots in `src/ai/`
  (`random-bot.ts`, `mcts-bot.ts`). Logs with time travel come built in.

**[c4](https://github.com/kenrick95/c4)**: `copy`, MIT, TypeScript. Connect Four on canvas, pushed
in September 2026. Learn from:
- A clean split into `core/` (rules, players), `browser/` and `server/`.
- Minimax with alpha-beta pruning (`core/src/player/player-ai.ts`); its README notes the evaluation
  function is hard-coded, so the AI is not optimal.
- Modes as separate classes: local, versus AI, AI versus AI, online (`browser/src/game/`), and an
  accessibility module with an end-to-end test.

**[Tabletop Club](https://github.com/drwhut/tabletop-club)**: `copy`, MIT, GDScript on Godot 3
(`config_version=4` in `game/project.godot`). A multiplayer virtual tabletop with physics. Learn from:
- Asset packs: each asset folder has a `config.cfg` whose entries carry `author`, `license` and
  `url` (`assets/TabletopClub/cards/config.cfg`).
- Pieces, stacks and private zones as scripts (`game/Scripts/Game/Pieces/Stack.gd`,
  `game/Scripts/Game/3D/HiddenArea.gd`), and translations through Weblate.

**[XMage](https://github.com/magefree/mage)**: `copy`, MIT, Java (cataloged under strategy). A full
rules engine for Magic: The Gathering with a server, client and AI. Learn from:
- Scale through tests: its README cites about 9000 unit tests and a test mode for setting up game
  situations; every card is a Java class under `Mage.Sets`.
- Hidden information enforced server-side; the README calls it "cheat-proof by design".
- Caution: the code is MIT, but card names, rules text and art belong to the card game's publisher.

**[OpenEtG](https://github.com/serprex/openEtG)**: `copy`, MIT, Rust and JavaScript. An open fork of
the Flash card game Elements. Learn from:
- The game core in Rust compiled to WebAssembly (`src/rs/src/`: `game.rs`, `rng.rs`, `deckgen.rs`,
  `aisearch.rs`, `aieval.rs`) with a fuzzing target in `src/rs/fuzz/`.
- A Rust server over PostgreSQL in `src/rs/server/`.

**[Forge](https://github.com/Card-Forge/forge)**: `study only`, GPL-3.0, Java (cataloged under
strategy). A rules engine for the same card game as XMage, with desktop and mobile clients. Learn
from:
- Cards as a small text language: each file in `forge-gui/res/cardsfolder/` declares cost, types and
  abilities (`A:SP$ Token | TokenScript$ ...`). Compare with XMage's classes before choosing.
- Puzzle scenarios as data (`forge-gui/res/puzzle/*.pzl`) and a separate `forge-ai` module.

**[Lichess](https://github.com/lichess-org/lila)**: `study only`, AGPL-3.0, Scala 3. The chess
server. Learn from:
- Rules kept in their own module (`scalachess`), WebSockets on a separate server (`lila-ws`) talking
  over Redis, engine analysis farmed out to a separate worker network (fishnet).
- A public HTTP API and a free database of every rated game in PGN.

**[PySol Fan Club edition](https://github.com/shlomif/PySolFC)**: `study only`, GPL-3.0, Python
(cataloged under strategy). A large solitaire collection. Learn from:
- Game families as Python modules in `pysollib/games/` (107 files), rules pages as HTML in
  `html-src/rules/`, and several front ends (`pysollib/tk`, `pysollib/kivy`, `pysollib/pysolgtk`).
- Its README asks for a new primary maintainer: popularity is not the same as maintenance.

## 4. Reusable permissive code

| catalog project | reuse class, license | language | use it for |
|---|---|---|---|
| [boardgame.io](https://github.com/boardgameio/boardgame.io) | `copy`, MIT | TypeScript | turn-based state, player views, multiplayer, lobby, MCTS bots; install from npm |
| [c4](https://github.com/kenrick95/c4) | `copy`, MIT | TypeScript | a compact minimax with alpha-beta, and the core/browser/server layout |
| [Tabletop Club](https://github.com/drwhut/tabletop-club) | `copy`, MIT | GDScript | stacks, hands, hidden zones and asset-pack loading for Godot 3 |
| [OpenEtG](https://github.com/serprex/openEtG) | `copy`, MIT | Rust | game-tree search and evaluation for a card game, compiled to WebAssembly |
| [XMage](https://github.com/magefree/mage) | `copy`, MIT | Java | patterns for stack, priority and triggered abilities in a rules-heavy card game |

Not in the catalog; license read from each repository on 2026-09-23 (all would class as `copy`):

| library | license | use it for |
|---|---|---|
| [chess.js](https://github.com/jhlywa/chess.js) | BSD-2-Clause | chess move generation and validation, check, checkmate and stalemate: "everything but the AI" |
| [Colyseus](https://github.com/colyseus/colyseus) | MIT | an authoritative Node.js server with room-based matchmaking, reconnection and delta-compressed state sync; client SDKs for many engines |
| [OpenSpiel](https://github.com/google-deepmind/open_spiel) | Apache-2.0 | search and reinforcement-learning algorithms for perfect and imperfect information games, to build or test a bot offline |

Chess engines worth reading, such as Stockfish (cataloged under strategy), are `study only`, GPL-3.0.
Write your own search, or run an engine as a separate program over its protocol and check what its
license requires when you distribute it. Do not copy its code.

## 5. Engine options (engine-neutral)

| engine | license (catalog class) | fits | trade-off |
|---|---|---|---|
| [boardgame.io](https://github.com/boardgameio/boardgame.io) with React or [Phaser](https://github.com/phaserjs/phaser) | MIT (`copy`) | browser games, online play and bots in weeks | turn-based only; rich animation is up to your view layer |
| [Godot](https://github.com/godotengine/godot) | MIT (`copy`) | desktop, mobile and web card and tabletop games with custom UI | Tabletop Club and the Godot Card Game Framework target Godot 3; porting either to Godot 4 is work |
| [Tabletop Club](https://github.com/drwhut/tabletop-club) as a platform | MIT (`copy`) | publish a game as an asset pack, no code | a physics table: players move the pieces themselves, as at a real table |
| [LibGDX](https://github.com/libgdx/libgdx) | Apache-2.0 (`copy`) | Java on desktop and Android; Forge's mobile client is built on it | code first, no scene editor |
| [MonoGame](https://github.com/MonoGame/MonoGame) | MS-PL and MIT per list (`check first`; its `LICENSE.txt` is MS-PL with MIT-licensed portions) | C#, code-first 2D | you build the UI tooling yourself |

The [Godot Card Game Framework](https://github.com/db0/godot-card-game-framework) is `study only`,
AGPL-3.0. Its card scripting in plain dictionaries is worth reading, but building on it would put
your whole game under the AGPL.

## 6. Assets

Code licenses say nothing about art, card text, rules text or data. Check every asset separately and
give it a row in `THIRD_PARTY.md` ([template](../templates/THIRD_PARTY.md)).

- **[Kenney](https://kenney.nl/assets)**: CC0, no attribution required. Packs that fit: Board Game
  Pack, Playing Cards Pack, Board Game Icons, UI Pack, Interface Sounds.
- **[game-icons.net](https://game-icons.net)**: icons for card abilities and resources under
  CC BY 3.0. Attribution is required.
- **[OpenGameArt.org](https://opengameart.org)**: licenses vary per submission. Tabletop Club's
  standard card fronts are CC0 from there; its card back is CC BY 3.0.
- **[Freesound](https://freesound.org)**: shuffle, deal and dice sounds, each with its own license
  (CC0 through CC BY-NC).

Cautions from the reference projects:
- **Pretend You're Xyzzy** (`copy`, BSD-2-Clause) is a web clone of a party card game. Its code is
  BSD, but its `WebContent/license.html` says the card content is under CC BY-NC-SA 3.0, which rules
  out commercial use. The card database ships in the same repository as the code.
- XMage and Forge implement a commercial card game. Forge's README says it is not affiliated with
  the publisher. The code license covers neither the card text nor the art.
- In many places game mechanics are not protected by copyright, while rulebook text, card text, art
  and names are, and names can be trademarks. Write your own text. This is not legal advice.

## 7. Building it with AI tools

Follow the stage table in [../ai/README.md](../ai/README.md): Claude plans and reviews, Codex
implements one scoped task at a time, Grok reviews blind, a person playtests. What changes here:

| stage | lead | board and card artifact |
|---|---|---|
| design | Claude (plan mode) | `docs/rules.md`: zones, turn structure, every card or piece, every win and draw rule |
| failure list | Claude, attacked by Codex | illegal moves accepted, hidden state leaked, unfair shuffles, games that never end |
| slice | Codex | rules core with `legal_moves` and `apply`, a random bot, hotseat |
| bot | Codex, reviewed by Claude | bot-versus-bot batch results over many seeds |
| rules disputes | Grok and Codex, blind | the rules text, the move log and the rules code, never your reading of it |

Prompts, in build order (fill the angle brackets; one task per Codex run):

```text
1. Rules spec (Claude, plan mode): Read ../opensource/playbooks/board-card.md and
docs/design.md. Write docs/rules.md: zones, setup, turn phases, every move with its
preconditions and effects, every win, lose and draw condition. Number each rule. List
situations the rules do not decide and propose a ruling for each.

2. Rules core (Codex): Implement src/rules/ in <language> with no UI imports: State,
legal_moves(state, player), apply(state, move) that raises on any move not in
legal_moves, and result(state). Shuffles and dice use an RNG stored in State. Add a CLI,
sim --seed N --bots random,random --games 1000, printing wins per seat, draws, the
longest game and any exception. Show one run.

3. Player views and server (Codex): Add view(state, player) that removes every hidden
field. The server sends only views and validates every incoming move with apply. Add a
test client that tries a move for the wrong seat and one that is illegal; show both
rejected. Dump one view per seat for a mid-game state.

4. Bot (Codex): Implement <minimax with alpha-beta | Monte Carlo tree search> that uses
only view(state, bot_seat). Run 500 games against the random bot and 500 against itself;
print win rates and average think time per move.
```

To borrow a design from a `study only` project such as Forge's card scripting, write your own notes
and give a fresh session only the notes (the clean-room prompt in ../ai/README.md).

### Board and card playtest checklist (add to the general one in ../ai/README.md)

- [ ] The server rejects a move for the wrong seat, an illegal move and a replayed old move.
- [ ] Captured network traffic for one seat never contains another seat's hand or the deck order.
- [ ] Over 10,000 seeded shuffles, each card lands in each position about equally often.
- [ ] 1000 bot-versus-bot games finish without an exception, and none exceeds the turn limit.
- [ ] Every win, lose and draw rule in `docs/rules.md` has been reached in a logged game.
- [ ] A player who disconnects and returns sees the same state; the other player was told.
- [ ] Replaying a finished game's seed and move log reproduces its result.
- [ ] A new player finishes a game after the tutorial without asking what a card does.

## 8. Genre-specific pitfalls

- **Trusting the client.** Sending the full state and hiding it in the UI leaks every hand to anyone
  who opens the browser's developer tools. Filter on the server, as boardgame.io's player views and
  XMage's server-side enforcement do.
- **Rules edge cases.** Card interactions multiply. XMage's roughly 9000 tests are the scale a
  rules-heavy game reaches; write a test for every ruling in `docs/rules.md` as you make it.
- **Bad shuffles.** `sort` with a random comparator is biased, and an unseeded RNG cannot be replayed
  or audited. Use a Fisher-Yates shuffle on a seeded RNG kept in the state.
- **Games that never end.** Random bots and some rule sets loop forever. Add repetition and turn-limit
  rules, and cap every simulation.
- **An AI that sees too much.** A bot given the full state plays well and teaches nothing about the
  real game. Give it the same view a human seat gets.
- **Copyleft foundations.** Lichess and the Godot Card Game Framework are AGPL-3.0, Forge and PySolFC
  GPL-3.0: excellent to study, but building on one puts your game under that license.
- **Card text and art you do not own.** See Pretend You're Xyzzy, XMage and Forge above. Mechanics
  can inspire you; text, art and names must be your own.
- **Async multiplayer drop-off.** Long games lose players. Add turn timers, reminders and a rule for
  abandoned games before launch, not after.
