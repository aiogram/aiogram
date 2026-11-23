# F-05 — Storage record and batch API (`get_records` / `apply_writes`) with fallbacks

| Field | Value |
|---|---|
| Status | `done` |
| Story | F — FSM & scenes |
| Target branch | `dev-4.x` |
| Depends on | [F-01](F-01-thread-safe-memory-storage.md) |
| Blocks | [F-06](F-06-redis-storage-legacy-layout.md), [F-07](F-07-mongo-remove-motor-key-validation.md), [F-13](F-13-scenes-d33.md) |
| Gate-conditional | no |
| Decisions | D27, D30 (atomic `update_data` note), D33 (batched history), D113, R14, R15 |
| Sources | [04-fsm.md §4 note, §8 History](../../research/04-fsm.md), [19 D113](../../research/19-review-resolutions.md), [codex-review.md R14, R15](../../research/codex-review.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

D113 promises a "pipelined state+data read in 1 RTT" for Redis and D33 promises that all history operations of one
scene transition go to storage "as one batch" (a `goto` drops from ≈5 Redis round trips to 1–2). The `BaseStorage`
ABC (`aiogram/fsm/storage/base.py`) has no operation that reads or writes more than one part, so neither promise has a
caller or an entry point. The FSM middleware reads only the state eagerly (D27) and must not start prefetching data on
every update (extra bandwidth, stale reads after `release_isolation`).

Scene history lives under a **different key** (`destiny="scenes_history"`, `HistoryManager` in
`aiogram/fsm/scene.py`), so a transition touches two keys.

## Scope

**In:**
- `StorageRecord` (frozen, slots): `state: str | None`, `data: dict[str, Any]`. Keep `MemoryStorageRecord` as the
  Memory internal record (scenes currently return it; F-13 decides whether to switch).
- `BaseStorage.get_records(*keys: StorageKey) -> list[StorageRecord]`: non-abstract; default fallback calls
  `get_state` + `get_data` per key sequentially.
- `StorageWrite(key, state=UNCHANGED, data=UNCHANGED)` and `BaseStorage.apply_writes(*writes) -> None`: non-abstract;
  default fallback applies `set_state` / `set_data` in order. `state=None` clears the state, `data={}` clears data
  (same as 3.x `set_*`).
- **Contract (documented in `BaseStorage` docstrings):** no atomicity across keys or parts is promised by any
  storage; serialisation of one FSM key comes from isolation (D28). `update_data` is atomic in the built-in storages;
  the base fallback is get + set and is **not** atomic for custom storages. An atomic merge does not make an
  application read-modify-write atomic (R14): two callers can both read `n=0` and write `n=1`.
- `MemoryStorage` implements both under its single lock (one critical section per call).
- `FSMContext.get_record()` convenience returning the record for its key.

**Out:**
- Redis pipelined implementation: [F-06](F-06-redis-storage-legacy-layout.md).
- Mongo `bulk_write` implementation: [F-07](F-07-mongo-remove-motor-key-validation.md).
- Using the API in scenes: [F-13](F-13-scenes-d33.md).
- Changing the middleware's eager read (stays state-only, D27).

## Checklist

- [ ] `StorageRecord`, `StorageWrite`, `UNCHANGED` sentinel in `aiogram/fsm/storage/base.py`.
- [ ] `BaseStorage.get_records` / `apply_writes` fallbacks; docstrings with the atomicity contract above.
- [ ] `MemoryStorage` overrides (single critical section).
- [ ] `FSMContext.get_record()`.
- [ ] Tests: fallback on a minimal custom storage (only the abstract methods) gives identical results to Memory; write
      ordering; `UNCHANGED` leaves parts untouched; Memory override is one lock acquisition (patched lock counter).
- [ ] Tests (100% coverage of new code)
- [ ] Changelog fragment in `CHANGES/` (additive API).

## Acceptance criteria

- A custom storage implementing only the 3.x abstract methods passes the shared storage test suite including the new
  methods (`tests/test_fsm/storage/test_storages.py` parametrised over Memory and the custom one).
- `MemoryStorage.apply_writes` of 3 writes over 2 keys takes the lock once.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Prefetch data together with state in the middleware | Changes D27's eager-state contract, costs bandwidth, stale after `release_isolation` | D27 |
| Lua script for multi-key atomic transitions | No Lua; cluster-unsafe across keys; user codec hooks can't run server-side | D113, R15 |
| Promise cross-key atomicity | No backend can give it cheaply (Mongo would need transactions); isolation serialises a key | R15 |

## Validation

```bash
make dev
uv run pytest tests/test_fsm -q
uv run pytest tests
make lint
```

## Workflow notes

- F-06 and F-07 implement backend versions in parallel after this lands; F-13 consumes the API.

## Notes
