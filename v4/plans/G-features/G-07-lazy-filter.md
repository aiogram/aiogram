# G-07 — `LazyFilter`

| Field | Value |
|---|---|
| Status | `todo` |
| Story | G — User-facing additions |
| Target branch | `dev-4.x` |
| Depends on | [G-03](G-03-i18n-core.md) |
| Blocks | [G-20](G-20-aiogram-i18n-final-release.md) |
| Gate-conditional | no |
| Decisions | D25, D34, D37 |
| Sources | [06-utils.md §3](../../research/06-utils.md), [03-routing.md §3](../../research/03-routing.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Reply-keyboard buttons send their localised text back. `LazyFilter("menu-settings")` matches the message text
against that key rendered in the **current** locale, so one handler serves every language (06 §3). `aiogram_i18n`
users rely on it, and G-20 maps it one to one.

## Scope

**In:**
- `LazyFilter(key, **kwargs)` in `aiogram.i18n` (module path per G-03). It is a `Filter` subclass that compares
  `message.text` (or a configurable attribute; see the Decide item) with `i18n.get(key, **kwargs)` for the locale
  that G-03's middleware set.
- Runs inline (D34; sync, no I/O).
- **Not compiled into rejectors.** It is locale-dependent, so it is opaque to E-09's literal index. Document that it
  costs one render per candidate check.
- Without an active i18n context, it raises `I18nNotConfiguredError` with a hint to install the middleware on
  `dp.update`.

**Out:**
- Matching against all locales at once (not in D25).
- Compiled rejectors: E-09 (no change needed; confirm it treats unknown `Filter` subclasses as opaque).

## Checklist

- [ ] `LazyFilter` implementation, with `__repr__` for route diagnostics (H-15).
- [ ] **Decide whether `LazyFilter` also matches `callback_query.data` / `caption`** (proposed default: text only, as
      `aiogram_i18n`, plus an `attribute=` override). Lazy values are not equal to their rendering, so
      `F.caption == L.key()` does not work and the docs must say so.. Record in Notes and
      flag to owner.
- [ ] Docs section on the i18n page.
- [ ] Tests (100% coverage of new code): `en` / `uk` match and miss; no context; inside `and_f` / `~`.
- [ ] Changelog fragment (`feature`).

## Acceptance criteria

- The same handler registered with `LazyFilter("menu-settings")` matches "Settings" for an `en` user and
  "Налаштування" for a `uk` user, and does not match "Settings" for the `uk` user.
- An E-09 agreement test still passes: no rejector is generated for a candidate carrying a `LazyFilter`.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Matching any locale's translation | Ambiguous across locales; not in D25 | D25 |
| Compiling into the literal index | Value depends on the locale at match time | D37, E-09 |

## Validation

```bash
make dev
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Consumes G-03 (context, `i18n.get`).
- Output: the name and behaviour for G-20's mapping.
- Runs in parallel with G-04 and G-05.

## Notes
