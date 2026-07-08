from __future__ import annotations

from pathlib import Path

from mythings.ledger import Ledger

from mytodo.plan import read_plan


def _write_plan(path: Path, plan: list[dict], flags: list[str]) -> None:
    Ledger(path).record(
        tool="myplanner",
        kind="plan",
        outcome="success",
        detail="plan",
        plan=plan,
        flags=flags,
    )


def test_missing_ledger_is_empty_signal() -> None:
    signal = read_plan(Path("/nonexistent/ledger.jsonl"))
    assert signal.items == []
    assert signal.flags == []
    assert signal.paused is False


def test_none_ledger_is_empty_signal() -> None:
    assert read_plan(None).items == []


def test_reads_latest_plan_items_and_flags(tmp_path: Path) -> None:
    path = tmp_path / "ledger.jsonl"
    _write_plan(path, [{"item": "old", "rationale": "", "horizon": "later"}], [])
    _write_plan(
        path,
        [
            {"item": "build MySearcher", "rationale": "unblocks reviewer", "horizon": "next"},
            {"item": "add diff()", "rationale": "", "horizon": "soon"},
            {"item": "", "rationale": "dropped", "horizon": "next"},
        ],
        ["pause new tools for a week"],
    )
    signal = read_plan(path)

    assert [i.item for i in signal.items] == ["build MySearcher", "add diff()"]
    assert signal.items[0].horizon == "next"
    assert signal.paused is True


def test_unknown_horizon_falls_back_to_later(tmp_path: Path) -> None:
    path = tmp_path / "ledger.jsonl"
    _write_plan(path, [{"item": "x", "rationale": "", "horizon": "whenever"}], [])
    assert read_plan(path).items[0].horizon == "later"
