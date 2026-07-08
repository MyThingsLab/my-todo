from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from mythings.ledger import Ledger

# Same pacing vocabulary MyOrchestrator matches on, kept in sync by convention.
_PAUSE_MARKERS = ("pause new tool", "freeze new tool", "no new tool", "hold new tool")
HORIZONS = ("next", "soon", "later")


@dataclass(frozen=True)
class PlanItem:
    item: str
    rationale: str
    horizon: str  # next | soon | later


@dataclass(frozen=True)
class PlanSignal:
    items: list[PlanItem] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)

    @property
    def paused(self) -> bool:
        return any(
            isinstance(f, str) and any(m in f.lower() for m in _PAUSE_MARKERS) for f in self.flags
        )


def read_plan(plan_ledger: str | Path | None) -> PlanSignal:
    # Reads MyPlanner's own runtime ledger (its kind=plan entries live there, not
    # in any repo's dev-ledger), exactly the seam MyOrchestrator uses. A missing
    # ledger means no signal, so the plan is a soft, optional input.
    if plan_ledger is None:
        return PlanSignal()
    path = Path(plan_ledger)
    if not path.exists():
        return PlanSignal()
    plans = [e for e in Ledger(path) if e.kind == "plan"]
    if not plans:
        return PlanSignal()
    latest = plans[-1]
    items: list[PlanItem] = []
    for raw in latest.data.get("plan") or []:
        text = str(raw.get("item", "")).strip()
        if not text:
            continue
        horizon = str(raw.get("horizon", "later"))
        items.append(
            PlanItem(
                item=text,
                rationale=str(raw.get("rationale", "")),
                horizon=horizon if horizon in HORIZONS else "later",
            )
        )
    flags = [f for f in (latest.data.get("flags") or []) if isinstance(f, str)]
    return PlanSignal(items=items, flags=flags)
