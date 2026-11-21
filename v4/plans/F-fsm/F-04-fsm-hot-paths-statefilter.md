# F-04 — FSM hot paths, StateFilter introspection, public isolation-key function

| Field | Value |
|---|---|
| Status | `done` |
| Story | F — FSM & scenes |
| Target branch | `dev-4.x` |
| Depends on | [A-01](../A-contracts/A-01-bootstrap-dev-4x.md), [A-05](../A-contracts/A-05-bench-harness.md) |
| Blocks | [F-15](F-15-statefilter-state-index.md), [E-22](../E-runtime/E-22-single-bot-sharding.md) |
| Gate-conditional | no |
| Decisions | D27, D33, PD-06 |
| Sources | [04-fsm.md §1, §3 Middleware](../../research/04-fsm.md), [09-3x-quick-wins.md #12, #13](../../research/09-3x-quick-wins.md), [07-free-threading.md §1](../../research/07-free-threading.md), [12-runtime.md §3](../../research/12-runtime.md), [plans README §1 PD-06](../README.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

The FSM costs 8.2 µs of 28.8 µs per `feed_update` (04 §1). Small items:

- `State.state` (`aiogram/fsm/state.py`) rebuilds an f-string on every access, and `StateFilter`
  (`aiogram/filters/state.py`) compares through it: 1.8 µs for 2 states.
- `FSMContextMiddleware.get_context` (`aiogram/fsm/middleware.py`) reads `bot.id` per update.
- PD-06: single-bot thread sharding ships in 4.0. E-22 shards one bot's updates across Runner threads **by isolation
  key**, so it needs the key computed from the event context without creating an `FSMContext` or touching storage.
- F-15's state index needs to ask a `StateFilter` which exact states it accepts.

## Scope

**In:**
- `State.state` cached: computed when the state is bound and **recomputed when its group's parent changes** (nested
  `StatesGroup`s get `__parent__` when the outer class is created, `StatesGroupMeta._prepare_child`, so the full
  name changes after the inner class exists). The cache is invalidated by `set_parent` and by parent assignment.
- `StateFilter.__init__` precomputes `frozenset` of exact state strings and a flag for "has wildcard / `None` / custom
  callable". `__call__` uses the set first, then falls back to the 3.x loop for custom entries.
- `StateFilter.exact_states -> frozenset[str | None] | None`: the set of exact `raw_state` values the filter accepts,
  or `None` if it contains `"*"`, a `State` subclass that overrides `__call__`, a `StatesGroup` instance or class
  whose `__call__` is overridden, or anything else non-exact. `StatesGroup` (not overridden) expands to
  `__all_states_names__`.
- Public pure function `FSMContextMiddleware.resolve_key(bot_id, event_context, destiny=DEFAULT_DESTINY) -> StorageKey | None`,
  split out of `resolve_event_context` / `resolve_context` (strategy, `key_on_sender_chat`, guest, business connection
  rules unchanged). No I/O, no `FSMContext`. `resolve_event_context` calls it.
- `bot.id` read once per Bot (cache keyed by the bot object, or reuse the D-01 cached property if it exists by then).
- `StorageKey` built once per update (the middleware builds one and passes it).

**Out:**
- The state index: [F-15](F-15-statefilter-state-index.md).
- `DisabledEventIsolation` `nullcontext`: [F-02](F-02-isolation-lock-table-default-on.md).
- Sharding itself: E-22.
- 3.x counterparts 3x-12 (small dispatch costs) on `dev-3.x`; superseded here.

## Checklist

- [ ] Cached `State.state` with invalidation on parent changes; tests for nested groups declared inner-first.
- [ ] `StateFilter` precomputation + `exact_states`.
- [ ] `FSMContextMiddleware.resolve_key` (public, documented as the isolation-key function used by sharding).
- [ ] `bot.id` cache; one `StorageKey` per update.
- [ ] Tests in `tests/test_fsm/test_state.py`, `tests/test_filters/test_state.py`, `tests/test_fsm/test_middleware.py`:
      parity with the 3.x results for every existing case; `exact_states` for each input kind; `resolve_key` equals
      `resolve_event_context(...).key` for all strategies.
- [ ] Tests (100% coverage of new code)

## Acceptance criteria

- `StateFilter` with 2 exact states: ≤ 0.5 µs per call on the A-05 reference machine (3.x: 1.8 µs).
- All existing `tests/test_fsm` and `tests/test_filters` tests pass unchanged.
- `resolve_key` performs no `await` and no storage access (asserted with a storage mock that fails on any call).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Computing `State.state` only at class creation | Wrong for nested groups whose parent is assigned later | this plan |
| Lazy state loading | `raw_state` contract | D27 |

## Validation

```bash
make dev
uv run pytest tests/test_fsm tests/test_filters -q
uv run pytest tests
make lint
```

## Workflow notes

- Parallel with F-01, F-02, F-08.
- `exact_states` is consumed by F-15; `resolve_key` by E-22. Keep both signatures stable once merged.

## Notes
