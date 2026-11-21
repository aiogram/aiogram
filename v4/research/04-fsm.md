# 04 — FSM: Python, made thread-safe (no Rust)

Verdict (D5): **stays Python.** The in-process FSM costs ≈8 µs of ≈29 µs dispatch. Pure Python recovers
3–4 µs and halves memory. A Rust store must still hold user data as Python objects, so it would save ≈250 B
per context at most. Redis/Mongo are dominated by round-trips.

## 1. Today

Path: `fsm/middleware.py:46-53` (`bot.id` re-parses the token each call) → `resolve_event_context` (:55)
→ `apply_strategy` (`fsm/strategy.py:19`) → `StorageKey` (frozen dataclass, `storage/base.py:13`) →
`FSMContext` (:123) → `events_isolation.lock(key)` (`memory.py:84`, `asynccontextmanager`) → eager
`get_state()` (:51).

| What | Cost |
|---|---|
| FSM share of `feed_update` | 8.2 µs of 28.8 µs |
| `SimpleEventIsolation.lock` enter/exit | 2.06 µs (raw `asyncio.Lock` 0.52) |
| `StorageKey()` | 0.75 µs (frozen `object.__setattr__`) |
| `StateFilter` (2 states) | 1.8 µs; `State.state` rebuilds f-string each compare (`state.py:25-36`) |
| 100k contexts with state+data | 657 B/ctx = 65.7 MB |
| 100k users **never given a state** | 537 B/ctx = 53.7 MB, because `get_state` reads a `defaultdict` (`memory.py:35,46`) |
| Lock table | +332 B per key ever seen, never pruned (`memory.py:82`) |
| Redis per update | ≥3 round-trips (lock SET NX, Lua release, GET); `update_data` +2; Scene `goto` ≈5 |

## 2. Thread-safety bugs (found with the GIL on, worse without)

| Bug | Evidence |
|---|---|
| Lock table create-then-insert race (`defaultdict(Lock)`, `memory.py:82,86`) | 13/3000 trials returned two different locks for one key, so isolation silently broken |
| `asyncio.Lock` bound to one loop | shared isolation across 2 loops: 400/800 ops `RuntimeError: bound to a different event loop` |
| `MemoryStorage` read-modify-write (`memory.py:43-55`, `base.py:187-189`) | 4×20 000 increments ended at 26 078 |
| Scene history aliasing | `get_data` shallow copy; `HistoryManager.push/pop` (`scene.py:39-60`) mutates the stored list |

## 3. v4 design

- **`MemoryStorage`**: **one `dict` + one `threading.Lock`** (PD-21); no shards until contention is measured.
  Read paths use `.get()` (no record creation). `update_data` is one critical section. Data copies are made inside
  the lock. `HistoryManager` copies the history list before mutating.
- **Isolation**: new lock table that works across threads and loops: per key `{held, waiters: deque[(loop, future)]}`
  under a shard lock. Hand-off on release via `waiter_loop.call_soon_threadsafe(fut.set_result, None)`,
  or a direct `set_result` when on the same loop (keeps the single-loop fast path). Cancelled waiters pass the
  hand-off on. Entries are pruned when there is no holder and no waiters. `DisabledEventIsolation.lock` returns a shared
  `nullcontext()`. **Re-entrant acquisition** of the same key in the same task raises `RuntimeError` (PD-26), so the
  breaking-change-15 deadlock becomes an error.
- **`StorageKey`**: `slots=True`. Keep it frozen (users rely on `dataclasses.replace`, `scene.py:36`);
  `slots` alone saves memory, and the speedup comes from building fewer keys (cache per update).
- **Middleware**: cache `bot.id`; `StateFilter` precomputes a `frozenset` of state strings; `State.state`
  is computed once at class creation.
- **Redis**: 4.0 ships the legacy `RedisStorage` layout only (D113, revises D29; §6). It gets batched
  `HistoryManager` ops and a pipelined state+data read, with no Lua and no multi-key scripts. It is **single-loop**
  in 4.0 (PD-09): use from a second loop raises a clear error, and multi-Runner or sharded deployments with Redis are
  documented as unsupported in 4.0.
- **Mongo**: remove the deprecated `MongoStorage` (motor, no free-threaded wheels); `PyMongoStorage` (PyMongo
  async, already in 3.x) is the only Mongo backend ([11](11-removals.md) §5). Data keys containing `.`, a leading
  `$` or the empty string are rejected with a clear error (D113; dotted-path bug in 3.x). Single-loop like Redis
  (PD-09).
- JSON hooks stay, and the default codec stays **stdlib `json`** (PD-22). The Rust core encoder, which handles
  aiogram types natively (pydantic is not a dependency, D14), is opt-in. Session `json_*` params are a separate,
  deprecated mechanism that never reaches FSM storages (PD-08, 05 §2.3).

