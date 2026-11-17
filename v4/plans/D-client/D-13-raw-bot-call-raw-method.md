# D-13 — Raw `bot.call(...)` and internal `RawMethod`

| Field | Value |
|---|---|
| Status | `todo` |
| Story | D — Client & wire |
| Target branch | `dev-4.x` |
| Depends on | [B-01](../B-spike/B-01-crate-maturin-skeleton.md), [B-13](../B-spike/B-13-gate-run-and-decision.md), [D-07](D-07-rust-encoder-json.md), [D-08](D-08-rust-encoder-multipart.md), [D-09](D-09-response-decoder.md), [D-11](D-11-session-on-new-codec.md), [C-20](../C-butcher/C-20-rust-methods-shortcuts-emitter.md) |
| Blocks | [D-15](D-15-request-response-differential-cases.md), [G-13](../G-features/G-13-retry-middleware.md), [H-11](../H-testing-observability/H-11-generated-toolkit-tables.md) |
| Gate-conditional | yes (assumes the milestone B gate passes, D104; re-validate after B-13) |
| Decisions | D96, D97, D98, D87, PD-25 |
| Sources | [01-models.md §3.3](../../research/01-models.md), [05-network.md §2.1](../../research/05-network.md), [14-testing.md §1](../../research/14-testing.md), [README breaking change 20](../../research/README.md), [plans README §1 PD-25](../README.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

3.x users call unreleased Bot API methods by subclassing `TelegramMethod` (`aiogram/methods/base.py`). In 4.0
generated method classes are Rust pyclasses and not subclassable (D96); the replacement is a raw call:

```python
await bot.call("sendGift2", {"chat_id": 1, "photo": FSInputFile("a.jpg")}, returns=Message, request_timeout=None)
```

Internally the call builds a `RawMethod(name, params, returns)` so request middlewares (Retry, RateLimit, logging,
OTel) and the testing toolkit (`env.on("sendGift2")`) see it like any method.

## Scope

**In:**
- `Bot.call(name: str, params: Mapping[str, Any] | None = None, *, returns=None, request_timeout: int | None = None)`
  — hand-written, stable signature (not generated, so D100/PD-23 don't apply).
- `RawMethod`: frozen, `isinstance(raw, TelegramMethod)` is true, `__api_method__ == name`, attributes `name`,
  `params` (read-only mapping), `returns`; `chat_id` readable from `params` for G-14.
- Generic encoder path (Rust, sharing D-07/D-08 code): params walked once; `InputFile` anywhere (nested included)
  extracted to `attach://`; values may be aiogram types, builtins, plain wire-shape dicts, or any object with
  `to_dict()`; other objects → `TypeError` (D87 JSON-shaped rule).
- `returns` resolution (D98): omitted → decoded JSON as builtins; an aiogram type → Rust decoder (bound to the bot);
  builtin/container (`bool`, `int`, `str`, `list[T]`, `dict`) → checked conversion; a class with
  `from_dict(data, *, bot=None)` → called; any other callable `(raw) -> T` → called.
- Retry policy for raw calls: only 429 is retried (PD-25) — expose `RawMethod` as non-idempotent so G-13 needs no
  special case.
- `TelegramMethod` stays importable for typing / `isinstance`.

**Out:**
- Making generated classes non-subclassable → B/C (C-20). Migration checker rule for `TelegramMethod` subclasses →
  I-16/I-19 (this plan only adds the registry entry).
- Fake-server handling of raw names → H-11.

## Checklist

- [ ] `Bot.call` + `RawMethod`.
- [ ] Generic encoder path with nested file extraction.
- [ ] `returns` resolution for all D98 forms.
- [ ] Decide what `aiogram.Raw` is (proposed default: a public type alias
      `Raw: TypeAlias = None | bool | int | float | str | list["Raw"] | dict[str, "Raw"]` exported from `aiogram`, used
      as the return annotation of `bot.call` without `returns`) — record in Notes and flag to owner.
- [ ] `RawMethod` marked non-idempotent (PD-25).
- [ ] Typing: `@overload`s so `await bot.call("x", {}, returns=Message)` is typed `Message`, without `returns` →
      `Raw`; `assert_type` tests.
- [ ] Docs: "Unreleased API methods" page with the D96 example.
- [ ] Tests (100% coverage of new code), incl. a request middleware observing `RawMethod`.
- [ ] Migration-registry entry (PD-13, `removal-4.0`): user `TelegramMethod` subclasses unsupported → `bot.call`
      (README breaking change 20).
- [ ] Changelog fragments (`feature`, `removal`).

## Acceptance criteria

- `bot.call("sendMessage", {"chat_id": 1, "text": "x"}, returns=Message)` sends the same wire body as
  `SendMessage(chat_id=1, text="x")` (diffed in D-15) and returns a bound `Message`.
- Nested `InputFile` in params produces multipart with `attach://` references.
- A param holding `object()` raises `TypeError` before any network I/O.
- A registered request middleware receives a `RawMethod` with `name == "sendMessage"`.
- With a Retry stand-in following `idempotent`, a raw call is not retried on a network error and is retried on 429.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Keep user `TelegramMethod` subclasses | Generated classes are Rust pyclasses; raw call covers the need | D96 |
| Raw calls bypass middlewares | Middlewares and the toolkit must see them | D96 |
| Retry raw calls on network errors by default | Idempotency unknown | PD-25 |

## Validation

```bash
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
make dev
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Inputs: D-07/D-08/D-09 codec, D-11 session path.
- Outputs: `RawMethod` contract for G-13/G-14 (policy, `chat_id`), H-11 (fake interception by name), D-15 cases.

## Notes
