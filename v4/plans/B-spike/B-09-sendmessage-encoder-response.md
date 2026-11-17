# B-09 — `SendMessage` + encoder + response path

| Field | Value |
|---|---|
| Status | `todo` |
| Story | B — Model spike |
| Target branch | `dev-4.x` |
| Depends on | [B-04](B-04-spike-type-set.md), [B-05](B-05-views-cache-gc-routing-keys.md), [B-06](B-06-value-semantics-native-api.md), [B-07](B-07-bound-views.md), [B-01](B-01-crate-maturin-skeleton.md), [B-14](B-14-unions-envelope-batch-decode.md) |
| Blocks | [B-11](B-11-cache-gc-teardown-ft-tests.md), [B-12](B-12-dispatch-harness.md), [B-13](B-13-gate-run-and-decision.md), [D-07](../D-client/D-07-rust-encoder-json.md), [D-08](../D-client/D-08-rust-encoder-multipart.md), [D-09](../D-client/D-09-response-decoder.md), [D-10](../D-client/D-10-request-snapshot-and-render-hook.md), [C-20](../C-butcher/C-20-rust-methods-shortcuts-emitter.md) |
| Gate-conditional | no |
| Decisions | D99, D100, D117 (hook only), PD-07, PD-08, PD-11, PD-20, PD-29, R18, B17, B22, B24 |
| Sources | [05-network.md §1, §2.1–§2.3](../../research/05-network.md), [01-models.md §3.3, §3.4](../../research/01-models.md), [06-utils.md §3 (risks)](../../research/06-utils.md), [13-aiogram-rust-review.md B17, B22, B24](../../research/13-aiogram-rust-review.md), [19 R18, §8](../../research/19-review-resolutions.md) |
| Size | L (4–5 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

The spike deliverables include request encoding, and the gate covers the bot's real response paths (B24: the
`sendMessage` response and the `getUpdates` batch). The 3.x outbound cost is 93 µs per `SendMessage` with a keyboard
and entities: `model_dump` + recursive `prepare_value` in `aiogram/client/session/base.py` and `build_form_data` in
`aiogram/client/session/aiohttp.py`. The JSON-body quick win (3x-09) brings it to ≈21 µs. The spike must show that a
Rust method struct + encoder fits the D11 / D100 model. It must also show that the encoder can call back into
Python (lazy text) without holding a Rust lock (06 §3).

## Scope

**In:**
- **Method class.** `SendMessage` as `#[pyclass(frozen)]` in `crates/aiogram-core/src/generated/methods/send_message.rs`
  (emitted shape, PD-30, golden for C-20).
  - Keyword-only `#[new]` (D100) with `text_signature` using `...` (19 §8).
  - Kwargs validated in Rust.
  - `Default("parse_mode")`-style Python-visible sentinels for defaulted parameters.
  - Parameters whose types are outside the spike set accept dicts / `to_dict()` objects through the generic value
    path (D97 rule).
  - Unknown kwargs allowed if JSON-shaped and forwarded, with a one-time warning per `(method, name)` (D99).
- **Encoder.** `_core.encode(method, defaults) -> JsonBody | Multipart`.
  - It walks the Rust struct, with no Python recursion.
  - `Default(...)` is resolved against a Rust snapshot of `DefaultBotProperties` (`aiogram/client/default.py`, made
    frozen by D-01 per PD-20), built once per bot.
  - No files → `JsonBody(bytes)`.
  - Any `InputFile` (recognised by `isinstance` against `aiogram.types.InputFile`, which stays plain Python) →
    `Multipart(fields, files)`, with `attach://` names and the files returned as `(name, InputFile)` pairs. The
    spike's multipart JSON-encoding map for `SendMessage` is hand-written.
- **Value writer rules.**
  - `datetime` → unix int; naive = local time.
  - Half-even rounding.
  - **`timedelta` → `now + delta` absolute unix time, computed at encode time (PD-11)**, matching 3.x
    `BaseSession.prepare_value`.
  - A `timeout <= 0` means no deadline (B17; applies to D-11, noted only).
  - `SendMessage` has no DateTime parameter, so the rule is tested through the shared value writer on a test-only
    method struct.
- **Lazy-text hook.** If a display-text field (`text`) holds an object implementing the render protocol (06 §3), the
  encoder calls it exactly once per encode with **no Rust lock held** and uses the returned text **and** entities
  together (D117). Context capture rules (PD-07) are D-10 / G-06; here only the call-out contract is proven.
