# Prompt-cache compatibility checks (2026-10-16)

The first OFF receipt compared bytes with expected JSON serialization, not a running main version. The new test executes pinned main and candidate code in separate subprocesses and compares the upstream payload hashes, lengths, headers, status and response for each scenario. Its default mode uses the actual Unix relay. `--handler-only` instead executes the real HTTP handler against in-memory input/output and a synthetic upstream, with no socket or provider. These modes are distinct evidence.

The local sandbox refused Unix socket binding. Six **direct-handler** comparisons passed against main `6f727a790529b1e708a7f6a9bf4314c503f3bca2`: first writer turn, tool history, UTF-8 expansion, oversized input, and reviewer requests with 128/256 output limits. Full Unix relay and a new pinned-container run remain unverified. The rerun includes the already-landed 8x reviewer and host-run changes; pixel/view, context and protocol checks pass in the combined candidate. Current main `8cf7b5c2319fc8405a9d4c85052b133e337f81a9` has the same relay-source blob as the pinned comparison baseline; later main commits change calibration documents and scorer checks. The older container receipt describes its original source hashes, not this revision.

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
| `agent.py` | Validates counters, ignores receipt-only metadata, accumulates all input categories | Actual agent main with mock response, plus protocol fixtures |
| `cache_api.py` | Normalizes the eight counters; estimates and tariff metadata are output fields | Legacy/extended equality and malformed-counter fixtures |
| `reviewer.py` | Normalizes counters before parsing the review | Actual response parser with extended usage; reviewer fixture suite |
| `run.py` event aggregation | Selects `FIELDS`, adds normalized counters; final cumulative event is not added twice | Source audit plus parser test; full host/container aggregation remains the older receipt until rerun |
| `run.py` failure captures | Serializes usage and result without enforcing a usage key set | Actual failed_capture round-trip, including tariff URL/date |
| `common.py` and `supervisor.py` capture transport | Bounded JSON/opaque protected file bytes; no fixed usage field set | Actual frame codec and source audit; full container transfer not rerun |
| `selftest.py` checker | Requires protected files; does not interpret usage fields | Actual synthetic checker run with extended usage |
| `replay.py` and `evals/studio/replay_local.py` | Transport opaque captured files / create empty synthetic usage; do not tally counters | Source audit; no new replay-container claim |
| Runner fixture readers | Select fields rather than require an exact usage key set | Source audit and executed offline cache/reviewer suites |
| `pack_lib.py`, checker libraries, calibration scorer | Bundle metadata, delivered assets/transcript or separate calibration records; no usage/result schema consumer found | Tracked source search and source audit |
| External operator tally/checkpoint scripts | Not present in this snapshot | **Not verified. Owner must name/check these before closing the all-consumer claim.** |

No compatibility claim is made for arbitrary future consumers that reject unknown keys. Unknown model prices remain unpriced. Per-run write/read counters remain separate so cross-run cache reuse can be recognized; costs are estimates, not an invoice or independent cold-run costs.

## Native protocol and live limits

The writer output ceiling is 32768; the reviewer keeps 128/256. Native sampling and thinking use provider defaults; compatibility mode retains temperature zero and seed zero. These settings must be named in any later calibration/comparison registration. Provider identity, real usage fields, live caching and reviewer-sized default-thinking output remain unmeasured. A probe proposal on the PR has not been executed.

Caller text and native-history cache markers now explicitly refuse. Tests cover both, malformed-type signatures and unknown blocks with retained usage, and raw synthetic keys inside thinking/tool input. String signatures are round-tripped, not cryptographically validated locally; provider validation is a separate boundary. No signature authenticity is claimed by the fixtures.

Tariff source: [Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing), rechecked 2026-10-16. The plan now includes the one-hour rates already in the implementation; receipts carry the source URL and date.
