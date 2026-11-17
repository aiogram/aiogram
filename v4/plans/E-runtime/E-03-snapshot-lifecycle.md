# E-03 — Routing snapshot lifecycle: topology epoch, caching, refresh, mutation warning

| Field | Value |
|---|---|
| Status | `todo` |
| Story | E — Routing & runtime |
| Target branch | `dev-4.x` |
| Depends on | [E-02](E-02-dispatch-table-executor.md) |
| Blocks | [E-05](E-05-typed-observers-unknown-update.md), [E-13](E-13-runner-lifecycle-bot-registry.md), [E-19](E-19-multi-runner-free-threading-sharding.md), [F-13](../F-fsm/F-13-scenes-d33.md), [G-01](../G-features/G-01-param-resolver-hook.md), [H-06](../H-testing-observability/H-06-tracing-in-executor.md), [E-21](E-21-e-exit-gate.md), [F-15](../F-fsm/F-15-statefilter-state-index.md), [H-14](../H-testing-observability/H-14-delivery-through-runner.md), [I-19](../I-distribution/I-19-heuristic-behaviour-rules.md) |
| Gate-conditional | no |
| Decisions | D114, D19 (superseded), PD-18, B15, README breaking change 4 |
| Sources | [19 D114](../../research/19-review-resolutions.md), [03-routing.md §3 "Late registration", §4](../../research/03-routing.md), [12-runtime.md §3](../../research/12-runtime.md), [13 B15](../../research/13-aiogram-rust-review.md), [codex-review R11](../../research/codex-review.md), [plans README PD-18](../README.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

D114: each Runner compiles an immutable snapshot at start; dispatchers and routers stay ordinary mutable objects;
changes apply on restart or `runner.refresh()`; a one-time warning fires when someone mutates a graph a running
snapshot references; `dp.feed_update()` without a Runner compiles and caches a snapshot keyed by a topology epoch.
Nothing raises (D19's "raise while running" is superseded). This plan owns that lifecycle; E-02 only compiles.

## Scope

**In:**
- **Snapshot** = the E-02 `DispatchTable` plus everything D114 lists as captured: chains, copied flags, filter plans,
  `Depends` plans (via the compile seam G-01 fills), the scene registry (this plan copies `SceneRegistry._scenes`
  itself — a shallow `MappingProxyType` copy — until F-13 adds `SceneRegistry.snapshot()` and swaps the capture to
  it; E-03 does not depend on F-13, so there is no E→F→E cycle),
  `workflow_data` as a `MappingProxyType` copy, the tracer list (H-06), `dp.param_resolvers`,
  `dp.dependency_overrides`.
- **Topology epoch:** one process-wide integer bumped on any routing-relevant mutation: handler/filter registration
  on any observer, `observer.filter()`, middleware register/unregister (outer, inner, per-handler via E-06),
  `include_router` / `parent_router` changes, `Router(flags=)` changes, and — PD-18 — mutation of the
  **epoch-bumping containers** `dp.tracers`, `dp.param_resolvers`, `dp.dependency_overrides` and `dp.workflow_data`.
  These become small list/dict subclasses (or wrappers) whose mutators bump the epoch; reads stay plain.
- **`dp.feed_update()` cache:** compile lazily, cache `(epoch, snapshot)` on the dispatcher; recompile when the epoch
  moved. Concurrent first compiles may both compile; the loser is dropped (same rule as R03 wrapper caches; no lock
  held while user code runs).
- **Runner snapshots:** a `SnapshotHolder` object (used by E-13) that compiles at start, exposes `current` (an atomic
  reference read once per update), and `refresh()` that compiles a new snapshot and swaps the reference; in-flight
  updates finish on the old one.
- **Mutation warning:** routers/dispatchers record the live holders that reference them (weak set); a mutation of
  such an object emits one `RuntimeWarning` per (holder, object) saying the change applies after `runner.refresh()`
  or restart. Nothing raises.
- Free-threading: snapshot objects are deeply immutable containers (tuples, frozen dataclasses, `MappingProxyType`);
  the reference swap is a single attribute assignment; the epoch counter tolerates benign races (worst case: an extra
  recompile).

**Out:**
- `runner.refresh()` as public Runner API and when Runners compile (E-13 wires the holder).
- `SceneRegistry.snapshot()` and the switch of the capture to it (F-13), Depends plan compile (G-01/G-02), tracer pickup (H-06): this plan provides
  the capture/compile seam they register with.

## Checklist

- [ ] Process-wide epoch + bump calls at every mutation site listed above.
- [ ] Epoch-bumping containers for `tracers`, `param_resolvers`, `dependency_overrides`, `workflow_data` (PD-18);
  `Dispatcher(**kwargs)` still seeds `workflow_data`.
- [ ] `dp.feed_update` lazy compile + epoch cache.
- [ ] `SnapshotHolder` with `current` and `refresh()`.
- [ ] Scene registry captured by copying `SceneRegistry._scenes` (interim; F-13 replaces it with `snapshot()`).
- [ ] Capture-hook registry for other stories (`register_snapshot_capture(name, fn)` or equivalent, internal API).
- [ ] One-time mutation warning for graphs referenced by a live holder.
- [ ] Decide which snapshot `dp.feed_update()` uses when called **inside** an update processed by a Runner (re-entrant
  feeds, tests) (proposed default: read the Runner and its `SnapshotHolder` from H-01's per-update log-context object,
  where E-13 writes the Runner — no new ContextVar; outside a Runner the epoch cache is used) — record in Notes and flag
  to owner.
- [ ] Decide what a mutation of a user object *inside* the snapshot means, e.g. a filter instance's attribute
  (proposed default: nothing — D114 "the snapshot captures structure, not object state"; documented only) — record in
  Notes.
- [ ] Migration-registry entry (PD-13) for breaking change 4 ("changes after start apply on refresh/restart") and a
  changelog fragment.
- [ ] Tests: register after first `feed_update` → next feed sees it; mutate `workflow_data` → next feed sees it;
  holder snapshot does not change until `refresh()`; warning fires exactly once; two holders over one dispatcher are
  independent; concurrent compile from 8 threads on 3.14t returns equivalent snapshots.

## Acceptance criteria

- After any listed mutation, `dp.feed_update` routes with the new graph on the next call; without a mutation the
  cached snapshot object is reused (`is` identity checked in a test).
- A holder started before a mutation keeps routing on the old graph until `refresh()`; the warning appears once.
- A scene registered after a holder started is absent from its snapshot until `refresh()` (the `_scenes` copy is not
  aliased to the live registry).
- Repeated `feed_update` with no mutation costs no compile (bench: steady-state per-update time within 1% of a
  pre-compiled snapshot on the A-05 routing scenario).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Raise `RuntimeError` on registration while running | Shared routers/dispatchers make "running" a shared lifetime; leases needed | D114 replaces D19 |
| Freeze routers (leases per Runner) | Stopping one Runner must not thaw a graph another uses (R11); snapshots need no leases | D114, R11 |
| Copy-on-write live graph | More machinery for the same visible behaviour; can come in 4.x | D19, D114 |
| Plain `list`/`dict` for tracers/resolvers/overrides/workflow_data | Mutations would silently not apply | PD-18 |

## Validation

```bash
make dev
uv run pytest tests -q
PYTHON_GIL=0 uv run --python 3.14t pytest tests/test_dispatcher -q   # free-threaded interpreter
make lint
uv run mypy aiogram
```

## Workflow notes

- E-13 owns when the holder compiles (start) and exposes `runner.refresh()`.
- G-01 / G-02 register the Depends plan compile through the capture seam; H-06 the tracer list. The scene registry
  is captured here by copying `SceneRegistry._scenes`; F-13 later swaps that line for `SceneRegistry.snapshot()`
  (F-13 depends on E-03, never the reverse). Publish the seam's signature in this plan's Notes when done.
- 3x-11 implements a 3.x topology epoch for prebuilt chains; reuse its invalidation points list.

## Notes
