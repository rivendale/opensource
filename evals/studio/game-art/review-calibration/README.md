# Review calibration set

A control set for the **model reviewer** that the studio runner can put in front of a game-art delivery: a fresh-context model that first names what it sees in two native-size
renders (no brief, no subject word), and then answers subject-free yes/no questions about them. Before such a reviewer is allowed to gate a run, it should be shown to be right about
images whose answers are known. This directory holds those images, the answers, a scorer with absolute floors, and a selfcheck that proves the scorer can fail. It makes no model call.

The images and `answers.json` name the subjects (coin, key, potion, heart, mushroom, boot). They belong with the evaluation cases and must never be copied into a skill directory,
a brief, or anything a writer model can read.

## The set (14 images, `images/`, neutral 8-hex names, pixel-exact PNG with no ancillary chunks)

| kind | n | what it is | the answer that does not come from a model |
|---|---|---|---|
| reference | 3 | the three leg-1 reference icons | the drawer's name |
| non-subject | 3 | a heart, a mushroom, a boot, drawn for this set | the drawer's name |
| packet | 5 | the five images of the first blind packet of the follow-up pilot (`source/`) | two human readers' verdicts: 2 yes, 3 no (the second reader saw the first's names before opening the packet, so the agreement is not independent) |
| wrong | 3 | a flat blue square, an empty picture, random noise | none of these depicts anything |

Six subject-free questions (`answers.json`, `questions`) are asked of every image. Their answers are **computed from the pixels** (dark outline round the whole shape, any part touching the
picture edge, at least three non-outline colours, lower-right half darker than upper-left, a single flat colour, a left-right mirror image), so they are ground truth, not opinion. The selfcheck
recomputes them from the stored images and requires each question to be true for at least two images and false for at least two.

## Floors (absolute, in `score.py`)

Each image is answered `>= 3` times (repeats), and a name or answer counts when more than half of the repeats agree.

| rule | floor |
|---|---|
| `records` | every image answered, the same number (>= 3) of repeats numbered from 0, well-formed records |
| `names_drawn` | at least 5 of the 6 drawn icons named correctly (whole-word match to the accepted words; a negation makes it a miss) |
| `packet_agree` | the reviewer's yes/no on the 5 pilot images agrees with the human yes/no on at least 4 |
| `packet_false_yes` | at most 1 of the 3 human-no images named as its intended subject |
| `wrong_named` | none of the 3 wrong images named as a known object |
| `feature_all` | at least 0.85 of the 84 answers equal the pixel truth |
| `feature_each` | at least 0.70 on every one of the six questions |
| `stable` | at least 0.90 of the (image, field) cells identical across repeats |

A reviewer that meets every floor has shown that, on these 14 images, it names and answers like the ground truth. It has **not** shown agreement with humans beyond five images and two readers, accuracy on
other subjects or larger art, or independence from the writer (the reviewer uses the same pinned model).

## How it could fail (written before the scorer), and what stops it

1. **The scorer cannot fail.** The selfcheck runs 2 reviewers that answer correctly and 9 with known defects (all-yes, all-no, always names the intended subject, generic names, names shifted by one image, one question
   backwards, flips on repeat 2, calls the human-no images yes, names the wrong images as objects) and 4 broken record sets (a missing image, a duplicated repeat, two repeats, 0/1 instead of booleans);
   each must fail exactly the listed floors, and every floor must be failed by at least one of them.
2. **A floor passes because nothing was measured.** Each question is balanced on the set (so answering all one way scores about 0.45 or 0.55, below 0.85); a missing or malformed record fails closed and
   every other rule reports "not measured" instead of passing.
3. **The name matcher is too generous or too strict.** Whole words only ("coincidence", "monkey", "keyboard" do not match), simple plural stemming, and any negation ("not a key") is a miss; the selfcheck lists
   positives and negatives. Near-miss words are recorded in the key but a near-miss is never a yes.
