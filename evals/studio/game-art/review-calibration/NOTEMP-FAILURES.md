# No-temperature batch and compatibility preflight: failure list first

- Register the fallback before implementation; omit only temperature, keep seed zero,
  model, caching off, 16x views, questions, floors, pairs, order and 116-request limit.
- Explicitly give up determinism; the three repeats measure variability rather than
  assuming that a seed alone establishes deterministic provider behavior.
- A compatibility preflight is exactly one minimal text-only request, never an image,
  retry, silent fallback or batch. Its token usage and estimated cost must be recorded;
  a minimal check is not a guarantee of zero provider billing.
- A paid run requires a successful preflight receipt for this exact registered model,
  settings, run-list hash and source commit; rejected, modified, stale-source or missing
  preflight evidence must refuse before credential intake or batch requests.
- Preserve the $1 stop including preflight spend; never borrow another model's rate.
- On any stop preserve HTTP status when available and a bounded error type/message
  from the provider's error object, in events and receipt. Do not retain request bodies,
  unrelated response fields, headers, URLs, arbitrary local exception text or keys.
- Scan raw and decoded error fields for keys. A key-bearing error produces an incident,
  suppresses data artifacts and exposes only a fixed redacted diagnostic.
- Non-JSON, malformed, oversized and missing error bodies must still explain the stop
  through a fixed diagnostic and HTTP status without inventing provider text.
- Preflight HTTP rejection, model mismatch, refusal, invalid/missing usage or non-text
  reply cannot authorize a batch. A compatibility success is not a calibration pass.
- Ordinary reviewer transport must keep its previous temperature-zero default.
- Tests first for both error recording and preflight, using synthetic transports only;
  no key access, provider/model call or paid batch by the author. Independent review
  and operator execution remain required. Historical registrations stay unchanged.
