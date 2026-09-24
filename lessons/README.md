# Lessons from small games we built

These lessons come from a few small browser and server games we built. Each is a mistake or a
practice that worked, stated for any engine; a named tool or host is only an example.

## Architecture

1. **Deterministic rules, AI at the edges.** Keep scoring, parsing, damage, resources and replays
   in ordinary deterministic code. AI players submit plain text that fixed rules parse; nothing
   they send is executed. Generated art is curated offline; the image API is a build-time tool,
   never a runtime dependency. That makes replays verifiable and lets untrusted agents play at all.
2. **Two implementations need one source of truth.** When an offline client ports the server's
   engine, write the rule down: when they disagree, the server is correct; port the fix. Without
   that rule, a browser table of settings effects drifted from the server's and gave browser
   players on three settings extra energy.
3. **Reject what you do not recognize.** An order plan with a misspelled ruleset version was
   accepted, echoed back, then discarded, because unknown versions were coerced to the default.
   Refuse an unknown version with a reason code instead.
4. **Look for actions that parse, cost, and do nothing.** Three verbs sat in the cost and
   permission tables, so they parsed and were charged, then fell through every dispatch branch.
   Nothing failed, so nothing was logged, and one faction's specialty was inert.
5. **Reset means reset.** A new season rewrote the state file but left the last game's order files,
   so unfiled seats replayed old orders, which looked like computer players declining to act. A
   reset should empty every round directory and print how many it cleared.
6. **Play whole games with bots before tuning.** A 14-round all-bot run found a crash from round 3
   and a season in which five seats scored one point in total: the only scoring verb was banned in
   round 2, and that ban then held the only agenda slot. An A/B run had a player who re-optimized
   each round beat saved defaults by 29% (target: under 20%), because score had one source.
7. **Record a gap instead of improvising a rule.** Where the rules are silent, have the engine log
   a gap and take a documented default. The gaps are the point of a test run.
