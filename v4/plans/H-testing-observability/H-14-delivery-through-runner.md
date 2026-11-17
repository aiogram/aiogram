# H-14 — Toolkit delivery through the Runner

| Field | Value |
|---|---|
| Status | `todo` |
| Story | H — Testing & observability |
| Target branch | `dev-4.x` |
| Depends on | [H-10](H-10-testing-world-import.md), [E-03](../E-runtime/E-03-snapshot-lifecycle.md), [E-04](../E-runtime/E-04-router-graph-multi-parent-flags.md), [E-12](../E-runtime/E-12-runtime-errors.md), [E-13](../E-runtime/E-13-runner-lifecycle-bot-registry.md), [E-14](../E-runtime/E-14-feed-paths-forward-compat-dispatch.md), [E-23](../E-runtime/E-23-bot-registry.md) |
| Blocks | [H-15](H-15-route-diagnostics-on-trace-hook.md), [H-17](H-17-toolkit-feature-interop.md), [H-18](H-18-toolkit-docs.md), [H-20](H-20-integration-layer-exit-gate.md) |
| Gate-conditional | no |
| Decisions | D54, D114, D50, D56, D21, R12, PD-18 |
| Sources | [14-testing.md D54, §3 "Delivery"](../../research/14-testing.md), [12-runtime.md §3–4](../../research/12-runtime.md), [03-routing.md §5 D56](../../research/03-routing.md), [19 D114, R12](../../research/19-review-resolutions.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

The 3.x toolkit feeds `dp.feed_update` directly, and wraps the loop's task factory
(`BotTestEnvironment._install_task_factory` area in `environment.py`) to track background tasks.

4.0 has a `Runner` with sources (D21), in-flight task tracking, `runtime_errors` for background failures (D50) and
per-Runner routing snapshots (D114). Routing through a `WorldSource` gives tests the real lifecycle (`startup`,
`bot_added`, `shutdown`) and removes the task-factory hack.

`detach_router` exists only because a 3.x router can have one parent. D56 allows multiple parents, so it goes.

## Scope

**In:**
- `WorldSource` implements `UpdateSource` (12 §4: `start`, `stop`, `add_bot`, `remove_bot`). World events are
  delivered with `runner.feed(bot, update)`, which admits the update (R12). The environment awaits completion
  through Runner task tracking.
- Background failures come from `dp.runtime_errors` (D50) and fail the test, or are collected per the existing
  `assert_updates_handled` option.
- `env.feed(update)` stays as a convenience on the direct `dp.feed_update` path (epoch-keyed snapshot, D114).
- Per-test setup:
  - a fresh `Dispatcher` per environment, as the `bot_dispatcher` fixture already does;
  - or the user mutates the dispatcher and the environment calls `runner.refresh()`.

  `dp.dependency_overrides` / `dp.tracers` changes take effect because they bump the epoch (PD-18, E-03).
- Delete the task-factory install/uninstall and `aiogram/test/routing.py` (`detach_router`, also its export in
  `aiogram/test/__init__.py`).
- Single-loop only, documented (14 §3): the `World` has no locks.

**Out:**
- Route diagnostics (H-15).
- Binding (H-13).
- Docs port (H-18).
- Retry/flood interop (H-17).

## Checklist

- [ ] `WorldSource` and Runner-based delivery in `environment.py`.
- [ ] Remove the task-factory code and `detach_router`.
- [ ] **Decide sync fixture vs async lifecycle.** The 3.x `bot_env` fixture in `plugin.py` is sync and tears down
      with `dispose_sync()`; `aiogram[test]` pulls in only pytest (proposed default: `bot_env` stays sync and
      lifecycle-free, using direct feed as today; tests that need `startup`/`bot_added`/`shutdown` use
      `async with bot_env.running():`, which starts and stops a Runner with the `WorldSource`. No async pytest
      plugin becomes a dependency). Record the decision in *Notes* and flag it to the owner.
- [ ] Tests:
  - [ ] `startup` and `bot_added` fire once inside `running()`, and `shutdown` on exit;
  - [ ] a background task failure surfaces through `runtime_errors` and fails the env check;
  - [ ] a module-level router is included in two fresh dispatchers across two tests (D56);
  - [ ] a dependency override set after a first feed takes effect (PD-18);
  - [ ] mutating a running dispatcher plus `runner.refresh()` takes effect.
- [ ] Port affected `tests/test_testing/**` scenarios.
- [ ] Changelog fragment if `detach_router` was ever released (see the H-10 decision); otherwise none. Migration-
      registry entry (PD-13) only if #1887 shipped in 3.x.

## Acceptance criteria

- No `set_task_factory` call remains in `aiogram/test/**`.
- The lifecycle tests above pass. A failing background task makes `assert_updates_handled` fail with the original
  exception.
- The toolkit suite passes with the plugin's default fixtures unchanged for sync-style tests.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Keeping task-factory wrapping | Runner task tracking already covers it | 14 §3 |
| Swapping `dp.fsm.storage` / `workflow_data` while running | Runners route on snapshots; use a fresh dispatcher or `refresh()` | D54, D114 |
| `detach_router` | Multiple parents are allowed | D56 |
| Making pytest-asyncio/anyio a dependency of `aiogram[test]` | Not needed under the proposed default; pending decision | — |

## Validation

```bash
make dev
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Not gate-conditional. It can run on either model layer, so it may land before H-12/H-13.
- Inputs:
  - E-13: Runner lifecycle; E-23: bot registry;
  - E-14: feed paths;
  - E-12: `runtime_errors`;
  - E-03: snapshot + epoch containers (PD-18);
  - E-04: multi-parent routers.
- Outputs: delivery and lifecycle that H-15, H-17, H-18 and H-20 build on.

## Notes
