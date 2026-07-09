from __future__ import annotations

from mytodo.plan import PlanSignal
from mytodo.sources import TodoItem

# Deterministic fallback grouping, by label, when no engine override is given.
_NOW_LABELS = {"safety", "bug", "critical"}
_NEXT_LABELS = {"core-contract", "needs-decision"}
_SECTIONS = ("Now", "Next", "Later")


def _section_of(item: TodoItem) -> str:
    labels = set(item.labels)
    if labels & _NOW_LABELS:
        return "Now"
    if labels & _NEXT_LABELS:
        return "Next"
    return "Later"


def _line(item: TodoItem, *, with_repo: bool) -> str:
    ref = f"{item.repo}#{item.number}" if with_repo and item.repo else f"#{item.number}"
    tags = "".join(f" `{lbl}`" for lbl in item.labels)
    prefix = "⚠ " if "critical" in item.labels else ""
    return f"- [ ] {prefix}{ref} {item.title}{tags}"


def render_todo(
    items: list[TodoItem],
    plan: PlanSignal,
    *,
    scope: str,
    with_repo: bool = False,
    sections: dict[int, str] | None = None,
) -> str:
    # `sections` (issue number -> "Now"/"Next"/"Later") is the optional engine
    # judgment override; anything missing falls back to the deterministic
    # label-based grouping, so the file is well-formed with or without a model.
    has_plan = bool(plan.items or plan.flags)
    lines = [
        f"# TODO — {scope}",
        "",
        "_Curated by **my-todo** from open issues"
        + (" + MyPlanner's plan._" if has_plan else "._"),
        "",
    ]
    if plan.paused:
        lines += ["> ⏸ **Planner flag:** pause new tools — hold scaffolds / new builds.", ""]
    focus = [it.item for it in plan.items if it.horizon == "next"]
    if focus:
        lines += ["**Planner focus (next):** " + "; ".join(focus), ""]

    buckets: dict[str, list[TodoItem]] = {s: [] for s in _SECTIONS}
    for item in items:
        section = (sections or {}).get(item.number) or _section_of(item)
        if section not in buckets:
            section = "Later"
        buckets[section].append(item)

    for section in _SECTIONS:
        group = sorted(buckets[section], key=lambda it: (it.repo or "", it.number))
        if not group:
            continue
        lines.append(f"## {section}")
        lines += [_line(it, with_repo=with_repo) for it in group]
        lines.append("")

    if not items:
        lines += ["_No open issues — nothing to do._", ""]
    return "\n".join(lines).rstrip() + "\n"
