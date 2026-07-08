from __future__ import annotations

from pathlib import Path

import pytest
from mythings.engine import ClaudeCLIEngine

from mytodo.cli import _default_plan_ledger, build_engine, main


def test_build_engine_noop_is_none() -> None:
    assert build_engine("noop") is None


def test_build_engine_claude_cli() -> None:
    assert isinstance(build_engine("claude-cli"), ClaudeCLIEngine)


def test_default_plan_ledger_points_at_sibling_planner(tmp_path: Path) -> None:
    source = tmp_path / "my-todo"
    source.mkdir()
    got = _default_plan_ledger(source, None)
    assert got == tmp_path / "my-planner" / ".mythings" / "ledger.jsonl"


def test_explicit_plan_ledger_wins(tmp_path: Path) -> None:
    explicit = tmp_path / "custom.jsonl"
    assert _default_plan_ledger(tmp_path, explicit) == explicit


def test_missing_subcommand_errors() -> None:
    with pytest.raises(SystemExit):
        main([])
