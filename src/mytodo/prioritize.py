from __future__ import annotations

import json

from mythings.engine import Engine, EngineRequest

from mytodo.plan import PlanSignal
from mytodo.sources import TodoItem

_VALID = {"Now", "Next", "Later"}
_SYSTEM = (
    "You triage a repo's open issues into a TODO list. Put each issue into exactly one "
    "of Now, Next, Later by urgency and dependency order, honouring the planner focus and "
    "any pause flag. Reply with ONLY a JSON object mapping the issue number as a string to "
    'its group, e.g. {"6": "Now", "35": "Next"}. No prose, no code fences.'
)


def engine_sections(engine: Engine, items: list[TodoItem], plan: PlanSignal) -> dict[int, str]:
    # The single judgment call. Any empty or unparsable reply returns {}, so the
    # caller degrades to the deterministic label-based grouping (never fabricates).
    if not items:
        return {}
    listing = "\n".join(f"#{it.number} [{','.join(it.labels)}] {it.title}" for it in items)
    focus = "; ".join(f"{it.item} ({it.horizon})" for it in plan.items) or "none"
    prompt = f"Planner focus: {focus}\nPause new tools: {plan.paused}\nOpen issues:\n{listing}"

    reply = engine.run(EngineRequest(prompt=prompt, system=_SYSTEM)).text.strip()
    try:
        raw = json.loads(reply) if reply else {}
    except json.JSONDecodeError:
        return {}
    if not isinstance(raw, dict):
        return {}

    numbers = {it.number for it in items}
    out: dict[int, str] = {}
    for key, value in raw.items():
        try:
            number = int(key)
        except (TypeError, ValueError):
            continue
        if number in numbers and value in _VALID:
            out[number] = value
    return out
