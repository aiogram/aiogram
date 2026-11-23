# E-06 — Middleware API: context protocol, prebuilt chains, ordering anchors, per-handler middlewares, generic `BaseMiddleware`

| Field | Value |
|---|---|
| Status | `todo` |
| Story | E — Routing & runtime |
| Target branch | `dev-4.x` |
| Depends on | [E-02](E-02-dispatch-table-executor.md), [D-06](../D-client/D-06-request-middleware-manager.md) |
| Blocks | [E-21](E-21-e-exit-gate.md), [G-03](../G-features/G-03-i18n-core.md) |
| Gate-conditional | no |
| Decisions | D38, D39, D40, D41; the D-06 middleware design (PR #2103) |
| Sources | [03-routing.md §5 "Middlewares"](../../research/03-routing.md), [05-network.md §2.3](../../research/05-network.md), D-06 (`aiogram/client/session/middlewares/`) |
| Size | L (4–5 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.
>
> **Design source.** Router middlewares (outer, inner and per-handler) take the design of the request-middleware
> manager that D-06 shipped:
> - one context object per chain invocation, passed explicitly, with `await ctx.next()`;
> - prebuilt chains;
> - `before=` / `after=` anchors with the same resolution rules;
> - a 3.x-signature adapter with a deprecation.
>
> Two statements on the research pages predate this and are superseded here: 03 §5 D41 says "typing only; the
> runtime is unchanged", and 03 §4 lists the 3.x `__call__(handler, event, data)` contract as kept. 3.x middlewares
> keep running through the adapter.

## Motivation

- In 3.x, middleware order is registration order only, so a user middleware can't be placed relative to the built-in
  `UserContextMiddleware` / `FSMContextMiddleware` on `dp.update`.
- Per-handler middlewares don't exist; users emulate them with flags and a router-wide middleware.
- `BaseMiddleware.__call__(handler, event, data)` is untyped, and its `handler` is a `functools.partial` built on
  every update.
- D-06 replaced the same shape on the session side with an explicit context and a prebuilt chain. Router middlewares
  take that design, so aiogram has one middleware model.
- D39–D41 are delivered on top of it. D38 keeps the `SkipHandler` data-sharing semantics and documents them.

## Design

```python
from aiogram.dispatcher.middlewares.base import BaseMiddleware, MiddlewareContext

@dp.update.outer_middleware(before=FSMContextMiddleware)
async def ban_check(ctx: MiddlewareContext[Update, OuterData]) -> Any:
    if is_banned(ctx.data["event_from_user"]):
        return None                      # short-circuit: no ctx.next()
    return await ctx.next()

class Throttle(BaseMiddleware[Message, AppData]):
    async def __call__(self, ctx: MiddlewareContext[Message, AppData]) -> Any:
        ctx.data["throttled"] = False    # inner scope, typed by AppData (D41)
        return await ctx.next()

@router.message(Command("x"), middlewares=[Throttle()])  # D40, innermost
async def handler(message: Message) -> None: ...
```

- **Context (`MiddlewareContext[EventT, DataT]`, name to confirm at the plan gate).**
  - `ctx.event` is the event.
  - `ctx.data` is the data dict of this chain's R09 scope, the same dict 3.x passes as `data`:
    - update scope for the `dp.update` outer chain;
    - router scope for a router's outer chain;
    - observer-trigger scope for inner and per-handler chains.
  - `await ctx.next()` runs the rest of the chain, then the chain's terminal (the frame body or the handler).
  - Calling `next()` again after it returns works (continuation called twice). Returning without calling it
    short-circuits. Concurrent `next()` calls on one context are not supported (documented), as in D-06.
  - A middleware replaces the event or the data by assigning `ctx.event` / `ctx.data` before `next()`. The value
    stays for the rest of that invocation, as `ctx.method` does in D-06.
  - The executor (E-02) creates one context per chain invocation over a prebuilt tuple of middlewares. The
    three per-update partial layers (`wrap_middlewares`, `functools.wraps`, the router closure) are gone.
  - Only middlewares get the context. Handlers and filters keep kwargs DI by name (D31 rejected a `ctx: Context`
    for them, and that stands).
- **3.x middlewares.**
  - `register` inspects the signature once, as D-06's `_adapt` does:
    - 3 required positional parameters is a 3.x `(handler, event, data)` middleware: it runs through an adapter,
      with a `DeprecationWarning` at registration;
    - 1 required positional parameter is the new protocol;
    - anything else raises `TypeError`, whose message mentions `functools.wraps`.
  - The adapter's `handler(event, data)` runs each call on its own fork of the context (D-06 `_fork`). So a 3.x
    middleware that calls `handler` twice, concurrently, or with a replaced event or data behaves exactly as in
    3.x, and the A-10 differential cases keep passing with 3.x-signature middlewares.
  - The warning points at the registration line for every form (`outer_middleware(m)`, `middleware(m)`, the
    decorators, `register(..., middlewares=[m])`). The test checks `record[0].filename`, as in D-06.
  - Registry: one `deprecation-4.x` entry, with the id allocated by the orchestrator when this plan starts.
- **Anchors (D39)**, the same rules as D-06 so both sides behave alike:
  - `outer_middleware(m, before=X)` / `after=X`, the same on `middleware(...)` (inner).
  - `X` is a class (the first registered instance, subclasses included, the middleware itself excluded) or a
    registered object (identity).
  - Anchors resolve once at snapshot compile.
  - A missing anchor raises `ValueError` naming the middleware, the anchor and the observer. Conflicting anchors raise
    `ValueError` naming the cycle (`A -> B -> A`).
  - The order is registration order; each entry is placed after everything that must run outside it (a DFS in
    registration order), so entries no anchor relates keep their registration order. Kahn's algorithm with index
    tie-breaking does not: it reorders unrelated entries, which D-06's tests caught.
  - Anchors relate entries of one manager only: outer and inner are separate lists, as are observers.
  - Iterating a manager gives execution order.
  - Default (no anchors): 3.x order.
- **Shared resolver.** D-06's `_resolve` / `_find` / `_name` (`aiogram/client/session/middlewares/manager.py`) move to
  one dispatcher-free module that both managers import (proposed `aiogram/utils/_middleware_order.py`). The D-06
  ordering and error tests move with them.
- **Per-handler middlewares (D40):**
  - `register(cb, *filters, flags=..., middlewares=[...])` and `@router.message(Command("x"),
    middlewares=[Throttle(2)])`;
  - the same protocol and adapter;
  - innermost (after the router-chain inner middlewares);
  - run only once the handler's filters pass;
  - prebuilt per candidate at compile.

  Flags and `get_flag` keep working.
- **Generic `BaseMiddleware[EventT, DataT]` (D41)** in `aiogram/dispatcher/middlewares/base.py`, defaults
  `TelegramObject`, `dict[str, Any]`. Its abstract method is `__call__(self, ctx: MiddlewareContext[EventT, DataT])`.
  `ctx.event` and `ctx.data` are typed by the parameters, and `DataT` is a D31 `TypedDict` (E-20).
- **Built-in middlewares are ported to the protocol:** `UserContextMiddleware`, `FSMContextMiddleware`,
  `ErrorsMiddleware` (until E-11), `CallbackAnswerMiddleware`, `ChatActionMiddleware` and the i18n middlewares.
  None of them goes through the adapter.
- **D38 documented:** a skipped handler's committed filter results and inner-middleware writes stay visible to the next
  candidate (already guaranteed by E-02). Add the docs paragraph and a test.

## Scope

**In:** everything under *Design*.

**Out:**
- Session / request middlewares (done in D-06; this plan only moves its resolver).
- The executor and its data scopes (E-02); snapshot caching and the topology epoch (E-03).

## Checklist

- [ ] `MiddlewareContext` with `event`, `data` and `next()`; the executor creates one per chain invocation over a
  prebuilt tuple.
- [ ] 3.x `(handler, event, data)` detection, an adapter with a per-call fork, a `DeprecationWarning` pointing at the
  caller for every registration form, and a registry entry.
- [ ] Built-in middlewares ported; no built-in goes through the adapter.
- [ ] `before=` / `after=` on outer and inner registration; stored, resolved in `compile_table`.
- [ ] Shared resolver module used by the session and router managers; D-06's tests moved with it.
- [ ] Errors: missing anchor (`ValueError`, naming the anchor and the observer), cycle (naming the cycle).
- [ ] `middlewares=[...]` on `register` and the decorator form; a prebuilt innermost chain per candidate.
- [ ] `BaseMiddleware` generic over the context; typing test with a D31 `TypedDict` (E-20) as `DataT`.
- [ ] Docs: the middlewares page (protocol, ordering, anchors, per-handler, D38 semantics, migration from
  `(handler, event, data)`).
- [ ] Changelog fragments (`feature`; `removal` for the deprecated signature).
- [ ] Tests:
  - anchors before and after the built-ins; instance vs class anchor; unrelated entries keep their order; missing
    anchor; cycle;
  - per-handler order relative to inherited inner middlewares; a per-handler middleware is not run when the filters
    fail;
  - D38 sharing;
  - a 3.x middleware that calls `handler` twice, concurrently, and with a replaced event or data.
- [ ] Bench `routing.52-handlers` (A-05) with the 2 outer + 2 inner middlewares: the protocol and the adapter
  against the 3.x baseline.

## Acceptance criteria

- `BanCheck` registered after the built-ins with `before=FSMContextMiddleware` runs before FSM (a test asserts the call
  order).
- A per-handler middleware runs exactly once per matched call and never for a candidate whose filters fail.
- With no anchors, the chain order equals 3.x, and the A-10 differential cases are unchanged with 3.x-signature
  middlewares (through the adapter, one `DeprecationWarning` each at registration).
- An outer middleware that calls `await ctx.next()` twice runs the rest of the chain twice; one that returns without
  `next()` short-circuits.
- The cost of the adapter is measured and recorded. D-06 measured a 3.x request middleware through its adapter at
  about 2.3× the 3.x chain with 3 middlewares, against 0.9× for the new protocol. Whether the router adapter's cost
  is acceptable, or the 3.x signature becomes a hard break instead, is decided at this plan's gate, by the same rule
  as D-06.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Keep `(handler, event, data)` with a prebuilt `partial` chain | Two middleware models (session and router); the per-call state stays implicit | D-06 design |
| A ContextVar carrier with the 3.x signature unchanged | Rejected for D-06 in favour of an explicit context; one model for both | D-06 design |
| A context copy per chain level (safe concurrent `next()`) | An allocation per middleware per update; concurrent `next()` is documented as unsupported | D-06 design |
| Numeric priorities | Collide across libraries; anchors name intent | D39 |
| Per-handler middlewares via flags only | Already possible; a first-class form is clearer and prebuilt | D40 |
| Change `SkipHandler` data sharing | Users depend on it; documented instead | D38 |

## Validation

```bash
make dev
uv run pytest tests -q
uv run python -m differential run --kind routing --left pypi:aiogram==<A-10 pinned 3.x version> --right path:.
make lint
uv run mypy aiogram
uv run python -m benchmarks compare --base v4-baseline/3.x-optimised --head WORKTREE --cases routing.52-handlers
```

## Workflow notes

- The session manager keeps importing the shared resolver; keep that module free of dispatcher imports.
- E-20's TypedDicts are used in the typing test; if E-20 isn't done, use a local `TypedDict`.
- G-01 (param resolver), G-03 (i18n), H-06 (tracing seams) and the scenes code call or wrap middlewares: grep for
  `(handler, event, data)` and port every in-tree caller in this plan.

## Notes
