# Prompt-cache compatibility checks (2026-10-18)

The first OFF receipt compared bytes with expected JSON serialization, not a running main version. The new test executes pinned main and candidate code in separate subprocesses and compares the upstream payload hashes, lengths, headers, status and response for each scenario. Its default mode uses the actual Unix relay. `--handler-only` instead executes the real HTTP handler against in-memory input/output and a synthetic upstream, with no socket or provider. These modes are distinct evidence.

The local sandbox previously refused Unix socket binding; that action was not retried. Six **direct-handler** comparisons passed against main `350a45c62151c36ff310b5a513847386fcc1f6c9` (tree `c0dc5ec289ad33afe214fdadfe7be444c9f7449f`): first writer turn, tool history, UTF-8 expansion, oversized input, and reviewer requests with 128/256 output limits. The local archive used a reconstructed snapshot whose full Git tree was verified equal to that upstream tree. The calibration driver and its shared intake/output scanning helpers from that main revision are integrated unchanged. The old claim that current main has the same relay blob as `6f727a7` is withdrawn: main now factors output scanning into `Relay.output_has_key`.

The independent reviewer reported six real Unix-relay comparisons against both `6f727a7` and `350a45c`, and a sorting mutation that detected changed OFF request bytes (review received 2026-10-18). Those are reviewer-reported results, not local socket evidence. The client harness now catches `BrokenPipeError` during request transmission so it can read the relay's early 413 response; other errors still propagate. This client error is separate from the earlier local bind refusal. The older container receipt describes its original hashes, not this revision. Refreshed isolation/container evidence remains required before paid native-cache use.

The UTF-8 test first reproduced a regression: an input below the existing byte limit expanded during JSON serialization, main forwarded it, but the candidate returned 413 with caching OFF. The new post-conversion check is now limited to native model conversion. The existing incoming body limit is unchanged in both modes. An eighth native-block test proves that native expansion still refuses before upstream I/O. No real key is used by any test.

```sh
python3 skills/studio/runner/tests/cache_compat.py --receipt /tmp/cache-compat.json
python3 skills/studio/runner/tests/cache_consumers.py
python3 skills/studio/runner/tests/cache_blocks.py
```

The first command needs permission to bind a temporary Unix socket. If refused, stop that command and retain the refusal; `--handler-only` provides narrower unit evidence, never a relay or isolation receipt. Before paid use, the owner must run the full relay test on an approved host and refresh the image/isolation receipt.

## Result consumers

A tracked source search for `result.json`, `usage.json`, `prompt_tokens`, `completion_tokens`, `total_tokens`, and usage reads identified the following repository paths. This is a repository audit, not a claim about untracked operator scripts or other repos.

| Consumer | Additive-field behavior | Evidence |
|---|---|---|
| `agent.py` | OFF retains the original three-counter aggregate and nonnegative-integer validation; native responses accumulate eight categories | Actual agent main with legacy and native mock responses, including legacy inconsistent totals |
| `cache_api.py` | Normalizes the eight counters; estimates and tariff metadata are output fields | Legacy/extended equality and malformed-counter fixtures |
| `reviewer.py` | OFF returns exactly the original three keys and retains its sum check; native responses validate eight categories | Actual legacy/native response parser plus full calibration collection/batch tests |
| `run.py` event aggregation and result receipts | OFF keeps the three keys, original integer validation, and no tariff metadata or `prompt_cache` result key; native mode adds eight categories, tariffs and cache policy | Actual OFF/native parsing and receipt tests; full host/container aggregation remains the older receipt until rerun |
| `run.py` failure captures | Serializes usage and result without enforcing a usage key set | Actual failed_capture round-trip, including tariff URL/date |
| `common.py` and `supervisor.py` capture transport | Bounded JSON/opaque protected file bytes; no fixed usage field set | Actual frame codec and source audit; full container transfer not rerun |
| `selftest.py` checker | Requires protected files; does not interpret usage fields | Actual synthetic checker run with extended usage |
| `replay.py` and `evals/studio/replay_local.py` | Transport opaque captured files / create empty synthetic usage; do not tally counters | Source audit; no new replay-container claim |
| Runner fixture readers | Select fields rather than require an exact usage key set | Source audit and executed offline cache/reviewer suites |
| `evals/studio/game-art/review-calibration/driver.py` | Requires exactly three reviewer usage keys; cache remains disabled by its fixed settings | Actual full mock collection (8 tests) and disk batch (7 tests) pass; all driver suites and mutations run against the combined tree |
| `pack_lib.py`, checker libraries, calibration scorer | Bundle metadata, delivered assets/transcript or separate calibration records; no usage/result schema consumer found | Tracked source search and source audit |
| External operator tally/checkpoint scripts | Not present in this snapshot | Not verified; no compatibility claim outside the tracked repository inventory. |

No compatibility claim is made for arbitrary future consumers that reject unknown keys. Unknown model prices remain unpriced. Per-run write/read counters remain separate so cross-run cache reuse can be recognized; costs are estimates, not an invoice or independent cold-run costs.

## Native protocol and live limits

The writer output ceiling is 32768; the reviewer keeps 128/256. Native sampling and thinking use provider defaults; compatibility mode retains temperature zero and seed zero. These settings must be named in any later calibration/comparison registration. Provider identity, real usage fields, live caching and reviewer-sized default-thinking output remain unmeasured. A probe proposal on the PR has not been executed.

Caller text and native-history cache markers now explicitly refuse. Tests cover both, malformed-type signatures and unknown blocks with retained usage, and raw synthetic keys inside thinking/tool input. String signatures are round-tripped, not cryptographically validated locally; provider validation is a separate boundary. No signature authenticity is claimed by the fixtures.

Tariff source: [Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing), rechecked 2026-10-16. The plan now includes the one-hour rates already in the implementation; receipts carry the source URL and date.
