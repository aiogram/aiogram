# F-13 — Scenes (D33): batched history, copy-on-write, action warning, registry snapshot hook

| Field | Value |
|---|---|
| Status | `todo` |
| Story | F — FSM & scenes |
| Target branch | `dev-4.x` |
| Depends on | [F-01](F-01-thread-safe-memory-storage.md), [F-03](F-03-release-isolation-warn-after.md), [F-05](F-05-storage-record-batch-api.md), [F-06](F-06-redis-storage-legacy-layout.md), [F-07](F-07-mongo-remove-motor-key-validation.md), [E-03](../E-runtime/E-03-snapshot-lifecycle.md) |
| Blocks | [F-14](F-14-typed-scene-data.md), [F-15](F-15-statefilter-state-index.md), [F-16](F-16-race-suite-314t.md), [F-17](F-17-fsm-docs-migration-page.md) |
| Gate-conditional | no |
| Decisions | D33, D113, D114, R14, R15 |
| Sources | [04-fsm.md §2, §8](../../research/04-fsm.md), [19 D114](../../research/19-review-resolutions.md), [03-routing.md §3 Late registration, §5](../../research/03-routing.md), [codex-review.md R14, R15](../../research/codex-review.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

D33 keeps the 3.x scene semantics (`aiogram/fsm/scene.py`) and changes only what is cheap and safe:

- `HistoryManager.push` / `pop` mutate the list returned by `get_data` (a shallow copy), so the stored history is
  aliased (04 §2).
- A scene `goto` costs ≈5 Redis round trips; D33: all history operations of one transition go to storage as **one
  batch**. History lives under a separate key (`destiny="scenes_history"`), so the batch spans two keys.
- When an action has no handler for the triggering update type, `SceneWizard._on_action` logs at debug level only;
  D33 makes it a `RuntimeWarning`, once per (scene, action, update type).
- `SceneHandlerWrapper.__call__` and `ScenesManager.enter` rebuild `{**data, **kwargs}` per call.
- D114: the `SceneRegistry` is captured in each Runner's snapshot; registration after start applies on
  `runner.refresh()` or restart.

## Scope

**In:**
- `HistoryManager`: copy the history list before mutating; snapshots follow F-01's aliasing rule (top-level copy of
  `data`).
- Transitions (`SceneWizard.enter/leave/exit/back/goto`, `HistoryManager.snapshot/rollback/push/pop/clear`) read with
  one `get_records(main_key, history_key)` and write with one `apply_writes(...)` (F-05), so Redis pipelines and Mongo
  `bulk_write` apply. No Lua; no cross-key atomicity promised (isolation serialises the key).
- `RuntimeWarning` for missing actions, once per (scene, action, update type), deduplicated with a lock-guarded set
  (free-threading safe).
- One merged data view per update instead of repeated `{**a, **b}` copies; same observable behaviour.
- `SceneRegistry.snapshot()` (or an equivalent read-only view) that E-03 captures at snapshot compile; mutation after
  capture triggers the D114 one-time warning through E-03's epoch mechanism.
- Docs (`docs/dispatcher/finite_state_machine/scene.rst`): scene data is shared with the user's FSM data;
  `reset_data_on_enter` clears all of the user's data; recommend namespaced keys; actions bypass the target scene's
  router middlewares (#1672, #1687); history needs `DefaultKeyBuilder(with_destiny=True)` on Redis/Mongo;
  `release_isolation` (F-03) inside scene handlers.

**Out:**
- Typed `Scene.data`: [F-14](F-14-typed-scene-data.md).
- StateFilter state index and the D111 test of `SceneRegistry` middlewares: [F-15](F-15-statefilter-state-index.md).
- Capturing the registry in the snapshot: E-03.

## Checklist

- [ ] Decide when the missing-action warning fires (**proposed default:** only when the scene defines the action for
      **some** update types but not the triggering one, the second debug branch of `_on_action`; a scene that defines
      no `leave`/`exit`/`back` at all stays silent, otherwise every transition would warn) — record in Notes and flag
      to owner.
- [ ] `HistoryManager` copy-on-write.
- [ ] Batched transitions on `get_records` / `apply_writes`.
- [ ] `RuntimeWarning` with dedup set.
- [ ] Merged data view.
- [ ] `SceneRegistry` snapshot hook.
- [ ] Docs as listed.
- [ ] Tests in `tests/test_fsm/test_scene.py`: all existing tests pass; aliasing regression (mutating a returned history
      record doesn't change storage); warning emitted once per tuple (`pytest.warns` + second call silent); round-trip
      counter (F-06 helper): `goto` ≤ 2 Redis round trips from storage operations; Mongo mock: `bulk_write` once per
      transition.
- [ ] Tests (100% coverage of new code)
- [ ] Changelog fragment in `CHANGES/` (the warning is user-visible; no registry entry needed: no removal).

## Acceptance criteria

- Scene `goto` against Redis issues ≤ 2 storage round trips (3.x ≈5), measured with the F-06 round-trip counter.
- History aliasing test from 04 §2 passes.
- `RuntimeWarning` appears once for a repeated (scene, action, update type).
- The full 3.x scene test suite passes unchanged except for tests that asserted the debug log.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Namespaced per-scene data | Changes 3.x semantics; docs recommend key prefixes instead | D33 |
| Diff-based history instead of full snapshots | Keep 3.x full `{state, data}` snapshots | D33 |
| Lua for atomic transitions | No Lua; codec hooks; cluster | D113, R15 |
| Running target-scene middlewares for actions | Unchanged from 3.x, documented | D33 |

## Validation

```bash
make dev
uv run pytest tests/test_fsm -q
uv run pytest --redis redis://localhost:6379/0 tests/test_fsm -q
uv run pytest --mongo mongodb://localhost:27017 tests/test_fsm -q
uv run pytest tests
make lint
```

## Workflow notes

- Needs F-05 and the backend implementations (F-06, F-07); the generic fallback works without them, but the
  round-trip acceptance needs F-06.
- E-03 does not wait for this plan: until the hook exists, E-03 captures a copy of `SceneRegistry._scenes` itself.
  This plan then adds `SceneRegistry.snapshot()` and switches E-03's capture to it (one-line change in the
  snapshot compiler; record the agreed name in Notes).

## Notes
