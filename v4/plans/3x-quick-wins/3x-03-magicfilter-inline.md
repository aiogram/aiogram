# 3x-03 — Resolve `MagicFilter` inline; backport `blocking(fn)` as the thread escape

| Field | Value |
|---|---|
| Status | `todo` |
| Story | 3x — 3.x quick wins & migration baseline |
| Target branch | `dev-3.x` |
| Depends on | [A-05](../A-contracts/A-05-bench-harness.md) (own-baseline measurement); [A-10](../A-contracts/A-10-routing-oracle.md) (routing oracle, used as an invariance check) |
| Blocks | [A-06](../A-contracts/A-06-record-3x-baselines.md), [3x-11](3x-11-prebuilt-middleware-chains.md), [E-07](../E-runtime/E-07-sync-filter-execution.md) |
| Gate-conditional | no |
| Decisions | D34 (forward-compatible subset), D37, D120, R27, PD-28 |
| Sources | [09 #1](../../research/09-3x-quick-wins.md), [03 §2](../../research/03-routing.md), [03 §5 Filters](../../research/03-routing.md), [codex-review R27](../../research/codex-review.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

`FilterObject.__post_init__` (`aiogram/dispatcher/event/handler.py`) replaces a `MagicFilter` with its sync
`.resolve` method. `CallableObject.awaitable` is then false, so `CallableObject.call` runs every `F` filter through
`asyncio.to_thread`: 43.4 µs instead of 0.78 µs per filter. On the 52-handler router, the worst case is 1 900 µs
per update instead of 220 µs (03 §2). This has been the case since #1661.

D120 and R27: inline resolution is a behaviour change. `F.func(blocking_fn)` would now block the loop, so the PR has
to ship with a thread-mode escape. A changelog note alone isn't enough.

## Scope

**In:**
- `MagicFilter` instances (aiogram's `F` and plain `magic_filter.F`) are resolved **inline** on the event loop. In
  `FilterObject`, the resolved callable is treated as "inline sync", not as a thread job.
- User sync filter functions and sync handlers **keep the thread** (no 3.x change here; D34's "sync filters inline by
  default" is 4.0 only, E-07).
- Backport `blocking(fn)` from D34 as the escape, in its 4.0 name and location so user code keeps working on 4.0.
  Location (agreed with E-07): exported as `aiogram.filters.blocking` (`from aiogram.filters import blocking`).
  - `blocking(F.func(slow))` or `blocking(some_magic)` runs that filter in a thread, as 3.x did before this fix.
  - Applied to a sync function, it is a no-op marker in 3.x, because those already run in a thread.
- Docs: filters page notes that magic filters run on the loop, with the `blocking()` recipe.

**Out:**
- `inline(fn)`, `SyncFilterMode` and `Dispatcher(sync_filters=…)`: 4.0 only, E-07. Backporting them would change the
  3.x default for user sync filters.
- Removing the `Recommendation` warning: [3x-21](3x-21-import-attribute-warnings.md) and E-01.

## Checklist

- [ ] Baseline with A-05 on `routing.52-handlers` (first / mid / last / unhandled) and `routing.20-ftext`.
- [ ] Change `FilterObject` so a `MagicFilter` callback runs inline. Keep `CallableObject.call` untouched for
      everything else.
- [ ] Add `blocking(fn)`:
  - a thin wrapper class recognised by `FilterObject` and `CallableObject`, which forces `asyncio.to_thread`;
  - export it from `aiogram.filters`;
  - type it so `blocking(F.x)` and `blocking(callable)` both type-check.
- [ ] `blocking()` on an **async** callable raises `TypeError` at wrap time, naming the callable — the behaviour E-07
      ships in 4.0 (E-07 scope and acceptance); test it.
- [ ] Run the A-10 routing oracle, parent commit vs this commit. Every case must be invariant except the timing.
- [ ] Tests:
  - an `F` filter doesn't enter `asyncio.to_thread` (patch and assert not called);
  - `blocking(F.func(fn))` does;
  - sync user filters still use the thread;
  - `Recommendation` still fires for a plain `magic_filter.F`.
- [ ] 100% coverage.
- [ ] Changelog fragment `CHANGES/<pr>.feature.rst`:
  - "Magic filters are resolved on the event loop instead of a worker thread (≈50× faster). Filters calling blocking
    code through `F.func(...)` should be wrapped in `blocking(...)`.";
  - ship in a 3.x **minor** (PD-28).
- [ ] Migration registry: no new entry. 4.0's breaking change 16 (sync filters inline) belongs to E-07, and
      `blocking()` keeps working on 4.0.

## Acceptance criteria

- A-05 `compare` on `routing.52-handlers`: the worst-case (unhandled) median falls by ≥ 5× against the parent
  commit. The research expectation is 1 900 → ≈220 µs; the A-05 numbers are authoritative.
- The A-10 routing oracle reports no mismatch apart from approved timing-only differences.
- `blocking` is importable from `aiogram.filters`, with the same name and semantics E-07 ships in 4.0.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Fix with only a changelog note | `.func(blocking_fn)` would block the loop silently | D120, R27 |
| 3.x-only knob (e.g. `Dispatcher(magic_filters_in_thread=True)`) | Creates debt that 4.0 removes; `blocking()` is forward-compatible | D34 |
| Backport `SyncFilterMode.INLINE` as the 3.x default | Changes user sync filters in a minor | D34 is 4.0 breaking change 16 |

## Validation

```bash
uv run pytest tests --cov=aiogram --cov-report=term-missing
make lint
uv run python -m benchmarks compare --base HEAD~1 --head HEAD --cases routing.52-handlers,routing.20-ftext
uv run python -m differential run --kind routing --left git:HEAD~1 --right git:HEAD   # A-07/A-10 CLI
```

## Workflow notes

- Biggest single input to the "optimised 3.x" dispatch baseline (A-06), which the end-to-end dispatch gate of B-13
  compares against.
- E-07 must keep the `blocking()` name and import path. Mention this PR in E-07's Notes when it starts.
- Parallel with 3x-11 and 3x-12. They all touch `aiogram/dispatcher/**`, so rebase in order 3x-03 → 3x-11 → 3x-12.

## Notes

- Coordinator default (reconciliation, K15): `blocking()` on an async callable raises `TypeError`, matching E-07.
