# 16x calibration batch: run list, written before the batch

This is the exact list for the third calibration batch of the model reviewer. The second batch used 8x views and failed three floors. This batch changes only the enlargement cap, from 8 to 16. The first-stage prompt sentence stays the same: it already describes enlarged views with each source pixel shown as a block.
Nothing here is run by the person who wrote it; the operator runs it and keeps the files below.

## Fixed (the batch is void if any of these differs from the second batch)

| | |
|---|---|
| reviewer model | `claude-sonnet-4-5-20250929` (the pinned model), the same route and key lane as the first batch |
| transport | the OpenAI-compatible route `/v1/chat/completions`, `temperature: 0`, `seed: 0`, **prompt caching off** (the opt-in caching change must not be enabled: it drops temperature and seed and would be a third change) |
| parser | the merged strict reply parser (one bare JSON object or one outer fence) |
| images and questions | the 14 images and six questions in `review-calibration/answers.json`, the 16 leg-1 plan pairs below, in the order below |
| repeats | 3, repeat-major: pair `14 * r + i` for repeat `r` in 0..2 and image index `i` below |
| views | scale `max(1, min(16, 512 // max(width, height)))` = 16, so every 16x16 image becomes 256x256 on mid-grey and on light grey; factor and dimensions recorded per request |
| runner image | a freshly built image from the merged runner, with the isolation self-test passing first (record the image digest) |
| requests | 58 pairs x 2 = 116 requests. Stops: any error, refusal, non-JSON or schema reply, key incident or malformed usage stops the batch with no retry and nothing loosened; a hard stop at 116 requests and at $1.00 |

## Pairs 0 to 41: the scoring set (six questions, `answers.json` order, three repeats)

Pair `p = 14 * r + i`. Each pair is the blind-name request followed by the six-question request in the same conversation.

| i | image | kind | is |
|---|---|---|---|
| 0 | `images/e62f4a63.png` | reference | a coin |
| 1 | `images/a397f5be.png` | reference | a key |
| 2 | `images/244e9266.png` | reference | a potion bottle |
| 3 | `images/bd99ccf4.png` | non-subject | a heart |
| 4 | `images/955cb439.png` | non-subject | a mushroom |
| 5 | `images/87c4c0d8.png` | non-subject | a boot |
| 6 | `images/67c058dd.png` | wrong | a flat blue square |
| 7 | `images/5f70bf18.png` | wrong | an empty picture |
| 8 | `images/b5f7cab6.png` | wrong | random coloured noise |
| 9 | `images/2fd20bc9.png` | packet | a key |
| 10 | `images/31834029.png` | packet | an orange ball |
| 11 | `images/f87d4fa3.png` | packet | a potion bottle |
| 12 | `images/729152ee.png` | packet | a stick or a wand, not a key |
| 13 | `images/b288076c.png` | packet | a large orange disc cropped by the picture, an orange or a sun |

## Pairs 42 to 57: the leg-1 plan pairs (repeat 0; the plan's five questions instead of the six)

| pair | plan (`review-plans/`) | image | is |
|---|---|---|---|
| 42 | `leg-1-coin-pickup.json` | `images/e62f4a63.png` | a coin |
| 43 | `leg-1-coin-pickup.json` | `images/31834029.png` | an orange ball |
| 44 | `leg-1-coin-pickup.json` | `images/b288076c.png` | a large orange disc cropped by the picture, an orange or a sun |
| 45 | `leg-1-coin-pickup.json` | `images/bd99ccf4.png` | a heart |
| 46 | `leg-1-coin-pickup.json` | `images/67c058dd.png` | a flat blue square |
| 47 | `leg-1-coin-pickup.json` | `images/5f70bf18.png` | an empty picture |
| 48 | `leg-1-key-pickup.json` | `images/a397f5be.png` | a key |
| 49 | `leg-1-key-pickup.json` | `images/2fd20bc9.png` | a key |
| 50 | `leg-1-key-pickup.json` | `images/729152ee.png` | a stick or a wand, not a key |
| 51 | `leg-1-key-pickup.json` | `images/244e9266.png` | a potion bottle |
| 52 | `leg-1-key-pickup.json` | `images/b5f7cab6.png` | random coloured noise |
| 53 | `leg-1-potion-pickup.json` | `images/244e9266.png` | a potion bottle |
| 54 | `leg-1-potion-pickup.json` | `images/f87d4fa3.png` | a potion bottle |
| 55 | `leg-1-potion-pickup.json` | `images/955cb439.png` | a mushroom |
| 56 | `leg-1-potion-pickup.json` | `images/87c4c0d8.png` | a boot |
| 57 | `leg-1-potion-pickup.json` | `images/67c058dd.png` | a flat blue square |

## Files to keep

`records.json` (the scorer's four keys only: `image`, `repeat`, `name`, `features`; the scorer refuses any other key), `plan-records.json` (as in the first batch: image, repeat, name, features, plan,
`review_accepted`), `events.jsonl` (every request and reply, with the image hashes, the scale and the dimensions), `receipt.json` (image digest, commit, token counts, spend, `score_exit`), and the scorer's
output whole (`score.py records.json`) with its exit code. The scale and dimensions go in `events.jsonl` and the receipt, not in `records.json`.

## What will be read, and in what order

1. The scorer output and exit code, whole: every floor with its measured value.
2. The blind names against the images, all three repeats, by a person (the first batch's pattern: the model named what survives at 16 px and missed the rest, and misdescribed colours).
3. The per-question table against the pixel truth (the first batch: outline 0.93 and flat colour 1.00 held; edge 0.64, colour count 0.64, shade direction 0.57, mirror 0.71 did not).
4. The plan records against the author's expectations (`review-plans/expectations.json`; first batch 13 of 16).
5. `compare_batches.py OLD NEW`: per image, the name class in each batch and the answers that changed. Reported, never scored.

## Pre-registered reading

- **All floors pass:** record "16x views pass calibration"; the review stays a column, never a gate, until the operator decides otherwise.
- **Some floors still fail:** the next change is the reviewer model, in its own registered batch of this size. The questions and every floor stay fixed. No further enlargement or question change is bundled into that batch.
- **Nothing is called a pass on the number of improved images.** Improvement against the first batch is reported by `compare_batches.py`; the floors are the only threshold.
- **No floor moves** to fit the result.