8. **Choose the smallest stack the game needs.** A turn-based game on a fixed map chose a 2D
   renderer, [pixi.js](https://github.com/pixijs/pixijs) (`copy`), over a framework such as
   [Phaser](https://github.com/phaserjs/phaser) (`copy`), and a fixed map over procedural ones so
   saved strategies like "hold the chokepoint" stay valid. A web export from
   [Godot](https://github.com/godotengine/godot) (`copy`) needs a secure context, so testing from
   another device on the LAN needs TLS.
9. **Make destructive actions impossible, not checked.** When an AI helper edits the world, use
   the engine's operation that only fills empty space, so the server itself refuses to overwrite
   anything a player built.

## Deploying small games

The examples use Fly.io; each lesson has an equivalent on other hosts.

1. **Deploy on merge, with an app-scoped token.** A deploy run by hand from a laptop ships whatever
   sits in that working tree. Deploy from CI on merge with a token that can manage one app only.
2. **Check the site after deploying.** `flyctl deploy` exits 0 for an app with no IP allocated.
   Request the site afterward, with retries: a scale-to-zero app pays a cold start on the first
   request, and one impatient request would call a healthy app broken.
3. **A 200 is not a working page.** A page can return 200 and still be blank: without a trailing
   slash on the path, relative asset URLs resolve one level up and 404. Check the served bytes per
   hostname; two hosts answering 200 would also be true if one file were served to both.
4. **Hosts ignore config they do not recognize.** In `fly.toml`, `restart` is an array of tables,
   `[[restart]]`. Written as `[restart]` it parses, deploys and is ignored. Walk the parsed config
   in a test, and prove the test by breaking that stanza.
5. **Key rate limits on the identity your ingress guarantees.** Behind a proxy or tunnel the socket
   peer is the proxy, so a limit keyed on it puts every visitor in one bucket and one client can
   lock out everyone. Trust a forwarded client header only where your ingress guarantees it.
6. **In-memory state resets on every deploy.** Rate limiters held in memory hand every client a
   fresh budget on each deploy. If you persist them and the keys are client IPs, hash the keys
   first, or the fix writes visitor addresses to disk.
7. **Check that the image holds real files.** Without Git LFS on the build host, tracked files are
   pointer stubs, and the image serves pointer text as PNG and reports success. Fail the build on
   the LFS pointer signature, and make `.dockerignore` an allowlist.
8. **Game servers bring their own networking rules.** Read your host's UDP documentation: some
   require a special bind address (Fly.io documents `fly-global-services`). Pin any protocol bridge
   or proxy to one checksum-verified build; a component that upgrades early can advertise a newer
   protocol than your clients speak.
9. **Restarts interrupt players, so schedule them.** A deploy takes a persistent world offline
   briefly. Pick a low-traffic window and announce restarts in game.

## Secrets and paid resources

1. **Secrets go on stdin, never argv.** `fly secrets set NAME=VALUE` puts the value in process
   arguments, readable from `/proc/<pid>/cmdline`. Pipe it to `fly secrets import --stage` instead.
   That parser is loose (`#` truncates, quotes are stripped, a newline starts an entry), so validate
   each value against what it accepts, and count argv exposures under strace before and after.
2. **`cmd | grep -q` guards fail open.** Under `set -euo pipefail`,
   `if ! fly ... list | grep -q NAME` reads "not found" when grep matches and exits early (SIGPIPE
   fails the pipeline) and when fly hits an auth or network error. Either way a create-if-missing
   script buys a paid volume it already has, or rotates a live secret. Capture, then test the text.
3. **Put paid calls behind a flag.** Runs that call model providers need an operator shell and an
   explicit opt-in such as `--allow-paid-api`. Public routes never read keys or call providers.
4. **Public reads, keyed writes.** Serve public data publicly; require a key for anything that
   changes game state, and prove it with a negative check (a write without the key returns 401).
5. **Harden development tools like production.** Decode a path before validating it, never treat
   forwarded requests as local, and refuse to bind a public interface without a token.

## Testing: prove each check can fail

1. **A control that cannot fail is not a control.** Make every guard in a container entrypoint
   (missing volume, unset token, a child process dying) fire at least once.
2. **Tests written with the code share its blind spot.** A text filter's tests all used bare
   lowercase words, so a change that made it block less passed every one. Vary the inputs the way
   real users type.
3. **Check the tests actually run.** Three regression tests sat after
   `if __name__ == "__main__": unittest.main()`, so a direct run skipped them and said OK.
4. **Test the caller, not only the module.** Disconnecting a chat watcher from the code that
   started it failed no test, because the suite only exercised the watcher module.
5. **Quality gates must be read-only.** A `make qa` that rebuilt images with a non-deterministic
   encoder left modified files on every run. Gates run check modes that change nothing.
6. **Test the failure path.** An offline app cached a 2.9 MB image in the same atomic
   `cache.addAll()` as its shell, so one failed download blocked installation. Cache the shell
   alone, and serve real 404s in an install test. Handle `contextlost` on every canvas, too.
7. **Make invariants computable.** Hash the costs a balance test was measured against, and fail a
   pre-commit hook when they change unmeasured. The first time, it blocked its own author's commit.

## Chat filters and player input

1. **A claimed name is not an identity.** Grant admin rights only from an authenticated identity or
   the server's own operator list, never from a name a player supplies.
2. **Say what a filter guards.** Decide whether a filter moderates player chat or only guards an AI
   call, write that down, and name it accordingly, so nobody mistakes one for the other.
3. **Word lists fail in both directions.** A substring list blocks innocent words that contain a bad
   one and misses creative spellings, and each targeted patch tends to open a new hole. Normalize
   text in ways that only add matches, pair it with an allowlist, and review the allowlist by hand
   (a dictionary-derived allowlist contains slurs).
4. **Transform both sides of every comparison.** Normalizing the message but not the list, or the
   reverse, is a whole class of bug.
5. **Err toward blocking only while a false positive is cheap.** Before an automated alert reaches a
   person, name what a false alarm says and who reads it.
6. **A log watcher notices after the fact.** Players have already seen the message; plan what a
   watcher does (a private reminder, a record for a human) rather than treating it as a block.
7. **Know what no word list can see.** Unkindness in ordinary words, requests for personal details
   and invitations to move to another app need a human or a different mechanism. Decide how you
   handle them before launch.
8. **Count, so silence is readable.** Report notices, failed reminders and failed writes on a
   health endpoint. Zero after a week is either good behavior or a dead watcher.
9. **Treat text other models will read as hostile.** Scan agent-submitted text that other agents
   read for prompt hijack phrasing, narrowly enough to allow strategy prose like "override prior
   orders". Never let a submission change gameplay automatically.

## Building with AI agents in the loop

1. **Confirm the instruction file loads.** A file reached only by a markdown link may never load,
   and two that disagree split your tools. Ask a fresh session something only the file answers.
2. **Machine-merged prose drops meaning.** When instruction files are merged automatically, check
   the result token by token; merges quietly narrow rules and cut words.
3. **Verify commit messages against a run.** One commit said it "also fixed" three cases; none
   were. The message was written from intention.
4. **When every review round finds a new class of bug, change the design.** A filter took five
   rounds of patches before its matcher was restructured, and then the holes stopped.
5. **Ask an outside reader one narrow question.** A reviewer with no repo context, asked only which
   lines trust player-controlled input, found what many rounds of informed review had not.
6. **Check model review against the vendor's reference.** Model reviewers flagged correct
   `[[restart]]` and `[mounts]` stanzas as wrong; the host's documentation settled it.
7. **Inherited automation keeps spending.** Audit the CI of any repository you adopt for jobs that
   still call paid services.
8. **Check what the model recommends.** A top recommendation for an isometric JavaScript library
   was not on npm at all. Check every suggested package and version against its registry.

## Assets and licenses

A code license says nothing about art, audio, maps or data.

- **Register before you process.** Record each third-party file's source URL, author, license,
  size and SHA-256. Download only from an approved list and quarantine raw archives.
- **CC0 first; CC-BY with a credits screen; CC-BY-SA blocked by default** (share-alike reaches
  derived art); CC-BY-NC rules out commercial use. A forum post is not a license: save the
  permission with the files.
- **Buying art may not buy the right to run it through AI.** Some commercial asset licenses forbid
  using the content as AI training or prompt input. CC0 carries no such clause.
- **AI images are strong on single frames and weak on seamless tiles and animation.** Use CC0 or
  modeled geometry for tiles, AI for single pieces, and keep a provenance file per generated image.
- **Copyleft web clients bite hosted games.** [Freeciv-web](https://github.com/freeciv/freeciv-web)
  (`study only`) ships its web client under the AGPL, whose network clause covers a hosted game.
  Study its design; copy none of it.

## Cost

- **Scale to zero when players tolerate a cold start.** Let the machine stop when idle and keep
  state on a volume; verify by restarting and re-reading the state.
- **Stay always-on only when clients need it.** Some game clients cannot wake a stopped machine.
  Treat always-on capacity and larger machines as a cost decision with a named approver.
- **Plan for providers running dry.** When a model provider runs out of credits, disable its rows
  and keep a free scripted baseline enabled, so runs continue without spending.
