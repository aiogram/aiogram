# E — Routing & runtime

**Goal.** Replace the 3.x interpreted router and the lifecycle code inside `Dispatcher` with (1) an immutable routing
snapshot compiled per Runner (D114) and executed by a small loop with prebuilt chains, compiled `F` closures and
compiled rejectors (D37, D111, breaking 13), keeping 3.x data scopes exactly (R09); (2) the 4.0 router, middleware,
filter and error APIs (D34–D41, D47–D50, D55–D58, D112); (3) a per-loop `Runner` with pluggable update sources
(Poller, aiohttp webhook, ASGI, user sources), runtime bot add/remove, bounded admission, free-threaded multi-Runner
operation and single-bot sharding (D21–D24, R12, R13, PD-06). Routing stays Python (D5).

**Exit gate (README D121, milestone E):** routing differences match the decisions; lifecycle fault injection;
multi-Runner tests — verified by [E-21](E-21-e-exit-gate.md).

**Branch:** `dev-4.x`. Normative sources: [plans README §1](../README.md) (PD-xx) → [19](../../research/19-review-resolutions.md) → research pages.

## Tasks

| ID | Title | Depends on | Gate-cond. | Size |
|---|---|---|---|---|
| [E-01](E-01-dispatcher-filter-removals.md) | Dispatcher/filter legacy removals | A-01, A-11 | no | M |
| [E-02](E-02-dispatch-table-executor.md) | Compiled DispatchTable + executor | A-01, A-07, A-10, H-01 | no | L |
| [E-03](E-03-snapshot-lifecycle.md) | Snapshot lifecycle: epoch, cache, refresh, warning | E-02 | no | M |
| [E-04](E-04-router-graph-multi-parent-flags.md) | Router graph: multi-parent, diamonds, router flags | E-02 | no | M |
| [E-05](E-05-typed-observers-unknown-update.md) | Typed generated observers + `unknown_update` | C-16, E-03 | no | S |
| [E-06](E-06-middleware-api.md) | Middleware context protocol, prebuilt chains, anchors, per-handler middlewares, generic BaseMiddleware | D-06, E-02 | no | L |
| [E-07](E-07-sync-filter-execution.md) | Sync filter execution (`SyncFilterMode`) | 3x-03, E-02 | no | S |
| [E-08](E-08-magic-filter-compile.md) | `F` compiled to closures | E-07 | no | M |
| [E-09](E-09-routing-keys-compiled-rejectors.md) | Routing keys + compiled rejectors | B-05, B-13, C-16, C-19, E-02, E-08 | **yes** | L |
| [E-10](E-10-flag-spec.md) | `@flag_spec` | E-04 | no | S |
| [E-11](E-11-error-model-bubbling.md) | Error model, bubbling, PD-05 warning, update-scope hooks | A-11, C-12, E-02, E-04, F-03 | no | M |
| [E-12](E-12-runtime-errors.md) | `dp.runtime_errors` | E-11 | no | S |
| [E-13](E-13-runner-lifecycle-bot-registry.md) | Runner lifecycle, sources, task set | E-03, E-12, H-01 | no | M |
| [E-14](E-14-feed-paths-forward-compat-dispatch.md) | Feed paths + forward-compat dispatch | B-07, C-19, D-09, D-10, E-05, E-11, E-12, E-13, H-01 | partial (remount) | M |
| [E-15](E-15-poller.md) | Poller | D-09, D-11, E-05, E-14 | no | M |
| [E-16](E-16-webhook-core-aiohttp-sources.md) | Webhook core + aiohttp sources | D-09, D-10, D-14, E-14, E-23 | no | L |
| [E-17](E-17-asgi-app.md) | ASGI app | D-14, E-14, E-16 | no | S |
| [E-18](E-18-compat-wrappers.md) | Compat wrappers (`start_polling` …) | E-15, E-16 | no | S |
| [E-19](E-19-multi-runner-free-threading-sharding.md) | Multi-Runner over one Dispatcher, free-threading | E-03, E-13, E-15, E-23, F-02 | no | M |
| [E-20](E-20-typed-di-typeddicts.md) | Typed DI TypedDicts | E-01 | no | S |
| [E-21](E-21-e-exit-gate.md) | E exit gate | A-05, A-06, A-07, A-10, E-01, E-02, E-03, E-04, E-05, E-06, E-07, E-08, E-09, E-10, E-11, E-12, E-13, E-14, E-15, E-16, E-17, E-18, E-19, E-20, E-22, E-23 | partial | M |
| [E-22](E-22-single-bot-sharding.md) | Single-bot thread sharding (PD-06) | E-15, E-19, F-02, F-04 | no | M |
| [E-23](E-23-bot-registry.md) | Runner bot registry, shared-FSM ownership | E-12, E-13 | no | M |

Single-bot sharding (PD-06) is split out of E-19 into E-22, and the bot registry out of E-13 into E-23.

## Order and parallel lanes

1. **Start immediately** (after A-01): E-01, E-02 (needs A-07/A-10). E-20 after E-01.
2. **After E-02:** lane *routing* E-03 → E-05 (needs C-16); lane *graph* E-04 → E-10; lane *middleware* E-06;
   lane *filters* E-07 → E-08 → E-09 (waits for B-05 and the B-13 go); lane *errors* E-11 → E-12.
3. **After E-03 + E-12:** E-13 → E-23 (registry) and E-14 (needs D-09; remount needs B-07) → E-15 ∥ E-16 (needs D-14 + the 3.x webhook fixes).
4. **Then:** E-17 (after E-16), E-18 (after E-15 + E-16), E-19 (after E-15 + E-23 + F-02) → E-22 (after E-19 + F-04).
5. **Last:** E-21.

Until B-05 lands, the executor reads routing keys through a Python shim (E-02); only E-09 swaps it for the Rust call.

## What other stories get from E

- **F:** `FSMContextMiddleware` stays a `dp.update` outer middleware usable as an anchor class (E-06) and calls the
  E-11 `close_point` before releasing the isolation lock (PD-04), which runs F-03's `add_release_hook` hooks; snapshot
  capture for SceneRegistry (E-03 copies `_scenes` until F-13's `snapshot()`) and StatesGroup (E-03); frame-skip hook for the state index (E-02, F-15); `router.observers` kept (E-05); isolation-key sharding
  (E-22); storage close ownership across Runners (E-23 decision).
- **G:** update-scope hook protocol (start / record_escaped / close_point) and `DEPENDENCY`/`TEARDOWN` phases (E-11);
  per-snapshot callable compile seam with `param_resolvers` / `dependency_overrides` captured (E-03, E-07);
  `emit_runtime_error` (E-12); Runner/Poller/webhook APIs for the CLI
  (E-13…E-18).
- **H:** tracer list captured at compile and stage boundaries in the executor (E-02/E-03, H-06); Runner fields written
  into H-01's per-update log-context carrier and in-flight counters (E-13); `UpdateSource` + `runner.feed` for `WorldSource` (E-13/E-14);
  `ErrorEvent.router/handler/phase` (E-11).
- **D:** `order_middlewares` resolver reusable for session middleware anchors (E-06). E consumes D-09 (decode) and D-14
  (webhook reply encoding).
