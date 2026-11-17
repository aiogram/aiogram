# F-15 — StateFilter state index in the routing snapshot

| Field | Value |
|---|---|
| Status | `todo` |
| Story | F — FSM & scenes |
| Target branch | `dev-4.x` |
| Depends on | [F-04](F-04-fsm-hot-paths-statefilter.md), [F-13](F-13-scenes-d33.md), [E-02](../E-runtime/E-02-dispatch-table-executor.md), [E-03](../E-runtime/E-03-snapshot-lifecycle.md), [E-09](../E-runtime/E-09-routing-keys-compiled-rejectors.md) |
| Blocks | [F-16](F-16-race-suite-314t.md) |
| Gate-conditional | no |
| Decisions | D27, D33, D111, D114, PD-19 |
| Sources | [04-fsm.md §8 Routing](../../research/04-fsm.md), [03-routing.md §3](../../research/03-routing.md), [19 D111, D114](../../research/19-review-resolutions.md), [plans README §1 PD-19](../README.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Each scene router registers `StateFilter(scene_config.state)` as a filter on every observer (`Scene.add_to_router` in
`aiogram/fsm/scene.py`). With many scenes, every update checks every scene's root filter. The state is loaded eagerly
(D27), so D33 compiles these filters into a **state index** in the routing snapshot (D114): scene routers whose state
can't match are skipped. It is a skip optimisation under D111 (PD-19: a router's outer chain is entered iff at least
one candidate in its subtree survives the compiled rejectors), keeping wildcard/general handlers and DFS precedence.

## Scope

**In:**
- At snapshot compile (E-02/E-03), for each router observer whose root filters include a `StateFilter` with
  `exact_states is not None` (F-04), record `exact_states` as a rejector keyed on `raw_state`.
- At dispatch, the rejector reads `data["raw_state"]` **at router entry** (not a cached routing key: user middlewares
  may change it), and the executor skips the router's candidates when the state is not in the set.
- Index form: `dict[str | None, tuple[router positions]]` per event plan when it pays off; a per-router frozenset
  check is the fallback. Choose by measurement and record which in Notes.
- `StateFilter`s with `exact_states is None` (wildcard, custom states, custom callables) stay in the normal path.
- Agreement test: over a matrix of states × filters, whenever the index rejects, the real `StateFilter` returns
  `False` (same pattern as E-09's rejector agreement test).
- D111 check for scenes: `SceneRegistry` outer middlewares (`SceneRegistry._setup_middleware`) still inject `scenes`
  for scene handlers on their path.

**Out:**
- The compile/executor machinery and rejector framework: E-02, E-03, E-09.
- `StateFilter.exact_states`: [F-04](F-04-fsm-hot-paths-statefilter.md).

## Checklist

- [ ] Compile `StateFilter` root filters into state rejectors / index.
- [ ] Router-entry read of `raw_state`.
- [ ] Agreement test and DFS-order test (a general handler registered before scene routers still wins).
- [ ] D111 scene middleware test.
- [ ] Benchmark (A-05 / E bench): 50 scene routers, update in a state owned by the last scene.
- [ ] Tests (100% coverage of new code)
- [ ] Changelog fragment in `CHANGES/` (performance; behaviour unchanged).

## Acceptance criteria

- Agreement test: zero cases where the index rejects and the real filter accepts.
- Routing results equal the A-10 routing oracle for the scene corpus.
- With 50 scene routers, dispatch to the last scene costs ≤ 25% of the same snapshot without the index (record
  numbers in Notes).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Index on a routing key computed once per update | Middlewares may change `raw_state` before routing | D111 note, this plan |
| Indexing custom `State` subclasses | Their `__call__` may differ; same rule as the command index | 03 §3 |
| Lazy state loading | `raw_state` contract | D27 |

## Validation

```bash
make dev
uv run pytest tests/test_fsm tests/test_dispatcher -q
uv run pytest tests
make lint
```

## Workflow notes

- Waits for E's compiler (E-02/E-03) and rejector framework (E-09). E-21 (E exit gate) does not wait for this plan;
  if E-21 is still open, offer it the scene routing cases.

## Notes
