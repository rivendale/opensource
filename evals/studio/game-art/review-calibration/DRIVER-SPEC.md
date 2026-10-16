# Calibration batch driver: specification

The first calibration batch was run by an ad hoc driver that is not in the repository; only its output files exist (`records.json`, `plan-records.json`, `events.jsonl`, `receipt.json`). This is the
specification for a committed driver that runs the batch in `RUN-LIST-8x.md` (and any later batch of the same shape), written before the driver. It is the specification, not an implementation:
the driver is built by the owner of the runner and tested offline.

## What it is

A host-side program that, for each pair in the run list, sends the blind-name request and then the feature request in one conversation through the runner's **own trusted reviewer transport**
(`Relay.review_request` and `reviewer.review`), so that key handling, the route allow-list, the key scan, usage validation, the strict reply parser and the view renderer are the code the runs use, not a copy.
It makes no model call of its own, reads no key itself (the key arrives as the runner takes it: an inherited descriptor), and adds nothing to what a run may send.

## Inputs

- the run list (the 58 pairs: 14 images x 3 repeats, then the 16 plan pairs), read from `answers.json` and the plan files, in the order stated in `RUN-LIST-8x.md`;
- the images in `images/`, rendered by `reviewer.neutral_views` (the merged enlargement; the scale is the operator's policy, never an argument);
- the pinned model, host, route and settings, **checked against the run list's fixed table before the first request**: compatibility route, temperature and seed zero, caching off. Any difference voids the batch.

## Outputs (formats fixed by the first batch's files)

| file | content |
|---|---|
| `records.json` | list of `{"image", "repeat", "name", "features"}` and nothing else (the scorer refuses any other key); 42 rows for the scoring set |
| `plan-records.json` | list of `{"image", "repeat", "name", "features", "plan", "review_accepted"}`; 16 rows |
| `events.jsonl` | one JSON object per line: `kind` (`blind-name-request`, `blind-name-usage`, `blind-name`, `features-request`, `features-usage`, `features`), `pair` (0 to 57), `content`, `usage`; requests carry image hashes, byte counts, dimensions **and the scale** (not the pixels); replies are the raw text |
| `receipt.json` | date, source commit, image digest, model, status, requests used, pairs completed, record counts, prompt and completion tokens, spend with the rate table's date and source, key scan, `review_gate`, `score_exit`, and the sha256 of every file above |
| `score.stdout.json` | the scorer's output, whole, and its exit code beside it |

## Stops (each ends the batch; none is retried, loosened or skipped)

An HTTP or transport error; an unparseable or schema-violating reply; a refusal or an empty reply; usage that is missing or inconsistent; a key found in any reply (incident: the tree and records are suppressed, as in a run);
a model identity that differs from the pinned model; a request count about to pass the run list's total; a cost reaching the stated hard stop; an unwritable output file. A partial batch is recorded as partial (`status`, the pairs completed),
never scored as complete, and its records are not mixed into a later batch.

## How it could fail (written before the driver)

1. **It changes a setting silently** (route, temperature, seed, caching, scale) so a batch is not comparable. Stop: the fixed table is checked up front and each request's body is compared with the expected shape; the receipt records the settings.
2. **It sends something the runs would not** (a different instruction, a subject word, the filename, the answer key). Stop: the prompts come only from `reviewer.review`; a test asserts that no request body contains a filename, `answers.json` key or subject word.
3. **It retries or repairs** a bad reply and hides a failure. Stop: no retry path exists; a test injects each bad reply and expects the batch to end at that pair.
4. **Order or count drift:** the wrong order, a repeat missing or doubled, 116 requests promised and 115 or 117 made. Stop: the plan is built first and printed; a dry run asserts the 58 pairs and 116 requests with no network.
5. **Records disagree with the events** (a name or answer in `records.json` that the raw reply does not contain). Stop: records are derived from the recorded replies by the strict parser, and a final check re-derives them from `events.jsonl` and compares.
6. **A key leaks** into a file it writes. Stop: the key scan runs on every output before it is written, and the existing exact-key and pattern scan is used, not a new one.
7. **Cost is misreported** (a wrong rate, a missing category, caching counters ignored). Stop: cost is computed from the recorded counters and the dated rate table, and the receipt names the table's source; an unknown model is unpriced and stops the batch.
8. **It scores or interprets the batch.** Stop: the driver runs the scorer and writes its output; it never edits a record, drops a failed image or changes a floor.
9. **A resumed or repeated run mixes batches.** Stop: the output directory must be new, existing files are never overwritten, and a batch is identified by a run id written to every file.
10. **Consuming-end check missing.** The batch is not finished until `score.py` and `compare_batches.py` have both been run on the files as written, from disk, and their exits recorded.

## Tests required (offline; a mock provider, no key, no network)

A full mock batch reproduces 116 requests in order and writes files that `score.py` and `compare_batches.py` accept; for each stop above, a case that triggers it and expects the batch to end at the right pair with a partial status;
each of the ten failure modes has at least one case that fails when the guard is removed (a mutant, as in `selfcheck.py`); the files from the first batch, as a fixture, pass `score.py` unchanged.

## Not in scope

Any change to the reviewer, the questions, the floors, the run list or the views; a live run (which needs its own go and key lane); any gate.
