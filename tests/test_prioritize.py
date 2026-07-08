from __future__ import annotations

from mythings.engine import NoopEngine

from mytodo.plan import PlanSignal
from mytodo.prioritize import engine_sections
from mytodo.sources import TodoItem


def _items() -> list[TodoItem]:
    return [
        TodoItem(title="a", number=6, url="", labels=["safety"]),
        TodoItem(title="b", number=35, url="", labels=["core-contract"]),
    ]


def test_parses_valid_mapping_and_drops_unknowns() -> None:
    engine = NoopEngine(reply='{"6": "Now", "35": "bogus", "99": "Later"}')
    out = engine_sections(engine, _items(), PlanSignal())
    assert out == {6: "Now"}  # 35 invalid section, 99 not an open issue


def test_empty_reply_degrades_to_no_override() -> None:
    assert engine_sections(NoopEngine(reply=""), _items(), PlanSignal()) == {}


def test_unparsable_reply_degrades() -> None:
    assert engine_sections(NoopEngine(reply="not json"), _items(), PlanSignal()) == {}


def test_no_items_makes_no_call() -> None:
    assert engine_sections(NoopEngine(reply='{"6":"Now"}'), [], PlanSignal()) == {}
