# Operator review plans (leg-1)

One plan per leg-1 case, in the format the runner's `--review-plan` takes: `[{"file", "subject_words", "features"}]`. A plan is the **trusted operator's** statement of what a fresh-context model reviewer
must be asked about an export, after it has named the image blind. It is not an answer key for the checker and it must never be visible to the writer: it lives with the evaluation cases, it is passed to
the runner as a host file, and nothing under `skills/` may quote it. It names the case subjects, so do not copy it into a skill, a brief, or any input.

| plan | file reviewed | questions |
|---|---|---|
| `leg-1-coin-pickup.json` | `assets/ui/coin.png` | 5 |
| `leg-1-key-pickup.json` | `assets/ui/key.png` | 5 |
| `leg-1-potion-pickup.json` | `assets/ui/potion.png` | 5 |

## How they were written

- Each question is one visible property that a reader needs in order to recognise the subject, written without the subject's name or any of its synonyms (the `subject_words` list is what the runner's guard checks;
  it is casefolded, NFKC-normalised, maps common Greek and Cyrillic lookalikes and matches by prefix).
- A question must be answerable by yes or no from a 16x16 render on a grey or light background, and a decent drawing of the subject must be able to satisfy all of them. The reference icons and the pilot
  images the human readers called a key and a potion are the evidence; `expectations.json` records what the author expects of each plan on the calibration-set images, with the reason.
- The questions come after the reviewer has named the image, so they cannot prime its name; they can still hint at the subject ("small blocks sticking out to the side" is a key-like cue). That is intended: they are
  the bar for "recognisable", not a test of naming.
- The coin plan does not require a rim: the reference coin has none, and the pilot's coins failed on a missing mark on the face and on cropping, not on a missing rim.

## What they do not show

`expectations.json` is the author's reading of sixteen image-and-plan pairs (some images appear under more than one plan), not ground truth and not a calibration result. Whether the reviewer answers these questions the way a person does is measured by the live
calibration (a model call, under its own grant); a disagreement there is a finding about a question or about the reviewer, read by a person.

`python3 check_plans.py` checks the plans without a model call (shape, no subject word in any question, a primed question is refused, expectations name real calibration images) and applies the runner's
`validate_plan` from `skills/studio/runner/reviewer.py`; a missing reviewer, an import failure, or a run that applied the validator to fewer plans than exist is a failure.
