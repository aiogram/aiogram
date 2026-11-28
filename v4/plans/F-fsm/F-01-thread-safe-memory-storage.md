# F-01 — Thread-safe `MemoryStorage` (one dict + one lock)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | F — FSM & scenes |
| Target branch | `dev-4.x` |
| Depends on | [A-01](../A-contracts/A-01-bootstrap-dev-4x.md), [A-05](../A-contracts/A-05-bench-harness.md), [A-11](../A-contracts/A-11-migration-registry.md) |
| Blocks | [F-05](F-05-storage-record-batch-api.md), [F-13](F-13-scenes-d33.md), [F-16](F-16-race-suite-314t.md) |
| Gate-conditional | no |
| Decisions | D5, D27, D30 (atomic `update_data`), PD-21, R14 |
| Sources | [04-fsm.md §1–§5](../../research/04-fsm.md), [07-free-threading.md §3](../../research/07-free-threading.md), [09-3x-quick-wins.md #3](../../research/09-3x-quick-wins.md), [codex-review.md R14](../../research/codex-review.md), [19](../../research/19-review-resolutions.md), [plans README §1](../README.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

`aiogram/fsm/storage/memory.py` (3.x) has three problems (04 §1–§2):

- `MemoryStorage.storage` is a `defaultdict(MemoryStorageRecord)`. `get_state` / `get_data` / `get_value` **create a
  record on read**, so every user who ever sent an update costs ≈537 B even without a state (53.7 MB per 100k users).
- Read-modify-write is not atomic: `BaseStorage.update_data` does get → update → set across awaits. Under
  threads (free-threaded 3.14t, D8) 4×20 000 increments ended at 26 078.
- Data copies are made outside any lock.

D5 keeps FSM in Python. PD-21 (planning default) revises 04 §3: **one `dict` + one `threading.Lock`**, no 64 shards,
until contention is measured.

## Scope

**In:**
- `MemoryStorage.storage` becomes a plain `dict[StorageKey, MemoryStorageRecord]`; all reads use `.get()` and never
  create records. `set_state(None)` + empty data removes the record (no empty records retained).
- One `threading.Lock` guards every map operation. Critical sections hold only dict/record operations and copies,
  never an `await` and never user callbacks.
- `MemoryStorage.update_data` overrides the base fallback: read, merge, copy and write in **one** critical section;
  returns a copy of the merged dict (same contract as 3.x `BaseStorage.update_data`).
- `get_data` / `set_data` / `get_value` copy inside the lock (top-level `dict.copy()` / `copy.copy`, as in 3.x).
- `StorageKey` gets `slots=True` and stays `frozen=True` (`dataclasses.replace` is used by `HistoryManager` in
  `aiogram/fsm/scene.py` and by users).
- `storage.storage[key]` direct access keeps working on the plain dict (04 §5); document that direct access bypasses
  the lock and is not thread-safe.
- `MemoryStorageRecord` stays (scenes' `HistoryManager` returns it).

**Out:**
- Isolation lock table: [F-02](F-02-isolation-lock-table-default-on.md).
- Record/batch API (`get_record`, transition writes): [F-05](F-05-storage-record-batch-api.md).
- `HistoryManager` copy-on-write: [F-13](F-13-scenes-d33.md).
- Typed data: [F-09](F-09-fsmdata-typed-fsmcontext.md).
- The 3.x `.get()` fix ships separately as 3x-05 on `dev-3.x`; this plan supersedes it on `dev-4.x`.

## Checklist

- [ ] Rewrite `aiogram/fsm/storage/memory.py` `MemoryStorage`: plain dict, `threading.Lock`, `.get()` reads,
      record removal when state is `None` and data is empty.
- [ ] Atomic `MemoryStorage.update_data` (single critical section, returns a copy).
- [ ] `StorageKey` in `aiogram/fsm/storage/base.py`: `@dataclass(frozen=True, slots=True)`; check nothing in the
      tree sets attributes on it (`rg "StorageKey\("`, tests in `tests/test_fsm/`).
- [ ] Decide the nested-value aliasing contract (R14) (**proposed default:** copies stay **shallow at the top level**
      as in 3.x; nested mutable values returned by `get_data` / `get_value` are shared with the stored record; mutate
      them only through `set_data` / `update_data`; no `deepcopy` because MemoryStorage must keep arbitrary Python
      objects, 04 §5) — record in Notes and flag to owner. F-13 applies the same rule to history snapshots.
- [ ] Docstring of `MemoryStorage`: thread-safety boundary (map operations are locked; nested values and
      `storage.storage` direct access are not).
- [ ] Tests in `tests/test_fsm/storage/test_storages.py` (+ a new `test_memory.py` if clearer): no record created by
      reads; record removed on clear; `update_data` returns a copy; slots (`StorageKey.__slots__`, no `__dict__`);
      `dataclasses.replace` on `StorageKey`.
- [ ] Threaded regression test: 4 threads × 20 000 `update_data(n=...)` merges of **distinct keys in one record**
      lose no key (atomic merge). Read-modify-write increments are **not** asserted here (R14; F-16 covers them
      together with isolation).
- [ ] Tests (100% coverage of new code)
- [ ] Migration-registry entry (PD-13, `removal-4.0`/manual checklist): `MemoryStorage.storage` is a plain dict (no
      auto-created records; `storage.storage[key]` raises `KeyError` for unknown keys); `StorageKey` has `__slots__`.
- [ ] Changelog fragment in `CHANGES/` (per the A-01 branch policy).

## Acceptance criteria

- After 100 000 `get_state` / `get_data` calls on distinct keys, `len(storage.storage) == 0`.
- Memory per context with state+data, measured with the A-05 harness FSM scenario (pinned input: 100k keys, one state
  string, data `{"a": 1}`), is ≤ the 3.x baseline recorded by A-06 (657 B/ctx); result recorded in Notes.
- The threaded atomic-merge test passes on CPython 3.13 with `sys.setswitchinterval(1e-6)` and on 3.14t with
  `PYTHON_GIL=0` (the 3.14t run can be local until I-03 provides the CI job).
- No `await` or user code runs while the lock is held (verified by code review and a test that a `__eq__`-raising
  key doesn't leave the lock held: the next operation does not block).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| 64 sharded dicts with a lock per shard (04 §3) | No measured contention; breaks `storage.storage[key]` direct access (04 §5) | PD-21 |
| Rust store | Must still hold Python objects; saves ≈250 B/ctx at most | D5, 04 intro |
| `deepcopy` on every read | Slow, fails on arbitrary objects users store | 04 §5 (extensibility) |
| Unfrozen `StorageKey` | Users rely on `dataclasses.replace` and hashing | 04 §3 |

## Validation

```bash
make dev                                   # builds the _core extension (B-01 skeleton)
uv run pytest tests/test_fsm -q
uv run pytest tests
make lint                                  # ruff + mypy + pre-commit, as CI
PYTHON_GIL=0 uv run --python 3.14t pytest tests/test_fsm -q   # when a 3.14t interpreter is available
```

## Workflow notes

- Runs in parallel with F-02, F-04, F-08.
- Output used by F-05 (`get_record` Memory implementation), F-13 (aliasing rule) and F-16 (race suite).
- If 3x-05 already landed on `dev-3.x` and was merged forward, start from that code.

## Notes
