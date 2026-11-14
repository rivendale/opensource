# Shared game deployment

Call `.github/workflows/pages-game.yml` to test a game and deploy its Pages folder.
Enable GitHub Pages with GitHub Actions as the source in the calling repository.
Commands execute code from the calling repository, and Playwright installation can
install system packages. Use trusted commands and a committed npm lockfile. Actions
are pinned to full commits; see the [execution checklist](../ai/graphics.md).
If e2e is enabled, pin Playwright in the caller's package.json and package-lock.json
so `npx` uses that installed version.

| Input | Type | Default | Purpose |
|---|---|---|---|
| `node-version` | string | `22` | Node.js version |
| `install` | string | `npm ci` | Install dependencies |
| `typecheck` | string | empty | Optional typecheck command |
| `test` | string | `npm test` | Test command |
| `build` | string | `npm run build:pages` | Build command; empty skips it |
| `artifact-path` | string | `.output/public` | Folder relative to working-directory |
| `e2e` | string | empty | After build, install Playwright browsers with system dependencies, then run this command |
| `smoke-url` | string | empty | After deploy, check this URL with retries; callers are expected to set it |
| `deploy` | boolean | `true` | Deploy after successful tests, except on pull requests |
| `working-directory` | string | `.` | Checkout-relative directory for commands and artifact-path |

The setup step caches npm using `package-lock.json` in working-directory. Both
families need that lockfile, even with no dependencies. Optional commands run only
when nonempty. Commands, artifact upload, deployment and smoke failures fail the job.
The test job uploads an artifact even when deployment is disabled. The build family
uses artifact name `github-pages`; the static family uses `github-pages-static`.
Use at most one call per family in a run to avoid artifact name collisions.
Deployments share a repository concurrency group and do not cancel a running deploy.
GitHub may replace a pending deployment with a newer pending deployment.

Build family:

```yaml
name: Pages
on: [push, pull_request]
permissions:
  contents: read
  pages: write
  id-token: write
jobs:
  pages:
    uses: rivendale/opensource/.github/workflows/pages-game.yml@v1
    with:
      smoke-url: https://example.github.io/game/
```

Static family (committed site files in `public/`):

```yaml
name: Pages
on: [push, pull_request]
permissions:
  contents: read
  pages: write
  id-token: write
jobs:
  pages:
    uses: rivendale/opensource/.github/workflows/pages-game.yml@v1
    with:
      build: ""
      artifact-path: public
      smoke-url: https://example.github.io/game/
```

The `v1` tag is moved only after a reviewed merge.

The PR selftest calls the local workflow for both families with deployment disabled.
Local failure checks run with `python3 tests/tools/test_pages_game.py` in an
environment with PyYAML installed; they do not contact GitHub or deploy a site.
