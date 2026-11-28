# 3x-11 — Prebuilt middleware chains with a topology epoch

| Field | Value |
|---|---|
| Status | `todo` |
| Story | 3x — 3.x quick wins & migration baseline |
| Target branch | `dev-3.x` |
| Depends on | [A-05](../A-contracts/A-05-bench-harness.md), [A-10](../A-contracts/A-10-routing-oracle.md) (routing oracle, used as an invariance check), [3x-03](3x-03-magicfilter-inline.md) (rebase order) |
| Blocks | [A-06](../A-contracts/A-06-record-3x-baselines.md), [3x-12](3x-12-small-dispatch-costs.md) |
| Gate-conditional | no |
| Decisions | 13 B15 (topology epoch); D38 data scopes unchanged (R09) |
| Sources | [09 #11](../../research/09-3x-quick-wins.md), [03 §1–2](../../research/03-routing.md), [13 B15](../../research/13-aiogram-rust-review.md), [19 R09](../../research/19-review-resolutions.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Every update rebuilds `functools.partial` / `wraps` chains, which is about 38% of the fixed dispatch path (03 §2):
- `MiddlewareManager.wrap_middlewares` (`aiogram/dispatcher/middlewares/manager.py`), called from
  `TelegramEventObserver.wrap_outer_middleware` and `TelegramEventObserver.trigger`
  (`aiogram/dispatcher/event/telegram.py`);
- `_resolve_middlewares`, which walks `Router.chain_head` for every matched handler;
- `Router.propagate_event` (`aiogram/dispatcher/router.py`), which creates a closure per router;
- `RequestMiddlewareManager.wrap_middlewares` (`aiogram/client/session/middlewares/manager.py`), called from
  `BaseSession.__call__` for every API request.

The estimate is ≈5–8 µs per update. aiogram_rust measured 18.6 → 13.4 µs for one handler.

## Scope

**In:**
- A process-global integer **topology epoch**, bumped on every event that can change a chain:
  - middleware `register` / `unregister` (including the decorator form) on any `MiddlewareManager`;
  - `Router.parent_router` assignment (`include_router` / `include_routers`);
  - observer handler registration, if inner chains are cached per handler.
- Cache the outer chain per observer and the inner chain per (observer, handler), keyed by the epoch. Rebuild lazily
  when the epoch has moved. Also cache the resolved inner middleware list per observer (aiogram_rust doesn't).
- The session middleware chain is cached per session, invalidated on its manager's register/unregister. The
  per-call values (`bot`, `method`, `timeout`) stay call arguments; the chain no longer captures them through
  `partial`.
- Semantics unchanged:
  - middleware call order;
  - the mutable `data` dict and the R09 scopes;
  - short-circuit and calling `handler` twice;
  - registering while running takes effect for the next update. That is the 3.x behaviour; D114's snapshot is 4.0
    only.

**Out:**
- The compiled `DispatchTable` and routing snapshot: E-02 / E-03 (4.0).
- Skipping outer middlewares (D111): 4.0 only.

## Checklist

- [ ] Baseline with A-05 on `routing.1-handler`, `routing.52-handlers` (first match) and an API-call case
      (`request.sendMessage.plain` through `bot(...)`).
- [ ] Add the epoch (a module-level counter in `aiogram/dispatcher/middlewares/manager.py` or a tiny shared module)
      and bump it at every mutation site listed above. Grep for every writer of `_middlewares` and `_parent_router`.
- [ ] Cache the outer and inner chains on the observer. Make sure a cached chain never keeps a stale `data` dict:
      the chain takes `(event, data)` per call.
- [ ] Session chain cache.
- [ ] Run the A-10 routing oracle, parent vs this commit, including scenarios that register middleware **during**
      handling: all invariant.
- [ ] Tests:
  - a middleware registered after the first update applies to the next one;
  - unregistering works;
  - `include_router` after the first update rebuilds the chain;
  - a session middleware added at runtime applies to the next request.
- [ ] 100% coverage.
- [ ] Changelog fragment `CHANGES/<pr>.misc.rst`.
- [ ] Migration registry: no entry.

## Acceptance criteria

- A-05 `compare` on `routing.1-handler`: fixed-path median ≥ 15% faster than the parent commit. The research expects
  ≈5–8 µs of ≈21.6 µs.
- The A-10 oracle reports zero mismatches.
- No new strong references keep routers or handlers alive after the dispatcher is dropped (a `weakref` test).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Freeze routers while running in 3.x | Behaviour break; 4.0 uses per-Runner snapshots instead and never raises | D114 (replaces D19) |
| A per-router dirty flag instead of a global epoch | A parent change invalidates descendants; a global counter is simpler and correct | 13 B15 |

## Validation

```bash
uv run pytest tests --cov=aiogram --cov-report=term-missing
make lint
uv run python -m benchmarks compare --base HEAD~1 --head HEAD --cases routing.1-handler,routing.52-handlers,request.sendMessage.plain
uv run python -m differential run --kind routing --left git:HEAD~1 --right git:HEAD
```

## Workflow notes

- The epoch idea carries into 4.0: E-03 keys `dp.feed_update()`'s cached snapshot by a topology epoch (D114, PD-18).
- Rebase after 3x-03 and before 3x-12.

## Notes
