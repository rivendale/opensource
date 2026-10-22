# Independent fixtures for the glean and harvest tools

Written from the spec's failure list and the CLI contract before the tools existed, by someone other than the builder, so
the builder never grades its own work.

```
python3 tools/evals/runner.py glean            # every fixture under tools/evals/glean/fixtures
python3 tools/evals/runner.py glean --only 09  # ids starting with 09
python3 tools/evals/runner.py glean --list     # id, failure-list item, tag, what it checks
python3 tools/evals/runner.py glean --tools DIR   # test the tools in another directory
```

Exit 0 when every selected fixture passes, 1 when one fails, 3 when a tool does not exist (never read as "all passed").

A fixture is a directory with one `case.json`: the input files, the tool and its arguments, optional local stub servers
(a fake GitHub, GitLab, arXiv and Crossref on 127.0.0.1) and a fake `gh`, and what the run must do (exit code, JSON fields,
findings, stderr, which requests the stubs saw, that nothing was written). Each run uses a fresh directory, an empty HOME
and a PATH of symlinked system tools only; no real network and no real `gh`.

Tags: `spec` (the spec or a ruling states it), `principle` (a failure to read is never an empty success, never a crash),
`assumption` (the spec is silent; settle the spec, then change the fixture or the tool).
