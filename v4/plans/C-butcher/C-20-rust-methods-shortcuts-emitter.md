# C-20 — Rust methods, encoder tables, shortcuts, `send_copy`, method metadata

| Field | Value |
|---|---|
| Status | `todo` |
| Story | C — Reproducible butcher |
| Target branch | `dev-4.x` |
| Depends on | [C-07](C-07-fill-dsl.md), [C-10](C-10-ledger-diff.md), [C-11](C-11-import-legacy.md), [C-18](C-18-rust-type-emitter.md), [B-09](../B-spike/B-09-sendmessage-encoder-response.md), [B-13](../B-spike/B-13-gate-run-and-decision.md), [I-12](../I-distribution/I-12-deprecation-machinery-registry-ci.md) |
| Blocks | [C-21](C-21-generated-tests-emitter.md), [C-25](C-25-historical-scenario-tests.md), [D-07](../D-client/D-07-rust-encoder-json.md), [D-08](../D-client/D-08-rust-encoder-multipart.md), [D-13](../D-client/D-13-raw-bot-call-raw-method.md), [G-06](../G-features/G-06-lazy-text-capture.md), [G-13](../G-features/G-13-retry-middleware.md), [D-09](../D-client/D-09-response-decoder.md), [I-06](../I-distribution/I-06-largest-codegen-unit-guard.md) |
| Gate-conditional | yes |
| Decisions | D11, D96–D100, D72, R18, R19, PD-02, PD-23, PD-25, 19 §8 (text_signature) |
| Sources | [01-models.md §3.3, §3.4](../../research/01-models.md), [02-butcher.md §4, §5, §5.1](../../research/02-butcher.md), [05-network.md §2, §2.5](../../research/05-network.md), [06-utils.md §3](../../research/06-utils.md), [11-removals.md §1](../../research/11-removals.md), [19 §2 R18, R19, §8](../../research/19-review-resolutions.md), [plans README PD-25](../README.md) |
| Size | L (4–5 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Methods are generated as `#[pyclass(frozen)]` with a validating keyword-only `#[new]`, and the Rust encoder (D-07/D-08)
needs generated per-method tables. Shortcuts are generated in Rust from the fill-DSL (D11). `send_copy` comes from the
overlay content map, not from the removed `ContentType` (11 §1). Retry safety needs explicit `idempotent` metadata, not
a `get*` prefix (R19, PD-25).

## Scope

**In:** `crates/butcher/src/emit/rust_methods.rs` → `crates/aiogram-core/src/generated/methods/**` and the shortcut
`#[pymethods]` blocks:
- **Method pyclasses** (`module = "aiogram.methods"`): `#[new]` validates kwargs (types, unions, `Default` sentinels).
  `text_signature` is keyword-only with `...` for nonliteral defaults (19 §8). Unknown kwargs are forwarded with a
  one-time `AiogramUnknownParameterWarning` (class defined by I-12) per (method, name) and must be JSON-shaped (D99, D87). Methods are not
  subclassable (D96).
- **Encoder tables** for D-07/D-08: per-method field order, wire names, `Default` fields, `InputFile`-capable fields
  and multipart `encoding` (C-04), and lazy display fields (`display.toml`, rendered through D-10's encoder render hook; G-06 integrates the lazy values).
- **Return-type table** for `decode_response` (05 §2; D-09).
- **`idempotent` table** (R19, PD-25) from `methods.toml`: every method carries an explicit value, and `getUpdates` is
  marked excluded (the Poller owns it). Raw `bot.call` is non-idempotent (PD-25: retries only 429).
- **Shortcuts** from the C-07 resolved table:
  - synchronous `#[pymethods]`: build the method, then return `bot(method)` (the coroutine), never awaiting inside;
  - keyword-only, with `require`/`forbid` guards;
  - `handwritten` shortcuts are skipped and left to `*_ext.rs`.
- **`send_copy`** from `content.toml`: content kind → method + field map. The legacy reply params
  (`reply_to_message_id`, `allow_sending_without_reply`) and the `disable_web_page_preview=Default(...)` on
  `answer`/`reply` are gone (11 §1). A content kind without a mapping fails `check` (C-23).
- **Ledger deprecations:** setting or reading a kept-deprecated field or param emits `AiogramApiDeprecationWarning` once (D72).

**Out:** the encoder runtime (D-07/D-08), raw `bot.call` (D-13), `RetryMiddleware` (G-13), the lazy-text encoder render hook (D-10; protocol G-03), generated tests (C-21).

## Checklist

- [ ] Method pyclass emitter with `#[new]` validation and `text_signature`.
- [ ] Encoder, return-type and `idempotent` tables (interface agreed with D-07/D-09; if D-07 landed first, follow its table trait).
- [ ] Shortcut emitter with guards.
- [ ] `send_copy` emitter from `content.toml`.
- [ ] Ledger deprecation warnings (fixture ledger entry).
- [ ] Golden diff against B-09's hand-written `SendMessage` (PD-30).
- [ ] Parity test: for every one of the 189 shortcuts, the method built by `message.<shortcut>(…)` equals the 3.x shortcut's method fields, run on A-09 request oracle cases with manifested differences (keyword-only, removed legacy params).
- [ ] Migration-registry entry (PD-13): D100 keyword-only shortcuts and `bot.*` (breaking change 21), D96 custom `TelegramMethod` subclasses (20), `send_copy` legacy params removal; verify the A-11 seed. Changelog fragment.
- [ ] Tests (100% coverage of new code)

## Acceptance criteria

- `inspect.signature(SendMessage)` and `inspect.signature(Message.answer)` succeed and are keyword-only.
- `message.answer("hi")` raises `TypeError`, and `message.answer(text="hi")` returns a coroutine without awaiting (test with a fake bot).
- `SendMessage(chat_id=1, text="x", new_param=1)` warns once with `AiogramUnknownParameterWarning`, and a non-JSON value raises `TypeError`.
- Every IR method has an explicit `idempotent` entry. Removing one makes `check` fail (C-23 rule, unit-tested here).
- The B-09 `SendMessage` golden diff has 0 semantic differences, and the B-02 encode bench (pinned input) is within 5% of B-09.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| User `TelegramMethod` subclasses | Raw `bot.call` only | D96 |
| `get*` prefix as retry rule | Not a safety property | R19, PD-25 |
| Python facade for shortcuts | One class per type | D11 |
| `send_copy` via public `ContentType` | Removed | 11 §1 |
| Positional shortcuts / `keep_position` | Keyword-only | D100, PD-02 |

## Validation

```bash
cargo clippy --all-targets -- -D warnings
cargo test -p aiogram-core methods
cargo xtask butcher emit && maturin develop --release
uv run pytest tests
uv run mypy aiogram
cargo xtask butcher check
```

## Workflow notes

- D-07/D-08 consume the encoder tables, D-09 the return-type table, G-13 the `idempotent` table, G-06 the display-field marks.
- C-27 ports the shortcuts marked `handwritten` (expected 0, C-07) and the other helpers.

## Notes
