# web: read public pages as text, safely

Two command-line readers for agents and people who need the text of a public web page without trusting the page.

| tool | use it for | how it stays safe |
|---|---|---|
| `bin/fetch <url\|doi\|arxiv-id>` | articles, papers and PDFs; sites that refuse plain clients | tries scholarly APIs (arXiv, Europe PMC, Crossref), then a direct GET reduced to article text, then the Wayback Machine. Every connection resolves through a filter that drops private, loopback, link-local and CGNAT addresses, checked again on each redirect. |
| `bin/browse <url>` | pages that build themselves with JavaScript (form builders, school and government sites) | headless Chrome with no direct network: every request goes through a proxy inside the tool that resolves once through `fetch`'s public-only filter and dials that IP. Design and failure list: [SPEC.md](SPEC.md). |

Both print text and never pass page text to a model or a shell. Treat their output as untrusted data.

## Install

```sh
python3 -m venv ~/.venvs/fetch && ~/.venvs/fetch/bin/pip install trafilatura      # optional; a stdlib fallback exists
python3 -m venv ~/.venvs/browse && ~/.venvs/browse/bin/pip install 'playwright==1.63.0'
~/.venvs/browse/bin/python -m playwright install chromium-headless-shell
```

Each script re-executes itself under its venv when the library is missing. Override the locations with
`FETCH_VENV` and `BROWSE_VENV`. Keep `fetch` and `browse` in the same directory: `browse` loads `fetch`'s address
filter from beside itself, so the rules have one home.

## Use

```sh
bin/fetch https://example.com/article
bin/fetch 10.1038/s41586-020-2649-2          # a DOI goes to the open scholarly APIs first
bin/browse https://example.com/app           # rendered text
bin/browse --show-refused URL                # also list every request the proxy refused
bin/browse --partial --timeout 45 URL        # print text that was still changing, labeled PARTIAL
```

Exit codes: 0 text printed; 1 failed or blocked (the reason is printed); 2 refused (a non-web scheme or a private
address).

## Tests

`tests/` holds 212 independent fixtures for `browse`, written from the failure list by a seat that did not write the
code, plus the builder for the weakened copies each fixture must fail against. See [tests/README.md](tests/README.md).
They need network access to httpbin.org and example.com.

## When not to use these

They read public pages only. For pages behind a login, use the site's API with your own credentials. For deliberate,
supervised browsing, use a browser you control.
