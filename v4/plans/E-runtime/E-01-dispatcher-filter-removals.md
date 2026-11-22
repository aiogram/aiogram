# E-01 — Dispatcher and filter legacy removals

| Field | Value |
|---|---|
| Status | `done` |
| Story | E — Routing & runtime |
| Target branch | `dev-4.x` |
| Depends on | [A-01](../A-contracts/A-01-bootstrap-dev-4x.md), [A-11](../A-contracts/A-11-migration-registry.md) |
| Blocks | [E-20](E-20-typed-di-typeddicts.md), [E-21](E-21-e-exit-gate.md) |
| Gate-conditional | no |
| Decisions | D12, D42, 11 §3, README breaking change 11 |
| Sources | [11-removals.md §3, §7](../../research/11-removals.md), [README breaking changes](../../research/README.md), [19](../../research/19-review-resolutions.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

11 §3 lists the dispatcher/filter code that exists only for 2.x or early-3.x compatibility. Removing it first gives
the routing rewrite (E-02 onward) a smaller surface: no class-based handler special case in `HandlerObject`, no
`REJECTED` branch in propagation, and no `event_from_user` keys to model in the typed DI dicts (E-20).

## Scope

**In:**
- **Class-based handlers (D42):** delete `aiogram/handlers/` (11 files: `BaseHandler`, `BaseHandlerMixin`,
  `MessageHandler`, `CallbackQueryHandler`, `ChatMemberHandler`, `ChosenInlineResultHandler`, `ErrorHandler`,
  `InlineQueryHandler`, `PollHandler`, `PreCheckoutQueryHandler`, `ShippingQueryHandler`), the
  `issubclass(callback, BaseHandler)` branch in `HandlerObject.__post_init__` (`aiogram/dispatcher/event/handler.py`),
  `tests/test_handler/`, the `BaseHandler` cases in `tests/test_dispatcher/test_event/test_handler.py`, and
  `docs/dispatcher/class_based_handlers/` with its toctree entry.
- **`CancelHandler`** (`aiogram/dispatcher/event/bases.py`) and its use in
  `aiogram/dispatcher/middlewares/error.py` (`except (SkipHandler, CancelHandler)`).
- **`REJECTED`** sentinel (`event/bases.py`) and the `response is REJECTED` branch in `Router._propagate_event`.
- **`UnsupportedKeywordArgument`** (`aiogram/exceptions.py`, raised in `TelegramEventObserver.register`): replace with a
  plain `TypeError` with the same message.
- **`Recommendation` warning** for `from magic_filter import F` (`FilterObject.__post_init__`,
  `aiogram/utils/warnings.py`); the `aiogram.utils.magic_filter.MagicFilter` subclass (with `.as_()`) stays. Add a
  docs note in the magic-filters page.
- **`BaseFilter = Filter`** alias and its `__all__` entry in `aiogram/filters/__init__.py`.
- **`dp["k"] = v` / `del dp["k"]`**: remove `Dispatcher.__setitem__` / `__delitem__`; keep `__getitem__` and `get`.
- **`event_from_user` / `event_chat` / `event_thread_id` injection (D12):** remove the keys and their writes in
  `aiogram/dispatcher/middlewares/user_context.py` (`EVENT_FROM_USER_KEY`, `EVENT_CHAT_KEY`, `EVENT_THREAD_ID_KEY`);
  `event_context` stays the only injected context. Switch `aiogram/utils/i18n/middleware.py`
  (`SimpleI18nMiddleware.get_locale`) to `data["event_context"].user`.
- **`event_business_connection_id`** (11 §3): documented as a handler kwarg (declared in `MiddlewareData`,
  `aiogram/dispatcher/middlewares/data.py`, and rendered on the dependency-injection docs page) but never set by any
  middleware. Proposed: remove it from the docs (no runtime change, nothing injects it); E-20's rewritten TypedDicts
  don't include it. See the Decide item.
- Delete `tests/deprecated.py` (`check_deprecated`, no callers) and the compat-only test cases 11 §7 names for this
  area (`event_from_user` cases in the user-context tests, the Recommendation case in `test_handler.py`).

**Out:**
- The typed-DI TypedDicts in `middlewares/data.py` (E-20 removes the `event_*` keys there).
- `utils.markdown`, `utils.mixins`, `deep_linking` re-exports (G-10); `content_type` (C/B stories); `RestartingTelegram`
  (D-02); `MongoStorage` (F-07).
- The i18n core rewrite (G-03/G-05); this plan only changes the one lookup line so the middleware keeps working.

## Checklist

- [ ] Remove `aiogram/handlers/` and every import of it; `HandlerObject` loses the `BaseHandler` branch.
- [ ] Remove `CancelHandler`, `REJECTED`, `UnsupportedKeywordArgument` (→ `TypeError`), `Recommendation`.
- [ ] Remove `BaseFilter`.
- [ ] Remove `Dispatcher.__setitem__` / `__delitem__`; reads stay.
- [ ] Stop injecting `event_from_user`, `event_chat`, `event_thread_id`; i18n middleware reads `event_context.user`.
- [ ] **Decide the fate of the documented-but-never-set `event_business_connection_id`** (proposed default: remove
      it from the docs and from `MiddlewareData`, with a `removal-4.0` registry entry pointing to
      `event_context.business_connection_id`; nothing to remove at runtime) — record in Notes and flag to owner.
- [ ] Delete the tests, docs pages and toctree entries listed in Scope; grep `docs/` and `examples/` for leftovers.
- [ ] Migration-registry entries (PD-13, `aiogram/_migration/registry.toml`, kind `removal-4.0`, ids from A-11):
  one each for `aiogram.handlers`, `CancelHandler`, `REJECTED`, `BaseFilter`, `UnsupportedKeywordArgument`,
  `dp[...]` writes, `event_from_user`/`event_chat`/`event_thread_id`, with replacement text from 11 §3.
- [ ] Changelog fragment(s) in `CHANGES/` (category `removal`).
- [ ] Tests (100% coverage of touched code): `register(cb, unknown_kw=...)` raises `TypeError`; `dp["k"] = v` raises
  `TypeError` (no `__setitem__`); handler data contains `event_context` and none of the removed keys.

## Acceptance criteria

- `python -c "import aiogram.handlers"` fails with `ModuleNotFoundError`.
- `grep -rn "CancelHandler\|REJECTED\|BaseFilter\|UnsupportedKeywordArgument\|event_from_user\|event_chat\b\|event_thread_id\|Recommendation" aiogram/`
  returns nothing (except the registry file and changelog).
- `grep -rn "event_business_connection_id" docs/ aiogram/` returns nothing (except the registry file and changelog).
- Full suite passes; coverage of `aiogram/dispatcher/**` and `aiogram/filters/**` stays at 100%.
- Each removed name has a registry entry that `I-12`'s registry CI accepts.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Keep class-based handlers behind a deprecation | No real usage found; they force a special case into `HandlerObject` | D42 |
| Keep `event_from_user` as a deprecated alias for one window | 4.0 resets compat; `event_context` has existed since 3.5 | D12 |
| Keep `dp[...] = v` writes | Writes after start would bypass the routing snapshot (D114); set data through `Dispatcher(**kw)` / `workflow_data` | 11 §3, D114 |
| Remove `MagicFilter.as_()` subclass along with the warning | Users rely on `.as_()`; only the warning is legacy | 11 §3 |

## Validation

```bash
make dev                       # build the extension (maturin develop --release)
uv run pytest tests -q
make lint                      # ruff check/format + mypy, as CI
uv run mypy aiogram
uv run --extra docs bash -c 'cd docs && make html'   # docs pages removed
```

## Workflow notes

- Can run in parallel with E-02 (touches different symbols); rebase E-02 on top if it lands first.
- E-20 consumes the removal of the `event_*` keys.
- G-05 (3.x `utils.i18n` compat layer) must keep the `event_context.user` lookup this plan introduces.

## Notes
