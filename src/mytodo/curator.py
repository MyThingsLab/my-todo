from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from mythings.engine import Engine
from mythings.github import GitHub, PullRequest
from mythings.isolation import Workspace, in_github_actions
from mythings.ledger import Ledger
from mythings.policy import ALLOW, Action, Decision, Policy, PolicyResult

from mytodo.plan import read_plan
from mytodo.prioritize import engine_sections
from mytodo.render import render_todo
from mytodo.sources import Runner, gh, issues_to_items, search_org_open_issues

_TODO = "TODO.md"


class _AllowPolicy:
    def evaluate(self, action: Action) -> PolicyResult:
        return ALLOW


class PolicyDenied(RuntimeError):
    pass


@dataclass(frozen=True)
class Result:
    outcome: str  # success | skipped | failure
    scope: str
    pr: int | None
    detail: str
    items_count: int = 0


class Curator:
    def __init__(
        self,
        *,
        source: str | Path,
        target_repo: str,
        ledger: Ledger,
        github: GitHub,
        base: str = "main",
        plan_ledger: str | Path | None = None,
        engine: Engine | None = None,
        policy: Policy | None = None,
        runner: Runner = gh,
    ) -> None:
        self.source = Path(source)
        self.target_repo = target_repo
        self.ledger = ledger
        self.github = github
        self.base = base
        self.plan_ledger = plan_ledger
        self.engine = engine
        self.policy: Policy = policy or _AllowPolicy()
        self.runner = runner

    def curate(self, *, org: str | None = None, open_pr: bool = True) -> Result:
        scope = org if org else self.target_repo
        try:
            if org:
                items = search_org_open_issues(org, runner=self.runner)
                with_repo = True
            else:
                items = issues_to_items(self.github.list_issues(state="open", limit=200))
                with_repo = False
            plan = read_plan(self.plan_ledger)
            overrides = engine_sections(self.engine, items, plan) if self.engine else {}
            content = render_todo(
                items, plan, scope=scope, with_repo=with_repo, sections=overrides
            )
            return self._write(content, scope, len(items), open_pr)
        except PolicyDenied as denied:
            self._record("failure", scope, 0, str(denied), None)
            return Result("failure", scope, None, str(denied))

    def _write(self, content: str, scope: str, count: int, open_pr: bool) -> Result:
        with Workspace(self.source, self.base) as tree:
            (tree / _TODO).write_text(content, encoding="utf-8")
            if open_pr and not self._has_changes(tree):
                self._record("skipped", scope, count, "TODO.md already up to date", None)
                return Result("skipped", scope, None, "TODO.md already up to date", count)
            pr = self._open_pr(tree, scope) if open_pr else None
        detail = f"{count} open item(s) for {scope}"
        self._record("success", scope, count, detail, pr.number if pr else None)
        return Result("success", scope, pr.number if pr else None, detail, count)

    def _has_changes(self, tree: Path) -> bool:
        proc = subprocess.run(
            ["git", "-C", str(tree), "status", "--porcelain", "--", _TODO],
            capture_output=True,
            text=True,
        )
        return bool(proc.stdout.strip())

    def _open_pr(self, tree: Path, scope: str) -> PullRequest:
        branch = "my-todo/curate"
        title = f"chore: refresh TODO.md ({scope})"
        body = f"Curated `{_TODO}` for {scope} from open issues + MyPlanner's plan."
        self._git(tree, ["checkout", "-B", branch])
        self._git(tree, ["add", _TODO])
        self._git(tree, ["commit", "-m", title])
        # The tool's own dedicated branch, recreated from base each run, so a
        # force overwrite is the intended refresh (never touches a shared branch).
        self._git(tree, ["push", "--force", "-u", "origin", branch])
        self._guard(f"gh pr create --head {branch} --base {self.base}")
        return self.github.open_pr(title=title, body=body, base=self.base, head=branch)

    def _git(self, tree: Path, argv: list[str]) -> None:
        self._guard("git " + " ".join(argv))
        proc = subprocess.run(["git", "-C", str(tree), *argv], capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"git {' '.join(argv)} failed: {proc.stderr.strip()}")

    def _guard(self, command: str) -> None:
        result = self.policy.evaluate(Action(kind="bash", payload={"command": command}))
        if result.under(unattended=in_github_actions()) is not Decision.ALLOW:
            raise PolicyDenied(f"policy blocked: {command} ({result.reason or result.decision})")

    def _record(
        self, outcome: str, scope: str, items_count: int, detail: str, pr: int | None
    ) -> None:
        self.ledger.record(
            tool="mytodo",
            kind="todo",
            outcome=outcome,
            detail=detail,
            scope=scope,
            items_count=items_count,
            pr=pr,
        )
