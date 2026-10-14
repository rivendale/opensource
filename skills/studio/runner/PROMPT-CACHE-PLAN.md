# Native prompt caching: feasibility and build plan

Documentation checked October 14, 2026. The implementation is opt-in; no live cache hit or cost saving has been
measured. Compatibility behavior has not been empirically probed with a real key.

The OpenAI-compatible endpoint does not support prompt caching. Anthropic's
[compatibility documentation](https://platform.claude.com/docs/en/cli-sdks-libraries/libraries/openai-sdk)
explicitly lists this limitation. Native `/v1/messages` on `api.anthropic.com`
is required for this change.

[Native caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
supports five-minute ephemeral caching with `cache_control`. This runner uses
explicit markers only on the operator-owned system/skill and initial brief,
not automatic breakpoints on growing writer history. Cache
reuse depends on a matching prefix and minimum length: 1,024 tokens for Sonnet
4.5 and 512 for Opus 5.5. Zero cache counters must still complete normally.
Native total input is uncached input plus cache creation plus cache reads.
Retain these categories separately instead of billing their sum at the base rate.

[Standard global rates](https://platform.claude.com/docs/en/about-claude/pricing),
in USD per million tokens:

| Model | Uncached input | Five-minute write | Read | Output |
| --- | ---: | ---: | ---: | ---: |
| Sonnet 4.5 | 3 | 3.75 | 0.30 | 15 |
| Opus 5.5 | 4 | 5 | 0.20 | 20 |

Estimated cost is the sum of each category multiplied by its own rate, divided
by one million. Token limits still count all input categories and output.
Receipt/checkpoint pricing must name its dated tariff; unknown model rates must
remain unpriced rather than silently use another model's rate.

## Protocol work

Keep the sandbox's existing tool interface and trusted route restrictions.
Adapt system messages, text and image blocks, fixed tool declarations, tool calls
and results, model identity, stop reasons and usage at the trusted relay boundary.
Use native authentication/version headers. Scan the raw provider response for
keys before normalization. Preserve request/response limits, redirect refusal,
key redaction and failure capture.

Native migration also needs model-specific protocol checks. The
[Messages guide](https://platform.claude.com/docs/en/build-with-claude/working-with-messages)
says current models reject unsupported sampling parameters, including
`temperature: 0` on Opus 5.5. The
[API reference](https://platform.claude.com/docs/en/api/messages/create)
requires thinking blocks and signatures to roundtrip unchanged when enabled.
Do not discard them while converting tool history. Any explicit thinking or
sampling policy must be recorded for the later model comparison.

Carry cache counters through writer events, reviewer usage, host aggregation,
protected `.run/usage.json`, results and failure receipts. Count cache tokens
once. An uncached provider response remains valid with zero cache counters.
No paid warm-up or automatic retry is part of this implementation.

## Failure cases to prove before shipping

- A second synthetic native turn reports cache reads and the correct discounted
  cost; cold writes use the write rate, not the ordinary input rate.
- A provider that ignores caching completes with zero cache counters.
- Writer and fresh-context reviewer counters both survive aggregation and capture.
- Native text, images, tool history and signed thinking blocks roundtrip without
  changing the sandbox's fixed tool authority.
- Invalid counters, model identity, stop reasons and unsupported content fail
  with retained known usage where possible.
- Key echoes, including inside non-text native blocks, still suppress the tree;
  diagnostic redaction and the existing refusing-direction checks still pass.

Review and merge precede live evaluation. Model-comparison cases require a
separate run registration and explicit operator go. Human 1x reads remain
separate from model review; this change enables no acceptance gate.
