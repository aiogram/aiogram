# 3x-06 — `SimpleEventIsolation`: prune unused locks safely

| Field | Value |
|---|---|
| Status | `todo` |
| Story | 3x — 3.x quick wins & migration baseline |
| Target branch | `dev-3.x` |
| Depends on | [A-05](../A-contracts/A-05-bench-harness.md) |
| Blocks | — |
| Gate-conditional | no |
| Decisions | R27 (pruning must account for holders and waiters; a bare lock bypasses bookkeeping) |
| Sources | [09 #4, #12](../../research/09-3x-quick-wins.md), [04 §1, §3](../../research/04-fsm.md), [codex-review R27](../../research/codex-review.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

`SimpleEventIsolation._locks` (`aiogram/fsm/storage/memory.py`) is a `defaultdict(Lock)` that is never pruned. The
code carries `# TODO: Unused locks cleaner is needed`. It costs 332 B per key ever seen. Entering and leaving the
`@asynccontextmanager` costs 2.06 µs, against 0.52 µs for a raw `asyncio.Lock` (04 §1).

R27 says pruning must account for holders **and** waiters. It also says #12's "return the bare `asyncio.Lock`" would
bypass that bookkeeping, so #12's lock part is folded in here and dropped if the two conflict.

## Scope

**In:**
- Per-key entry `{lock, users}`. `users` counts holders plus waiters: increment before `acquire`, decrement after
  `release`, including on cancellation and exceptions.
- Delete the entry when `users == 0`.
- There is no `await` between the check and the delete, so this is safe on one event loop.
- Replace the generator-based `@asynccontextmanager` with a small class implementing `__aenter__` / `__aexit__`. It
  is faster, and it keeps the bookkeeping. This is the compatible form of 09 #12.
- Document that `SimpleEventIsolation` is single-loop (as `asyncio.Lock` already is). Cross-thread or free-threaded
  use is out of scope for 3.x.

**Out:**
- Returning a bare `asyncio.Lock` from `lock()` (09 #12 as written). It can't decrement `users`, so pruning would be
  impossible. Rejected unless the session proves otherwise; record the result in Notes.
- The thread-safe lock table: F-02 (4.0).
- `DisabledEventIsolation` `nullcontext()`: [3x-12](3x-12-small-dispatch-costs.md).

## Checklist

- [ ] Baseline with A-05 on `isolation.simple.lock` (enter/exit) and memory after 100k distinct keys.
- [ ] Implement the refcounted entry and the class-based context manager. `lock(key)` keeps its public signature and
      still works as `async with isolation.lock(key):`.
- [ ] Race tests:
  - 3 000 concurrent tasks on one key never run two holders at once (the research saw 13/3000 duplicate-lock races
    with the old creation path);
  - waiters keep the entry alive;
  - a waiter cancelled while queued decrements correctly;
  - the table is empty after all tasks finish.
- [ ] `close()` still clears.
- [ ] 100% coverage.
- [ ] Changelog fragment `CHANGES/<pr>.bugfix.rst`.
- [ ] Migration registry: no entry.

## Acceptance criteria

- After 100k distinct keys have been locked and released, `len(isolation._locks) == 0`.
- No duplicate holders in the 3 000-task race test, run 20 times.
- A-05 `compare` on `isolation.simple.lock`: median not slower than the parent commit. The expected gain is ≈1.5 µs.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Bare `asyncio.Lock` from `lock()` (09 #12) | Bypasses holder/waiter bookkeeping, so pruning can't be done | R27 |
| `setdefault` only | Fixes one creation race, not growth | R27 |
| Weak-value dict of locks | A lock with only waiters can be collected mid-wait if nothing holds it strongly; refcount is explicit | — |

## Validation

```bash
uv run pytest tests --cov=aiogram --cov-report=term-missing
make lint
uv run python -m benchmarks compare --base HEAD~1 --head HEAD --cases isolation.simple.lock
```

## Workflow notes

The pruning rule ("no holder and no waiters") is the one F-02 implements thread-safely in 4.0. Link this PR from
F-02's Notes.

## Notes
