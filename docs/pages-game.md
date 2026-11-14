# Shared game deployment

Call `.github/workflows/pages-game.yml` to test a game and deploy its Pages folder.
Enable GitHub Pages with GitHub Actions as the source in the calling repository.
Commands execute code from the calling repository, and Playwright installation can
install system packages. Use trusted commands and commit an npm lockfile when installing dependencies.
Actions are pinned to full commits.
If e2e is enabled, pin Playwright in the caller's package.json and package-lock.json
so `npx` uses that installed version.

| Input | Type | Default | Purpose |
|---|---|---|---|
| `node-version` | string | `22` | Node.js version |
| `install` | string | `npm ci` | Install dependencies; empty skips it |
| `typecheck` | string | empty | Optional typecheck command |
| `test` | string | `npm test` | Test command; empty skips it |
| `build` | string | `npm run build:pages` | Build command; empty skips it |
| `artifact-name` | string | `github-pages` | Name used for artifact upload and deployment; use a distinct name per call in a run |
| `artifact-path` | string | `.output/public` | Folder relative to working-directory |
| `e2e` | string | empty | After build, install Playwright browsers with system dependencies, then run this command |
| `smoke-url` | string | empty | After deploy, check this URL with retries; callers are expected to set it |
| `deploy` | boolean | `true` | Deploy after successful tests only on push or workflow_dispatch on the default branch |
| `working-directory` | string | `.` | Checkout-relative directory for commands and artifact-path |

The lockfile is optional. The setup step caches npm only when `package-lock.json`
exists in working-directory. A caller without a lockfile must also clear `install`.
Optional commands run only
when nonempty. Commands, artifact upload, deployment and smoke failures fail the job.
The test job uploads an artifact even when deployment is disabled. Set a distinct `artifact-name` for each call in a run to avoid artifact name collisions.
Deployments share a repository concurrency group and do not cancel a running deploy.
GitHub may replace a pending deployment with a newer pending deployment.

A push to any other branch must never deploy; the caller filters pushes and the shared workflow enforces the default branch.

Build family:

```yaml
name: Pages
on:
  push:
    branches: [main]
  pull_request:
  workflow_dispatch:
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
on:
  push:
    branches: [main]
  pull_request:
  workflow_dispatch:
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

Bare static site (no package.json):

```yaml
name: Pages
on:
  push:
    branches: [main]
  pull_request:
  workflow_dispatch:
permissions:
  contents: read
  pages: write
  id-token: write
jobs:
  pages:
    uses: rivendale/opensource/.github/workflows/pages-game.yml@v1
    with:
      install: ""
      test: ""
      build: ""
      artifact-path: public
      smoke-url: https://example.github.io/game/
```

The `v1` tag is moved only after a reviewed merge.

The PR selftest calls the local workflow for build, static and bare static fixtures with deployment disabled.
The bare fixture has no package.json or lockfile and skips install, test and build.
Local failure checks run with `python3 tests/tools/test_pages_game.py` in an
environment with PyYAML installed; they do not contact GitHub or deploy a site.
