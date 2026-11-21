# G-04 — Fluent engines

| Field | Value |
|---|---|
| Status | `todo` |
| Story | G — User-facing additions |
| Target branch | `dev-4.x` |
| Depends on | [G-03](G-03-i18n-core.md) |
| Blocks | [G-20](G-20-aiogram-i18n-final-release.md) |
| Gate-conditional | no |
| Decisions | D25, D69, D70 |
| Sources | [06-utils.md §3](../../research/06-utils.md), [08-build-release.md §8](../../research/08-build-release.md), [07-free-threading.md §4](../../research/07-free-threading.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Most `aiogram_i18n` users run Fluent. D25 ships two Fluent engines behind extras, so moving off `aiogram_i18n`
(README breaking change 14) needs no third-party package.

## Scope

**In:**
- `FluentRuntimeCore` (on `fluent.runtime` + `fluent.syntax`), behind the extra `aiogram[fluent-runtime]`.
- `FluentCompilerCore` (on `fluent-compiler`), behind the extra `aiogram[fluent-compiler]`.
- Both implement G-03's `BaseCore`:
  - `get(key, locale, **kw)`;
  - `available_locales`;
  - `default_locale`;
  - `startup()` / `shutdown()`;
  - `reload()`.
- Directory layout: `<path>/<locale>/**/*.ftl`, the same as `aiogram_i18n`, so that existing projects work
  unchanged. Record the exact layout and any difference in Notes.
- Fallback chain: requested locale → default locale → key, with one warning per (locale, key), as G-03 defines.
- Fluent errors (missing variables, bad references) map to G-03's `I18nFormatError` / missing-key behaviour.
- Importing either engine without its extra raises `ImportError` with an install hint (`pip install
  'aiogram[fluent-runtime]'`).
- Extras added to `pyproject.toml` with **lower bounds only** (D70).
- Free-threading: add `fluent.runtime`, `fluent.syntax` and `fluent-compiler` to the 07 §4 watch list in docs (not
  research). Engine objects are read-only after load; a `reload()` swaps an immutable bundle map atomically.

**Out:**
- Key extraction (FTL-Extract stays external).
- The `aiogram_i18n` mapping page and the final release: G-20.

## Checklist

- [ ] `FluentRuntimeCore` with bundle per locale, built once at `startup()` (or lazily on first use, Notes).
- [ ] `FluentCompilerCore` with compiled bundle per locale.
- [ ] Extras `fluent-runtime`, `fluent-compiler` in `pyproject.toml`. Coordinate with I-07, which owns the full
      extras restructure. If I-07 already merged, add to its layout; otherwise add them and note it there.
- [ ] Import guard with an install hint.
- [ ] Parity test: the same `.ftl` corpus renders identically with both engines (select expressions, plurals,
      `NUMBER`, terms, attributes).
- [ ] Docs: engine choice (runtime = simplest; compiler = faster render, slower load), directory layout, extras.
- [ ] Tests (100% coverage of new code), skipped cleanly when an extra is not installed; CI installs both.
- [ ] Changelog fragment (`feature`).

## Acceptance criteria

- The shared `.ftl` test corpus renders byte-identical output with `FluentRuntimeCore` and `FluentCompilerCore` for
  every key × locale.
- `import aiogram.i18n` with neither extra installed succeeds. Instantiating a Fluent core then raises `ImportError`
  naming the extra.
- An `aiogram_i18n` example project's `locales/` directory loads unchanged (fixture copied into tests).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| One `fluent` extra pulling both libraries | Users pick one engine; the compiler pulls extra deps | D69 |
| Upper version caps on fluent libraries | Lower bounds only, CI on newest and lowest | D70 |
| Built-in key extraction | Stays external (FTL-Extract) | 06 §3 |

## Validation

```bash
make dev
uv sync --extra fluent-runtime --extra fluent-compiler
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Consumes G-03's `BaseCore` and error behaviour.
- Output: engine names for G-20's mapping page. The extras feed I-07 and I-21 (fresh-machine install rehearsal).
- Can run in parallel with G-05 and G-07.

## Notes
