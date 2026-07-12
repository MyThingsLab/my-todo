from __future__ import annotations

import subprocess
from pathlib import Path

from mythings.github import GitHub, Issue
from mythings.ledger import Ledger

from conftest import fake_gh, fake_search, issue, make_target_repo, org_hit
from mytodo.curator import Curator
from mytodo.plan import PlanSignal
from mytodo.render import render_todo
from mytodo.sources import issues_to_items


def _show(repo: Path, ref: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), "show", ref], capture_output=True, text=True, check=True
    )
    return proc.stdout


def test_curate_repo_writes_todo_and_opens_pr(tmp_path: Path) -> None:
    repo = make_target_repo(tmp_path)
    fake = fake_gh(
        [issue(6, "vuln scanning", ("safety",)), issue(11, "MySearcher", ("tool-build",))]
    )
    ledger = Ledger(tmp_path / "led.jsonl")
    curator = Curator(
        source=repo,
        target_repo="o/r",
        ledger=ledger,
        github=GitHub("o/r", runner=fake),
        plan_ledger=None,
    )

    result = curator.curate()

    assert result.outcome == "success"
    assert result.pr == 7
    assert result.items_count == 2

    subprocess.run(["git", "-C", str(repo), "fetch", "-q", "origin"], check=True)
    todo = _show(repo, "origin/my-todo/curate:TODO.md")
    assert "## Now" in todo and "- [ ] #6 vuln scanning `safety`" in todo
    assert "#11" in todo

    recorded = list(Ledger(tmp_path / "led.jsonl"))
    assert recorded[-1].tool == "mytodo" and recorded[-1].kind == "todo"
    assert recorded[-1].outcome == "success"


def test_curate_skipped_when_todo_unchanged(tmp_path: Path) -> None:
    repo = make_target_repo(tmp_path)
    issues = [Issue(6, "vuln scanning", "", "u", ["safety"])]
    content = render_todo(issues_to_items(issues), PlanSignal(), scope="o/r")
    (repo / "TODO.md").write_text(content, encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "TODO.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "seed todo"], check=True)
    subprocess.run(["git", "-C", str(repo), "push", "-q", "origin", "main"], check=True)

    fake = fake_gh([issue(6, "vuln scanning", ("safety",))])
    curator = Curator(
        source=repo,
        target_repo="o/r",
        ledger=Ledger(tmp_path / "led.jsonl"),
        github=GitHub("o/r", runner=fake),
        plan_ledger=None,
    )

    result = curator.curate()
    assert result.outcome == "skipped"
    assert result.pr is None
    assert ["pr", "create"] not in [c[:2] for c in fake.calls]


def test_curate_org_rolls_up_with_repo_prefixes(tmp_path: Path) -> None:
    into = make_target_repo(tmp_path)
    search = fake_search(
        [
            org_hit("my-things-core", 35, "add diff()", ("core-contract",)),
            org_hit("fleet-dispatch", 6, "vuln scanning", ("safety",)),
        ]
    )
    curator = Curator(
        source=into,
        target_repo="MyThingsLab/fleet-dispatch",
        ledger=Ledger(tmp_path / "led.jsonl"),
        github=GitHub("MyThingsLab/fleet-dispatch", runner=fake_gh([])),
        plan_ledger=None,
        runner=search,
    )

    result = curator.curate(org="MyThingsLab")

    assert result.outcome == "success"
    assert result.pr == 7
    subprocess.run(["git", "-C", str(into), "fetch", "-q", "origin"], check=True)
    todo = _show(into, "origin/my-todo/curate:TODO.md")
    assert "fleet-dispatch#6" in todo
    assert "my-things-core#35" in todo


def test_no_pr_writes_but_skips_pr(tmp_path: Path) -> None:
    repo = make_target_repo(tmp_path)
    fake = fake_gh([issue(6, "vuln", ("safety",))])
    curator = Curator(
        source=repo,
        target_repo="o/r",
        ledger=Ledger(tmp_path / "led.jsonl"),
        github=GitHub("o/r", runner=fake),
        plan_ledger=None,
    )

    result = curator.curate(open_pr=False)
    assert result.outcome == "success"
    assert result.pr is None
    assert ["pr", "create"] not in [c[:2] for c in fake.calls]