4. **A question leaks a subject.** The selfcheck refuses any question containing a subject word or its stem. The lexical guard is weaker than a human reader; the questions here are simple enough to read.
5. **The answer key is wrong.** Feature truth is recomputed from the stored pixels on every selfcheck; the file names are hash-derived; the human names for the pilot images are stored with their provenance.
6. **The images leak the subject.** No ancillary chunks (no text), neutral names, nothing under a skill directory.
7. **A lucky run passes.** Three repeats, a strict majority, and the stability floor; a tie is "unstable", which no floor counts as correct.
8. **Overfitting to five images.** The five pilot images are only one third of the set, the drawn icons and wrong images have their own floors, and the README states what five images and two readers can show.
9. **The render path differs from the real one.** The operator must feed each image through the same `reviewer.neutral_views` as a run; scoring a different render would calibrate a different reviewer.
10. **Silent count drift.** `records` compares the image count answered against 14 and every image's repeat count against the others.

## How to use it (operator)

1. For each file in `answers.json` and each repeat `0..2`, render the image with the runner's `reviewer.neutral_views` and run the blind-name request, then the six questions in `questions` order,
   on the pinned reviewer model with the same settings as a run (a new grant covers the model calls: 14 images x 3 repeats x 2 requests, about 84 requests).
2. Write the answers as a list of `{"image": "images/<hex>.png", "repeat": n, "name": "...", "features": [six booleans]}` and run `python3 score.py records.json`.
   Exit 0 means every floor is met, 1 that a floor is missed, 2 that a file could not be read; the output is `{"case", "rules": [{"id","pass","measured","threshold"}]}`.
3. `python3 selfcheck.py` (numpy and Pillow) checks the set and the scorer with no model call; `python3 build_set.py` regenerates `images/` and `answers.json` byte for byte.


## Committed batch driver

[driver.py](driver.py) implements the fixed 58-pair, 116-request [run list](RUN-LIST-8x.md).
The [specification](DRIVER-SPEC.md) and [failure list](DRIVER-FAILURES.md) define its stops.
Offline planning needs no credential or network:

```sh
python3 driver.py --dry-run
```

Live execution belongs to the operator after independent review and the separate paid-run approval.
The operator supplies the existing runner's inherited descriptor mapping; the driver and runner
share `common.read_key_fds`. Key values never belong in arguments. The following describes the
interface only; FD 3 must already be inherited through the operator's approved credential lane:

```sh
python3 driver.py --run --output runs/calibration-20261016 --baseline previous/records.json --key-fds '{"api.anthropic.com":3}'
python3 driver.py --verify runs/calibration-20261016
```

The parent output directory must exist; the run-id directory must be new. Execution requires committed,
unchanged tracked runner/calibration sources, with no untracked importable code in those trees. The source preflight runs before runner imports; untracked bytecode also refuses. There is no resume or overwrite mode. Records retain their
strict four- and six-key schemas. Each event and receipt carries the directory's run ID. The receipt hashes
all other outputs; its own hash is returned separately because a file cannot contain its own SHA-256.
Verification rejects a copied-in file, changed inventory, changed bytes or a foreign event run ID.

`complete` means all 116 requests, disk reconstruction, unchanged scorer and batch comparison finished,
and the receipt was verified. A missed scorer floor remains `score_exit: 1`; it does not become a pass.
The driver always leaves `review_gate: false`. Partial batches are not scored. An incident suppresses
records and events; an incident receipt contains only metadata. If even that metadata matches the key
scan, no receipt is written. Write failures return a partial report and never claim completion.

Run the offline checks in `tests/test_driver_plan.py`, `tests/test_driver_entry.py`,
`tests/test_driver_persist.py`, `tests/test_driver_collect.py`, `tests/test_driver_batch.py`,
and `tests/driver_mutants.py`. The rendered suites require the same ImageMagick `convert`
used by the reviewer. `tests/test_driver_fixture.py --fixture PATH` checks the operator-held first batch
without changing its scorer outcome; no path means an explicit `fixture absent` status.
The small synthetic fixture and checksums are public; raw first-batch outputs remain operator-held.

CI requires the actual reviewer renderer and runs every rendered suite without an optional skip. A missing `convert` fails the job. No dependency download is configured in this offline workflow.
