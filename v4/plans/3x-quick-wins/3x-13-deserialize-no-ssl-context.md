# 3x-13 — `deserialize_telegram_object`: no SSL context per call

| Field | Value |
|---|---|
| Status | `todo` |
| Story | 3x — 3.x quick wins & migration baseline |
| Target branch | `dev-3.x` |
| Depends on | [A-05](../A-contracts/A-05-bench-harness.md) |
| Blocks | — |
| Gate-conditional | no |
| Decisions | R27 (verify defaults, session ownership, cross-loop use; prefer removing the fake Bot) |
| Sources | [09 #14](../../research/09-3x-quick-wins.md), [11 §4](../../research/11-removals.md), [codex-review R27](../../research/codex-review.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

`deserialize_telegram_object` (`aiogram/utils/serialization.py`) calls `_get_fake_bot()` on every call, which
creates a new `Bot(token="42:Fake", default=…)`. Each `Bot` builds an `AiohttpSession`, which creates an SSL context.
The call costs 4.5 ms, against ≈50 µs without the context. The fake bot exists only so
`session.prepare_value(…, bot=fake_bot)` can resolve `Default(...)` values from `fake_bot.default`.

## Scope

**In:**
- Remove the per-call SSL context.
- The result must stay identical for every `default`: `prepare_value` resolves `Default` from the `default` passed
  in, or from a fresh `DefaultBotProperties()` when it is `None`.
- No session is ever opened, so there are no loop or resource concerns, and nothing is shared that holds per-loop
  state.

**Out:** the 4.0 reimplementation over the Rust encoder (D-14 / G-10).

## Checklist

- [ ] Baseline with A-05 on `utils.deserialize` (a small `SendMessage` with defaults).
- [ ] Decide the mechanism. Proposed default: build the fake `Bot` per call with
      `session=_shared_fake_session()`, where `_shared_fake_session()` is a module-level lazily created session that
      is never opened. `Bot` construction then stays cheap and `default` stays per call. The alternative R27 prefers
      is a shim with only `.default` and a `BaseSession.prepare_value` call without any `Bot`. Choose the smaller
      diff that passes the tests and record the choice in Notes.
- [ ] Verify that `prepare_value` doesn't touch anything on the bot besides `default` (grep in
      `aiogram/client/session/base.py`).
- [ ] Tests:
  - output equal to the parent commit for `default=None`, custom `parse_mode`, `link_preview`, and `protect_content`;
  - files are collected;
  - calling from two different event loops in two threads works;
  - no `ClientSession` is ever created.
- [ ] 100% coverage.
- [ ] Changelog fragment `CHANGES/<pr>.bugfix.rst`.
- [ ] Migration registry: no entry.

## Acceptance criteria

- A-05 `compare` on `utils.deserialize`: median ≥ 20× faster than the parent commit.
- Byte-identical `DeserializedTelegramObject.data` for the A-09 request cases.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Process-global cached fake `Bot` keyed by `default` | `DefaultBotProperties` isn't hashable; caching bots makes their ownership and lifetime unclear | R27 |

## Validation

```bash
uv run pytest tests --cov=aiogram --cov-report=term-missing
make lint
uv run python -m benchmarks compare --base HEAD~1 --head HEAD --cases utils.deserialize
```

## Workflow notes

Independent.

## Notes
