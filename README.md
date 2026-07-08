# my-todo

[![CI](https://github.com/MyThingsLab/my-todo/actions/workflows/ci.yml/badge.svg)](https://github.com/MyThingsLab/my-todo/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/MyThingsLab/my-todo/branch/main/graph/badge.svg)](https://codecov.io/gh/MyThingsLab/my-todo)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![MIT](https://img.shields.io/badge/license-MIT-green)

A [MyThingsLab](../mythings-core) `My[X]` tool: curate a `TODO.md` from live
signals — a repo's **open GitHub issues** plus **MyPlanner's** latest plan — and
open a PR. It's the prospective counterpart to MyReporter's retrospective digest:
a durable, checked-in "what to do next", grouped **Now / Next / Later**.

Curates either one repo's own `TODO.md` or an org-wide roll-up.

## Usage

```bash
# One repo's own TODO.md, from its open issues (+ MyPlanner's plan if present).
mytodo repo --repo MyThingsLab/my-todo --source .

# An org-wide roll-up, aggregating every repo's open issues into one board.
mytodo org --org MyThingsLab --into MyThingsLab/fleet-dispatch --source ../fleet-dispatch

# Preview without opening a PR; or let a model do the prioritising:
mytodo repo --repo MyThingsLab/my-todo --no-pr
mytodo repo --repo MyThingsLab/my-todo --engine claude-cli
```

Prioritising is the tool's **single, optional** Engine call. Against the default
`--engine noop` (zero tokens) issues are grouped deterministically by label
(`safety`/`bug` → Now, `core-contract`/`needs-decision` → Next, rest → Later);
`--engine claude-cli` lets a model do the triage, degrading to that same grouping
on any empty reply. MyPlanner's plan is read from its ledger on disk (the same
seam MyOrchestrator uses) — a `next` horizon surfaces as a **Planner focus** note
and a "pause new tools" flag as a banner. No plan ⇒ issues only, unchanged.

`my-todo` reads issues and writes one `TODO.md` PR — it never merges and never
mutates issues. Re-running with no changes is a no-op (`skipped`).

## Install (development)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ../mythings-core -e ".[dev]"
pytest
```

See [`CLAUDE.md`](CLAUDE.md) for the tool's seams and [`HARNESS.md`](HARNESS.md)
for the inherited build rules.

## License

MIT — see [`LICENSE`](LICENSE).