## 4. Decisions (D27–D30)

| # | Decision |
|---|---|
| **D27** | **State loading stays eager.** Every update with a user or chat takes the isolation lock and reads the state, then injects `state` + `raw_state`, as in 3.x. Lazy loading was considered and rejected: `raw_state` and middleware contracts stay unchanged |
| **D28** | **Isolation is on by default.** `Dispatcher(events_isolation=None)` means the new thread- and loop-safe in-process lock table (§3), not `DisabledEventIsolation`. Updates of one FSM key are serialised out of the box (≈0.5 µs per update). Multi-process Redis setups still opt into `RedisEventIsolation`; `DisabledEventIsolation()` stays available explicitly. **D110:** `async with state.release_isolation():` lets a handler wait for a later update of the same key, and a warning fires when a key's lock is held longer than `isolation_warn_after` (default 30 s). Incompatible patterns without it: "ask and wait" helpers and re-entrant `feed_update` for the same key (README breaking change 15) |
| **D29** | ~~Two Redis storages side by side~~ (revised by D113, see 19): 4.0 ships the legacy `RedisStorage` layout only; `RedisHashStorage` and its migration tooling are deferred to a 4.x minor (§6) |
| **D30** | **Typed FSM data** (§7): `FSMData` classes in `CallbackData` style with nested types, plus pluggable adapters for pydantic, attrs and msgspec. The dict API stays |

`update_data` is **atomic** in every built-in storage: one lock section for Memory (PD-21), isolation (D28) for
Redis (D113: no Lua, user codec hooks unchanged), and `$set` on `data.<k>` for PyMongo, which already keeps one
document per key and returns an atomic post-update snapshot. `BaseStorage.update_data` keeps its get+set fallback
for custom storages, now documented as non-atomic.

An atomic merge does not make an application read-modify-write atomic (R14): two callers can both read `n=0` and
each atomically write `n=1`. Such updates need isolation (on by default, D28) or a transactional mutation; the
race tests don't treat `update_data` alone as a fix for lost updates.

## 5. Must stay extensible

`BaseStorage`, `BaseEventIsolation`, `KeyBuilder` ABCs; user `StatesGroup`s (`StatesGroupMeta`
hooks); `Scene.__init_subclass__`; arbitrary Python objects in `MemoryStorage` data; `storage.storage[key]`
direct access (document the new shape as a 4.0 change). Registration (StatesGroup, SceneRegistry) after start
applies only on restart or `runner.refresh()` (D114); runtime registration from several threads is unsupported.

## 6. Redis: two layouts (D29, revised by D113)

**D113:** only the legacy `RedisStorage` ships in 4.0. `RedisHashStorage`, the dual read and the migration
tooling below are **deferred to a 4.x minor** and kept here as the plan for that release.

| Storage | Layout | Round trips | Notes |
|---|---|---|---|
| `RedisStorage` | **3.x layout, unchanged**: `…:state` and `…:data` string keys | state+data read pipelined (1 RTT); no Lua, atomicity through isolation (D28, D113) | upgrading from 3.x needs no migration; existing bots keep their states; user codec hooks unchanged; cluster-safe (no multi-key scripts) |
| `RedisHashStorage` (deferred to 4.x, D113) | one hash per key: fields `state`, `data` (JSON) | 1 RTT for any read or write; atomic `update_data` via Lua over `HGET`/`HSET` | `state_ttl`/`data_ttl` collapse into one `ttl` on the hash; per-field TTL is not supported on all Redis versions |

- **Opt-in dual read**: `RedisHashStorage(..., legacy_fallback=True)`. On a missing hash, it reads the 3.x keys,
  writes the hash and deletes the old keys in one Lua script, so records move over as users come back. Off by
  default because it adds a second lookup on every miss.
- **Bulk migration**: `await RedisHashStorage.migrate_from_legacy(redis, key_builder, batch=1000)` does a SCAN over
  the 3.x keys and migrates them idempotently, so it is safe to re-run or interrupt. Also exposed as
  `python -m aiogram.fsm.migrate redis --url … [--prefix fsm] [--dry-run]`. The reverse direction is provided for
  rollback.
- Both storages share `DefaultKeyBuilder` and isolation (`RedisEventIsolation`). The legacy layout follows the
  ledger policy: it stays for all of 4.x, and its future is decided when 5.0 is planned.

## 7. Typed FSM data (D30)

```python
class Address(FSMData):
    city: str
    zip: str | None = None

class OrderForm(FSMData):
    item_id: int
    qty: int = 1
    address: Address | None = None        # nested
    tags: list[str] = []
    created: datetime | None = None

form = await state.get_data(OrderForm)               # -> OrderForm (validated)
await state.update_data(OrderForm, qty=2)            # typed patch: validates each field (D115)
await state.update_data(OrderForm(item_id=5))        # merges only explicitly set fields; other keys kept
await state.set_data(form.replace(qty=2))            # writes the full model
await state.get_data()                               # dict API unchanged
```

