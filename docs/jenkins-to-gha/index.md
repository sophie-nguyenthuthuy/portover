# jenkins-to-gha: Jenkinsfile (declarative pipeline) → .github/workflows/*.yml (GitHub Actions)

Run it: `portover run jenkins-to-gha <dir>` (dry run) then `--write`.

One page per directive:

- [`checkout scm`](checkout.md) — Migrate Jenkins checkout scm to GitHub Actions
- [`agent any / agent { label } / agent { docker }`](agent.md) — Migrate Jenkins agent to GitHub Actions runs-on
- [`sh 'cmd' / bat 'cmd'`](sh.md) — Migrate Jenkins sh and bat steps to GitHub Actions run
- [`echo 'message'`](echo.md) — Migrate Jenkins echo steps to GitHub Actions
- [`environment { KEY = 'value' }`](environment.md) — Migrate Jenkins environment blocks to GitHub Actions env
- [`archiveArtifacts / junit / stash / unstash`](artifacts.md) — Migrate Jenkins artifact steps to GitHub Actions
- [`tools { jdk / nodejs / maven / go }`](tools.md) — Migrate Jenkins tools blocks to GitHub Actions setup-* actions
- [`options { timeout / disableConcurrentBuilds / buildDiscarder }`](options.md) — Migrate Jenkins options to GitHub Actions
- [`triggers { cron / pollSCM / upstream }`](triggers.md) — Migrate Jenkins triggers to GitHub Actions on:
- [`parameters { string / booleanParam / choice }`](parameters.md) — Migrate Jenkins parameters to workflow_dispatch inputs
- [`stages { stage('X') { steps { ... } } }`](stages.md) — Migrate Jenkins stages to GitHub Actions jobs
- [`when { branch / tag / changeRequest / environment / expression }`](when.md) — Migrate Jenkins when conditions to GitHub Actions if:
- [`stage { parallel { stage ... stage ... } }`](parallel.md) — Migrate Jenkins parallel stages to GitHub Actions jobs
- [`post { always / success / failure }`](post.md) — Migrate Jenkins post blocks to GitHub Actions
