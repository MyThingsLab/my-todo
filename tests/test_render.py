from __future__ import annotations

from mytodo.plan import PlanItem, PlanSignal
from mytodo.render import render_todo
from mytodo.sources import TodoItem


def _item(
    number: int, title: str, labels: tuple[str, ...] = (), repo: str | None = None
) -> TodoItem:
    return TodoItem(title=title, number=number, url="", labels=list(labels), repo=repo)


def test_groups_by_label_into_now_next_later() -> None:
    items = [
        _item(6, "vuln scanning", ("safety",)),
        _item(35, "add diff()", ("core-contract",)),
        _item(11, "build MySearcher", ("tool-build",)),
    ]
    out = render_todo(items, PlanSignal(), scope="o/r")

    now, nxt, later = out.index("## Now"), out.index("## Next"), out.index("## Later")
    assert now < nxt < later
    assert "- [ ] #6 vuln scanning `safety`" in out
    assert "#35" in out[nxt:later]
    assert "#11" in out[later:]


def test_plan_focus_and_pause_banner() -> None:
    plan = PlanSignal(
        items=[PlanItem(item="build MySearcher", rationale="", horizon="next")],
        flags=["pause new tools"],
    )
    out = render_todo([_item(6, "x", ("safety",))], plan, scope="o/r")
    assert "pause new tools" in out
    assert "Planner focus (next):** build MySearcher" in out


def test_org_mode_prefixes_repo() -> None:
    items = [_item(35, "diff", ("core-contract",), repo="my-things-core")]
    out = render_todo(items, PlanSignal(), scope="MyThingsLab", with_repo=True)
    assert "- [ ] my-things-core#35 diff" in out


def test_engine_override_wins_over_labels() -> None:
    items = [_item(11, "build MySearcher", ("tool-build",))]
    out = render_todo(items, PlanSignal(), scope="o/r", sections={11: "Now"})
    assert "## Now" in out and "#11" in out
    assert "## Later" not in out


def test_no_issues_message() -> None:
    out = render_todo([], PlanSignal(), scope="o/r")
    assert "No open issues" in out
