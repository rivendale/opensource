# Sonnet 5.5: failure list before implementation

- New run-list/plan material keeps selecting the old default.
- New cost accounting uses launch-day or guessed rates instead of the dated official pricing table.
- Five-minute creation, one-hour creation, cache-read and output counters use the wrong column.
- Unknown model IDs acquire a default price or silently become Sonnet.
- The new-plan helper overwrites an existing registered plan or starts a model request.
- Existing fixed run lists, calibration settings, tallies, receipts and historical model IDs change.
- Synthetic probe/replay behavior gains an implicit live model or credential.

Only new planning fragments use the new default. Actual runs retain explicit model/key/self-test requirements.
No live model call is part of this change.
