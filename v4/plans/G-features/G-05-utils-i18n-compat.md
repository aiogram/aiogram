# G-05 — 3.x `aiogram.utils.i18n` compatibility layer

| Field | Value |
|---|---|
| Status | `todo` |
| Story | G — User-facing additions |
| Target branch | `dev-4.x` |
| Depends on | [G-03](G-03-i18n-core.md), [A-11](../A-contracts/A-11-migration-registry.md) |
| Blocks | [G-20](G-20-aiogram-i18n-final-release.md) |
| Gate-conditional | no |
| Decisions | D25, D12, D71, D72, PD-13 |
| Sources | [06-utils.md §3](../../research/06-utils.md), [11-removals.md §3, §4](../../research/11-removals.md), [16-support-policy.md §1](../../research/16-support-policy.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

D25 keeps every 3.x `aiogram.utils.i18n` name, with **no renames** (unlike aiogram_rust, 13 §4). 3.x bots using
`I18n` + `SimpleI18nMiddleware` + `_` / `__` must keep working on 4.0 without code changes. Internally they become
thin wrappers over the G-03 engine.

## Scope

**In:**
- These modules stay importable with their 3.x public names:
  - `aiogram/utils/i18n/__init__.py`;
  - `core.py` (`I18n`);
  - `context.py` (`get_i18n`, `gettext`, `lazy_gettext`);
  - `lazy_proxy.py` (`LazyProxy`);
  - `middleware.py` (`I18nMiddleware`, `SimpleI18nMiddleware`, `ConstI18nMiddleware`, `FSMI18nMiddleware`).
- `I18n(path=, default_locale=, domain=)` wraps a `GettextCore`. `current_locale`, `use_locale`, `context()`,
  `reload()`, `available_locales` and `gettext` / `lazy_gettext` delegate to the G-03 `ContextVar` and core.
- `gettext` / `_` and `lazy_gettext` / `__` keep their signatures (`singular, plural=None, n=1, locale=None`).
  `lazy_gettext` returns the G-03 lazy value, which implements the render protocol, instead of `babel.support.LazyProxy`.
  `aiogram.utils.i18n.LazyProxy` becomes an alias of the core lazy class. Babel is no longer needed for laziness.
- The 3.x middlewares subclass or wrap the G-03 middleware. `SimpleI18nMiddleware` reads `event_context.user`
  instead of the removed `event_from_user` (D12; 3.x `middleware.py`). `FSMI18nMiddleware` uses `FSMManager`.
  `I18nMiddleware.setup(router, exclude=…)` keeps its signature.
- `I18n` no longer subclasses `ContextInstanceMixin` (G-10 removes `utils.mixins`).
- Only the **3.x shape** is kept. New features (Fluent, `I18nContext` injection) live in `aiogram.i18n`. The wrappers
  inject the `i18n` and `i18n_middleware` data keys exactly as 3.x does (check the 3.x middleware code; the data key
  names must not change).

**Out:**
- New API: G-03.
- Rendering lazy values inside frozen types: G-06. Until G-06 lands, passing `__("x")` into a type field is G-06's
  concern.
- Deprecating `aiogram.utils.i18n`: not planned for 4.0 (D25 keeps the names). Revisit in a 4.x minor under D71.

## Checklist

- [ ] Rewrite the four modules over G-03, keeping every public name and signature (compare with `dev-3.x`).
- [ ] **Decide the fate of `I18n.get_current()` / `I18n.set_current()`** (inherited from `ContextInstanceMixin` in
      3.x, used by `get_i18n()`). Proposed default: keep both as thin classmethods over the G-03 `ContextVar`,
      emitting `AiogramDeprecationWarning` pointing to `aiogram.i18n`. Record in Notes and flag to owner.
- [ ] **Decide the `i18n` data-key collision.** The 3.x middleware injects the `I18n` instance under `i18n_key`
      (default `"i18n"`) and itself under `middleware_key` (`"i18n_middleware"`). The G-03 middleware injects an
      `I18nContext` under `i18n`. Proposed default: the 3.x wrappers keep injecting the `I18n` instance; installing
      both middlewares on one dispatcher with the same key raises at snapshot compile. Record in Notes and flag to
      owner.
- [ ] Migration-registry entries (PD-13, A-11 schema):
  - the `get_current` / `set_current` deprecation (if kept as deprecated);
  - `lazy_gettext` returning a core lazy object instead of `babel.support.LazyProxy`, so code checking
    `isinstance(x, babel.support.LazyProxy)` changes (kind `removal-4.0`).
- [ ] Port the 3.x i18n tests (`tests/test_utils/test_i18n.py` on `dev-3.x`) unchanged as the compatibility oracle.
      Every 3.x test passes except those tied to `event_from_user` and `ContextInstanceMixin`, which are rewritten.
- [ ] Docs: the 3.x i18n page keeps working, with a box pointing to `aiogram.i18n` for new code.
- [ ] Tests (100% coverage of new code).
- [ ] Changelog fragment (`misc` or `removal` for the Babel `LazyProxy` type change).

## Acceptance criteria

- The ported 3.x i18n test suite passes on 4.0, with only the rewrites listed in the checklist.
- A 3.x example bot using `I18n` + `SimpleI18nMiddleware` + `_` + `__` runs unchanged in a MockedBot test.
- `aiogram.utils.i18n` imports without Babel installed. `_()` works with stdlib gettext catalogs.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Renaming the 3.x classes | No rename churn | D25 |
| Keeping `babel.support.LazyProxy` as the lazy type | It doesn't implement the render protocol the encoder needs | D25, D117 |
| Deprecating `aiogram.utils.i18n` in 4.0 | D25 keeps the names; deprecation is a later D71 decision | D25 |

## Validation

```bash
make dev
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Consumes G-03 (engine, `ContextVar`, managers, lazy class) and A-11 (registry schema).
- Output: the compatibility mapping that G-20 cites, and import paths for I-16's codemod (no rewrite is needed for
  `aiogram.utils.i18n`).
- Runs in parallel with G-04 and G-07.

## Notes