- **Model**: `FSMData` uses `typing.dataclass_transform` and is frozen. Fields may be scalars, `Enum`, `datetime`/`date`,
  `Decimal`, `UUID`, `X | None`, `Literal`, `list`/`tuple`/`dict[str, T]`, nested `FSMData`, stdlib dataclasses, and
  aiogram types (stored through the core encoder as wire JSON and decoded back with `from_dict`, D91).
- **Shared converters with `CallbackData` (D14)**: one converter table. `CallbackData` uses its flat-string
  subset and `FSMData` the JSON-shaped, nested superset. The table is built at class creation, so per call
  there is no reflection.
- **Typed patches (D115)**: `update_data(OrderForm, qty=2)` validates each field and needs no full model. Passing a
  model instance merges **only explicitly set fields** (`exclude_unset`), so the default `qty=1` doesn't overwrite a
  stored quantity. Mutable defaults (`tags: list[str] = []`) are copied per instance. `set_data(model)` writes the
  full model.
- **Storage stays dict-based**: models are converted at the `FSMContext` boundary, and storages and key layouts
  are unaffected. Keys that the model doesn't declare are ignored on load and kept on `update_data`.
- **Pluggable adapters** for third-party models:

  ```python
  class DataAdapter(Protocol):
      def supports(self, tp: type) -> bool: ...
      def load(self, tp: type[T], data: Mapping[str, Any]) -> T: ...
      def dump(self, obj: Any) -> dict[str, Any]: ...
  ```

  - Built in: `FSMData`, stdlib dataclasses.
  - Optional adapters ship in core and import their library lazily: `PydanticAdapter` (`BaseModel`),
    `AttrsAdapter`, `MsgspecAdapter` (`Struct`). No new dependencies (D14 still holds).
  - Selection: the first adapter whose `supports(tp)` is true, from `Dispatcher(fsm_data_adapters=[...])`, with
    the built-ins appended. So `await state.get_data(MyPydanticModel)` works once `PydanticAdapter()` is
    registered.
- **Errors**: data that can't be loaded raises `FSMDataError`, which carries the raw dict. Handlers can reset the
  state instead of crashing; this matters after a model changes between deploys.
- **Scenes**: `Scene` subclasses may declare `data: type[FSMData]`, which gives typed `self.wizard.get_data()`.
  This is an addition; the existing dict usage is untouched.

## 8. Scenes (D33)

The 3.x scene semantics are kept; only the parts that are cheap and safe change.

| Topic | 4.0 |
|---|---|
| Scene data | **shared with the user's FSM data, as in 3.x** (`wizard.get_data()` is `state.get_data()`). The docs warn that `reset_data_on_enter` clears all of the user's data and that scenes can collide on keys; namespaced key prefixes are the recommendation. Typed data is available through `Scene.data: type[FSMData]` (D30) |
| Actions picked by update type | rule unchanged. When a transition finds no `enter`/`leave`/`exit`/`back` action for the triggering update type, a **`RuntimeWarning`** names the scene, action and update type (it is a debug log today, `scene.py:578-586`). It fires once per (scene, action, type) |
| Middlewares for actions | unchanged: actions are called directly with the current update's data, and middlewares on the target scene's router don't run for them. This is now stated explicitly in the docs (#1672, #1687) |
| History | full `{state, data}` snapshots as in 3.x (size configurable, default 10). All history operations for one transition go to storage as **one batch** (pipeline on Redis, no Lua (D113), one update on Mongo); a `goto` drops from ≈5 Redis round trips to 1–2 |
| Routing | `StateFilter` on scene routers compiles into a **state index** in the routing snapshot (03 §3, D114). The state is loaded eagerly (D27), so scene routers whose state can't match are skipped instead of checking each scene's root filter. It is a skip optimisation under D111: wildcard/general handlers and DFS precedence are kept |
| Per-call copies | `scenes.data = {**scenes.data, **kwargs}` (`scene.py:260, 715`) becomes one merged view per update. Behaviour is the same, with fewer dict copies |
| Registration | `SceneRegistry` is captured in each Runner's snapshot (D114); `add`/`register` after start applies on restart or `runner.refresh()`, with a one-time warning |

## 9. Tests

Race tests from §2 become regression tests, run on the normal build with tiny `sys.setswitchinterval` and on
3.14t in CI ([07](07-free-threading.md)). Redis: pipelined legacy read, codec hooks, cluster mode (the migration
tests move to the 4.x release that ships `RedisHashStorage`, D113). Mongo: rejected data keys. `release_isolation`
and the hold-time warning (D110). Typed data: converter parity with `CallbackData`, nested round trips,
and one round-trip test per adapter, skipped when the library is missing.
