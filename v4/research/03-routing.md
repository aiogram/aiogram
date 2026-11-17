# 03 — Routing & dispatch: Python redesign (no Rust)

Verdict (D5): **stays Python.** Every filter, middleware and handler is a Python awaitable. A Rust core
could only speed up the glue between them (≈1–3 µs/update *est.*), while bridging awaits costs tens of µs.
The big wins are Python fixes plus a precompiled routing snapshot per Runner (D114), which free-threading needs anyway.

## 1. Today's path (per update)

1. `Dispatcher.feed_update` (`dispatcher.py:145`): re-validate if `update.bot != bot` (:165), merge
   kwargs (:168-177), log (:183).
2. `update.wrap_outer_middleware` (`event/telegram.py:96`) → `wrap_middlewares` (`middlewares/manager.py:56`)
   builds a **new `functools.wraps` + `partial` chain on every call**. Errors → UserContext
   (`resolve_event_context` if-chain, `user_context.py:63`) → FSMContext (`fsm/middleware.py:41-56`).
3. `_listen_update` (:260) → `update.event_type` (if-chain, `types/update.py:185`) →
   `Router.propagate_event` (`router.py:166`): a new closure per router, outer middlewares wrapped again.
4. `_propagate_event` (:182) → `observer.trigger` (`telegram.py:111`) → per handler `HandlerObject.check`
   (`handler.py:119`) → `FilterObject.call` (`handler.py:73`, two kwargs dict copies + a `partial` each).
   On a match the inner chain is rebuilt (`_resolve_middlewares` walks `chain_head`).
5. On a miss → recurse into `sub_routers` (:206).

## 2. Measurements

Bench: dp→r1→r2→r3, 52 handlers (half `Command`, half `F.text ==`), 2 outer + 2 inner middlewares,
`MockedBot`, 10k updates.

| Scenario | Today | With MagicFilter called inline |
|---|---|---|
| first handler matches | 98 µs | 33.5 µs |
| mid / last / unhandled | 1 720–1 916 µs | 215–223 µs |
| fixed overhead, FSM on / off | 30.2 / 21.6 µs | — |

**Root cause of the worst case**: `FilterObject` swaps a `MagicFilter` for its sync `.resolve`
(`handler.py:85-89`) without marking it awaitable, so every `F` filter runs through `asyncio.to_thread`
(`handler.py:77`): 43.4 µs vs 0.78 µs inline. This has been the case since #1661 and is a 3.x bugfix ([09](09-3x-quick-wins.md)).

Remaining cost ≈4 µs per handler checked, spread over `check`/`trigger`/`_prepare_kwargs`,
`Command` parsing (each `Command` filter re-parses the text: 3.3 µs), `wrap_middlewares`
(≈38% of the fixed path).

## 3. v4 design: compiled `DispatchTable` (per-Runner routing snapshot, D114)

Compiled by each Runner at start (polling **and** webhook) as an immutable snapshot; `dp.feed_update()` without a
Runner compiles one and caches it keyed by a topology epoch (recompiled after any change):

```
DispatchTable (immutable)
  outer_chain: callable                       # prebuilt middleware chain for dp.update
  by_event: dict[str, EventPlan]              # "message", "callback_query", ...
EventPlan
  candidates: tuple[(router, HandlerObject, inner_chain), ...]   # DFS order == today's order
  command_index: dict[str, tuple[int, ...]]   # positions of handlers whose plain Command matches name
  root_filters: tuple[...]                    # per router, incl. dp.update.filter
workflow_data: MappingProxyType
```

- **Order stays the same**: the table is a flattening of the router tree. Inner middleware semantics,
  `SkipHandler`, `UNHANDLED`, filter-returned dicts merged into kwargs, `flags`, DI by signature: all unchanged.
- **Flatten everything (D111, documented break)**: the compiled plan for a matched candidate wraps only the outer
  middlewares of the routers **on its path**. Outer middlewares of routers that hold no matching candidate are
  **skipped**, although in 3.x they run for every update reaching them. Routing keys are computed once per update,
  so an outer middleware that replaces the event doesn't change routing. Continuation-called-twice and
  short-circuit still work on the path. README breaking change 24. The scene state index (04 §8) is a skip
  optimisation under the same rule: it keeps wildcard/general handlers and DFS precedence.
- **Command index** is only a *skip* optimisation. It covers the exact `Command` class with plain-string
  commands. Regex, `ignore_case`, subclasses and custom prefixes stay in the normal path. The command is
  parsed once per update and cached in the data dict.
