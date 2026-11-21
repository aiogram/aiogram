# I-19 — Checker: heuristic and manual-checklist behaviour rules

| Field | Value |
|---|---|
| Status | `todo` |
| Story | I — Distribution & migration beta |
| Target branch | `dev-4.x` |
| Depends on | [I-14](I-14-migrate-engine.md), [E-03](../E-runtime/E-03-snapshot-lifecycle.md), [E-07](../E-runtime/E-07-sync-filter-execution.md), [E-09](../E-runtime/E-09-routing-keys-compiled-rejectors.md), [E-11](../E-runtime/E-11-error-model-bubbling.md), [F-03](../F-fsm/F-03-release-isolation-warn-after.md), [F-11](../F-fsm/F-11-callbackdata-without-pydantic.md) |
| Blocks | [I-22](I-22-migration-rehearsal.md), [I-23](I-23-beta-pre-release.md) |
| Gate-conditional | partly: the `CallbackData` rule follows F-11 (D14, gate-conditional); the rest is gate-independent |
| Decisions | D14, D28, D34, D42, D48, D110, D111, D114, PD-05, PD-26, R13, R28, 03 §3 (compiled rejectors) |
| Sources | [16-support-policy.md §2.2–2.3](../../research/16-support-policy.md), [18-docs-migration.md §2 scope](../../research/18-docs-migration.md), [README breaking changes 4, 12, 13, 15–17, 24](../../research/README.md), [11-removals.md §3, §4 CallbackData](../../research/11-removals.md), [19 D110, D111, D114, R13](../../research/19-review-resolutions.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Several 4.0 changes alter **behaviour** rather than names, so static analysis can't find them reliably (R28, 18 §2):
- isolation on by default (D28 / D110);
- sync filters running inline (D34);
- error bubbling (D48);
- skipped outer middlewares (D111);
- snapshot routing (D114);
- compiled rejectors (README breaking change 13).

R28 requires each such finding to be classed honestly as **heuristic** (with confidence) or a **manual checklist**
item (the guide lists it and `check` prints it once per project). Only class-based handlers and pydantic `CallbackData`
features have a mechanical part.

## Scope

**In.** Rules on the I-14 engine.

| Rule | Pattern | Class |
|---|---|---|
| Class-based handlers (D42) | `class X(MessageHandler)` etc. from `aiogram.handlers`: when the class has only `async def handle(self)` using `self.event` / `self.data` / `self.bot`, rewrite to `async def x(event, bot, **data)` and keep the decorator / `register`; otherwise report | definite fix for the simple pattern / definite report |
| `CallbackData` pydantic features (D14) | `Field(...)`, `@field_validator` / `@validator` / `model_validator`, `model_*` on `CallbackData` subclasses: report with the `__post_init__` recipe (11 §4) | definite report |
| Isolation-sensitive code (D28, D110, PD-26) | inside a handler, awaiting a future / `asyncio.Event` / queue that another handler of the same chat sets, or calling `dp.feed_update` / `feed_raw_update` from a handler: report with `async with state.release_isolation():` | heuristic, low |
| Sync filters doing I/O (D34) | a sync function used as a filter (positional filter argument or `F.func(fn)`) whose body calls `time.sleep`, `requests.*`, `open(`, `socket`, `subprocess`: report with `blocking(fn)` / `SyncFilterMode.THREAD` | heuristic, medium |
| Error handlers in sibling routers (D48, PD-05) | a router that has `@router.errors` handlers but no handler routers beneath it, or error handlers on a router other than the one raising: report "move to a common parent / dispatcher". Same pattern PD-05 warns about at snapshot compile | heuristic, medium |
| Outer middlewares (D111) | `router.<observer>.outer_middleware(...)` on a non-root router: manual-checklist item "outer middlewares of routers without a matching handler are skipped; middleware that must see every update belongs on `dp.update`" | manual |
| Registration after start (D114) | `include_router` / `.register(` / `.middleware(` inside `on_startup` callbacks or handlers: report "applies on `runner.refresh()` or restart" | heuristic, medium |
| Filters with side effects before a compiled rejector (breaking change 13) | a user filter placed before `Command(...)` / `F.x == literal` in the same handler's filter list whose body writes state (assignments to globals / attributes, awaits): report | heuristic, low |
| `unknown_update` with derived `allowed_updates` (R13) | `@router.unknown_update` (4.0 name) can't exist in 3.x code, so no finding. The guide carries the manual item | — |
| SkipHandler data reliance (D38, kept) | no finding: semantics kept as 3.x | — |
| Equality ignores binding (D108) | `==` / `in` / set and dict-key use of aiogram objects that relied on the bot binding: manual-checklist item "equality and hashing ignore the bound bot" | manual |
| `Unknown…` members on ambiguous unions (D107) | exhaustive `isinstance` / `match` over a union's variants: manual-checklist item "decoded unions can yield `Unknown…`; add a fallback branch" | manual |
| Nesting depth > 128 (`ValueError`) | constructing / decoding objects nested deeper than 128 levels: manual-checklist item | manual |
| Manual checklist summary | `check` prints the manual items (isolation default, sync filters inline, D111, D114, error bubbling, equality ignores binding, `Unknown…` on unions, depth > 128) once per run, with guide links, when the project imports `aiogram` | manual |

**Out:**
- Mechanical removals (I-16).
- Model semantics (I-17).
- Positional calls (I-18).

## Checklist

- [ ] Rule modules `rules/handlers.py`, `rules/callback_data.py`, `rules/behaviour.py`.
- [ ] The class-handler rewrite covers the 11 3.x handler classes in `aiogram/handlers/` (`MessageHandler`,
      `CallbackQueryHandler`, `ChatMemberHandler`, `ChosenInlineResultHandler`, `ErrorHandler`, `InlineQueryHandler`,
      `PollHandler`, `PreCheckoutQueryHandler`, `ShippingQueryHandler`, `BaseHandler`, `BaseHandlerMixin`).
- [ ] Manual-checklist output block (text and JSON), including the equality-ignores-binding, `Unknown…`-on-unions and
      depth > 128 items.
- [ ] Golden tests per rule, positive and negative, with expected confidence.
- [ ] Registry ids for breaking changes 4, 12, 13, 15, 16, 17 and 24 and for D42 (A-11 seed). Set class and coverage.
- [ ] Re-check the D48 / PD-05 pattern definition against E-11's implementation, so the warning and the finding agree.
      Record any mismatch in Notes.
- [ ] Tests (100% coverage of the rule modules).
- [ ] Changelog fragment `CHANGES/<id>.feature.rst` (behaviour checks in `aiogram migrate check`).

## Acceptance criteria

- Golden tests pass. The class-handler rewrite's `after` files compile and register the same observers.
- The manual block lists the equality-ignores-binding, `Unknown…`-on-unions and depth > 128 items.
- Every README breaking change in {4, 12, 13, 15, 16, 17, 24} maps to a heuristic rule or a manual item. A test checks
  this against the registry entries.
- Low-confidence findings are hidden unless `--min-confidence low` is passed (default `medium`). They always appear in
  JSON output.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Claiming the checker finds all behaviour changes | Not statically decidable; manual checklist | R28, 18 §2 |
| Rewriting sync filters to `blocking(fn)` automatically | Can't prove the I/O; report only | D34, R28 |
| Flagging SkipHandler data sharing | 3.x semantics kept | D38, R09 |

## Validation

```bash
make dev
uv sync --extra migrate
uv run pytest tests/test_migrate -q
uv run pytest tests
uv run mypy aiogram
uv run python scripts/migration_registry.py check
make lint
```

## Workflow notes

- Inputs: I-14 (engine); E-03, E-07, E-09, E-11 and F-03 (final behaviour and names); F-11 (`CallbackData` replacement).
- The `CallbackData` row blocks only if B-13 is a no-go.
- Runs in parallel with I-16 to I-18.

## Notes

(empty)
