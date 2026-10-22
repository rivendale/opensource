# Glean CI failure list before implementation

- The existing fixture runner is omitted, narrowed or allowed to fail while the job stays green.
- An incorrect fixture expectation is accepted as a passing run.
- A broken relative Markdown link does not fail the link-check step.
- The link checker selftest is omitted or its failure is ignored.
- A relevant pull request change skips the workflow.
- Checkout is mutable, retains credentials, or the job has write permissions or secrets.
- A dependency install or external request is added beyond checkout; fixtures must use their existing local stubs.

Prove a broken fixture and a broken link separately on this branch before restoring both.
The final tree must retain the existing independent fixtures byte-for-byte.

[Intentional broken-link denial probe](ci-intentionally-missing.md)
