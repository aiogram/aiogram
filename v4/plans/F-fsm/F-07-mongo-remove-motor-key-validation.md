# F-07 — Mongo: remove motor `MongoStorage`; `PyMongoStorage` key validation, batching, single-loop

| Field | Value |
|---|---|
| Status | `todo` |
| Story | F — FSM & scenes |
| Target branch | `dev-4.x` |
| Depends on | [F-05](F-05-storage-record-batch-api.md), [A-11](../A-contracts/A-11-migration-registry.md) |
| Blocks | [F-13](F-13-scenes-d33.md), [F-17](F-17-fsm-docs-migration-page.md), [I-07](../I-distribution/I-07-dependencies-extras-restructure.md) |
| Gate-conditional | no |
| Decisions | D113, PD-09, README breaking change 6 |
| Sources | [11-removals.md §5](../../research/11-removals.md), [04-fsm.md §3 Mongo, §4 note](../../research/04-fsm.md), [19 D113 + corrections](../../research/19-review-resolutions.md), [codex-review.md R15](../../research/codex-review.md), [07-free-threading.md §3–§4](../../research/07-free-threading.md), [plans README §1 PD-09](../README.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

- `aiogram/fsm/storage/mongo.py` (`MongoStorage`, motor) is documented as deprecated, and motor has no free-threaded
  wheels. `PyMongoStorage` (`aiogram/fsm/storage/pymongo.py`, PyMongo async) already replaces it (README breaking
  change 6).
- `PyMongoStorage.update_data` builds `{f"data.{key}": value}`: a data key containing `.` becomes a nested path,
  a leading `$` is an operator, and `""` is invalid. D113: reject such keys with a clear error.
- `PyMongoStorage.update_data` already returns an atomic post-update snapshot (19 correction); keep it.
- PD-09: Mongo storages are single-loop in 4.0.

## Scope

**In:**
- Delete `aiogram/fsm/storage/mongo.py`, `tests/test_fsm/storage/test_mongo.py`, `test_mongo_mock.py`, the
  `mongo_server` / `mongo_storage` fixtures in `tests/conftest.py` (keep the `pymongo_*` ones), the `MongoStorage`
  autoclass in `docs/dispatcher/finite_state_machine/storages.rst`, `motor` from the `mongo` extra and `motor-types`
  from the dev group in `pyproject.toml` (coordinate with I-07, which restructures extras).
- Key validation in `PyMongoStorage.set_data` and `update_data` (scope per the decision below), raising a
  `DataNotDictLikeError`-style `ValueError` subclass with the offending key.
- `get_records`: one `find({"_id": {"$in": ids}})`, 1 RTT. `apply_writes`: one `bulk_write` of `UpdateOne` /
  `DeleteOne` ops (ordered), 1 RTT, **not atomic across documents** (documented; isolation serialises a key).
- Empty-document cleanup semantics of 3.x `set_state(None)` / `set_data({})` kept in both paths.
- Single-loop detection (PD-09), same rule and message style as F-06.

**Out:**
- Mongo transactions for cross-document atomicity (not promised, F-05 contract).
- The 3.x baseline deprecation warning for `MongoStorage`: 3x-21.

## Checklist

- [ ] Decide the scope of Mongo key validation (**proposed default:** validate **top-level** data keys in both
      `set_data` and `update_data`: reject non-`str` keys, `""`, keys containing `.`, keys starting with `$`; nested
      keys follow MongoDB's own rules and are not checked by aiogram) — record in Notes and flag to owner.
- [ ] Remove motor storage, tests, fixtures, docs, deps (list in Scope).
- [ ] Validation + error type; docstring lists the rule.
- [ ] `get_records` / `apply_writes` implementations.
- [ ] Loop-binding check (PD-09).
- [ ] Tests: `tests/test_fsm/storage/test_pymongo_mock.py` (validation errors for each rejected form; `bulk_write`
      called once; second-loop `RuntimeError`), `test_pymongo.py` under `--mongo` (round trips, post-update snapshot
      unchanged, a 3.x-written document reads back identically).
- [ ] Tests (100% coverage of new code)
- [ ] Migration-registry entries (PD-13): `MongoStorage` removed → `PyMongoStorage` (`removal-4.0`, definite); invalid
      data keys now raise; single-loop rule (shared entry with F-06).
- [ ] Changelog fragment in `CHANGES/`.

## Acceptance criteria

- `rg -n "motor|MongoStorage\b" aiogram tests docs pyproject.toml` finds nothing except migration docs/registry.
- `update_data(**{"a.b": 1})`, `{"$x": 1}`, `{"": 1}` and `{1: "x"}` raise with the key in the message; nothing is
  written.
- `apply_writes` over 2 keys issues exactly one `bulk_write`; `get_records` over 2 keys one `find`.
- Using one `PyMongoStorage` from a second running loop raises `RuntimeError`.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Keep motor `MongoStorage` | Deprecated in 3.x, no free-threaded wheels | 11 §5, D8 |
| Escape dotted keys (e.g. `．`) instead of rejecting | Silent data-shape change; reject with a clear error | D113 |
| Multi-document transactions for scene transitions | Needs a replica set; isolation already serialises a key | F-05 contract |

## Validation

```bash
make dev
uv run pytest tests/test_fsm -q
uv run pytest --mongo mongodb://localhost:27017 tests/test_fsm -q
uv run pytest tests
make lint
```

## Workflow notes

- Parallel with F-06 after F-05. If I-07 lands first and already removed motor from `pyproject.toml`, skip that item.
- See F-06 Notes for the PD-09 vs PD-06 open question; it applies to Mongo too.

## Notes
