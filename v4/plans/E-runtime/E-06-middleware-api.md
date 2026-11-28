# E-06 — Middleware API: ordering anchors, per-handler middlewares, generic `BaseMiddleware`

| Field | Value |
|---|---|
| Status | `todo` |
| Story | E — Routing & runtime |
| Target branch | `dev-4.x` |
| Depends on | [E-02](E-02-dispatch-table-executor.md) |
| Blocks | [E-21](E-21-e-exit-gate.md), [G-03](../G-features/G-03-i18n-core.md) |
| Gate-conditional | no |
| Decisions | D38, D39, D40, D41 |
| Sources | [03-routing.md §5 "Middlewares"](../../research/03-routing.md), [05-network.md §2.3](../../research/05-network.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

In 3.x, middleware order is registration order only, so a user middleware can't be placed relative to the built-in
`UserContextMiddleware` / `FSMContextMiddleware` on `dp.update`. Per-handler middlewares don't exist (users emulate
them with flags + a router-wide middleware). `BaseMiddleware.__call__` is untyped. D39–D41 address these; D38 keeps the
`SkipHandler` data-sharing semantics and documents them.

## Scope

**In:**
- **Anchors (D39):** `outer_middleware(m, before=X)` / `after=X` and the same on `middleware(...)` (inner), where `X`
  is a middleware class (first match) or instance. Resolved once at snapshot compile; a missing anchor raises at
  compile; conflicting anchors raise naming the cycle. Default stays registration order.
  Example: `dp.update.outer_middleware(BanCheck(), before=FSMContextMiddleware)`.
- The resolver is a pure function `order_middlewares(entries) -> tuple` in `aiogram/dispatcher/middlewares/manager.py`
  (or a sibling module) so D-06 can reuse it for session middlewares.
- **Per-handler middlewares (D40):** `register(cb, *filters, flags=..., middlewares=[...])` and
  `@router.message(Command("x"), middlewares=[Throttle(2)])`. Innermost (after router-chain inner middlewares), run only
  once the handler's filters pass, prebuilt at compile. Flags + `get_flag` keep working.
- **Generic `BaseMiddleware[EventT, DataT]` (D41)** in `aiogram/dispatcher/middlewares/base.py`, defaults
  `TelegramObject`, `dict[str, Any]`. Typing only; unparameterised subclasses unchanged.
- **D38 documented:** a skipped handler's committed filter results and inner-middleware writes stay visible to the next
  candidate (already guaranteed by E-02); add the docs paragraph and a test.

**Out:**
- Session/request-middleware anchors (D-06 consumes the resolver; resolution there happens at register time because
  sessions have no snapshot).

## Checklist

- [ ] `before=` / `after=` on outer and inner registration; stored, resolved in `compile_table`.
- [ ] Errors: missing anchor (`LookupError` or `ValueError`, message names the anchor and observer), cycle (names the
  cycle).
- [ ] `middlewares=[...]` on `register` and the decorator form; prebuilt innermost chain per candidate.
- [ ] `BaseMiddleware` generic; typing test with a D31 `TypedDict` (E-20) as `DataT`.
- [ ] Docs: middlewares page (ordering, anchors, per-handler, D38 semantics).
- [ ] Changelog fragment (`feature`).
- [ ] Tests: anchor before/after built-ins, instance vs class anchor, missing anchor, cycle, per-handler order relative
  to inherited inner middlewares, per-handler middleware not run when filters fail, D38 sharing.

## Acceptance criteria

- `BanCheck` registered after the built-ins with `before=FSMContextMiddleware` runs before FSM (test asserts call
  order).
- A per-handler middleware runs exactly once per matched call and never for a candidate whose filters fail.
- No anchors registered → chain order equals 3.x (A-10 differential cases unchanged).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Numeric priorities | Collide across libraries; anchors name intent | D39 |
| Per-handler middlewares via flags only | Already possible; first-class form is clearer and prebuilt | D40 |
| Change `SkipHandler` data sharing | Users depend on it; documented instead | D38 |

## Validation

```bash
make dev
uv run pytest tests -q
make lint
uv run mypy aiogram
```

## Workflow notes

- D-06 imports `order_middlewares` for request middlewares; keep it free of dispatcher imports.
- E-20's TypedDicts are used in the typing test; if E-20 isn't done, use a local `TypedDict`.

## Notes
