# 3x-22 — Registration- and class-creation-time warnings

| Field | Value |
|---|---|
| Status | `todo` |
| Story | 3x — 3.x quick wins & migration baseline |
| Target branch | `dev-3.x` |
| Depends on | [3x-20](3x-20-deprecation-machinery.md), [3x-21](3x-21-import-attribute-warnings.md) (shares `dispatcher/event/handler.py`; land after), [A-11](../A-contracts/A-11-migration-registry.md) |
| Blocks | [3x-24](3x-24-migration-baseline-release.md) |
| Gate-conditional | no |
| Decisions | D12, D14, D42, D96, D72, D74, R28, PD-13 |
| Sources | [16 §1–2](../../research/16-support-policy.md), [11 §3–4](../../research/11-removals.md), [README breaking changes 11, 12, 20](../../research/README.md), [01 §3.3](../../research/01-models.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Some 4.0 removals show up in how user code is *declared*: handler signatures, subclasses, `CallbackData` fields.
16 §1 says to warn **at registration** (`CallableObject` already inspects signatures) or at class creation. That
costs nothing per update.

## Scope

**In:**

| # | Pattern | Site | 4.0 change |
|---|---|---|---|
| 1 | A handler or filter callable that declares a parameter named `event_from_user`, `event_chat` or `event_thread_id` | `CallableObject.__post_init__` (`aiogram/dispatcher/event/handler.py`), once per callable. A `**kwargs` catch-all can't be detected, so it is left to the checker | D12: use `event_context.user` / `.chat` / `.thread_id` |
| 2 | Registering a class-based handler (`issubclass(callback, BaseHandler)` branch in `handler.py`), plus subclassing `BaseHandler` outside aiogram (`BaseHandler.__init_subclass__`) | registration + class creation | D42: write an `async def` handler |
| 3 | Subclassing `TelegramMethod` outside the `aiogram.` package (unreleased or custom methods) | `TelegramMethod.__pydantic_init_subclass__` (or `__init_subclass__`), checking `cls.__module__` | D96: `await bot.call("method", {...}, returns=Type)` |
| 4 | `CallbackData` subclasses using pydantic-only features: `Field(...)` with constraints / alias / `default_factory`, `field_validator` / `model_validator`, `model_config` overrides | `CallbackData` class creation. This is a heuristic: inspect `model_fields[*]` metadata and `__pydantic_decorators__` | D14: `CallbackData` becomes a dataclass-style class; replace validators with `__post_init__` |

Internal code also moves off the deprecated pattern: `aiogram/utils/i18n/middleware.py` reads `event_from_user`
from `data` → switch it to `event_context.user` (11 §3). Data-dict reads emit no warning, but the 4.0 path must be
exercised.

**Out:**
- Middlewares reading `data["event_from_user"]`: can't be detected at runtime. It is a heuristic checker rule
  (I-19).
- `model_*` method calls on `CallbackData`: checker (I-17).

## Checklist

- [ ] Row 1: warn once per callable at registration. Tests:
  - a handler with `event_from_user: User` warns at `router.message.register(...)`;
  - a handler with `**kwargs` doesn't warn;
  - a filter callable with `event_chat` warns.
- [ ] Row 2: registration and subclass warnings. aiogram's own `aiogram/handlers/*` classes are exempt
      (`cls.__module__.startswith("aiogram.")`).
- [ ] Row 3: warn for non-aiogram subclasses only. Every generated method under `aiogram.methods` stays silent (a
      test iterates `aiogram.methods.__all__` under the 3x-20 guard).
- [ ] Row 4: decide the exact heuristic. Proposed default: warn when any field has non-default `FieldInfo` metadata
      (constraints, `alias`, `validation_alias`, `default_factory`, `discriminator`), or when the class defines
      validators or overrides `model_config`. A plain `x: int = 0` doesn't warn. Record the final rule in Notes;
      false positives become `heuristic` in the registry entry.
- [ ] Switch `utils/i18n/middleware.py` to `event_context`.
- [ ] Add each trigger to 3x-20's sync-test table.
- [ ] Each row's entry exists in `registry.toml`, with the correct `warn_3x.site` (`registration` /
      `class-creation`) and `detection` (`definite` for rows 1–3, `heuristic` for row 4).
- [ ] 100% coverage. The full suite passes with the 3x-20 guard on, after wrapping existing tests of
      `tests/test_handler/`, `BaseHandler` cases and event_* cases in `pytest.warns`.
- [ ] Changelog fragment `CHANGES/<pr>.removal.rst`.

## Acceptance criteria

- Each row warns exactly once per declaration, with its registry id, pointing at the user's registration call or
  `class` statement.
- No warning is emitted for aiogram's own classes, or for any example in `examples/` that already follows the 4.0
  pattern. Run `examples/` imports under `-W error::DeprecationWarning`; examples that use deprecated APIs are listed
  in Notes for I-20.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Warn per update when `event_from_user` is injected | A runtime cost on every update | 16 §1 |
| Warn on every `CallbackData` subclass | Most declarations keep working unchanged in 4.0 | D14 ("same declaration syntax") |

## Validation

```bash
uv run pytest tests --cov=aiogram --cov-report=term-missing
make lint
```

## Workflow notes

- E-01 (removals) and F-11 (`CallbackData` without pydantic) implement the 4.0 side.
- D-13 implements `bot.call`.
- The checker rules for the undetectable cases are I-19 / I-17.

## Notes
