# E-04 — Router graph: multiple parents, diamond check, router-level flags

| Field | Value |
|---|---|
| Status | `todo` |
| Story | E — Routing & runtime |
| Target branch | `dev-4.x` |
| Depends on | [E-02](E-02-dispatch-table-executor.md) |
| Blocks | [E-10](E-10-flag-spec.md), [E-11](E-11-error-model-bubbling.md), [E-21](E-21-e-exit-gate.md), [G-12](../G-features/G-12-commands-from-handlers.md), [H-14](../H-testing-observability/H-14-delivery-through-runner.md) |
| Gate-conditional | no |
| Decisions | D56, D57, D90, D114 |
| Sources | [03-routing.md §5 "Router API and flags"](../../research/03-routing.md), [19 D114](../../research/19-review-resolutions.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

3.x allows one parent per router (`Router.parent_router` setter raises on re-attach), so one router can't be reused
across dispatchers or trees. D56 allows multiple parents, keeps the graph a DAG, and rejects diamonds inside one
dispatcher because their handlers would be tried twice. D57 adds `Router(flags=...)` inherited per path. Both are
resolved at snapshot compile (E-02), per path.

## Scope

**In:**
- `include_router(child)`: raises on self-inclusion, on cycles (DFS over the child's subtree looking for the new
  parent), and when the same child is included twice under the same parent. Each router keeps
  `parent_routers: tuple[Router, ...]`.
- `parent_router`: returns the single parent; with several parents it raises and points to `parent_routers`.
  Setting `parent_router` keeps working as "add a parent". `Dispatcher.parent_router` keeps raising as today.
- **Diamond check at compile:** within one dispatcher, a router reachable through two paths raises at snapshot compile
  (`RuntimeError` naming both paths, e.g. `dp > a > shared` and `dp > b > shared`).
- **Per-path compile:** inner-middleware inheritance (`chain_head`) is resolved per path, not through a single
  `parent_router` chain.
- **Router flags (D57):** `Router(flags={...})`; merged at compile from the outermost router to the innermost, then the
  handler's own flags (decorators, `register(flags=)`, `Filter.update_handler_flags`); nearest wins.
- `data["handler"]` with merged flags: the snapshot holds a per-path handler view.

**Out:**
- `@flag_spec` typed flags (E-10).
- Router-level filters (rejected, D55).

## Checklist

- [ ] `parent_routers` storage, `include_router` cycle/duplicate checks, `parent_router` compatibility rules.
- [ ] Epoch bump on every graph change (E-03 hook).
- [ ] Diamond detection in `compile_table` with both paths in the message.
- [ ] Per-path inner-middleware inheritance.
- [ ] `Router(flags=)` + per-path merge into the candidate's flags.
- [ ] Decide what `data["handler"]` is once flags are merged per path (proposed default: a frozen per-snapshot
  `HandlerView` exposing `callback`, `filters`, merged `flags`, `name`, and `original` pointing at the registered
  `HandlerObject`; `get_flag` and `check_flags` work on it; identity with the registered object is not kept) —
  record in Notes and flag to owner.
- [ ] Docs: router page section "reusing a router" (multi-parent, diamonds) and flags inheritance.
- [ ] Migration-registry entry (PD-13) if `data["handler"]` stops being the registered `HandlerObject`; changelog
  fragment (`feature`).
- [ ] Tests: cycle, self, duplicate, diamond (message names both paths), same router under two dispatchers routes in
  both, per-path flag merge with conflicting values, `parent_router` with two parents raises.

## Acceptance criteria

- A router included in two dispatchers handles updates in each with that dispatcher's inherited inner middlewares and
  flags (test with differing parent flags).
- Diamond inside one dispatcher raises at the first `feed_update` / Runner start, never at `include_router`.
- 3.x single-parent code passes the A-10 differential cases unchanged.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Allow diamonds, dedupe at runtime | Handlers would be tried twice or order becomes ambiguous | D56, D90 |
| Router-level filter | Per-observer `.filter()` covers it; avoids a second root-filter API | D55 |
| Flags only on handlers (3.x) | Throttle/chat-action flags per router are a common ask | D57 |

## Validation

```bash
make dev
uv run pytest tests -q
make lint
uv run mypy aiogram
```

## Workflow notes

- Builds on E-02's per-path compile; E-10 adds typed specs on top of the merged flags.
- F-13 (scenes) and E-11 (error bubbling along the router path) rely on the per-path router chain stored here.

## Notes
