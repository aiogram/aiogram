# F — FSM & scenes

Branch: `dev-4.x`. Sources: [04-fsm.md](../../research/04-fsm.md), [07-free-threading.md](../../research/07-free-threading.md),
[19-review-resolutions.md](../../research/19-review-resolutions.md) (normative), planning decisions in
[../README.md §1](../README.md).

## Goal

The FSM stays Python (D5) and becomes safe under free-threading and per-thread loops:

- a thread-safe `MemoryStorage` (one dict + one lock, PD-21);
- an isolation lock table that works across threads and loops and is **on by default** (D28), with
  `release_isolation()`, `isolation_warn_after` (D110), release hooks for Depends teardown (PD-04) and a
  re-entrancy error (PD-26);
- `RedisStorage` on the 3.x layout with pipelined 1-RTT reads (D113; `RedisHashStorage` deferred to 4.x);
- `PyMongoStorage` only, with key validation (motor `MongoStorage` removed);
- stdlib json as the default codec (PD-22), and single-loop Redis/Mongo storages (PD-09);
- typed FSM data (`FSMData`, typed patches, adapters; D30, D115) on a converter core shared with a pydantic-free
  `CallbackData` (D14);
- scenes with batched history, a missing-action `RuntimeWarning` and a state index in the routing snapshot (D33).

## Exit gate

Race tests pass on 3.14t (F-16), and the application lost-update limits are documented (F-16, F-17).

## Tasks

| ID | Title | Depends on | Gate-cond. | Size |
|---|---|---|---|---|
| [F-01](F-01-thread-safe-memory-storage.md) | Thread-safe `MemoryStorage` (PD-21) | A-01, A-05, A-11 | no | M |
| [F-02](F-02-isolation-lock-table-default-on.md) | Isolation lock table, on by default | A-01, A-05, A-06, A-11, H-01 | no | L |
| [F-03](F-03-release-isolation-warn-after.md) | `release_isolation`, `warn_after`, release hooks, re-entrancy error | A-11, F-02, H-01 | no | M |
| [F-04](F-04-fsm-hot-paths-statefilter.md) | FSM hot paths, StateFilter introspection, isolation-key function | A-01, A-05 | no | S |
| [F-05](F-05-storage-record-batch-api.md) | Storage record/batch API | F-01 | no | M |
| [F-06](F-06-redis-storage-legacy-layout.md) | `RedisStorage` 3.x layout, pipelines, single-loop | A-11, F-05 | no | M |
| [F-07](F-07-mongo-remove-motor-key-validation.md) | Mongo: remove motor, key validation | A-11, F-05 | no | M |
| [F-08](F-08-shared-converter-core.md) | Shared converter core | A-01 | no | L |
| [F-09](F-09-fsmdata-typed-fsmcontext.md) | `FSMData` + typed `FSMContext` | F-08 | no | L |
| [F-10](F-10-pydantic-attrs-msgspec-adapters.md) | pydantic/attrs/msgspec adapters | F-09 | no | M |
| [F-11](F-11-callbackdata-without-pydantic.md) | `CallbackData` without pydantic | A-11, B-13, F-08 | **yes** | M |
| [F-12](F-12-aiogram-types-in-fsmdata.md) | aiogram types in FSM data; opt-in core codec | B-06, B-13, D-07, F-09 | **yes** | S |
| [F-13](F-13-scenes-d33.md) | Scenes D33 | E-03, F-01, F-03, F-05, F-06, F-07 | no | M |
| [F-14](F-14-typed-scene-data.md) | Typed scene data | F-09, F-13 | no | S |
| [F-15](F-15-statefilter-state-index.md) | StateFilter state index | E-02, E-03, E-09, F-04, F-13 | no | M |
| [F-16](F-16-race-suite-314t.md) | Race suite on 3.14t (**exit gate**) | E-22, F-01, F-02, F-03, F-06, F-13, F-15, I-03 | no | M |
| [F-17](F-17-fsm-docs-migration-page.md) | FSM docs + migration page | F-03, F-06, F-07, F-09, F-10, F-11, F-12, F-13, F-14, F-16, I-10, I-12 | no | S |

## Order and parallel lanes

```
lane 1 (storage):     F-01 ─▶ F-05 ─▶ F-06 ┐
                                   └▶ F-07 ┴▶ F-13 ─▶ F-14
lane 2 (isolation):   F-02 ─▶ F-03 ───────────┘ (F-13 also needs F-03)
lane 3 (routing):     F-04 ───────────────── + E-02/E-03/E-09 + F-13 ─▶ F-15
lane 4 (typed data):  F-08 ─▶ F-09 ─▶ F-10
                        │       └──▶ F-12 (after B-13 go)
                        └─▶ F-11 (after B-13 go)
final:                F-16 (exit gate, needs I-03) ─▶ F-17
```

- F-01, F-02, F-04 and F-08 start immediately once `dev-4.x` exists (A-01). None of them needs the B gate.
- Only F-11 and F-12 are gate-conditional. If B-13 is a no-go, they become `blocked`; F-08/F-09 still ship
  (FSMData without a shared CallbackData).
- F-15 is the only plan that waits on story E.

## Open owner questions collected from the plans

- PD-09 vs PD-06: single-loop Redis/Mongo vs single-bot sharding (F-06 Notes).
- R14 hand-off state machine (F-02) and nested-value aliasing contract (F-01).
- Startup warning for in-process isolation with a `create_isolation()` storage (F-02).
- `isolation_warn_after` configuration and channel (F-03).
- JSON-shaped typed dumps in every storage; adapter reach for manual `FSMContext` (F-09).
- Mongo key validation scope (F-07).
- Lax coercion on `CallbackData.unpack` (F-11); `Fraction` support (F-08).
- When the scene missing-action warning fires (F-13).
