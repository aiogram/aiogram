# G-01 — ParamResolver hook

| Field | Value |
|---|---|
| Status | `todo` |
| Story | G — User-facing additions |
| Target branch | `dev-4.x` |
| Depends on | [E-02](../E-runtime/E-02-dispatch-table-executor.md), [E-03](../E-runtime/E-03-snapshot-lifecycle.md), [E-07](../E-runtime/E-07-sync-filter-execution.md) |
| Blocks | [G-02](G-02-depends-scope-teardown.md) |
| Gate-conditional | no |
| Decisions | D31, D32, D114, PD-01, PD-18 |
| Sources | [03-routing.md §5 "Dependencies", "Dependency injection (D31)"](../../research/03-routing.md), [19 D114, §8](../../research/19-review-resolutions.md), [codex-review.md R17](../../research/codex-review.md), [plans README §1](../README.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

D32 adds a small public hook so that a parameter annotated `Annotated[T, marker]` can be filled by something other
than the by-name lookup in `data`. Third-party DI containers use it directly. The built-in `Depends` (G-02) is the
reference resolver. Kwargs DI (D31) stays the base mechanism. The two **cooperate**: resolvers claim annotated
parameters, and every unclaimed parameter keeps the 3.x lookup (19 §8).

**PD-01 supersedes the "Additive (4.x; can ship in 4.0 if ready)" wording** in 03 §5 and in README D32. Story G
blocks GA, so this hook ships in 4.0.0.

## Scope

**In:**
- A `ParamResolver` protocol in `aiogram.dispatcher.di`, roughly:
  ```python
  class ParamResolver(Protocol):
      def claim(self, param: inspect.Parameter, annotation: Any, metadata: tuple[Any, ...]) -> ResolvedParam | None: ...
  class ResolvedParam(Protocol):
      async def resolve(self, scope: ResolveScope, data: Mapping[str, Any]) -> Any: ...
  ```
  The exact names are the implementer's choice, recorded in Notes. `ResolveScope` is the per-update object that G-02
  fills (cache, teardown stack). G-01 defines it as an opaque handle that resolvers may use.
- `dp.param_resolvers` uses E-03's ordered, **epoch-bumping** container (PD-18; E-03 builds it). Mutating it
  invalidates cached snapshots and triggers the D114 one-time warning when a running snapshot references the
  dispatcher.
- **Resolution plan.** `CallableObject` (3.x: `aiogram/dispatcher/event/handler.py`, `CallableObject.__post_init__`
  and `_prepare_kwargs`) computes a per-callable plan: which parameters are claimed, by which resolver, and which go
  by name. The signature is inspected once, at registration. The plan is **bound to resolvers at snapshot compile**
  (E-02/E-03), not at registration, because `param_resolvers` may still change before start. Cycle and precedence
  checks also run then, against the final configuration (R17).
- **Zero-cost path.** A callable with no `Annotated` metadata (or none claimed) keeps the 3.x `_prepare_kwargs` path
  with no extra dict, await or branch per call. A benchmark proves it (see Acceptance).
- **Call sites.** Handlers, filters (function filters and `Filter.__call__`), error handlers, and everything that goes
  through `CallableObject`. Flag callables and middlewares are G-02 (see the Decide item there).
- Unparameterised `Annotated[T, "doc string"]` (a marker no resolver claims) behaves like plain `T`: by-name lookup.

**Out:**
- The `Depends` resolver, per-update scope lifetime, cache and teardown: G-02.
- Typed DI `TypedDict`s (D31 docs): E-20.
- Snapshot compile and epoch machinery: E-03 (this plan only registers `param_resolvers` with it).

## Checklist

- [ ] `ParamResolver` / `ResolvedParam` / `ResolveScope` protocols, documented in a module docstring.
- [ ] `dp.param_resolvers` uses E-03's epoch-bumping container (PD-18); do not build one here.
- [ ] `CallableObject` plan: claimed vs by-name parameters, computed once. `**kwargs` callables keep receiving all of
      `data` plus the resolved values.
- [ ] Bind resolvers at snapshot compile; raise at compile (not at registration) for configuration errors, naming the
      callable and the parameter.
- [ ] **Decide resolver precedence and multiple markers** (proposed default: resolvers are asked in
      `param_resolvers` order and the **first claim wins**; a parameter whose `Annotated` metadata holds two markers
      that two different resolvers would claim raises at snapshot compile with both resolvers named) — record in
      Notes and flag to owner.
- [ ] **Decide what a claimed parameter does when its name is also in `data`** (proposed default: the resolver wins
      and the `data` value is ignored silently, same as FastAPI) — record in Notes and flag to owner.
- [ ] Positional-only parameters: a claimed positional-only parameter raises at compile (3.x passes kwargs only).
- [ ] Docs: "Dependency injection" concept page section on the hook, with a 20-line example of a third-party
      container resolver. State plainly that kwargs DI and resolvers cooperate.
- [ ] Tests (100% coverage of new code): plan with no markers, unclaimed marker, claimed marker, `**kwargs` callable,
      ordering, conflicting markers, epoch bump on `param_resolvers.append`, sync and async callables.
- [ ] Changelog fragment (`feature`). No migration-registry entry, because nothing breaks.

## Acceptance criteria

- A handler with no `Annotated` parameters is within **±3%** of the E-02 baseline on the pinned "first handler
  matches" dispatch bench (A-05 harness, 03 §2 scenario). Measured with and without one unrelated resolver
  registered.
- A test resolver that claims `Annotated[int, Answer()]` delivers `42` to a handler, to a function filter and to a
  `Filter.__call__` in the same update.
- Appending to `dp.param_resolvers` after a snapshot is compiled increments the epoch. `dp.feed_update()` then
  recompiles, and a running Runner emits the D114 one-time warning.
- A configuration error (conflicting markers, positional-only claimed parameter) raises at snapshot compile with a
  message naming the callable's qualname and the parameter.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Typed `ctx: Context` argument as a second DI style | A second style for a purely additive gain | D31 |
| Decorator that rewrites handler signatures (`@inject`) | The hook plugs containers in with no signature rewriting | D32 |
| Binding resolvers at registration | `param_resolvers` can change before start; R17 asks for checks after the final configuration | R17, D114 |
| Plain list for `param_resolvers` | Mutation would not invalidate cached snapshots | PD-18 |

## Validation

```bash
make dev                      # or: maturin develop --release
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Consumes the snapshot compile and epoch API from E-03 and the `CallableObject` rework in E-02.
- G-02 builds directly on the protocols. Agree the `ResolveScope` handle with G-02 before merging if both run in
  parallel.
- H-17 (toolkit interop) and E-20 (typed DI docs) reference this hook in docs only.

## Notes
