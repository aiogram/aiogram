# E-07 — Sync filter execution: `SyncFilterMode`, `inline()` / `blocking()`, dict-overwrite warning

| Field | Value |
|---|---|
| Status | `todo` |
| Story | E — Routing & runtime |
| Target branch | `dev-4.x` |
| Depends on | [E-02](E-02-dispatch-table-executor.md), [3x-03](../3x-quick-wins/3x-03-magicfilter-inline.md) |
| Blocks | [E-08](E-08-magic-filter-compile.md), [G-01](../G-features/G-01-param-resolver-hook.md), [E-21](E-21-e-exit-gate.md), [I-19](../I-distribution/I-19-heuristic-behaviour-rules.md) |
| Gate-conditional | no |
| Decisions | D34, D35, D36, README breaking change 16 |
| Sources | [03-routing.md §5 "Filters"](../../research/03-routing.md), [09 #1](../../research/09-3x-quick-wins.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

`CallableObject.call` runs every non-awaitable callable through `asyncio.to_thread` (≈43 µs per hop vs 0.78 µs inline),
including sync filters, and filters share the default thread pool with sync handlers (03 §5). D34 makes sync filters
inline by default with a global and per-filter escape. 3x-03 already backports `blocking(fn)` on 3.x; this plan
implements the 4.0 default.

## Scope

**In:**
- `SyncFilterMode(StrEnum)` in `aiogram.filters` (hand-written): `INLINE = "inline"`, `THREAD = "thread"`.
  `Dispatcher(sync_filters=SyncFilterMode.INLINE)` default; strings accepted.
- `inline(fn)` and `blocking(fn)` markers in `aiogram.filters`, working for lambdas and `Filter` instances.
  `blocking` is exported as `aiogram.filters.blocking` — the same name, path and semantics 3x-03 backports to 3.x.
  Applying `blocking()` or `inline()` to an **async** callable (or an awaitable-returning `Filter`) raises `TypeError`
  at wrap time, naming the callable.
- The awaitable / inline / thread decision is part of the **compiled filter plan** (per snapshot, because the mode is
  per dispatcher and a router can be shared): `CallableObject` keeps its cached signature spec; the execution kind is
  chosen in `compile_table`.
- Sync **handlers** keep `to_thread` (unchanged).
- **D36:** when a filter's dict result overwrites an existing key in `data`, a `RuntimeWarning` fires once per
  (filter, key); the merge is unchanged (later wins).
- **D35:** confirm `Filter` defines no `__and__` / `__or__`; `and_f`, `or_f`, `invert_f` / `~` stay the combinators
  (`aiogram/filters/logic.py`). Add a test that `Filter() & Filter()` raises `TypeError`.

**Out:**
- `F` compilation (E-08); compiled rejectors (E-09).

## Checklist

- [ ] `SyncFilterMode`, `inline`, `blocking`, exported from `aiogram.filters`.
- [ ] `Dispatcher(sync_filters=...)` parameter (stored, epoch-bumping per E-03 if changed later).
- [ ] Execution kind compiled per snapshot; `blocking(fn)` always threads; `inline(fn)` always inline.
- [ ] D36 warning once per (filter, key).
- [ ] D35 test.
- [ ] Docs: filters page section "sync filters run on the event loop" with `blocking()` and `SyncFilterMode.THREAD`.
- [ ] Migration-registry entry (PD-13) for breaking change 16 (heuristic checker rule: sync function filters doing
  I/O) and a changelog fragment.
- [ ] Tests: sync filter runs in the loop thread under INLINE, in a worker thread under THREAD and with `blocking`;
  same router shared by two dispatchers with different modes behaves per dispatcher.

## Acceptance criteria

- A sync filter under the default mode never leaves the event-loop thread (`threading.get_ident()` assertion).
- Bench (A-04 case `routing.52-handlers` with its 26 `F.text ==` filters replaced by sync lambdas, A-05 harness): per-filter cost ≤ 2 µs (vs ≈43 µs threaded).
- Warning count for a repeated overwrite over 1 000 updates is exactly 1.
- `from aiogram.filters import blocking` works, and code written against the 3x-03 backport runs unchanged.
- `blocking(async_fn)` and `inline(async_fn)` raise `TypeError` immediately.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Keep 3.x thread default for filters | 43 µs per hop and pool contention with blocking handlers | D34 |
| `&` / `|` operators on `Filter` | Precedence surprises (`&` binds tighter than `==`) | D35 |
| Raise on dict-result overwrite | Breaks existing code relying on later-wins | D36 |

## Validation

```bash
make dev
uv run pytest tests -q
make lint
uv run mypy aiogram
uv run python -m benchmarks compare --base v4-baseline/3.x-optimised --head WORKTREE --cases routing.52-handlers
```

## Workflow notes

- G-01 (ParamResolver) uses the same per-snapshot callable compile seam; keep it a function taking
  `(callable_object, snapshot_config)` so resolvers can attach.

## Notes

- Coordinator default (reconciliation, K15): `blocking()` / `inline()` on an async callable raise `TypeError`; 3x-03
  ships the same behaviour.
