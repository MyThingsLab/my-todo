# my-todo — agent instructions

You are developing **my-todo**, a MyThingsLab My[X] tool.

**Inherited rules:** obey [`./HARNESS.md`](./HARNESS.md) in full — the vendored
MyThingsLab build-harness rules. Do not restate or override them. Anything not
covered here defers to `HARNESS.md`, then `mythings-core/docs/CONVENTIONS.md`.

## This tool

- **Purpose:** curate a `TODO.md` — a repo's own (`mytodo repo`) or an org-wide
  roll-up (`mytodo org`) — from live signals (open GitHub issues + MyPlanner's
  latest `kind=plan` entry), then open a PR. The prospective counterpart to
  MyReporter's retrospective digest.
- **The single Engine call:** prioritising the gathered issues into
  Now / Next / Later (`prioritize.engine_sections`). Optional and off by default
  (`--engine noop`): with no engine it uses a deterministic label-based grouping,
  and any empty/unparsable reply degrades to that same grouping — never
  fabricates or reorders blindly.
- **Invariants / rules:**
  - Reads issues via `mythings.github.GitHub.list_issues`; reads the plan via
    MyPlanner's ledger on disk (the `read_plan` seam, same one MyOrchestrator
    uses) — **no package dependency on other tools**, runtime dep is
    `mythings-core` only.
  - Writes exactly one file (`TODO.md`) and opens exactly one PR through
    `Policy`; **never merges**, never mutates issues.
  - Idempotent: a re-run with no issue changes writes an identical `TODO.md` and
    is `skipped` (no empty PR).
- **Backlog label:** `my-todo`.
