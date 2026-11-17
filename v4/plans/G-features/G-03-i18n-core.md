# G-03 — i18n core: engines, context, managers, lazy values

| Field | Value |
|---|---|
| Status | `todo` |
| Story | G — User-facing additions |
| Target branch | `dev-4.x` |
| Depends on | [E-06](../E-runtime/E-06-middleware-api.md), [E-20](../E-runtime/E-20-typed-di-typeddicts.md) |
| Blocks | [G-04](G-04-fluent-engines.md), [G-05](G-05-utils-i18n-compat.md), [G-06](G-06-lazy-text-capture.md), [G-07](G-07-lazy-filter.md), [G-10](G-10-utils-removals.md), [G-12](G-12-commands-from-handlers.md), [G-20](G-20-aiogram-i18n-final-release.md) |
| Gate-conditional | no |
| Decisions | D25, D69, D12, D39, D111 |
| Sources | [06-utils.md §3](../../research/06-utils.md), [08-build-release.md §8](../../research/08-build-release.md), [11-removals.md §3–§4](../../research/11-removals.md), [13-aiogram-rust-review.md §4](../../research/13-aiogram-rust-review.md), [15-observability.md](../../research/15-observability.md), [codex-review.md R21](../../research/codex-review.md) |
| Size | L (4–5 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

D25 absorbs i18n into core. `aiogram_i18n`'s `LazyProxy` relies on pydantic, and aiogram types are no longer
pydantic (D4), so lazy text in keyboards and captions needs core support either way (06 §3).

This plan builds the **pure-Python** half:
- the engine protocol and the gettext engine;
- `I18nContext`;
- the locale managers;
- the middleware;
- the lazy value objects (`L`, `LazyProxy`) as plain Python values.

Rendering lazy values inside frozen types and at encode time is G-06 (gate-conditional). This split keeps G-03, G-05
and G-07 independent of the B gate.

## Scope

**In:**
- **Module path.** 06 §3 doesn't name one. Proposed: `aiogram.i18n` (it matches the `aiogram.i18n` logger in 15).
  3.x `aiogram.utils.i18n` stays as the compatibility surface (G-05).
- **Engines**: `BaseCore` (abstract: `get(key, locale, **kw) -> str`, `available_locales`, `default_locale`,
  `startup()` / `shutdown()` hooks) and the built-in `GettextCore` (`.mo`/`.po` directory layout as 3.x
  `aiogram/utils/i18n/core.py` `I18n.find_locales`, plural forms, `reload()`). The Fluent engines are G-04.
- **Locale managers**: `BaseManager` (`get_locale(data) -> str`, optional `set_locale`).
  - `UserLocaleManager` is the default. It reads `event_context.user.language_code` and does no I/O. 3.x read
    `event_from_user`, which D12 removes.
  - `FSMManager(fallback=…)` stores the locale in FSM data.
  - `ConstManager(locale)`.
- **`I18nContext`**, injected into `data` as `i18n`: `i18n.get("key", **kw)`, `i18n.key(**kw)` (attribute access →
  key), `i18n.locale`, and `with i18n.use_locale("uk"):`. Add the `i18n` key to the inner `AiogramData` TypedDict
  (E-20).
- **Context**: one module-level `ContextVar` holding the active `(core, locale)`. It is set by the middleware and
  reset after the handler. Outside handlers, `use_locale(...)` or the engine default applies.
- **Middleware**: `I18nMiddleware(core=…, manager=…)` with `setup(dp)`, which registers it as an **outer middleware on
  `dp.update`**. With D111, a middleware on a sub-router is skipped for updates that don't match a candidate in that
  subtree. When the manager is `FSMManager`, it registers with an `after=FSMContextMiddleware` anchor (D39, E-06).
- **Lazy values**: `L.key(**kw)` and `LazyProxy("key", **kw)` are immutable objects that implement a small
  **render protocol**, owned by this plan: `__aiogram_render__(ctx: RenderContext) -> tuple[str, tuple[MessageEntity, ...] | None]` (plain lazy strings return `(text, None)`; a lazy `Text`, G-09,
  returns its entities). `str(obj)` renders with the current `ContextVar` (3.x `lazy_gettext` behaviour) and returns
  only the text. D-10's encoder render hook calls the protocol; G-06 and G-09 consume it. The protocol type itself is
  `LazyText` in `aiogram/_lazy.py`, the engine-free module from C-14 (create if absent): `L` / `LazyProxy` implement
  it, and `aiogram.i18n` re-exports `LazyText`. Define it in a private module that
  D-10 can import without importing engines.
- **Behaviour definitions (R21)**:
  - missing key → return the key and log one warning per (locale, key) on `aiogram.i18n`;
  - formatting errors → raise `I18nFormatError` with the key and locale;
  - unknown locale → fall back to the engine default.
- **Multiple Runners (R21)**: one middleware instance carries one core, so different dispatchers may use different
  cores. `core.startup()` / `shutdown()` are hooked to `dp.startup` / `dp.shutdown` once per Dispatcher, not per
  Runner.
- **Locale enumeration**: `core.available_locales` is public. G-12 uses it for localised command descriptions.
- Extra `i18n` stays `Babel` (D69). `GettextCore` itself needs only stdlib `gettext`; Babel is needed for `pybabel`
  tooling and plural/locale helpers.
- Remove the `ContextInstanceMixin` dependency (3.x `aiogram/utils/i18n/core.py` subclasses it). The mixin module's
  removal is G-10.

**Out:**
- Fluent engines: G-04.
- The 3.x-named wrappers (`I18n`, `gettext`, `_`, `lazy_gettext`, `__`, `SimpleI18nMiddleware`, …): G-05.
- Lazy values inside frozen types, encode-time render, D117 capture: G-06.
- `LazyFilter`: G-07.
- Key extraction tooling stays external (FTL-Extract, 06 §3). This plan only documents which call shapes it must
  recognise: `i18n.get`, `i18n.key()`, `L.key()`, `LazyFilter`.

## Checklist

- [ ] Confirm the module path `aiogram.i18n` (proposed). If the owner picks another, record it in Notes; G-04 to G-07
      and G-20 follow it.
- [ ] `BaseCore`, `GettextCore` (port of 3.x `I18n.find_locales` / `gettext` incl. plurals).
- [ ] `BaseManager`, `UserLocaleManager`, `FSMManager`, `ConstManager`.
- [ ] `I18nContext` + `I18nMiddleware.setup(dp)` with the D39 anchor for `FSMManager`.
- [ ] `ContextVar` and `use_locale` context manager. It is safe under free-threading because `ContextVar` is
      per-context (07).
- [ ] `L` / `LazyProxy` implement `LazyText` from `aiogram/_lazy.py` (the module from C-14; create if absent) and
      `aiogram.i18n` re-exports it.
- [ ] Lazy value classes + render protocol `__aiogram_render__(ctx: RenderContext) -> tuple[str, tuple[MessageEntity, ...] | None]` (private `aiogram.i18n._render` or equivalent, no engine import).
- [ ] Missing-key, format-error and unknown-locale behaviour, with the `aiogram.i18n` logger (H-01 hierarchy).
- [ ] **Decide whether `i18n.key(**kw)` attribute access maps `_` to `-`** for Fluent ids (proposed default: yes,
      `i18n.hello_user()` → `hello-user`, as `aiogram_i18n` does; gettext keys are used verbatim via `get`). Record in
      Notes and flag to owner.
- [ ] Docs: the i18n concept page (engines, managers, middleware placement under D111, lazy values) and the tutorial
      step (18). Free-threading note: gettext catalogs are read-only after load.
- [ ] Tests (100% coverage of new code): each manager; the middleware on `dp.update`; `FSMManager` ordering via the
      anchor; `use_locale` nesting; missing key; plurals; two dispatchers with two cores in one process; `str(L.key())`
      inside and outside a handler.
- [ ] Changelog fragment (`feature`). Migration-registry entry (PD-13) for `event_from_user` → `event_context.user` in
      custom 3.x i18n middlewares (kind `removal-4.0`, linked to the D12 entry if A-11 already seeded it).

## Acceptance criteria

- A bot with `I18nMiddleware(core=GettextCore(path), manager=UserLocaleManager())` answers in the user's
  `language_code` and falls back to the default locale for an unknown one, in a MockedBot test.
- `L.greeting(name="A")` stored in a plain Python variable renders differently inside two concurrent updates with
  locales `en` and `uk`.
- `import aiogram.i18n` does not import `babel` or `fluent` (checked with `-X importtime` or a `sys.modules` assertion).
- With the middleware set up on `dp.update`, `i18n` is available to handlers in every router, including routers
  whose outer chain D111 skips.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Keep i18n external (`aiogram_i18n`) | Its `LazyProxy` needs pydantic; lazy text in frozen types needs core support anyway | D25, 06 §3 |
| Rename 3.x classes as aiogram_rust did | Rename churn for users | D25, 13 §4 |
| Locale lookup with I/O in the default manager | The default must be free; `FSMManager` is opt-in | 06 §3 |
| Render lazy values only at `str()` time inside types | Frozen Rust types need the encoder to render (G-06) | D117 |

## Validation

```bash
make dev
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Consumes:
  - E-06 middleware anchors (`after=`);
  - E-20 typed DI TypedDicts, to add `i18n`;
  - H-01 logger names, if merged; otherwise use `logging.getLogger("aiogram.i18n")` directly.
- Outputs:
  - the render protocol for D-10 (encoder render hook), G-06 and G-09;
  - `available_locales` for G-12;
  - the public API names for G-20's mapping and for I-16 (codemod import rewrites).
- G-04, G-05 and G-07 can run in parallel once this merges.

## Notes

- Coordinator default (reconciliation, K5): this plan owns the render protocol and its return type
  `tuple[str, tuple[MessageEntity, ...] | None]`; D-10 owns the encoder render hook; G-06 integrates storage + capture.
