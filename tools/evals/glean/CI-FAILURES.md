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

## Branch denial evidence

- Broken fixture: commit `7981a9a551ce745616755fbc754c19d1bf2c5d91`,
  [CI run 39775966988](https://github.com/rivendale/opensource/actions/runs/39775966988).
  Checkout passed; Existing independent glean fixtures failed; later checks skipped.
  Locally the wrong expectation reports `done` versus `intentional-ci-denial-probe`.
- Restoring the original fixture passes all 320 existing cases locally.
- Broken link: commit `0dd81ae97ef74a7fb7cd0d923fc3b35179f0862b`,
  [CI run 39776387776](https://github.com/rivendale/opensource/actions/runs/39776387776).
  The fixture step passed; Relative Markdown links failed.
  Locally the checker exits 1 and names the temporary missing file.
- Both probes are restored. The independent fixture tree matches its original bytes;
  all 320 fixtures, 470 relative links and 33 link-checker selftests pass locally.

The final workflow uses Ubuntu's system Python and only the pinned checkout action.
There is no dependency install, model call, repository secret reference or external service step.
