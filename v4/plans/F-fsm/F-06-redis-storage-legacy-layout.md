# F-06 — `RedisStorage`: 3.x layout, pipelined reads/writes, single-loop detection

| Field | Value |
|---|---|
| Status | `todo` |
| Story | F — FSM & scenes |
| Target branch | `dev-4.x` |
| Depends on | [F-05](F-05-storage-record-batch-api.md), [A-11](../A-contracts/A-11-migration-registry.md) |
| Blocks | [F-13](F-13-scenes-d33.md), [F-16](F-16-race-suite-314t.md), [F-17](F-17-fsm-docs-migration-page.md) |
| Gate-conditional | no |
| Decisions | D28, D29 (revised), D113, PD-09, PD-22, PD-06 (conflict, see Notes) |
| Sources | [04-fsm.md §3 Redis, §6, §9](../../research/04-fsm.md), [19 D113](../../research/19-review-resolutions.md), [codex-review.md R15](../../research/codex-review.md), [07-free-threading.md §1](../../research/07-free-threading.md), [plans README §1 PD-09, PD-22](../README.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

`aiogram/fsm/storage/redis.py` (3.x) costs ≥3 round trips per update (lock `SET NX`, Lua release, `GET`),
`update_data` +2, a scene `goto` ≈5 (04 §1). D113: 4.0 ships **only the legacy layout** (`…:state` / `…:data`
string keys, no migration), with a pipelined state+data read in 1 RTT, no Lua, user codec hooks unchanged, atomicity
through isolation, cluster-safe. PD-22: stdlib `json` stays the default codec. PD-09: Redis storages are
**single-loop** in 4.0; use from a second loop raises a clear error.

## Scope

**In:**
- Key layout, `DefaultKeyBuilder`, `state_ttl` / `data_ttl`, `json_loads` / `json_dumps` hooks: unchanged.
  Default codec stays `json.loads` / `json.dumps` (PD-22).
- `get_records(*keys)`: one pipeline (`transaction=False`) of `GET state` + `GET data` per key, so **1 RTT**.
- `apply_writes(*writes)`: one pipeline of `SET … EX` / `DEL` per part, so 1 RTT, no Lua, no multi-key scripts.
  Pipelines are non-transactional (cluster-safe across slots); serialisation of one FSM key comes from isolation.
- `update_data`: get + merge + set, documented as atomic **only under isolation** of the same key; under the default
  in-process isolation (D28) that means per process. Multi-process deployments must use `RedisEventIsolation`
  (`storage.create_isolation()`); F-02 emits the startup warning if decided.
- **Single-loop detection (PD-09)** in `RedisStorage` and `RedisEventIsolation`: remember the running loop on first
  use; any later call from a different running loop raises `RuntimeError` naming the class and saying "one storage
  per event loop; multi-Runner/sharded deployments with Redis are unsupported in 4.0". Cost: one
  `asyncio.get_running_loop()` comparison per call.
- Cluster-mode test (redis-py `RedisCluster`) for state/data and pipelines.
- Docs (`docs/dispatcher/finite_state_machine/storages.rst`): single-loop rule, multi-process isolation guidance, the
  redis-py lock `timeout=60` caveat (F-03), scenes need `DefaultKeyBuilder(with_destiny=True)` (3.x rule, history key).

**Out:**
- `RedisHashStorage`, dual read, `migrate_from_legacy`, `python -m aiogram.fsm.migrate`: deferred to 4.x (D113).
- Rust encoder as codec: opt-in helper in [F-12](F-12-aiogram-types-in-fsmdata.md) (PD-22).
- Release/re-acquire of `RedisEventIsolation`: [F-03](F-03-release-isolation-warn-after.md).

## Checklist

- [ ] `RedisStorage.get_records` / `apply_writes` (pipelines), keep every 3.x method's behaviour and key names.
- [ ] Loop-binding check in `RedisStorage` and `RedisEventIsolation` (PD-09) with a clear error message.
- [ ] Round-trip counter test helper (wrap the connection's `send_packed_command` or use `CLIENT INFO`/`MONITOR` on the
      test server) used in acceptance tests.
- [ ] Tests: `tests/test_fsm/storage/test_redis_mock.py` (pipeline shape, codec hooks called once per part, second-loop
      `RuntimeError`), `test_storages.py` under `--redis` (layout unchanged: a record written by the 3.x code path is
      readable, and vice versa), cluster test (skipped without a cluster URL).
- [ ] Docs as listed in Scope.
- [ ] Tests (100% coverage of new code)
- [ ] Migration-registry entry (PD-13): Redis/Mongo storages are single-loop in 4.0 (manual checklist).
- [ ] Changelog fragment in `CHANGES/`.

## Acceptance criteria

- `get_records(key)` and `apply_writes(...)` over 2 keys each take exactly 1 round trip (round-trip counter).
- Data written by 3.x `RedisStorage` (pinned 3.x venv, PD-12) is read back identically by 4.0 and vice versa: no
  migration.
- Custom `json_dumps`/`json_loads` hooks are called and their output stored as-is.
- Using one `RedisStorage` from a second running loop raises `RuntimeError` with the documented message.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| `RedisHashStorage` (one hash per key, 1 RTT, Lua `update_data`) + migration tooling | Deferred to a 4.x minor: TTL collapse, codec-in-Lua, cluster and mixed-version migration problems | D113 (revises D29), R15 |
| Lua read/merge/write for atomic `update_data` | Can't run user codec hooks; atomicity comes from isolation | D113 |
| Rust encoder as the default `json_dumps` | Changes stored bytes and makes the default gate-dependent | PD-22 |
| Per-loop client map | Not decided for 4.0; see the open question in Notes | PD-09 |

## Validation

```bash
make dev
uv run pytest tests/test_fsm -q
uv run pytest --redis redis://localhost:6379/0 tests/test_fsm -q
uv run pytest tests
make lint
```

## Workflow notes

- Parallel with F-07 after F-05. F-13 relies on `apply_writes` for batched scene transitions.
- E-19 (multi-Runner, PD-09 guard) and E-22 (sharding) must document Redis as unsupported for sharded deployments while PD-09 stands.

## Notes

- **Open owner question (PD-09 vs PD-06).** PD-06 ships single-bot thread sharding in 4.0 (one bot's updates over
  N Runner threads, each with its own loop). PD-09 makes Redis/Mongo storages single-loop. A sharded deployment that
  uses Redis therefore can't share one storage, and since the storage hangs off the thread-shared `Dispatcher`, it
  can't use Redis at all. Options:
  - **(a)** keep the restriction as decided: sharded or multi-Runner deployments with Redis/Mongo are documented as
    unsupported in 4.0, and the loop check raises;
  - **(b)** a per-loop client map for `from_url`-built storages: the storage keeps the URL and connection kwargs and
    lazily creates one `Redis` client per running loop (weakly keyed by the loop, closed in `close()`); a storage built
    from a user-passed `Redis` instance stays single-loop and raises as in (a).

  This plan implements (a). If the owner picks (b), add it as a follow-up plan in F and update PD-09.
