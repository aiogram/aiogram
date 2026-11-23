# E-20 — Typed DI: base `TypedDict`s for handler and middleware data

| Field | Value |
|---|---|
| Status | `done` |
| Story | E — Routing & runtime |
| Target branch | `dev-4.x` |
| Depends on | [E-01](E-01-dispatcher-filter-removals.md) |
| Blocks | [E-21](E-21-e-exit-gate.md), [G-03](../G-features/G-03-i18n-core.md) |
| Gate-conditional | no |
| Decisions | D31, D41, 19 §3 confirmation 2, D12 |
| Sources | [03-routing.md §5 "Dependency injection (D31)"](../../research/03-routing.md), [19 §2 "§8" row, §3](../../research/19-review-resolutions.md), [codex-review §8](../../research/codex-review.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

D31 keeps kwargs DI and documents typed access through PEP 692 (`**kw: Unpack[AppData]`). 3.x already ships
`aiogram/dispatcher/middlewares/data.py` (`DispatcherData`, `UserContextData`, `FSMData`, `I18nData`,
`MiddlewareData`), but with `total=False` everywhere — which makes nothing reliably required — and with the removed
`event_from_user` / `event_chat` / `event_thread_id` keys. 19 §3 confirms: `state`, `raw_state`, `event_router` and
`handler` belong to the **inner** `TypedDict`; outer-middleware data types omit them.

## Scope

**In:**
- Rewrite `aiogram/dispatcher/middlewares/data.py`:
  - outer base (for `dp.update` outer middlewares): `bot`, `bots`, `dispatcher`, `event_update`, `event_context`,
    `fsm_storage` (+ workflow keys added by users);
  - `AiogramData` (inner middlewares, filters, handlers) extending it with `state`, `raw_state`, `event_router`,
    `handler`, and the `i18n` key (`NotRequired`, the G-03 `I18nContext`; set only when the i18n middleware is
    installed);
  - rename the 3.x `FSMData` TypedDict to `FSMKeysData` (no alias; migration-registry entry), because F-09
    introduces the user-facing `aiogram.fsm.data.FSMData` class;
  - keys only some paths set as `NotRequired[...]`; required keys plain (no `total=False` on the bases).
- Remove the `event_*` keys (E-01) and the 3.x "polling only" note on `bots`. The never-set
  `event_business_connection_id` key is not carried over (E-01 removes its docs).
- Keep `MiddlewareData` as a deprecated alias of `AiogramData` for one D71 window.
- Docs example from 03 §5 (`class AppData(AiogramData): db: Database`) and with `BaseMiddleware[Message, AppData]`
  (E-06).

**Out:**
- Runtime changes (docs/typing only); typed `ctx: Context` (rejected, D31).

## Checklist

- [ ] New TypedDicts with correct required / `NotRequired` keys, including `i18n` on `AiogramData` (G-03 consumes it).
- [ ] Decide the shape for **router-level** outer middlewares (`router.message.outer_middleware`), which see
  `event_router`, `state`, `raw_state` but not `handler` — the two-dict split doesn't model them (proposed default: a
  third `RouterOuterData(OuterData)` with `event_router`, `state`, `raw_state` as `NotRequired`, and `AiogramData`
  extends it with `handler`) — record in Notes and flag to owner.
- [ ] Decide the `bots` type (3.x `list[Bot]`; the Runner registry exposes a cached tuple, E-23) (proposed default:
  `tuple[Bot, ...]`, with a migration-registry entry for code that mutates it) — record in Notes and flag to owner.
- [ ] Name clash resolved: rename the 3.x `middlewares/data.py` `FSMData` TypedDict to `FSMKeysData` (no alias,
  registry entry, PD-13), since D30 / F-09 introduce the user-facing `FSMData` class; F-09 states the same rename.
- [ ] Typing tests in `tests/typing/` (directory from B-01; create if absent), run by mypy (`assert_type`, `reveal_type` checks) for a handler with `**kw: Unpack[AppData]` and a
  generic middleware.
- [ ] `MiddlewareData` deprecated alias (registry entry kind `deprecation-4.x`, PD-13).
- [ ] Changelog fragment.

## Acceptance criteria

- mypy (strict, as the repo config) accepts `kw["bot"]` without narrowing and rejects `kw["handler"]` on the outer
  type.
- `aiogram.dispatcher.middlewares.data` exports `FSMKeysData` and no `FSMData`; `AiogramData` has an `i18n` key.
- No runtime behaviour change (full suite green; no import cost increase measurable on `python -X importtime`).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Typed `ctx: Context` parameter | A second DI style for an additive gain | D31 |
| `total=False` subclass to make inherited keys optional | Doesn't make inherited required keys optional | codex §8, 19 §2 |

## Validation

```bash
make dev
uv run pytest tests -q
make lint
uv run mypy aiogram tests/typing
```

## Workflow notes

- G-02 / G-01 docs reuse `AiogramData` in `Depends` examples; F-09 may add an `FSMData`-typed example. The 3.x
  `FSMData` TypedDict is renamed `FSMKeysData` here (agreed with F-09, which introduces the user-facing `FSMData`
  class); G-03 relies on the `i18n` key.

## Notes