- **Prebuilt chains**: outer chain per path, inner chain per handler, built at snapshot compile.
- **3.x data scopes kept exactly (D38, R09)**: update, router (copy at router entry), observer-trigger (shared,
  D38) and candidate-check (copied lazily at the first dict-returning filter, committed only on success).
  `CallableObject` keeps its cached signature spec.
- **MagicFilter**: resolved inline (sync, cheap), compiled to closures at snapshot compile (D37). User sync **filters**
  run inline by default (D34); sync **handlers** still go to a thread.
- **Event-type and event-context resolution**: replace the if-chains with a dict keyed by the first
  non-null update field. With Rust-native `Update` (01) the Rust side can expose `update.event_type` and
  `update.event` directly, which costs nothing extra.
- **Routing keys in one call (D26, 13 B14)**: `update.routing_keys()` returns event type, parsed command
  (name, mention, args, split with the exact 3.x `str.split` rule), text, callback data, chat type and content kind in one Rust call,
  cached for the update. Filters compiled below read from it rather than making one FFI getattr per handler.
  Without this, a Python router over native objects is about 13% slower than 3.x (aiogram_rust).
- **Compiled rejectors (13 B13)**: at snapshot compile, `Command` (plain strings, default prefix, no `magic`),
  truthy `F.a.b` and `F.a.b == literal` compile into per-candidate rejectors plus a literal index
  `{(path, literal): positions}`, generalising the command index. **Skip rule (as in aiogram_rust)**: a candidate
  is skipped as soon as any compiled filter is certainly false, even when user filters come before it. Those
  filters then don't run, so their side effects and exceptions are lost. This is a documented break (README
  breaking change 13): filters must not rely on running for handlers that can't match. An agreement test checks that whenever a rejector rejects, the real filter is false, over a matrix of filters
  × events (including U+001C–U+001F whitespace).