- **Shortcut.** A hand-written `message.answer(*, text, …)` in `message_ext.rs`, standing in for the C-07 / C-20
  generated shortcut. It fills `chat_id` / `message_thread_id` the way 3.x `Message.answer` does and returns
  `bot(method)`, a coroutine, never awaited in Rust (01 §3.4). The spike `Bot` shim is a minimal Python class in
  `tests/test_core/` and the bench, whose `__call__` encodes and posts to the B-02 fake Bot API.
- **Response path.** `_core.decode_response(SendMessage, raw: bytes, bot) -> Message`, bound in the root view
  (D103), using the B-14 envelope. `{"ok": false}` → `(error_code, description, parameters)` for Python.
  - A decode failure where Layer 1 doesn't suffice raises a spike error carrying `.raw`. Mapping it to
    `ClientDecodeError` with `.raw` is D-02 / D-09 (PD-29).
- **Differential check.** For the A-09 `SendMessage` request cases, the Rust JSON body equals, as parsed JSON, the
  3x-09 JSON body from the optimised-3.x side.

**Out:**
- All other methods, `RawMethod` / `bot.call` (D-13).
- The real Bot / session integration (D-11).
- Request snapshots and i18n capture (D-10, G-06).
- Webhook replies (D-14). Retries (G-13).
- `json_dumps` / `json_loads` session hooks: PD-08 says they don't affect the wire, so the spike ignores them.

## Checklist

- [ ] `SendMessage` pyclass in emitted shape with kwargs validation, `Default` sentinels, D97 generic values and D99
  unknown-kwarg forwarding + one-time warning.
- [ ] `DefaultBotProperties` → Rust snapshot conversion (reads the 3.x class attributes; no change to
  `aiogram/client/default.py` here).
- [ ] `encode()` with `JsonBody` / `Multipart`, `attach://` extraction and the hand-written encoding map.
- [ ] Shared value writer with the PD-11 `timedelta` rule, naive-local datetimes and half-even rounding. Tests with a
  frozen clock (`now` injected) compare against 3.x `BaseSession.prepare_value` output.
- [ ] Lazy-text render call-out with no lock held. A test whose render hook re-enters `_core` (decodes an update,
  then encodes another method) must not deadlock, and must be called exactly once per encode.
- [ ] Hand-written `message.answer` in `message_ext.rs` and the spike Bot shim.
- [ ] `decode_response` for the `sendMessage` result and the error tuple.
- [ ] Register in B-02: encode with a 3×3 keyboard + 3 entities (the 05 §1 input, as pinned in A-04); `sendMessage`
  response decode (gated parse workload); shortcut up to the coroutine.
- [ ] Differential test against the A-09 `SendMessage` cases (parsed-JSON equality, approved differences listed per
  the R26 manifest rule).
- [ ] Tests in `tests/test_core/` (100% of new Python).
- [ ] No changelog or registry entry here (not wired, PD-03). Breaking change 21 (keyword-only) is registered by
  I-18; name it in Notes.

## Acceptance criteria

- `encode(SendMessage(chat_id=1, text="hi"), defaults)` returns a `JsonBody` whose parsed JSON equals the 3x-09 body
  for the same input. With an `InputFile` in a nested parameter it returns `Multipart` with an `attach://` reference.
- `SendMessage(1, "hi")` raises `TypeError` (keyword-only).
- The `timedelta(minutes=5)` test value encodes to `round(now + 300)` with the injected clock.
- The lazy-text re-entrancy test passes on cp311 and cp314t.
- `decode_response` on the pinned `sendMessage` response returns a `Message` whose `.bot` is the given bot. The
  B-02 workload for it runs.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Always multipart (aiogram_rust) | A JSON body is smaller and faster when there are no files | 05 §2.1, 13 §4 |
| `timedelta` as seconds | A bug: temporary restrictions would become permanent | PD-11 |
| A Rust HTTP client (reqwest / tokio) | +40–80 µs per request, fork/proxy/SSL losses | 05 §3, 13 §2 |
| Session JSON hooks routing wire encoding | The wire always uses the Rust codec | PD-08 |
| User subclasses of method classes | Not supported; use `bot.call` | D96 |
| A new `TelegramDecodeError` | Keep `ClientDecodeError` + `.raw` | PD-29 |

## Validation

```bash
cargo fmt --all --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
make dev
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Inputs: B-14 envelope, B-04 / B-05 / B-06 types and views, B-07 binding; A-04 pinned request inputs; A-09
  request / response oracle; the B-02 fake Bot API.
- Outputs: the encoder / decoder API shape and value-writer rules that D-07 / D-08 / D-09 generalise; the render-hook
  call-out contract for D-10; the golden method file for C-20.
- Can run in parallel with B-08, B-10 and B-11.

## Notes
