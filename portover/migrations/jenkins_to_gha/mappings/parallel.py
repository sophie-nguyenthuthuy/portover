"""parallel — concurrent stages. Consumed by stages.py."""

from portover.core import MappingMeta

SCOPE = "stage"  # dispatched from stages.py, not the pipeline driver

META = MappingMeta(
    id="parallel",
    directive="stage { parallel { stage ... stage ... } }",
    title="Migrate Jenkins parallel stages to GitHub Actions jobs",
    before="""stage('Test') {
  parallel {
    stage('unit') { steps { sh 'make unit' } }
    stage('lint') { steps { sh 'make lint' } }
  }
}""",
    after="""jobs:
  unit:
    needs: build
    steps: [ ... ]
  lint:
    needs: build
    steps: [ ... ]
  deploy:
    needs: [unit, lint]""",
    notes=(
        "GHA jobs are parallel by default — the migration is inverted: Jenkins "
        "marks parallelism explicitly, GHA marks *sequencing* (needs:) "
        "explicitly. Sibling parallel stages share the same needs; the next "
        "sequential stage needs all of them. For matrix-shaped duplication, "
        "collapse the jobs into strategy.matrix by hand."
    ),
    priority=46,
)


def matches(node) -> bool:
    return node.keyword() == "parallel"