- **Late registration (D114, replaces D19's "raise while running")**: at start, each Runner compiles an immutable
  snapshot of the routing table, chains, copied flags, filters, `Depends` plans and the scene registry.
  Dispatchers and routers stay ordinary mutable objects, and sharing across Runners and dispatchers is safe by
  construction. Changes after start apply **on restart or `runner.refresh()`**; a one-time warning fires when
  someone mutates a graph that a running snapshot references. Nothing raises. Readers take the snapshot reference
  once per update. The snapshot captures structure, not object state: filter and middleware instances are shared,
  and their thread safety is the user's.

Expected: worst case 220 → ≈60–90 µs, fixed 22 → ≈12–15 µs *est.*

## 4. Free-threading

Mutated at runtime today, and racy if routers are touched while running: `TelegramEventObserver.handlers`
(`telegram.py:30,86`), root filters (:45-47), `MiddlewareManager._middlewares`, `sub_routers`,
`HandlerObject.flags` (mutated by `Filter.update_handler_flags`), `SceneRegistry._scenes`,
`Dispatcher.workflow_data`. The routing snapshot removes all of them from the hot path (D114).

Loop-bound state on `Dispatcher` (`_running_lock`, `_stop_signal`, `_handle_update_tasks`,
`dispatcher.py:104-107, 442-443, 548-557`) moves into a **per-loop `Runner`** object (full design, with update sources and multi-bot, in [12](12-runtime.md)). One `Dispatcher`
(one snapshot per Runner) can then serve N threads, each with its own loop, its own `Bot`/session (aiohttp sessions are
loop-bound) and its own `Runner`. Already safe: sentinels, `ContextVar`s, `lru_cache` in `utils/token.py`,
`CallbackData` ClassVars, MagicFilter operation tuples.

## 5. Compatibility constraints (must keep)

`router.<event>.register(cb, *filters, flags=)` and decorators; filters as callables, `Filter` subclasses,
MagicFilters, or dict-returning; `BaseMiddleware.__call__(handler, event, data)` with a mutable `data`
(short-circuit, call `handler` more than once); inherited inner middlewares; `handler`/`event_router`/
`event_update`/`dispatcher`/`bot`/workflow data in kwargs, **identical for polling and webhook**; `get_flag`;
sync handlers in threads; Scenes registering through `router.observers[...]` (`scene.py:389`).

### Dependency injection (D31)

Kwargs DI stays the base mechanism: names are matched against `data`, or everything is passed when the callable
takes `**kwargs`. `Depends` / `ParamResolver` (D32) cooperate with it: they claim annotated parameters, and the
rest keep the by-name lookup. A typed `ctx: Context` argument was considered and **rejected**, because it would be a second
DI style for a purely additive gain. Typed DI is documented through PEP 692 instead, which needs no new
machinery:

```python
class AppData(AiogramData):  # inner data: handlers, filters, inner middlewares
    db: Database             # set by a user outer middleware

@router.message(Command("start"))
async def start(message: Message, **kw: Unpack[AppData]) -> None:
    await kw["db"].touch(message.from_user.id)
```

The docs ship **separate outer and inner base `TypedDict`s**, because keys become available at different points:
an outer one (`bot`, `bots`, `dispatcher`, `event_update`, `event_context`, `fsm_storage`) for `dp.update` outer
middlewares, and `AiogramData`, extending it with `state`, `raw_state`, `event_router` and `handler`, for inner
middlewares, filters and handlers. Keys that only some paths set are declared `NotRequired[...]`; subclassing with
`total=False` would not make the inherited keys optional. This is docs only; no runtime change.

### Filters (D34–D37)

| # | Decision |
|---|---|
| **D34** | **Sync filters run inline by default.** `Dispatcher(sync_filters=SyncFilterMode.INLINE)` is the 4.0 default; `SyncFilterMode.THREAD` restores 3.x globally. `SyncFilterMode` is a hand-written `StrEnum` in `aiogram.filters` (not generated), so `"inline"` / `"thread"` strings are accepted too. Per-filter overrides work for lambdas too: `inline(fn)` and `blocking(fn)` from `aiogram.filters`, e.g. `router.message(blocking(check_in_db))` or `inline(lambda m: …)`. Sync **handlers** keep `to_thread` (unchanged) |
| **D35** | No `&` / `\|` on `Filter`; `and_f` / `or_f` / `~` stay the only combinators (no operator-precedence surprises such as `&` binding tighter than `==`) |
| **D36** | When a filter's dict result overwrites a key that already exists in `data`, a **`RuntimeWarning`** fires once per (filter, key). The merge itself is unchanged (later wins) |
| **D37** | `magic-filter` stays an **external dependency**. At snapshot compile aiogram compiles each `F` expression into a specialised Python closure by reading its operation tuples (≈0.77 µs → ≈0.2 µs *est.*, no API change); compile support can move upstream later |

Why D34: many filters run per update while only one handler runs. Sync filters share the default thread pool
(`min(32, cpu+4)` workers) with sync handlers, so blocking handlers could stall routing for every update.
And each thread hop costs about 43 µs. The thread behaviour was never documented for filters
(`docs/dispatcher/filters/index.rst:34`). README breaking change 16.

### Middlewares (D38–D41)

| # | Decision |
|---|---|
| **D38** | **`SkipHandler` keeps the 3.x data semantics.** One observer-trigger `kwargs` dict is shared across candidate handlers (`telegram.py:111-128`). A skipped handler's filter results (committed because all its filters passed) and its inner-middleware writes stay visible to the next candidate; results of a candidate whose filters failed are not committed (R09). This is now documented |
| **D39** | **Registration order stays the default**, plus anchors: `outer_middleware(m, before=X)` / `after=X`, where `X` is a middleware class (first match) or instance, e.g. `dp.update.outer_middleware(BanCheck(), before=FSMContextMiddleware)`. Anchors resolve once at snapshot compile; a missing anchor raises at start; conflicting anchors raise with the cycle named. The same parameters exist on inner `middleware(...)` and on session middlewares |
| **D40** | **Per-handler middlewares**: `register(cb, *filters, flags=…, middlewares=[...])` and the decorator form `@router.message(Command("x"), middlewares=[Throttle(2)])`. They run **innermost**, after the router-chain inner middlewares and only once the handler's filters pass, and are prebuilt at snapshot compile. Flags + `get_flag` keep working |
| **D41** | **Generic `BaseMiddleware[EventT, DataT]`** (defaults `TelegramObject`, `dict[str, Any]`): `class M(BaseMiddleware[Message, AppData])` gets typed `event` and `data` (a D31 `TypedDict`) in `__call__`. Typing only; the runtime is unchanged and unparameterised subclasses keep working |

### Errors (D47–D50)

| # | Decision |
|---|---|
| **D47** | **API errors: a reason enum, no new classes.** The 3.x classes stay as they are (`TelegramBadRequest`, `TelegramForbiddenError`, …; `RestartingTelegram` removed). A generated `ErrorReason` `StrEnum` (from `errors.json`, 945 messages) is exposed as `e.reason`, or `None` for messages that aren't known yet; `e.reason_args` holds the values captured from the 37 `%s`/`%d` templates. Member names come from the MTProto code where one exists (`ADMINS_TOO_MUCH`), otherwise from a normalised slug, with overlay overrides for stable names (`MESSAGE_NOT_MODIFIED`, `BOT_BLOCKED`). Matching is lazy on first access: exact lookup, then the template regexes. Usage: `except TelegramBadRequest as e: if e.reason is ErrorReason.MESSAGE_NOT_MODIFIED`, or `@router.errors(F.exception.reason == ErrorReason.BOT_BLOCKED)` |
| **D48** | **Error handlers bubble.** An error raised while handling an update goes first to the `errors` observer of the router where it was raised (the matched handler's router, or the router whose middleware or filter failed). If that is `UNHANDLED`, it goes to the parent, and so on up to the dispatcher. Sibling routers no longer see each other's errors (README breaking change 17). The snapshot stores each handler's router path, so bubbling costs nothing when there is no error |
| **D49** | **`ErrorEvent` enriched**: it becomes a frozen dataclass (not a Bot API type) with `update`, `exception`, `bot`, `router`, `handler` (`HandlerObject \| None` before matching) and `phase` (`ErrorPhase` `StrEnum`: `OUTER_MIDDLEWARE`, `FILTER`, `INNER_MIDDLEWARE`, `HANDLER`, `DECODE`, plus `DEPENDENCY` and `TEARDOWN`, D112). Decode failures (10 §3, the `Update` shell with `decode_error`) arrive with `phase=DECODE` |
| **D50** | **`dp.runtime_errors` observer** for errors that happen outside update handling: polling fetch failures, startup/shutdown hooks, `bot_added`/`bot_removed` hooks, webhook background replies, `Depends` teardown (D32, phase `TEARDOWN`, D112) and RetryMiddleware giving up in the background. It receives `RuntimeErrorEvent(exception, phase, bot \| None, update \| None)`. When nothing handles the event it is logged as today. An exception raised inside a `runtime_errors` handler is only logged, so there is no recursion |

### Router API and flags (D55–D58)

Defaults:
- Router observers are **generated from the IR** as a `_RouterObservers` mixin, the same way as `_BotMethods`. The hand
  list in `router.py:38-101` goes away, and so does a Bot API bump step.
- Observers are typed, e.g. `TelegramEventObserver[Message]`, so mypy checks the handler's event parameter against
  `@router.message()`. Typing only.
- `resolve_used_update_types` reads the routing snapshot.

| # | Decision |
|---|---|
| **D55** | **No router-level filter.** Per-observer `.filter()` stays the only root-filter API |
| **D56** | **A router may have multiple parents.** `include_router` still raises on self-inclusion and on cycles: it does a DFS over the child's subtree looking for the new parent, so the graph stays a DAG. It also raises when the same router is included twice under the same parent. Each dispatcher's table compiles every path on its own, so inner-middleware inheritance and router flags (D57) are resolved per path. **Within one dispatcher**, a router reachable through two paths (a diamond) raises at snapshot compile (confirmed, D90; D114) and names both paths, because its handlers would otherwise be tried twice for the same update. Reuse is meant across dispatchers and trees. `parent_router` keeps working for a single parent. With several parents it raises and points to the new `parent_routers` tuple |
| **D57** | **Router-level flags**: `Router(flags={...})`, merged at snapshot compile from the outermost router to the innermost, then the handler's own flags (decorators, `register(flags=)`, `Filter.update_handler_flags`). The nearest value wins. With multiple parents the merge is per path |
| **D58** | **Optional typed flag specs.** `@flag_spec class Throttle: rate: float; key: str = "user"` (frozen dataclass, flag name `throttle` or `name=`). The spec instance works as a decorator (`@Throttle(rate=1)`) and in `Router(flags=[Throttle(rate=2)])`. `flags.throttle(rate=1)` is validated against the spec at registration. `get_flag(data, Throttle) -> Throttle \| None`, and `get_flag(data, "throttle")` still works. Plain string flags and unknown names stay allowed |

### Instrumentation (D54, revised by D63)

One official trace hook for the testing toolkit (14), OpenTelemetry (PR #1787) and logging. It takes the shape of
**sync span context managers**, so nesting works naturally:

```python
class DispatchTracer(Protocol):
    def span(self, kind: SpanKind, **attrs: Any) -> ContextManager[Span | None]: ...

# SpanKind: UPDATE, ROUTER, OUTER_MIDDLEWARE, FILTER, INNER_MIDDLEWARE, HANDLER, API_CALL, TEARDOWN
dp.tracers.append(MyTracer())            # picked up at snapshot compile (D114)
```

- Attributes include `update_id`, `update_type`, `bot_id`, `router`, `handler`, `middleware`, `filter`, `method`, and
  `result` / `exception`, which are set on the span before exit.
- With no tracer installed (checked once at snapshot compile) there is zero cost. With one, it costs one context-manager
  enter/exit per stage.
- Tracers are called manually (`__enter__` / `__exit__`) and exited in reverse order, with failures logged. Their
  return value is ignored and the original exception re-raised, so a tracer can never suppress or replace an app
  error (R23). `Span` is a small `set_attribute` protocol.
- Callback-style consumers (the testing toolkit's route diagnostics) use a small `CallbackTracer` adapter.
- `API_CALL` spans come from a request middleware that the integration installs (05).

Full observability design: [15](15-observability.md).

### Dependencies: resolver hook + minimal `Depends` (D32)

Additive (4.x; can ship in 4.0 if ready). The gain is per-handler resources: a DB session is opened only for
handlers that declare it, instead of by a middleware on every update. It also brings teardown and test overrides,
and typed parameters through `Annotated`.

```python
async def get_session(db: Database) -> AsyncIterator[Session]:   # `db` comes from data, as kwargs DI
    async with db.session() as s:
        yield s                                                  # teardown after the whole update

SessionDep = Annotated[Session, Depends(get_session)]

@router.message(Command("me"), IsRegistered())
async def me(message: Message, session: SessionDep) -> None: ...

class IsRegistered(Filter):
    async def __call__(self, message: Message, session: SessionDep) -> bool: ...   # same cached session
```

**Hook (public, small)**
- `ParamResolver` protocol. At registration `CallableObject` gives each parameter's `Annotated[T, *meta]` to the
  registered resolvers (`dp.param_resolvers`). A resolver that claims a parameter fills it at call time. Parameters
  nobody claims keep the 3.x by-name lookup in `data`.
- The resolution plan is computed once at registration. Callables without markers keep today's fast path, so there
  is zero overhead for code that doesn't use this.
- Third-party containers plug in through the same hook, with no decorator that rewrites signatures.

**Built-in `Depends(provider, *, use_cache=True)`** is the reference resolver, about 100 lines:
- A provider's own parameters are resolved the same way (`data` names, nested `Depends`), so sub-dependencies work.
  Cycles are detected at registration.
- Providers may be async/sync functions or async/sync generators. Sync providers are called inline, not in a thread,
  so I/O belongs in async providers (documented).
- **Cache per update**, keyed by provider and shared by filters, handlers and middlewares within that update.
  `use_cache=False` calls the provider every time.
- **Where it resolves**: handler parameters, filter parameters (function filters and `Filter.__call__`, resolved
  while matching), flag callables, error handlers. **Middlewares** use `session = await resolve(get_session, data)`
  (`aiogram.dispatcher.di.resolve`), which shares the same cache and teardown. The `(handler, event, data)`
  signature is unchanged.
- **Teardown after the whole update**: generators are closed in reverse setup order once `feed_update` has
  finished, after all outer middlewares. **Providers always see the exception (D112)**: the exception that escaped
  the handler chain is recorded and thrown into every yield-provider (`athrow` / `throw`) regardless of later
  handling by `errors` handlers, so transactions roll back; a provider that swallows it doesn't suppress it.
  Teardown errors go **only** to `dp.runtime_errors` (phase `TEARDOWN`) and are never re-raised from
  `feed_update`. Teardown completes before a source marks the update done. Because filters can resolve dependencies, a provider
  may run for a handler that ends up not matching; teardown still cleans it up.
- The per-update scope lives in `data` under a private key, created by `Dispatcher.feed_update`. That is the single
  boundary for polling, webhook background tasks and custom sources (12 §3).
- **Overrides**: `dp.dependency_overrides[get_session] = fake_session` for tests. Captured in the Runner's
  snapshot (D114), so it's safe under free-threading.
- Not included: application-level singletons and custom scopes. `workflow_data` / `Dispatcher(**kwargs)` already
  cover singletons; scopes beyond an update are left to resolvers plugged in through the hook.

## 6. Rust later?

Only if profiling after §3 still shows dispatch overhead mattering: a compiled MagicFilter evaluator for pure
attribute/compare chains. Expected ≤1–3 µs/update. Not planned for 4.0.
