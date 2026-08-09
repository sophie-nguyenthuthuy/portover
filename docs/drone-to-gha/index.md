# drone-to-gha: .drone.yml (Drone CI) → .github/workflows/*.yml (GitHub Actions)

Run it: `portover run drone-to-gha <dir>` (dry run) then `--write`.

One page per directive:

- [`commands: [...]`](commands.md) — Migrate Drone commands to GitHub Actions run steps
- [`kind: pipeline / secret / signature — and type: docker / exec / ssh`](kind.md) — Migrate Drone document kinds to GitHub Actions
- [`image: / pull:`](image.md) — Migrate the Drone step image to GitHub Actions
- [`platform / clone / workspace / volumes / node / image_pull_secrets`](pipeline-settings.md) — Migrate Drone pipeline settings to GitHub Actions
- [`environment: {NAME: value, NAME: {from_secret: x}}`](environment.md) — Migrate Drone environment and from_secret to GitHub Actions
- [`trigger: branch / event / ref / cron`](trigger.md) — Migrate Drone trigger to GitHub Actions
- [`services: [{name, image, environment}]`](services.md) — Migrate Drone services to GitHub Actions service containers
- [`when: branch / event / status / ref / path`](when.md) — Migrate Drone when conditions to GitHub Actions if
- [`settings: (a plugin step)`](settings.md) — Migrate Drone plugins to GitHub Actions
- [`failure / detach / privileged / volumes / depends_on / resources`](step-settings.md) — Migrate the remaining Drone step settings to GitHub Actions
- [`steps: [{name, image, commands}]`](steps.md) — Migrate Drone steps to GitHub Actions
- [`$DRONE_COMMIT_SHA, $DRONE_BRANCH, $DRONE_BUILD_NUMBER, ...`](variables.md) — Migrate Drone environment variables to GitHub Actions
