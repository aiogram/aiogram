# D-09 — Response decoder: `Response[T]` without pydantic, `getUpdates` per-update isolation

| Field | Value |
|---|---|
| Status | `todo` |
| Story | D — Client & wire |
| Target branch | `dev-4.x` |
| Depends on | [B-01](../B-spike/B-01-crate-maturin-skeleton.md), [B-09](../B-spike/B-09-sendmessage-encoder-response.md), [B-13](../B-spike/B-13-gate-run-and-decision.md), [C-19](../C-butcher/C-19-rust-forward-compat-emitter.md), [C-20](../C-butcher/C-20-rust-methods-shortcuts-emitter.md), [D-02](D-02-exceptions-error-reason-restarting-removal.md), [C-18](../C-butcher/C-18-rust-type-emitter.md), [B-14](../B-spike/B-14-unions-envelope-batch-decode.md) |
| Blocks | [D-11](D-11-session-on-new-codec.md), [D-13](D-13-raw-bot-call-raw-method.md), [D-15](D-15-request-response-differential-cases.md), [E-14](../E-runtime/E-14-feed-paths-forward-compat-dispatch.md), [E-15](../E-runtime/E-15-poller.md), [E-16](../E-runtime/E-16-webhook-core-aiohttp-sources.md) |
| Gate-conditional | yes (assumes the milestone B gate passes, D104; re-validate after B-13) |
| Decisions | D10, D103, D107, R04, R07, PD-29, 13 B22/B24 |
| Sources | [05-network.md §2.2](../../research/05-network.md), [10-forward-compatibility.md §3](../../research/10-forward-compatibility.md), [01-models.md §3.1](../../research/01-models.md), [13-aiogram-rust-review.md §7 B22, B24](../../research/13-aiogram-rust-review.md), [19 §1 D107, §2 R04, §3](../../research/19-review-resolutions.md), [plans README §1 PD-29](../README.md) |
| Size | L (4–5 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

3.x: `BaseSession.check_response` builds `Response[method.__returning__]` (pydantic generic in
`aiogram/methods/base.py`) and `model_validate_json`s the body: 47 µs for a 979 B reply, 4 930 µs for `getUpdates`×100
(05 §1). One bad update fails the whole batch and polling gets stuck (10 §1). 4.0 decodes the envelope by borrowing
`result` as a raw slice (no tree, B22) straight into the method's return type, and decodes `getUpdates` element by
element with per-update isolation (10 Layer 2), copying each update's bytes out of the batch buffer (R04).

## Scope

**In:**
- `aiogram._core.decode.decode_response(method_cls, raw: bytes, bot) -> Ok(result) | Err(error_code, description,
  parameters)` (Python-visible shape decided below). Return type from the C-20 tables (`mediaTypes`, e.g.
  `MessageOrTrueResult`). Bot bound once at the root view (D103).
- `getUpdates`: tuple of `Update` (D106); each element decoded from its own slice; bytes copied out of the batch
  buffer (R04, normative per 19 §3.3); a failing element becomes an `Update` with `update_id` (always extracted) and
  `decode_error: UpdateDecodeError(path, message)` + `raw`.
- `aiogram._core.decode.decode_update(raw: bytes, bot) -> Update` for webhook / feed bodies (one update, not an
  envelope): same per-update isolation as `getUpdates` — an undecodable body becomes the `Update` shell with
  `update_id` (when extractable) and `decode_error` + `raw`; honours `DecodePolicy`. This plan owns the production
  entry point (B-05's spike entry point of the same name is superseded). Consumed by E-14
  (`runner.feed` / `runner.process` / `feed_raw_update`) and E-16 (webhook core).
- Layer 1 tolerance comes from B/C (Unknown variants, tolerant enums); this plan wires it into the response path.
- Layer 2 for ordinary methods: if the result cannot be decoded even with Layer 1, raise `ClientDecodeError` with
  `.raw` = the `result` bytes (PD-29, D-02).
- `DecodePolicy` (`"lenient"` default / `"strict"`) on `Bot` (and passed by the dispatcher for updates, E-14): strict
  raises on any Unknown or decode error. aiogram's own suite runs strict.
- Error envelope → `raise_for_error(...)` from D-02.
- Plain-Python `aiogram.methods.Response[T]` (`ok`, `result`, `description`, `error_code`, `parameters`) generic
  class, no pydantic, for code that still consumes it (custom `check_response` overrides, D-12). Remove the unused
  pydantic `aiogram.methods.base.Request` model (not in 11's removal list; add it to the registry).
- Bench on the real path (B24): `getUpdates`×100 through the envelope and a `sendMessage` response, A-04 pinned
  inputs.

**Out:**
- Routing of decode shells and the feed/webhook call sites → E-14 / E-16. Poller offset handling → E-15.
- Session wiring (`resp.read()` → decode) → D-11. `check_response` override compatibility → D-12.
- Unknown variant generation → C-19.

## Checklist

- [ ] Envelope parse with borrowed `result` slice (jiter `current_index`/`known_skip`/`slice_to_current`).
- [ ] Typed decode of `result` via C-20 return-type tables; containers → tuples (D106).
- [ ] `getUpdates` element-wise decode, byte copy, `UpdateDecodeError` with `update_id`.
- [ ] Decide the Python-visible return shape of `decode_response` (proposed default: returns the result on success;
      on `ok:false` returns a small `ApiError(error_code, description, parameters)` value that Python passes to
      `raise_for_error`, so Rust never constructs Python exceptions) — record in Notes and flag to owner.
- [ ] `decode_update(raw, bot)` for single webhook/feed bodies, sharing the per-update shell logic with `getUpdates`.
- [ ] `ClientDecodeError.raw` on Layer 2 method failures.
- [ ] `DecodePolicy` lenient/strict; repo test config uses strict.
- [ ] Plain `Response[T]`; remove pydantic `Request`.
- [ ] Bench (B24 paths) via B-02/A-05 harness.
- [ ] Tests (100% coverage of new code), incl. the 10 §1 reproduction
      (`getUpdates` with one valid message + one `chat_member` with status `"superadmin"`).
- [ ] Migration-registry entries (PD-13): `aiogram.methods.Response` is no longer a pydantic model;
      `aiogram.methods.Request` removed.
- [ ] Changelog fragments (`feature`: per-update isolation; `removal`: `Request`).

## Acceptance criteria

- The 10 §1 reproduction returns a 2-tuple: a normal `Update` and one whose `message`/`chat_member` decodes to
  `UnknownChatMember` (lenient); under strict it raises.
- A batch with one structurally broken update returns all others intact plus one `Update` carrying
  `decode_error` and the correct `update_id`.
- A retained single child of a 100-update batch does not keep the batch buffer alive (weakref/RSS test from B-11).
- `decode_update(raw, bot)` on a valid webhook body returns an `Update` bound to `bot`; on a body with a valid
  `update_id` and a broken payload it returns the shell with that `update_id` and `decode_error` (lenient) and raises
  `ClientDecodeError` under strict.
- `getMe` response decodes to `User` bound to the bot; `ok:false` with `retry_after` raises `TelegramRetryAfter`.
- Bench: `getUpdates`×100 per-update and `sendMessage` response no slower than B-09's gate numbers (±10%), median of 7.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Decode to a dict / JSON tree first | Extra allocation; B22 borrow is faster | 13 B22 |
| Fail the whole batch on one bad update (3.x) | Stalls polling forever | D10, 10 §1 |
| New `TelegramDecodeError` | No new classes | PD-29 |
| Keep pydantic `Response[T]` | pydantic is not a dependency | D14 |

## Validation

```bash
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
make dev
uv run pytest tests
uv run mypy aiogram
cargo xtask butcher check
make lint
make bench
```

## Workflow notes

- Inputs: B-09 response path prototype, C-19/C-20 tables, D-02 `raise_for_error`.
- Outputs: `decode_response` for D-11/D-13; `decode_update` for E-14/E-16; `getUpdates` tuple with decode-error updates for E-15 (Poller always
  advances the offset) and E-14 (unknown_update routing, `phase=DECODE`).
- Parallel with D-07/D-08.

## Notes
