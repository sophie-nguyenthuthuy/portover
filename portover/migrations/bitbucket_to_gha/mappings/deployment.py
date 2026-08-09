"""deployment / trigger — environments and manual gates."""

from portover.core import MappingMeta

SCOPE = "step"

META = MappingMeta(
    id="deployment",
    directive="deployment: production / trigger: manual",
    title="Migrate Bitbucket Pipelines deployment and manual triggers to GitHub Actions",
    before="""- step:
    name: Deploy
    deployment: production
    trigger: manual
    script: [./deploy.sh]""",
    after="""deploy:
  environment: production     # deployment tracking + approvals + scoped secrets
  steps:
    - run: ./deploy.sh""",
    notes=(
        "`deployment:` and GHA environments line up well — both track "
        "deployments per environment and both scope secrets to them. That also "
        "solves `trigger: manual`: Bitbucket pauses the step until someone "
        "clicks, and the GHA equivalent is an environment with required "
        "reviewers, which pauses the job the same way. So a manual deployment "
        "step needs no extra plumbing beyond configuring reviewers on the "
        "environment in repository settings. A `trigger: manual` step WITHOUT "
        "a deployment gets an environment invented for it, which portover "
        "flags — the alternative is a separate workflow_dispatch workflow."
    ),
    priority=24,
)


def matches(key) -> bool:
    return key in ("deployment", "trigger")


def apply(key, value, job, ctx, report) -> None:
    if key == "deployment":
        job["environment"] = str(value)
        report.mapped(META.id, f"deployment: {value}", f"environment: {value}")
        return
    mode = str(value)
    if mode == "manual":
        if not job.get("environment"):
            job["environment"] = "manual-approval"
            report.manual(META.id, "trigger: manual",
                          "no per-job play button in GHA — this job now points at an Environment "
                          "('manual-approval'); add required reviewers to it in repository settings")
        else:
            report.manual(META.id, "trigger: manual",
                          f"add required reviewers to the '{job['environment']}' Environment "
                          "so the job waits for approval")
    else:
        report.mapped(META.id, f"trigger: {mode}", "automatic — the GHA default")
