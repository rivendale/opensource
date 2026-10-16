# Model comparison: cost projection method and stop test

Written before any run of the comparison in `model-comparison-plan.md`. It fixes how the cost is projected and when the $25 stop applies. It asserts no price: the rates come from the runner's dated
table (`RATES` and `RATES_DATE` in `skills/studio/runner/cache_api.py`, lines 9 to 12, which lives in the prompt-caching change and is **not merged yet**; until it merges there is no rate table in the runner and the run list must carry its own dated copy of these numbers),
which is the operator's assumption of the provider's published list and is recorded in every receipt.

## Cost of a run

`cost = (uncached_input * r_in + cache_write_5m * r_w5 + cache_write_1h * r_w1 + cache_read * r_read + output * r_out) / 1,000,000`, from the counters in the run's receipt (each category at its own rate). With caching off the
write and read terms are zero and `uncached_input` is the whole prompt. A model with no entry in the table is unpriced and stops the batch; nothing borrows another model's rate. Thinking tokens, when present, are output tokens.

## The projection written into the run list (before run 1)

The run list states three numbers per model, each computed from the receipts and the dated rates:

| | how it is chosen |
|---|---|
| expected | median prompt tokens per run of the earlier pilots (264,000 over the 11 runs listed below; the minimum was 148,000) and the completion share they showed (about 2.3% of prompt tokens, from the only run whose split was read: 4,671 of 205,207), at that model's rates |
| high | the largest earlier run (459,000 prompt tokens) at the same completion share |
| worst | the 600,000-token cap with the same completion share |

The eleven runs behind the median (total tokens per run, prompt plus completion as the runner recorded them; the first three are in `pilot-2026-10-12-tally.md`, the other eight are the `usage.total_tokens` of the second pilot's `result.json` files, which the operator holds and the reading host copied; the tally lists no token count for them): 205,207 (art-1a); 289,702 and 297,428 (two all-1a gems); 186,117, 148,105 and 202,847 (the three empty-root rebuild runs); 257,406, 334,679, 263,738, 270,290 and 459,046 (coin, key, potion, coin, key). Sorted: 148,105; 186,117; 202,847; 205,207; 257,406; 263,738; 270,290; 289,702; 297,428; 334,679; 459,046. The median is the sixth, 263,738, shown as 264,000. These are totals, so the prompt share is slightly smaller than the figure used; the effect is under 3%.

Total = 8 runs x model A + 8 runs x model B for each row. **A reading that needs Nick:** the run list goes to him before any run if the *expected* total exceeds $25. The *high* and *worst* totals are shown so the stop is not a surprise; they do not by themselves block the run list.

## Illustration, caching off, same tokens for both models (Estimate; rates as in the runner's table dated 2026-10-14, not verified by the author)

| per run | Sonnet 4.5 | Opus 5.5 |
|---|---|---|
| expected (264k prompt, 6k output) | $0.88 | $1.18 |
| high (459k, 10.5k) | $1.54 | $2.05 |
| worst (600k, 13.7k) | $2.0 | $2.7 |

16 runs: expected about **$16.5**, high about **$28.7**, worst about **$37.6**. Opus 5.5 may use fewer turns or more thinking tokens than Sonnet 4.5; the same token count for both is an assumption the first pair replaces.

If only the fixed operator prefix is cached (the opt-in change), the prefix is about 60% of the cumulative prompt tokens in the earlier pilots (average context about 9k tokens per turn, prefix about 5.5k) [Estimate]; at read rates the expected run falls to roughly $0.48 (Sonnet) and $0.60 (Opus), about $8.6 for 16. That depends on the cache reaching its minimum length, the five-minute lifetime not lapsing between turns and the prefix share the receipt will show; the receipt's own counters replace this estimate.

## The stop test, applied while running

1. **After the first pair** (coin on Sonnet, coin on Opus) recompute: `projected = 8 * cost_sonnet_first + 8 * cost_opus_first`, each multiplied by 1.25 for variation between cases. If `projected > $25`, stop and take it to Nick before the third run.
2. **After every run:** `spent + remaining_runs * max(cost of that model so far) > $25` pauses the batch and goes to Nick with the figures; it does not stop by itself while the projection from the *median* so far is under $25.
3. **Hard stop:** actual cumulative cost from the receipts reaches $25. The run in progress finishes only if the per-run cap allows; otherwise it is abandoned and recorded.
4. A run over the 600,000-token cap is a stop of that run, not a reason to raise the cap. Raising it is Nick's decision.

Cache reads count in the per-run token cap (the runner records `prompt_tokens` as uncached plus writes plus reads), so the cap keeps its meaning with or without caching.

## Schedule constraint

The promotional credit named in the task row expires on 27 October (UTC). The calibration batch, the model comparison and any follow-up must fit before it; the schedule is the operator's, and a stop under this method never extends a budget.
