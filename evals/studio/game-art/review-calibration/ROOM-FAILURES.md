# Answer-room fallback: failure list before implementation

- Register the new list before code. Preserve every image, pair, question, floor,
  scale, sampling setting and cache policy; change only the relay answer cap and stop.
- Ordinary reviewers keep their existing 256-token upper bound. Only this explicit
  Opus relay may send 1,024-token requests, for preflight and the 116-request batch.
- Preflight uses the first registered real image pair and the real strict reviewer:
  blind name then features, same conversation, registered 16x views and settings.
- Either rejected, incomplete, refused, unparseable, wrong-model or unpriced answer
  rejects preflight without retry. A second-answer failure preserves known spend
  from both responses and never authorizes the batch.
- Keep both provider response ids and a UTC creation time in the receipt. Missing,
  malformed, duplicate ids, a future time or an age over 24 hours refuse reuse.
- Bind the receipt to this source, run list, pair, view metadata and exact settings.
  A text-only or prior-list receipt cannot authorize this batch.
- Both preflight requests count toward the same $5 stop. Retain strict usage checks,
  redaction and exclusive/hash-checked artifacts. Unknown spend is never zero.
- Partial work is 'could not finish', never a scored floor result. No real provider,
  key, container or model calls by the builder; a separate operator runs it later.
