# F-02 — Cross-thread, cross-loop isolation lock table, on by default (D28)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | F — FSM & scenes |
| Target branch | `dev-4.x` |
| Depends on | [A-01](../A-contracts/A-01-bootstrap-dev-4x.md), [A-05](../A-contracts/A-05-bench-harness.md), [A-06](../A-contracts/A-06-record-3x-baselines.md), [A-11](../A-contracts/A-11-migration-registry.md), [H-01](../H-testing-observability/H-01-logger-hierarchy.md) |
| Blocks | [F-03](F-03-release-isolation-warn-after.md), [F-16](F-16-race-suite-314t.md), [E-19](../E-runtime/E-19-multi-runner-free-threading-sharding.md), [G-02](../G-features/G-02-depends-scope-teardown.md), [E-22](../E-runtime/E-22-single-bot-sharding.md) |
| Gate-conditional | no |
| Decisions | D8, D28, D110, R14, PD-21 (single lock rule applied to the table), PD-06 |
| Sources | [04-fsm.md §2–§4](../../research/04-fsm.md), [07-free-threading.md §1, §3](../../research/07-free-threading.md), [codex-review.md R14](../../research/codex-review.md), [19 D110](../../research/19-review-resolutions.md), [README breaking change 15](../../research/README.md), [plans README §1](../README.md) |
| Size | L (4–5 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

3.x `SimpleEventIsolation` (`aiogram/fsm/storage/memory.py`) is a `defaultdict(asyncio.Lock)`:

- create-then-insert race: 13/3000 trials returned two different locks for one key (isolation silently broken);
- `asyncio.Lock` is bound to one loop: with one shared isolation across 2 loops, 400/800 operations raised
  `RuntimeError: ... bound to a different event loop`;
- locks are never pruned (+332 B per key ever seen).

4.0 shares one `Dispatcher` (and its isolation) across Runner threads (07 §1, E-19). D28 makes isolation **on by
default**: `Dispatcher(events_isolation=None)` means this new table, not `DisabledEventIsolation`.

## Scope

**In:**
- New in-process isolation (keep the public name `SimpleEventIsolation`; it becomes the default) with a lock table
  `dict[StorageKey, _Entry]` guarded by **one** `threading.Lock` (PD-21 applied to the table). `_Entry` =
  `{holder, held_since, waiters: deque[_Waiter]}`, `_Waiter` = `(loop, future, state)`.
- Uncontended fast path: lookup/create entry, mark held, no future, no timer.
- Contended path: waiter future created on the **waiter's** loop; hand-off on release by
  `waiter_loop.call_soon_threadsafe(_grant, waiter)` or a direct grant when the releaser is on the same loop.
- Strict FIFO hand-off; new acquirers don't barge while waiters exist.
- Cancellation-safe hand-off and closed-loop waiters (see the state-machine decision below).
- Pruning: an entry is removed under the table lock when it has no holder and no waiters; acquire always looks
  up/creates under the table lock, so a pruned entry is never reused.
- `lock(key)` yields a **handle** object (3.x yields `None`); F-03 adds `release_isolation` / release hooks on it.
  `BaseEventIsolation.lock` stays an async context manager (custom isolations keep working; their handle is `None`).
- `DisabledEventIsolation.lock` returns one shared `nullcontext()` object.
- `Dispatcher.__init__` (`aiogram/dispatcher/dispatcher.py`): `events_isolation=None` → `SimpleEventIsolation()`;
  `DisabledEventIsolation()` stays available explicitly. Coordinate with E-01/E-13 if they touch the constructor.
- Benchmark against A-06 baselines.

**Out:**
- `release_isolation()`, `isolation_warn_after`, release hooks (PD-04), re-entrancy error (PD-26): [F-03](F-03-release-isolation-warn-after.md).
- Isolation-key computation for sharding (PD-06): [F-04](F-04-fsm-hot-paths-statefilter.md).
- `RedisEventIsolation` changes beyond the handle: F-03 (release) and F-06 (single-loop detection).
- The 3.x pruning fix ships as 3x-06 on `dev-3.x`; superseded here.

## Checklist

- [ ] Decide the R14 hand-off state machine (**proposed default:** waiter states `QUEUED → GRANTED → ACQUIRED`, plus
      `CANCELLED`/`DEAD`. The releaser, under the table lock, pops the first `QUEUED` waiter, sets it `GRANTED` and
      makes it the holder **before** scheduling the future result; ownership transfers at that moment. A waiter
      cancelled while `QUEUED` removes itself. A waiter cancelled while `GRANTED` already owns the lock and releases
      it in its `CancelledError` path (passes it on). If `call_soon_threadsafe` raises because the waiter's loop is
      closed, the waiter is marked `DEAD` and the releaser grants the next one. Strict FIFO, no barging; no starvation
      because every release grants exactly one waiter. The table lock is never held across `await` or user code, so
      an event-loop thread never blocks on a holder that needs that loop) — record in Notes and flag to owner.
- [ ] Decide the startup warning for in-process isolation with a storage that provides `create_isolation()` (e.g.
      `RedisStorage`) (**proposed default:** one `logging` WARNING on the `aiogram.fsm` logger (H-01) at dispatcher
      startup when `events_isolation` was not passed and `storage.create_isolation` exists, saying isolation and
      `update_data` atomicity are per-process only; passing `events_isolation=` explicitly suppresses it) — record in
      Notes and flag to owner.
- [ ] Implement the table, handle, FIFO hand-off, cancellation and closed-loop handling, pruning.
- [ ] `DisabledEventIsolation`: shared `nullcontext()`.
- [ ] Default switch in `Dispatcher.__init__`; update docstrings and `docs/dispatcher/finite_state_machine/index.rst`
      (isolation section) for breaking change 15 (F-17 writes the full page).
- [ ] Unit tests (`tests/test_fsm/storage/test_isolation.py`): one lock per key under 8 threads × concurrent first
      acquire; two loops in two threads share one isolation without `RuntimeError`; FIFO order; pruning to
      `len(table) == 0` after all releases; cancellation while queued and while granted (inject cancellation between
      grant and resumption with a controlled loop); closed waiter loop; no leaked entries after 10k random
      acquire/cancel cycles.
- [ ] Benchmark (A-05 harness): uncontended `async with isolation.lock(key)` enter/exit.
- [ ] Tests (100% coverage of new code)
- [ ] Migration-registry entry (PD-13): breaking change 15, isolation on by default; opt out with
      `events_isolation=DisabledEventIsolation()` (manual-checklist class, the I-19 heuristic rule reads it).
- [ ] Changelog fragment in `CHANGES/`.

## Acceptance criteria

- 3000/3000 trials of concurrent first acquisition from 8 threads observe a single holder at a time (the 3.x bug
  reproduced 13/3000).
- 800/800 operations across 2 loops in 2 threads succeed (3.x: 400/800 failed).
- After every acquire/release/cancel test, the table is empty.
- Adversarial cancellation tests at each state transition leave no holder without an owner and no waiter waiting
  forever (each test has a 5 s timeout).
- Uncontended enter/exit ≤ **1.0 µs** on the A-05 reference machine, and faster than the 3.x
  `SimpleEventIsolation.lock` baseline (2.06 µs, A-06). D28 states ≈0.5 µs; record the measured value in Notes.
- `Dispatcher()` with no `events_isolation` uses `SimpleEventIsolation`; existing dispatcher tests pass.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Isolation off by default (3.x) | Lost updates and racy scenes by default; kept on, with an escape hatch | D28, D110 |
| `asyncio.Lock` per key | Loop-bound; can't serve per-thread loops | 04 §2, 07 §1 |
| Sharded lock table | No measured contention; same reasoning as MemoryStorage | PD-21 |
| Blocking `threading.Lock` per key held across the handler | Blocks an event-loop thread while the holder may need it | R14 |
| Lazy state loading to avoid the lock | Breaks `raw_state` and middleware contracts | D27 |

## Validation

```bash
make dev
uv run pytest tests/test_fsm tests/test_dispatcher -q
uv run pytest tests
make lint
PYTHON_GIL=0 uv run --python 3.14t pytest tests/test_fsm -q   # when available; CI job comes from I-03
```

## Workflow notes

- Parallel with F-01, F-04, F-08.
- F-03 builds on the handle object; keep its type private but stable (`_IsolationHandle`) so F-03 can extend it.
- E-19 (multi-Runner) and E-22 (single-bot sharding, PD-06) rely on this table being thread-shared on the Dispatcher; the key function is
  in F-04.
- 3x-06 is the 3.x counterpart; it is not a dependency.

## Notes
