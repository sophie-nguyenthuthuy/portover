"""addons — apt packages, browsers, and friends."""

from portover.core import MappingMeta

META = MappingMeta(
    id="addons",
    directive="addons: apt / chrome / firefox / ...",
    title="Migrate Travis addons to GitHub Actions",
    before="addons:\n  apt:\n    packages:\n      - libpq-dev\n      - graphviz",
    after="- run: sudo apt-get update && sudo apt-get install -y libpq-dev graphviz",
    notes=(
        "apt packages become one explicit install step. chrome/firefox are "
        "preinstalled on GHA Ubuntu runners and are dropped. Other addons "
        "(sonarcloud, sauce_connect, ...) map to their own marketplace actions "
        "— flagged with the addon name so you can search for it."
    ),
    priority=22,
)


def matches(key) -> bool:
    return key == "addons"


def apply(key, value, ctx, report) -> None:
    if not isinstance(value, dict):
        return
    for addon, spec in value.items():
        if addon == "apt":
            pkgs = [str(p) for p in ((spec or {}).get("packages") or [])] if isinstance(spec, dict) else []
            if pkgs:
                ctx.pre_steps.append({"run": "sudo apt-get update && sudo apt-get install -y " + " ".join(pkgs)})
                report.mapped(META.id, f"apt.packages: {pkgs}")
            if isinstance(spec, dict) and spec.get("sources"):
                report.manual(META.id, f"apt.sources: {spec['sources']}",
                              "add the apt repository in the install step (add-apt-repository) — Travis source aliases don't exist on GHA")
        elif addon in ("chrome", "firefox"):
            report.mapped(META.id, f"addons.{addon}", "dropped — preinstalled on GHA Ubuntu runners")
        else:
            report.manual(META.id, f"addons.{addon}",
                          f"find the marketplace action for '{addon}' (no built-in equivalent)")
