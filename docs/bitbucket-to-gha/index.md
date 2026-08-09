# bitbucket-to-gha: bitbucket-pipelines.yml (Bitbucket Pipelines) → .github/workflows/*.yml (GitHub Actions)

Run it: `portover run bitbucket-to-gha <dir>` (dry run) then `--write`.

One page per directive:

- [`script / after-script`](script.md) — Migrate Bitbucket Pipelines script to GitHub Actions run steps
- [`image: name / image: {name, username, password}`](image.md) — Migrate Bitbucket Pipelines image to GitHub Actions container
- [`image / clone / options (top level)`](defaults.md) — Migrate Bitbucket Pipelines global settings to GitHub Actions
- [`clone: depth / lfs / enabled`](clone.md) — Migrate Bitbucket Pipelines clone settings to GitHub Actions checkout
- [`caches: [node, pip, custom-name]`](caches.md) — Migrate Bitbucket Pipelines caches to GitHub Actions
- [`definitions: caches / services / steps`](definitions.md) — Migrate Bitbucket Pipelines definitions to GitHub Actions
- [`artifacts: [dist/**] / artifacts: {paths, download}`](artifacts.md) — Migrate Bitbucket Pipelines artifacts to GitHub Actions
- [`services: [postgres, redis]`](services.md) — Migrate Bitbucket Pipelines services to GitHub Actions service containers
- [`deployment: production / trigger: manual`](deployment.md) — Migrate Bitbucket Pipelines deployment and manual triggers to GitHub Actions
- [`size / max-time / oidc / runs-on / fail-fast / condition`](step-settings.md) — Migrate the remaining Bitbucket Pipelines step settings to GitHub Actions
- [`pipelines: default / branches / tags / pull-requests / custom`](pipelines.md) — Migrate Bitbucket Pipelines sections to GitHub Actions workflows
- [`- parallel: [steps] / - parallel: {fail-fast, steps}`](parallel.md) — Migrate Bitbucket Pipelines parallel steps to GitHub Actions
- [`- pipe: atlassian/aws-s3-deploy:1.1.0`](pipe.md) — Migrate Bitbucket Pipes to GitHub Actions
- [`$BITBUCKET_COMMIT, $BITBUCKET_BRANCH, $BITBUCKET_BUILD_NUMBER, ...`](variables.md) — Migrate Bitbucket Pipelines variables to GitHub Actions
