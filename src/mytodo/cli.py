from __future__ import annotations

import argparse
from pathlib import Path

from mythings.engine import ClaudeCLIEngine, Engine
from mythings.github import GitHub
from mythings.ledger import Ledger

from mytodo.curator import Curator, Result

_ENGINES = ("noop", "claude-cli")


def build_engine(name: str, *, model: str | None = None) -> Engine | None:
    # noop -> None so the deterministic label grouping is used with no model call.
    if name == "claude-cli":
        return ClaudeCLIEngine(model=model)
    return None


def _default_plan_ledger(source: Path, explicit: Path | None) -> Path | None:
    if explicit is not None:
        return explicit
    # MyPlanner's runtime ledger, sibling to the target checkout under the
    # workspace root — the same default MyOrchestrator uses.
    return source.resolve().parent / "my-planner" / ".mythings" / "ledger.jsonl"


def _render(result: Result) -> str:
    line = f"{result.outcome}: {result.detail}"
    if result.pr is not None:
        line += f" (PR #{result.pr})"
    return line


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--source", type=Path, default=Path.cwd(), help="local checkout to write TODO.md into"
    )
    parser.add_argument("--base", default="main", help="base branch for the PR")
    parser.add_argument(
        "--plan-ledger",
        type=Path,
        default=None,
        help="MyPlanner's ledger (default: <source>/../my-planner/.mythings/ledger.jsonl)",
    )
    parser.add_argument("--ledger", type=Path, default=Path(".mythings/ledger.jsonl"))
    parser.add_argument(
        "--engine",
        choices=sorted(_ENGINES),
        default="noop",
        help="Engine for prioritising (default: noop — deterministic label grouping)",
    )
    parser.add_argument("--engine-model", default=None, help="model for --engine claude-cli")
    parser.add_argument("--no-pr", action="store_true", help="write TODO.md but skip the PR")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mytodo",
        description="Curate a TODO.md from open issues + MyPlanner's plan, and open a PR.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    repo = sub.add_parser("repo", help="curate one repo's own TODO.md")
    repo.add_argument("--repo", required=True, help="GitHub slug owner/name")
    _add_common(repo)

    org = sub.add_parser("org", help="curate one org-wide TODO.md into a target repo")
    org.add_argument("--org", required=True, help="GitHub org to aggregate open issues from")
    org.add_argument("--into", required=True, help="target repo slug owner/name for the roll-up")
    _add_common(org)

    args = parser.parse_args(argv)
    engine = build_engine(args.engine, model=args.engine_model)
    plan_ledger = _default_plan_ledger(args.source, args.plan_ledger)
    target = args.repo if args.cmd == "repo" else args.into

    curator = Curator(
        source=args.source,
        target_repo=target,
        ledger=Ledger(args.ledger),
        github=GitHub(target),
        base=args.base,
        plan_ledger=plan_ledger,
        engine=engine,
    )
    org_name = args.org if args.cmd == "org" else None
    result = curator.curate(org=org_name, open_pr=not args.no_pr)
    print(_render(result))
    return 0 if result.outcome != "failure" else 1


if __name__ == "__main__":
    raise SystemExit(main())
