# Reviewer model change: failure list before implementation

- Register the fourth batch before driver edits. Change the model only; retain all 58 pairs,
  their order, 16x views, six questions, parser, floors, temperature 0, seed 0 and caching off.
- Pin the new list and model together; refuse a recorded model that differs from the list,
  including a receipt with otherwise valid settings and artifact hashes.
- Preserve the 116-request and $1 stops. Use the selected model's existing cache_api.RATES
  entry for accounting and receipts; never reuse the former model's hardcoded price or add a rate.
- If the provider rejects temperature, seed or any fixed setting, stop after that request.
  Never retry with a setting dropped or silently enable caching/native transport.
- Existing tests and structural/rendered mutants must pass. Add synthetic model-mismatch
  and rejected-setting cases before implementation; no key, provider or model calls.
- Preserve all historical lists, images, questions and floors. A failed fourth batch means
  the next separately registered change is questions, not thresholds, size or another model.
- Keep the review a column, not a gate. Independent review and paid execution are operator work.
